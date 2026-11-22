"""Zrzuty ścieżki XML (zewnętrzny serwer dostawcy → portal → Wykaz AED) z portalu uruchomionego lokalnie.

    # serwer dostawcy musi działać: python demo/serwer_zewnetrzny.py --https
    # dane: demo/scenariusz/przygotuj_dane_xml.py, wykaz: manage.py create_main_aed_resource --eager
    uv run --with playwright python demo/scenariusz/zrzuty_xml.py

Identyfikatory zasobów podaj zmiennymi AED_XML_RESOURCE, AED_MAIN_DATASET, AED_MAIN_RESOURCE (wartości domyślne
pochodzą z uruchomienia z 22.11.2026). Korzysta z funkcji pomocniczych `zrzuty.py` (te same dane logowania).
"""
import json
import os
import re
import ssl
import sys
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
import zrzuty as z  # noqa: E402

XML_RESOURCE = os.environ.get("AED_XML_RESOURCE", "40250")
MAIN_DATASET = z.MAIN_DATASET
MAIN_RESOURCE = int(os.environ.get("AED_MAIN_RESOURCE", "40252"))
PROVIDER_URL = os.environ.get("AED_PROVIDER_URL", "https://localhost:8099")


def provider_xml(path: str) -> str:
    context = ssl.create_default_context()
    context.check_hostname, context.verify_mode = False, ssl.CERT_NONE
    return urllib.request.urlopen(f"{PROVIDER_URL}/{path}", context=context, timeout=10).read().decode("utf-8")


def xml_log() -> str:
    noise = re.compile(r"^(\[\w+\] sender:|NoneType: None|.*UserWarning: Overriding|\s+warnings\.warn)")
    lines = (z.RESULTS / "komenda_create_main_aed_resource_xml.txt").read_text(encoding="utf-8").splitlines()
    return "\n".join(line for line in lines if not noise.match(line) and ("AED" in line or line.startswith(("Zbiór", "Zasób", "Wiersze"))))


def main() -> int:
    z.OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="msedge", args=["--host-resolver-rules=MAP *.mcod.local 127.0.0.1, MAP mcod.local 127.0.0.1"]
        )
        page = browser.new_context(viewport={"width": 1440, "height": 900}, ignore_https_errors=True, locale="pl-PL").new_page()

        def shot(name, url=None, full_page=False, wait=None):
            if url:
                page.goto(url, wait_until="networkidle", timeout=120000)
            close = page.get_by_role("button", name="Zamknij")
            if close.count():
                close.first.click()
            if wait:
                page.wait_for_selector(wait, timeout=60000)
                page.locator(wait).first.scroll_into_view_if_needed()
            page.wait_for_timeout(3000)
            page.screenshot(path=str(z.OUT / name), full_page=full_page)
            print(name, page.url, "|", page.title())

        head = "\n".join(provider_xml("aed.xml").splitlines()[:34]) + "\n  …"
        page.set_content(z.text_page(f"GET {PROVIDER_URL}/aed.xml (zewnętrzny serwer dostawcy, początek pliku)", head))
        shot("10_zewnetrzny_xml.png", full_page=True)

        report = json.loads((z.RESULTS / "walidacja_xml.json").read_text(encoding="utf-8"))
        page.set_content(z.text_page("Walidacja XSD (mcod.resources.aed_xml.validate_aed_xml): poprawny i błędny plik",
                                     json.dumps(report, indent=2, ensure_ascii=False)))
        shot("11_walidacja_xsd.png", full_page=True)

        page.goto(f"{z.ADMIN}/login/", wait_until="networkidle")
        page.fill("input[name=username]", z.EMAIL)
        page.fill("input[name=password]", z.PASSWORD)
        page.click("[type=submit]")
        page.wait_for_load_state("networkidle")
        shot("12_zasob_xml_w_panelu.png", f"{z.ADMIN}/resources/resource/{XML_RESOURCE}/change/", full_page=True)

        page.set_content(z.text_page("Terminal: python manage.py create_main_aed_resource --eager (wybrane linie)", xml_log()))
        shot("13_komenda_wykaz_z_xml.png", full_page=True)

        shot("14_wykaz_z_xml_tabela.png", f"{z.FRONT}/dataset/{MAIN_DATASET}/resource/{MAIN_RESOURCE}/table", full_page=True)
        shot("15_wykaz_z_xml_mapa.png", f"{z.FRONT}/dataset/{MAIN_DATASET}/resource/{MAIN_RESOURCE}/map",
             wait="#resourceMap .leaflet-marker-icon, #resourceMap .leaflet-interactive")
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
