"""Zewnętrzny serwer dostawcy (demo): wystawia fikcyjne dane AED w XML i schemat XSD.

    python demo/serwer_zewnetrzny.py [--port 8099] [--host 0.0.0.0] [--https]

Portal przyjmuje tylko linki https, więc dla portalu uruchamiaj z --https (certyfikat samopodpisany tworzy openssl
w demo/.cert/, plik jest w .gitignore; portal pobiera z verify=False). Przez ngrok adres https dostajesz od ngroka.

Adresy:
    /aed.xml          6 rekordów zgodnych z XSD (źródło poprawne)
    /aed_bledny.xml   ten sam plik z 3 błędami (źródło niezgodne z XSD)
    /aed_punkty.xsd   schemat wzorca
Tylko odczyt (GET), tylko pliki z repozytorium, same fikcyjne dane. Tylko biblioteka standardowa.
Z kontenerów portalu serwer widać jako http://host.docker.internal:8099/aed.xml, a z sieci przez ngrok (demo/NGROK.md).
"""
import argparse
import ssl
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLIKI = {
    "/aed.xml": ROOT / "format_danych/przyklady/xml/aed_poprawny.xml",
    "/aed_bledny.xml": ROOT / "format_danych/przyklady/xml/aed_bledny.xml",
    "/aed_punkty.xsd": ROOT / "format_danych/schemat/aed_punkty.xsd",
}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        path = self.path.split("?", 1)[0]
        if path == "/":
            body = ("Zewnętrzny dostawca AED (demo): " + ", ".join(PLIKI)).encode("utf-8")
            kind = "text/plain; charset=utf-8"
        elif path in PLIKI:
            body = PLIKI[path].read_bytes()
            kind = "application/xml; charset=utf-8"
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    do_HEAD = do_GET  # noqa: N815


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=8099)
    ap.add_argument("--https", action="store_true")
    a = ap.parse_args()
    server = ThreadingHTTPServer((a.host, a.port), Handler)
    if a.https:
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
    print(f"Serwer dostawcy: http{'s' if a.https else ''}://{a.host}:{a.port}/aed.xml (Ctrl+C kończy)")
    server.serve_forever()
