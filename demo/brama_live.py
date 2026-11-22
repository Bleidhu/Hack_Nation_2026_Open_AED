"""Brama wersji live: cały portal, prototyp i serwer dostawcy pod JEDNYM adresem ngrok. Tylko biblioteka standardowa.

    python demo/brama_live.py [--port 8090] [--dostawca https://127.0.0.1:8098] [--bez-admina]

Darmowe konto ngrok ma jedną domenę (*.ngrok-free.dev); kilka tuneli w jednej sesji dostaje TEN SAM adres i ngrok
rozkłada między nie ruch losowo. Dlatego ngrok kieruje cały ruch do tej bramy (http://127.0.0.1:8090), a brama
rozdziela go po ścieżce:

    /dostawca/...          serwer dostawcy (demo/serwer_zewnetrzny.py, domyślnie https://127.0.0.1:8098)
    /demo/, /format_danych/, /branding/, /prezentacja/, kilka plików .md
                           pliki statyczne z repozytorium (ten sam układ co GitHub Pages; bez demo/.cert i plików ukrytych)
    /admin/...             panel administracyjny (admin.mcod.local; /admin/ to strona główna panelu)
    /login/, /datasets/, /resources/, /users/, ...  pozostałe ścieżki panelu (Django generuje je od korzenia)
    /live/                 strona startowa z odnośnikami do wszystkiego
    wszystko inne          frontend portalu (mcod.local), w tym /api/... (frontend przekazuje je do API)

Portal w Dockerze nie jest zmieniany. Brama łączy się z nginx portalu (https://127.0.0.1:443) i podstawia nagłówek
Host (mcod.local albo admin.mcod.local), a w odpowiedziach:
- zamienia adresy https://(api.|admin.|cms.)mcod.local na publiczny adres (API pod /api, CMS pod /cms),
- usuwa atrybut Domain=mcod.local z ciasteczek (inaczej przeglądarka odrzuci sesję panelu),
- przepisuje Referer i Origin na adres lokalny (kontrola CSRF Django porównuje je z nagłówkiem Host),
- nie przepuszcza konsoli debugera Werkzeug (?__debugger__) i zamienia strony błędów trybu DEBUG na zwykły komunikat.
Pliki danych (CSV, XLSX, obrazy) przechodzą bez zmian, bajt w bajt.
"""
import argparse
import base64
import gzip
import html
import http.client
import json
import mimetypes
import os
import re
import socket
import ssl
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
NGINX = ("127.0.0.1", 443)
KONIEC_LINII = chr(13) + chr(10)
VITE = ("127.0.0.1", 4200)  # serwer deweloperski frontendu (kontener mcod-frontend); tylko dla WebSocket HMR
HOST_FRONT = "mcod.local"
HOST_ADMIN = "admin.mcod.local"
HOST_API = "api.mcod.local"
DOMYSLNY_ZBIOR, DOMYSLNY_ZASOB = 4216, 40258

# Pierwsze segmenty ścieżek panelu (mcod admin, urls.py: aplikacje panelu i widoki pomocnicze). Frontend Angulara
# używa ścieżek z prefiksem języka (/pl/..., /en/...), więc te nazwy z nim nie kolidują.
ADMIN_SEGMENTY = frozenset(
    """login logout password_change jsi18n i18n nested_admin ckeditor organization-type dataset-license-labels r
    django_celery_results constance schedules organizations categories tags datasets resources users histories
    searchhistories reports alerts suggestions newsletter harvester laboratory academy guides special_signs showcases
    submissions""".split()
)
STATYCZNE_KATALOGI = frozenset({"demo", "format_danych", "branding", "prezentacja"})
STATYCZNE_PLIKI = frozenset(
    {"README.md", "INSTRUKCJA_DLA_JURY.md", "DODATKOWE_INFORMACJE.md", "ZMIANY_W_PORTALU.md", "WERSJA_LIVE.md",
     "portal/backend/CHANGELOG.md"}
)
WYKLUCZONE_SEGMENTY = frozenset({"__pycache__", "archiwum"})
HOP = frozenset({"connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailer", "trailers",
                 "transfer-encoding", "upgrade", "content-length", "accept-encoding", "host", "expect",
                 "x-forwarded-proto", "x-forwarded-host", "x-forwarded-port"})
