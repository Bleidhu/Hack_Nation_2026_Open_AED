"""Zewnętrzny serwer dostawcy (demo): wystawia opis zbioru AED w XML, plik CSV i schematy XSD. Dane fikcyjne.

    python demo/serwer_zewnetrzny.py [--port 8099] [--host 0.0.0.0] [--https]

Adresy (wszystkie odpowiadają kodem 200 i bez opóźnień):
    /opis.xml             opis zbioru zgodny z XSD: metadane, link do /aed.csv i suma md5 (źródło poprawne)
    /opis_bledny_md5.xml  opis zgodny z XSD, ale md5 nie pasuje do CSV (portal odrzuca import)
    /opis_bledny_xsd.xml  opis niezgodny z XSD (portal odrzuca import)
    /aed.csv              dane: CSV zgodny ze wzorcem AED v2
    /aed_opis_zbioru.xsd  /aed_punkty.xsd   schematy
    /stan                 stan serwera (JSON), do sprawdzenia, że serwer żyje
    /aed.xml              wariant dodatkowy: rekordy AED wprost w XML
Adres w opisie (link do CSV) serwer podstawia z nagłówka Host, więc ten sam opis działa lokalnie, z kontenera
(https://host.docker.internal:8099) i przez ngrok. Tylko odczyt (GET, HEAD), tylko pliki z repozytorium.

Portal przyjmuje tylko linki https, więc dla portalu uruchamiaj z --https (certyfikat samopodpisany tworzy openssl
w demo/.cert/, plik jest w .gitignore; portal pobiera z verify=False). Przez ngrok adres https dostajesz od ngroka
(wtedy uruchom bez --https, instrukcja: demo/NGROK.md).
Serwer słucha na IPv4 i IPv6 (adres „localhost” odpowiada od razu, ok. 10 ms). Drugiej kopii na zajętym porcie nie uruchomi
(komunikat zamiast cichego współdzielenia portu, które Windows dopuszcza przy SO_REUSEADDR).
"""
import argparse
import contextlib
import json
import os
import socket
import ssl
import subprocess
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OPIS = ROOT / "format_danych/przyklady/opis"
PLACEHOLDER = "dostawca.example.pl"
STATIC = {
    "/aed.csv": (OPIS / "aed_dostawcy.csv", "text/csv; charset=utf-8"),
    "/aed_opis_zbioru.xsd": (ROOT / "format_danych/schemat/aed_opis_zbioru.xsd", "application/xml; charset=utf-8"),
    "/aed_punkty.xsd": (ROOT / "format_danych/schemat/aed_punkty.xsd", "application/xml; charset=utf-8"),
    "/aed.xml": (ROOT / "format_danych/przyklady/xml/aed_poprawny.xml", "application/xml; charset=utf-8"),
    "/aed_bledny.xml": (ROOT / "format_danych/przyklady/xml/aed_bledny.xml", "application/xml; charset=utf-8"),
}
OPISY = {
    "/opis.xml": OPIS / "opis_poprawny.xml",
    "/opis_bledny_md5.xml": OPIS / "opis_bledny_md5.xml",
    "/opis_bledny_xsd.xml": OPIS / "opis_bledny_xsd.xml",
}
STARTED = time.time()


class Handler(BaseHTTPRequestHandler):
    server_version = "AEDDostawca/1.0"

    def _respond(self, body: bytes, kind: str, head_only: bool):
        self.send_response(200)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if not head_only:
            self.wfile.write(body)

    def _handle(self, head_only: bool):
        path = self.path.split("?", 1)[0]
        host = self.headers.get("Host") or f"localhost:{self.server.server_port}"
        scheme = self.headers.get("X-Forwarded-Proto") or ("https" if isinstance(self.server.socket, ssl.SSLSocket) else "http")
        if path == "/stan":
            body = json.dumps({"stan": "ok", "dzialanie_s": round(time.time() - STARTED, 1)}).encode("utf-8")
            kind = "application/json; charset=utf-8"
        elif path in OPISY:
            text = OPISY[path].read_text(encoding="utf-8")
            # link do CSV: ten sam host i https; tylko w opisie błędnym XSD zostaje http (to jest ten błąd)
            https_base = f"https://{host}" if scheme == "https" else f"http://{host}"
            text = text.replace(f"https://{PLACEHOLDER}", https_base).replace(f"http://{PLACEHOLDER}", f"http://{host}")
            body = text.encode("utf-8")
            kind = "application/xml; charset=utf-8"
        elif path == "/":
            paths = sorted(list(OPISY) + list(STATIC) + ["/stan"])
            body = ("Zewnętrzny dostawca AED (demo): " + ", ".join(paths)).encode("utf-8")
            kind = "text/plain; charset=utf-8"
        elif path in STATIC:
            file, kind = STATIC[path]
            body = file.read_bytes()
        else:
            self.send_error(404)
            return
        self._respond(body, kind, head_only)

    def do_GET(self):  # noqa: N802
        self._handle(False)

    def do_HEAD(self):  # noqa: N802
        self._handle(True)

    def log_message(self, fmt, *args):
        pass  # bez wpisów na konsoli; stan serwera: /stan


class Server(ThreadingHTTPServer):
    daemon_threads = True
    # Na Windows SO_REUSEADDR pozwala drugiemu procesowi zająć ten sam port bez błędu (dwa serwery, losowe odpowiedzi).
    allow_reuse_address = os.name != "nt"


class DualStackServer(Server):
    """IPv4 i IPv6 naraz: „localhost” rozwiązywany najpierw do ::1 nie czeka wtedy ~0,2 s na powrót do 127.0.0.1."""

    address_family = socket.AF_INET6

    def server_bind(self):
        with contextlib.suppress(Exception):
            self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        super().server_bind()


def make_server(host: str, port: int, https: bool = False) -> Server:
    if host in ("0.0.0.0", "") and socket.has_dualstack_ipv6():
        server = DualStackServer(("::", port), Handler)
    else:
        server = Server((host, port), Handler)
    if https:
        cert_dir = Path(__file__).resolve().parent / ".cert"
        cert, key = cert_dir / "cert.pem", cert_dir / "key.pem"
        if not cert.exists():
            cert_dir.mkdir(exist_ok=True)
            subprocess.run(
                ["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "30", "-subj", "/CN=dostawca-demo",
                 "-keyout", str(key), "-out", str(cert)],
                check=True, capture_output=True,
            )
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert, key)
        server.socket = context.wrap_socket(server.socket, server_side=True)
    return server


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=8099)
    ap.add_argument("--https", action="store_true")
    a = ap.parse_args()
    try:
        server = make_server(a.host, a.port, a.https)
    except OSError as exc:
        raise SystemExit(f"Nie można uruchomić serwera na porcie {a.port} ({exc}). Czy działa już inna kopia? Użyj --port.")
    print(f"Serwer dostawcy: http{'s' if a.https else ''}://localhost:{a.port}/opis.xml (Ctrl+C kończy)", flush=True)
    server.serve_forever()
