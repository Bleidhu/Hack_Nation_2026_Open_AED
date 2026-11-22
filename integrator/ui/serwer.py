"""Lokalny serwer UI integratora. Nasłuch **tylko** na 127.0.0.1, wyłącznie biblioteka standardowa.

    python integrator/ui/serwer.py [--port 8765]

Punkty końcowe (JSON, pliki w base64):
- POST /api/import    – importer.run() + raport duplikatów; CSV wynikowy tylko przy --cel portal,
                        gdy licencja przechodzi kontrolę (zadanie 03);
- POST /api/porownaj  – porównanie wykazu z OSM (zadanie 07), z oznaczeniem ODbL;
- POST /api/dodaj     – sprawdzenie rekordu (zadanie 08) i treść pliku po dopisaniu, do pobrania.

Serwer nie zapisuje nic na dysku: cała praca w pamięci, wynik wraca jako odpowiedź.
"""
from __future__ import annotations

import argparse
import base64
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

INTEGRATOR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(INTEGRATOR))

import importer  # noqa: E402
from adaptery.osm import wczytaj as osm_wczytaj  # noqa: E402
from rdzen.duplikaty import PROMIEN_DOMYSLNY, znajdz_kandydatow  # noqa: E402
from rdzen.licencje import LicencjaBlad  # noqa: E402
from rdzen.mapowanie import PRESETS, apply_mapping  # noqa: E402
from rdzen.porownanie import porownaj  # noqa: E402
from rdzen.rekord import RekordBlad, scal_tekst, sprawdz_rekord, zbuduj  # noqa: E402
from rdzen.wejscie import read_input  # noqa: E402

LIMIT_BAJTOW = 10 * 1024 * 1024  # rozmiar zdekodowanego pliku
HOST = "127.0.0.1"
INDEX = Path(__file__).resolve().parent / "index.html"


def _plik(req: dict, klucz: str) -> tuple:
    """(bytes, nazwa) z pola `klucz` base64; brak pola = (None, '')."""
    b64 = req.get(klucz)
    if not b64:
        return None, ""
    data = base64.b64decode(b64)
    if len(data) > LIMIT_BAJTOW:
        raise Blad(413, f"plik zbyt duży (limit {LIMIT_BAJTOW // 1024 // 1024} MB po zdekodowaniu)")
    return data, req.get(klucz + "_nazwa", "plik")


class Blad(Exception):
    def __init__(self, kod: int, komunikat: str):
        super().__init__(komunikat)
        self.kod, self.komunikat = kod, komunikat


def api_import(req: dict) -> dict:
    data, nazwa = _plik(req, "plik")
    if data is None:
        raise Blad(400, "brak pliku")
    cel = req.get("cel") or "portal"
    try:
        res = importer.run(data, nazwa, req.get("mapowanie"), preset=req.get("preset") or None,
                           licencja=req.get("licencja") or None, cel=cel)
    except LicencjaBlad as e:
        raise Blad(400, f"Odmowa: {e}. Dla użytku lokalnego wybierz cel „lokalny”.") from e
    except ValueError as e:  # nierozpoznany format itp.
        raise Blad(400, str(e)) from e
    r = res["raport"]
    dobre = [rec for rec in res["rekordy"] if rec.get("__status") != "odrzucony"]
    out = {"format": res["format"], "kolumny_zrodla": res["kolumny_zrodla"], "mapowanie": res["mapowanie"],
           "raport": r, "pochodzenie": res["pochodzenie"], "licencja_zrodla": res["licencja_zrodla"],
           "liczba_wierszy": r["liczba_wierszy"],
           "csv": importer.to_csv(dobre) if cel == "portal" and res["pochodzenie"]["do_publikacji"] else None,
           "duplikaty": znajdz_kandydatow(dobre, promien=req.get("promien") or PROMIEN_DOMYSLNY)}
    return out