TEKSTOWE = ("text/html", "application/json", "application/vnd.api+json", "text/javascript", "application/javascript",
            "application/xml", "text/xml", "application/ld+json")
TYPY = {  # jawnie: na Windows mimetypes czyta rejestr i potrafi zwrócić np. text/plain dla .js
    ".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8", ".md": "text/plain; charset=utf-8", ".txt": "text/plain; charset=utf-8",
    ".py": "text/plain; charset=utf-8", ".csv": "text/csv; charset=utf-8", ".xml": "application/xml; charset=utf-8",
    ".xsd": "application/xml; charset=utf-8", ".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg",
    ".pdf": "application/pdf", ".mp4": "video/mp4", ".webm": "video/webm", ".vtt": "text/vtt; charset=utf-8",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".geojson": "application/geo+json", ".ttl": "text/turtle; charset=utf-8", ".jsonld": "application/ld+json",
}
MAKS_PRZEPISANIE = 40 * 1024 * 1024
ADRES_LOKALNY = re.compile(rb"(https?:)?(//|\\/\\/)(admin\.|api\.|cms\.)?mcod\.local(?![\w.-])")
DOMENA_CIASTKA = re.compile(r";\s*domain=\.?([\w-]+\.)?mcod\.local", re.IGNORECASE)
STRONA_BLEDU = (
    "<!doctype html><html lang=\"pl\"><meta charset=\"utf-8\"><title>Błąd {kod}</title>"
    "<body style=\"font-family:sans-serif;max-width:40rem;margin:2rem auto;padding:0 1rem\"><h1>Błąd {kod}</h1>"
    "<p>{opis}</p><p><a href=\"/live/\">Strona startowa wersji live</a></p></body></html>"
)


def trasa(sciezka, referer_sciezka=""):
    """Zwraca (rodzaj, ścieżka_docelowa). Rodzaje: dostawca, statyczne, live, admin, front, przekieruj."""
    seg = sciezka.lstrip("/").split("/", 1)[0]
    if sciezka == "/dostawca":
        return "przekieruj", "/dostawca/"
    if sciezka.startswith("/dostawca/"):
        return "dostawca", sciezka[len("/dostawca"):]
    if sciezka in ("/live", "/prototyp", "/prototyp/"):
        return "przekieruj", "/live/" if sciezka == "/live" else "/demo/index.html"
    if sciezka == "/live/":
        return "live", sciezka
    if seg in STATYCZNE_KATALOGI or sciezka.lstrip("/") in STATYCZNE_PLIKI:
        return "statyczne", sciezka
    if sciezka == "/admin":
        return "przekieruj", "/admin/"
    if sciezka.startswith("/admin/"):
        return "admin", sciezka[len("/admin"):]
    if seg in ADMIN_SEGMENTY or seg.endswith("-autocomplete"):
        return "admin", sciezka
    if sciezka == "/" and referer_sciezka:
        rseg = referer_sciezka.lstrip("/").split("/", 1)[0]
        if referer_sciezka.startswith("/admin/") or rseg in ADMIN_SEGMENTY:
            return "admin", "/"  # np. „Strona główna” w okruszkach panelu
    return "front", sciezka


def przepisz_adresy(tresc, publiczny):
    """https://api.mcod.local/x -> {publiczny}/api/x itd. Obsługuje też zapis z ukośnikami ucieczki JSON (https:\\/\\/)."""
    pub = publiczny.encode("ascii")

    def zamien(m):
        sufiks = {b"api.": b"/api", b"cms.": b"/cms"}.get(m.group(3) or b"", b"")
        wynik = pub + sufiks
        if m.group(2) == b"\\/\\/":
            wynik = wynik.replace(b"/", b"\\/")
        return wynik

    return ADRES_LOKALNY.sub(zamien, tresc)


def plik_statyczny(sciezka):
    """Ścieżka URL -> plik w repozytorium albo None (poza listą, ukryty, wyjście poza katalog)."""
    wzgledna = unquote(sciezka).lstrip("/")
    czesci = [c for c in wzgledna.split("/") if c]
    if not czesci or any(c.startswith(".") or c in WYKLUCZONE_SEGMENTY or "\\" in c for c in czesci):
        return None
    if czesci[0] not in STATYCZNE_KATALOGI and "/".join(czesci) not in STATYCZNE_PLIKI:
        return None
    plik = (ROOT / Path(*czesci)).resolve()
    try:
        plik.relative_to(ROOT)
    except ValueError:
        return None
    if plik.is_dir():
        plik = plik / "index.html"
    return plik if plik.is_file() else None


class PolaczenieTLS(http.client.HTTPConnection):
    """HTTPS do nginx portalu na 127.0.0.1 z SNI wybranej domeny; certyfikat lokalny jest samopodpisany."""

    def __init__(self, adres, port, sni, timeout=300):
        super().__init__(adres, port, timeout=timeout)
        self._sni = sni

    def connect(self):
        super().connect()
        kontekst = ssl.create_default_context()
        kontekst.check_hostname = False
        kontekst.verify_mode = ssl.CERT_NONE
        self.sock = kontekst.wrap_socket(self.sock, server_hostname=self._sni)