def api_porownaj(req: dict) -> dict:
    wykaz, _ = _plik(req, "wykaz")
    osm, osm_nazwa = _plik(req, "osm")
    if wykaz is None or osm is None:
        raise Blad(400, "podaj oba pliki: wykaz AED (CSV z portalu) i plik OSM")
    try:
        _, wykaz_rows, _ = read_input(wykaz, "wykaz.csv")
        osm_rows, _ = osm_wczytaj(osm, osm_nazwa or "osm.json")
        return porownaj(wykaz_rows, apply_mapping(osm_rows, PRESETS["osm"]),
                        promien=req.get("promien") or PROMIEN_DOMYSLNY)
    except ValueError as e:
        raise Blad(400, str(e)) from e


def api_dodaj(req: dict) -> dict:
    plik, _ = _plik(req, "plik")  # pliku może nie być – wtedy tworzony jest nowy CSV
    try:
        stare = plik.decode("utf-8") if plik else None
        istniejace = read_input(plik, "aed.csv")[1] if plik else []
        pola = {k: v for k, v in (req.get("pola") or {}).items() if str(v).strip() != ""}
        rec = zbuduj(pola, prefiks=req.get("prefiks") or "AED",
                    istniejace_id={r.get("id_zrodlowe", "") for r in istniejace})
    except (RekordBlad, ValueError) as e:
        raise Blad(400, str(e)) from e
    wynik = sprawdz_rekord(rec, istniejace)
    out = {"rekord": {f: rec.get(f, "") for f in ("id_zrodlowe", "nazwa_lokalizacji", "miejscowosc")},
           "bledy": wynik["bledy"], "kandydaci": wynik["kandydaci"], "nowy_plik": None}
    if wynik["bledy"]:
        return out
    if wynik["kandydaci"] and not req.get("wymus"):
        out["wymaga_potwierdzenia"] = True
        return out
    out["nowy_plik"] = scal_tekst(stare, rec)
    return out


PUNKTY = {"/api/import": api_import, "/api/porownaj": api_porownaj, "/api/dodaj": api_dodaj}


class Handler(BaseHTTPRequestHandler):
    server_version = "IntegratorAED/1.0"

    def log_message(self, fmt, *args):  # cichy log: jedna linia, bez tracebacków
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _odpowiedz(self, kod: int, typ: str, tresc: bytes):
        self.send_response(kod)
        self.send_header("Content-Type", typ)
        self.send_header("Content-Length", str(len(tresc)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(tresc)

    def _json(self, kod: int, obj: dict):
        self._odpowiedz(kod, "application/json; charset=utf-8", json.dumps(obj, ensure_ascii=False).encode("utf-8"))

    def do_GET(self):  # noqa: N802
        if self.path in ("/", "/index.html"):
            self._odpowiedz(200, "text/html; charset=utf-8", INDEX.read_bytes())
        else:
            self._json(404, {"blad": "nie ma takiej strony"})

    def do_POST(self):  # noqa: N802
        if self.path not in PUNKTY:
            self._json(404, {"blad": "nie ma takiego punktu końcowego"})
            return
        try:
            n = int(self.headers.get("Content-Length") or 0)
            if n > 3 * LIMIT_BAJTOW:  # base64 ~4/3 rozmiaru
                raise Blad(413, "żądanie zbyt duże")
            req = json.loads(self.rfile.read(n) or b"{}")
            wynik = PUNKTY[self.path](req)
            self._json(200, wynik)
        except Blad as e:
            self._json(e.kod, {"blad": e.komunikat})
        except json.JSONDecodeError as e:
            self._json(400, {"blad": f"zły JSON: {e}"})
        except Exception as e:  # noqa: BLE001
            self._json(500, {"blad": f"nieoczekiwany błąd: {e}"})


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--port", type=int, default=8765)
    a = ap.parse_args()
    httpd = ThreadingHTTPServer((HOST, a.port), Handler)
    print(f"Integrator AED działa lokalnie: http://{HOST}:{a.port}/  (Ctrl+C kończy)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nkonczę")


if __name__ == "__main__":
    main()