class Brama(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "brama-live"
    sys_version = ""

    # --- pomocnicze -------------------------------------------------------------------------------------------
    def publiczny(self):
        host = self.headers.get("X-Forwarded-Host") or self.headers.get("Host") or f"127.0.0.1:{self.server.server_port}"
        proto = self.headers.get("X-Forwarded-Proto") or "http"
        return f"{proto}://{host.split(',')[0].strip()}"

    def wyslij(self, kod, tresc=b"", typ="text/html; charset=utf-8", naglowki=(), skompresuj=True):
        if skompresuj and len(tresc) > 1024 and "gzip" in (self.headers.get("Accept-Encoding") or ""):
            tresc = gzip.compress(tresc, 6)
            naglowki = list(naglowki) + [("Content-Encoding", "gzip"), ("Vary", "Accept-Encoding")]
        self.send_response(kod)
        if typ:
            self.send_header("Content-Type", typ)
        for k, v in naglowki:
            self.send_header(k, v)
        bez_tresci = self.command == "HEAD" or kod in (204, 304) or 100 <= kod < 200
        self.send_header("Content-Length", "0" if kod in (204, 304) else str(len(tresc)))
        self.end_headers()
        if not bez_tresci:
            self.wfile.write(tresc)

    def blad(self, kod, opis):
        self.wyslij(kod, STRONA_BLEDU.format(kod=kod, opis=html.escape(opis)).encode("utf-8"))

    def czytaj_cialo(self):
        if "chunked" in (self.headers.get("Transfer-Encoding") or "").lower():
            czesci = []
            while True:
                rozmiar = int(self.rfile.readline().split(b";")[0].strip() or b"0", 16)
                if rozmiar == 0:
                    while self.rfile.readline() not in (b"\r\n", b"\n", b""):
                        pass
                    return b"".join(czesci)
                czesci.append(self.rfile.read(rozmiar))
                self.rfile.readline()
        dlugosc = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(dlugosc) if dlugosc > 0 else None

    # --- obsługa ----------------------------------------------------------------------------------------------
    def obsluz(self):
        start = time.time()
        czesci = urlsplit(self.path)
        sciezka = czesci.path or "/"
        if "__debugger__" in self.path:
            self.blad(403, "Konsola debugera jest niedostępna w wersji live.")
            return
        referer = self.headers.get("Referer") or ""
        rodzaj, cel = trasa(sciezka, urlsplit(referer).path if referer.startswith(self.publiczny()) else "")
        if rodzaj == "admin" and self.server.bez_admina:
            self.blad(403, "Panel administracyjny jest wyłączony w tej wersji live.")
            return
        if rodzaj == "admin" and self.server.admin_auth and self.headers.get("Authorization") != self.server.admin_auth:
            self.wyslij(401, STRONA_BLEDU.format(kod=401, opis="Panel wymaga hasła dostępu.").encode("utf-8"),
                        naglowki=[("WWW-Authenticate", 'Basic realm="Panel portalu (wersja live)", charset="UTF-8"')])
            return
        zapytanie = ("?" + czesci.query) if czesci.query else ""
        if rodzaj == "przekieruj":
            self.wyslij(302, b"", naglowki=[("Location", cel + zapytanie)])
        elif rodzaj == "live":
            self.wyslij(200, self.strona_live().encode("utf-8"))
        elif rodzaj == "statyczne":
            self.statyczne(cel)
        elif rodzaj == "dostawca":
            adres = urlsplit(self.server.dostawca)
            self.przekaz(adres.hostname, adres.port or (443 if adres.scheme == "https" else 80), adres.scheme == "https",
                         None, cel + zapytanie, rodzaj)
        elif rodzaj == "front" and (self.headers.get("Upgrade") or "").lower() == "websocket":
            self.tunel_ws(cel + zapytanie)
        else:
            vhost = HOST_ADMIN if rodzaj == "admin" else HOST_FRONT
            self.przekaz(NGINX[0], NGINX[1], True, vhost, cel + zapytanie, rodzaj)
        if self.server.dziennik:
            print(f"{time.strftime('%H:%M:%S')} {self.command} {self.path[:150]} -> {rodzaj} ({time.time() - start:.2f} s)",
                  flush=True)

    do_GET = do_POST = do_PUT = do_PATCH = do_DELETE = do_OPTIONS = do_HEAD = obsluz  # noqa: N815

    def statyczne(self, sciezka):
        if self.command not in ("GET", "HEAD"):
            self.blad(405, "Pliki statyczne są tylko do odczytu.")
            return
        plik = plik_statyczny(sciezka)
        if plik is None:
            self.blad(404, "Nie ma takiego pliku w udostępnionej części repozytorium.")
            return
        if sciezka.endswith("/") is False and (ROOT / unquote(sciezka).lstrip("/")).is_dir():
            self.wyslij(302, b"", naglowki=[("Location", sciezka + "/")])
            return
        typ = TYPY.get(plik.suffix.lower()) or mimetypes.guess_type(plik.name)[0] or "application/octet-stream"
        rozmiar = plik.stat().st_size
        tekstowy = typ.startswith(("text/", "application/json", "application/xml", "image/svg"))
        if tekstowy and rozmiar < MAKS_PRZEPISANIE:
            self.wyslij(200, plik.read_bytes(), typ, [("Cache-Control", "no-cache")])
            return
        self.send_response(200)
        self.send_header("Content-Type", typ)
        self.send_header("Content-Length", str(rozmiar))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        if self.command == "GET":
            with plik.open("rb") as f:
                while True:
                    kawalek = f.read(256 * 1024)
                    if not kawalek:
                        break
                    self.wfile.write(kawalek)

    def tunel_ws(self, sciezka):
        """WebSocket klienta Vite (HMR) wprost do serwera frontendu; nginx portalu nie przekazuje nagłówka Upgrade,
        a bez tego klient Vite próbuje potem połączyć się z wss://localhost:4000 (błąd w konsoli przeglądarki)."""
        try:
            gora = socket.create_connection(VITE, timeout=10)
        except OSError:
            self.blad(502, "Serwer frontendu nie odpowiada.")
            return
        linie = [f"{self.command} {sciezka} HTTP/1.1"]
        for k, v in self.headers.items():
            kl = k.lower()
            if kl in ("host", "origin") or kl.startswith(("ngrok-", "x-forwarded")):
                continue
            linie.append(f"{k}: {v}")
        linie += [f"Host: {HOST_FRONT}", f"Origin: https://{HOST_FRONT}"]
        gora.sendall((KONIEC_LINII.join(linie) + KONIEC_LINII * 2).encode("latin-1"))
        gora.settimeout(None)
        self.connection.settimeout(None)

        def pompa(z, do):
            try:
                while True:
                    dane = z.recv(65536)
                    if not dane:
                        break
                    do.sendall(dane)
            except OSError:
                pass
            finally:
                for gniazdo in (z, do):
                    try:
                        gniazdo.shutdown(socket.SHUT_RDWR)
                    except OSError:
                        pass

        watek = threading.Thread(target=pompa, args=(gora, self.connection), daemon=True)
        watek.start()
        pompa(self.connection, gora)
        watek.join(5)
        gora.close()
        self.close_connection = True

    def przekaz(self, adres, port, tls, vhost, sciezka, rodzaj):
        pub = self.publiczny()
        pub_host = urlsplit(pub).netloc
        lokalny = f"https://{vhost}" if vhost else pub
        naglowki = []
        for k, v in self.headers.items():
            kl = k.lower()
            if kl in HOP or kl.startswith("ngrok-"):
                continue
            if kl in ("referer", "origin") and vhost and v.startswith(pub):
                v = lokalny + v[len(pub):]
                if rodzaj == "admin" and kl == "referer" and urlsplit(v).path.startswith("/admin/"):
                    v = lokalny + v[len(lokalny) + len("/admin"):]
            if kl == "authorization" and rodzaj == "admin" and self.server.admin_auth:
                continue
            naglowki.append((k, v))
        naglowki.append(("Host", vhost or pub_host))
        naglowki.append(("Accept-Encoding", "identity"))
        if not vhost:
            naglowki.append(("X-Forwarded-Proto", urlsplit(pub).scheme))
        cialo = self.czytaj_cialo()
        try:
            if tls:
                polaczenie = PolaczenieTLS(adres, port, vhost or adres)
            else:
                polaczenie = http.client.HTTPConnection(adres, port, timeout=300)
            polaczenie.putrequest(self.command, sciezka, skip_host=True, skip_accept_encoding=True)
            for k, v in naglowki:
                polaczenie.putheader(k, v)
            if cialo is not None:
                polaczenie.putheader("Content-Length", str(len(cialo)))
            polaczenie.endheaders(cialo)
            odp = polaczenie.getresponse()
        except (OSError, http.client.HTTPException) as e:
            self.blad(502, f"Usługa lokalna nie odpowiada ({rodzaj}: {e.__class__.__name__}). Wersja live może być w trakcie restartu.")
            return
        try:
            self.odeslij(odp, pub, rodzaj)
        finally:
            polaczenie.close()

    def odeslij(self, odp, pub, rodzaj):
        typ = odp.getheader("Content-Type") or ""
        kodowanie = (odp.getheader("Content-Encoding") or "").lower()
        naglowki = []
        for k, v in odp.getheaders():
            kl = k.lower()
            if kl in HOP:
                continue
            if kl == "location":
                v = przepisz_adresy(v.encode("latin-1"), pub).decode("latin-1")
                if rodzaj == "dostawca" and v.startswith("/"):
                    v = "/dostawca" + v
                if rodzaj == "admin":
                    cz = urlsplit(v)
                    if cz.path == "/" and (not cz.netloc or v.startswith(pub)):
                        v = "/admin/" + (("?" + cz.query) if cz.query else "")
            elif kl == "set-cookie":
                v = DOMENA_CIASTKA.sub("", v)
            naglowki.append((k, v))
        dlugosc = odp.getheader("Content-Length")
        tekstowy = typ.split(";")[0].strip().lower() in TEKSTOWE and kodowanie in ("", "identity")
        if tekstowy and (dlugosc is None or int(dlugosc) <= MAKS_PRZEPISANIE):
            tresc = odp.read()
            if rodzaj == "dostawca":
                # link do CSV serwer dostawcy składa z nagłówka Host; dokładamy prefiks /dostawca
                tresc = tresc.replace(pub.encode() + b"/", pub.encode() + b"/dostawca/")
                tresc = tresc.replace(("http://" + urlsplit(pub).netloc + "/").encode(),
                                      ("http://" + urlsplit(pub).netloc + "/dostawca/").encode())
            else:
                tresc = przepisz_adresy(tresc, pub)
            if rodzaj == "admin" and typ.startswith("text/html"):
                tresc = tresc.replace(b'href="/"', b'href="/admin/"')
            if odp.status >= 400 and (b"DEBUG = True" in tresc or b"Werkzeug Debugger" in tresc or b"__debugger__" in tresc):
                tresc = STRONA_BLEDU.format(kod=odp.status, opis="Usługa portalu zwróciła błąd.").encode("utf-8")
                naglowki = [(k, v) for k, v in naglowki if k.lower() != "content-type"]
                typ = "text/html; charset=utf-8"
            naglowki = [(k, v) for k, v in naglowki if k.lower() not in ("content-type", "content-encoding")]
            self.wyslij(odp.status, tresc, typ, naglowki)
            return
        # strumień bez zmian (pliki danych, obrazy, duże odpowiedzi)
        self.send_response(odp.status)
        for k, v in naglowki:
            self.send_header(k, v)
        bez_tresci = self.command == "HEAD" or odp.status in (204, 304) or odp.status < 200
        if dlugosc is not None:
            self.send_header("Content-Length", dlugosc)
            self.end_headers()
            if not bez_tresci:
                self.kopiuj(odp, None)
            return
        if bez_tresci:
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()
        self.kopiuj(odp, True)

    def kopiuj(self, odp, chunked):
        while True:
            kawalek = odp.read(256 * 1024)
            if not kawalek:
                break
            if chunked:
                self.wfile.write(b"%x\r\n%s\r\n" % (len(kawalek), kawalek))
            else:
                self.wfile.write(kawalek)
        if chunked:
            self.wfile.write(b"0\r\n\r\n")

    def identyfikatory(self):
        """Zbiór i zasób Wykazu AED z /aed-aggregated (API portalu); przy błędzie wartości domyślne."""
        try:
            p = PolaczenieTLS(NGINX[0], NGINX[1], HOST_API, timeout=10)
            p.request("GET", "/1.4/aed-aggregated", headers={"Host": HOST_API, "Accept": "application/json"})
            dane = json.loads(p.getresponse().read().decode("utf-8"))
            p.close()
            return int(dane["dataset_id"]), int(dane["resource_id"])
        except Exception:  # noqa: BLE001 - strona startowa ma działać także bez API
            return DOMYSLNY_ZBIOR, DOMYSLNY_ZASOB

    def strona_live(self):
        z, r = self.identyfikatory()
        pozycje = [
            ("Portal (frontend)", [("Strona główna portalu", "/pl")]),
            ("Wykaz AED w portalu", [
                ("Zbiór „Wykaz defibrylatorów AED”", f"/pl/dataset/{z}"),
                ("Zasób zbiorczy: tabela", f"/pl/dataset/{z}/resource/{r}/table"),
                ("Zasób zbiorczy: mapa", f"/pl/dataset/{z}/resource/{r}/map"),
            ]),
            ("API portalu", [
                ("Dane zasobu zbiorczego (JSON:API)", f"/api/resources/{r}/data?per_page=20"),
                ("Informacja o Wykazie AED (/aed-aggregated)", "/api/aed-aggregated"),
                ("Metadane zbioru", f"/api/datasets/{z}"),
            ]),
            ("Panel administracyjny", [("Logowanie do panelu", "/admin/")]),
            ("Prototyp i dokumenty", [
                ("Klikalny prototyp (demo/index.html)", "/demo/index.html"),
                ("Instrukcja dla jury", "/INSTRUKCJA_DLA_JURY.md"),
                ("Wzorcowy zakres danych (XLSX)", "/format_danych/wzorcowy_zakres_danych.xlsx"),
            ]),
            ("Serwer dostawcy (dane fikcyjne)", [
                ("Opis zbioru w XML", "/dostawca/opis.xml"),
                ("Plik CSV", "/dostawca/aed.csv"),
                ("Stan serwera", "/dostawca/stan"),
            ]),
        ]
        sekcje = []
        for tytul, linki in pozycje:
            li = "".join(f'<li><a href="{html.escape(u)}">{html.escape(n)}</a> <code>{html.escape(u)}</code></li>'
                         for n, u in linki)
            sekcje.append(f"<h2>{html.escape(tytul)}</h2><ul>{li}</ul>")
        return (
            "<!doctype html><html lang=\"pl\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"><title>Wykaz AED: wersja live</title>"
            "<style>body{font-family:system-ui,sans-serif;max-width:46rem;margin:0 auto;padding:1rem;line-height:1.5;"
            "color:#1a1a1a;background:#fff}a{color:#0b4ea2}code{font-size:.85em;color:#444;word-break:break-all}"
            "li{margin:.35rem 0}@media (prefers-color-scheme:dark){body{background:#121212;color:#eee}a{color:#8cb8ff}"
            "code{color:#bbb}}</style></head><body><main><h1>Wykaz AED: wersja live</h1>"
            "<p>Zmodyfikowany portal dane.gov.pl uruchomiony w Dockerze u zespołu, wystawiony tymczasowo przez tunel ngrok. "
            "Działa tylko wtedy, gdy zespół ma włączony komputer z tunelem. Wszystkie dowody są także plikami w repozytorium.</p>"
            + "".join(sekcje) + "</main></body></html>"
        )

    def log_message(self, fmt, *args):
        pass


class Serwer(ThreadingHTTPServer):
    daemon_threads = True
    request_queue_size = 256  # ngrok otwiera wiele połączeń naraz; domyślne 5 dawało odmowy połączeń (502 w ngroku)
    allow_reuse_address = os.name != "nt"


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Brama wersji live: portal, prototyp i serwer dostawcy pod jednym adresem.")
    ap.add_argument("--port", type=int, default=8090)
    ap.add_argument("--host", default="127.0.0.1", help="adres nasłuchu (domyślnie tylko lokalnie; ruch z zewnątrz daje ngrok)")
    ap.add_argument("--dostawca", default="https://127.0.0.1:8098", help="adres serwera demo/serwer_zewnetrzny.py")
    ap.add_argument("--bez-admina", action="store_true", help="nie udostępniaj panelu administracyjnego (403)")
    ap.add_argument("--admin-auth-env", default="BRAMA_ADMIN_AUTH",
                    help="zmienna środowiskowa z „login:hasło”; gdy ustawiona, panel wymaga dodatkowego hasła (Basic)")
    ap.add_argument("--cicho", action="store_true", help="bez dziennika żądań na konsoli")
    a = ap.parse_args(argv)
    serwer = Serwer((a.host, a.port), Brama)
    serwer.dostawca = a.dostawca.rstrip("/")
    serwer.bez_admina = a.bez_admina
    auth = os.environ.get(a.admin_auth_env, "")
    serwer.admin_auth = ("Basic " + base64.b64encode(auth.encode("utf-8")).decode("ascii")) if ":" in auth else None
    serwer.dziennik = not a.cicho
    print(f"Brama live: http://{a.host}:{a.port}/live/  (dostawca: {serwer.dostawca}; panel: "
          f"{'wyłączony' if a.bez_admina else ('z hasłem Basic' if serwer.admin_auth else 'włączony')})", flush=True)
    try:
        serwer.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    socket.setdefaulttimeout(None)
    sys.exit(main())
