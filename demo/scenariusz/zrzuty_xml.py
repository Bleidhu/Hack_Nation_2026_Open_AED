"""Zrzuty ścieżki „opis zbioru XML + CSV” (serwer dostawcy → import z md5 → portal → Wykaz AED z deduplikacją).

    # serwer dostawcy: python demo/serwer_zewnetrzny.py --https [--port 8099]
    # dane: demo/scenariusz/przygotuj_dane_xml.py, import: manage.py import_aed_xml (log w demo/wynik/),
    # wykaz: manage.py create_main_aed_resource --eager (log: demo/wynik/komenda_create_main_aed_resource_opis.txt)
    uv run --with playwright python demo/scenariusz/zrzuty_xml.py            # zrzuty 09 i 16–23
    uv run --with playwright python demo/scenariusz/zrzuty_xml.py --stare    # dawne zrzuty 10–15 (rekordy w XML)

Identyfikatory podaj zmiennymi AED_OPIS_DATASET, AED_OPIS_RESOURCE, AED_MAIN_DATASET, AED_MAIN_RESOURCE, a adres
serwera dostawcy widziany z hosta zmienną AED_PROVIDER_URL (wartości domyślne pochodzą z uruchomienia z 22.11.2026).
Korzysta z funkcji pomocniczych `zrzuty.py` (te same dane logowania).
"""
import hashlib
import json
import os
import re
import ssl
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
import zrzuty as z  # noqa: E402

OPIS_DATASET = int(os.environ.get("AED_OPIS_DATASET", "4251"))
OPIS_RESOURCE = int(os.environ.get("AED_OPIS_RESOURCE", "40253"))
MAIN_DATASET = z.MAIN_DATASET
MAIN_RESOURCE = int(os.environ.get("AED_MAIN_RESOURCE", "40258"))
PROVIDER_URL = os.environ.get("AED_PROVIDER_URL", "https://localhost:8098").rstrip("/")
NOISE = re.compile(r"^(\[\w+\] sender:|NoneType: None|.*UserWarning: Overriding|\s+warnings\.warn)")


def provider_get(path: str):
    context = ssl.create_default_context()
    context.check_hostname, context.verify_mode = False, ssl.CERT_NONE
    started = time.perf_counter()
    with urllib.request.urlopen(f"{PROVIDER_URL}/{path}", context=context, timeout=10) as response:
        body = response.read()
        return response.status, body, (time.perf_counter() - started) * 1000


def result_lines(name: str):
    return (z.RESULTS / name).read_text(encoding="utf-8").splitlines()


def dedup_log() -> str:
    lines = [line for line in result_lines("komenda_create_main_aed_resource_opis.txt") if not NOISE.match(line)]
    start = next(i for i, line in enumerate(lines) if line.startswith("$"))
    body = [line for line in lines[start:] if line.startswith("$") or ("AED" in line and "Created main AED file" not in line)]
    body += [line for line in lines if line.startswith(("Zbiór", "Zasób", "Wiersze"))]
    stats = json.loads((z.RESULTS / "statystyki_opis_dedup.json").read_text(encoding="utf-8"))
    summary = [f'  "{k}": {stats[k]},' for k in ("wiersze_przed_deduplikacja", "wiersze", "wiersze_zdeduplikowane")]
    pairs = [f"    {json.dumps(d, ensure_ascii=False)}," for d in stats["duplikaty"]]
    return "\n".join(
        body + ["", "Statystyki zadania (demo/wynik/statystyki_opis_dedup.json, wybrane pola):", "{"] + summary
        + ['  "duplikaty": ['] + pairs + ["  ]", "}"]
    )


def api_rows(page, columns, wanted):
    url = f"{z.API}/resources/{MAIN_RESOURCE}/data?per_page=100"
    page.goto(url, wait_until="networkidle")
    body = json.loads(page.inner_text("body"))
    headers = body["meta"]["headers_map"]
    rows = [{headers[c]: v["val"] for c, v in row["attributes"].items() if c in headers} for row in body["data"]]
    picked = [{c: row.get(c) for c in columns} for row in rows if row.get("id_zrodlowe") in wanted]
    with_serial = sum(1 for row in rows if row.get("numer_seryjny"))
    excerpt = {
        "meta.count": body["meta"]["count"],
        "liczba kolumn (meta.headers_map)": len(headers),
        "wiersze z numer_seryjny": with_serial,
        "wiersze (wybrane kolumny)": picked,
    }
    return url, excerpt


def main(old: bool = False) -> int:
    if old:
        return old_xml_shots()
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

        if (z.RESULTS / "testy.txt").exists():
            page.set_content(z.text_page("Testy portalu: Wykaz AED i regresja DGA (pytest w kontenerze)", z.tests_log()))
            shot("09_testy.png", full_page=True)

        status, opis, ms = provider_get("opis.xml")
        csv_status, csv_body, csv_ms = provider_get("aed.csv")
        text = (
            f"GET {PROVIDER_URL}/opis.xml  →  {status}, {ms:.0f} ms, {len(opis)} B\n\n{opis.decode('utf-8')}\n"
            f"GET {PROVIDER_URL}/aed.csv  →  {csv_status}, {csv_ms:.0f} ms, {len(csv_body)} B, "
            f"md5 pobranego pliku: {hashlib.md5(csv_body).hexdigest()}"
        )
        page.set_content(z.text_page("Serwer dostawcy (demo/serwer_zewnetrzny.py, dane fikcyjne): opis zbioru XML i CSV", text))
        shot("16_opis_xml_dostawcy.png", full_page=True)

        log = "\n".join(line for line in result_lines("komenda_import_aed_xml.txt") if line.startswith("$") or not line or (
            not line.startswith(("Import opisu", "Serwer dostawcy", "port 8098", "Kolejno", "zapisano", "Pominięto"))))
        page.set_content(z.text_page("Terminal: python manage.py import_aed_xml (opis poprawny, błędne md5 i XSD, powtórka)",
                                     log.strip()))
        shot("17_import_opisu_komenda.png", full_page=True)

        page.goto(f"{z.ADMIN}/login/", wait_until="networkidle")
        page.fill("input[name=username]", z.EMAIL)
        page.fill("input[name=password]", z.PASSWORD)
        page.click("[type=submit]")
        page.wait_for_load_state("networkidle")

        page.goto(f"{z.ADMIN}/datasets/dataset/{OPIS_DATASET}/change/", wait_until="networkidle")
        field = page.locator(".field-customfields, [class*=customfields]").first
        field.scroll_into_view_if_needed()
        page.evaluate("window.scrollBy(0, -250)")
        shot("18_zbior_z_opisu_w_panelu.png")

        page.set_content(z.text_page("Terminal: python manage.py create_main_aed_resource --eager (wybrane linie)", dedup_log()))
        shot("19_wykaz_deduplikacja.png", full_page=True)

        shot("20_zasob_csv_z_opisu_w_panelu.png", f"{z.ADMIN}/resources/resource/{OPIS_RESOURCE}/change/", full_page=True)

        columns = ["id_aed", "id_zrodlowe", "nazwa_lokalizacji", "producent", "model", "numer_seryjny",
                   "wydawca_zasobu", "id_zasobu_zrodlowego"]
        url, excerpt = api_rows(page, columns, {"CT-01", "OL-001"})
        page.set_content(z.text_page(f"GET {url}  (wybrane pola odpowiedzi API, sformatowane)",
                                     json.dumps(excerpt, indent=2, ensure_ascii=False)))
        shot("21_api_wykaz_numer_seryjny.png", full_page=True)

        page.goto(f"{z.FRONT}/dataset/{MAIN_DATASET}/resource/{MAIN_RESOURCE}/table", wait_until="networkidle", timeout=120000)
        header = page.locator("th", has_text="numer_seryjny").first
        header.wait_for(timeout=60000)
        header.scroll_into_view_if_needed()
        page.evaluate("window.scrollBy(0, -120)")
        shot("22_wykaz_tabela_opis.png")
        shot("23_wykaz_mapa_opis.png", f"{z.FRONT}/dataset/{MAIN_DATASET}/resource/{MAIN_RESOURCE}/map",
             wait="#resourceMap .leaflet-marker-icon, #resourceMap .leaflet-interactive")
        browser.close()
    return 0


def old_xml_shots() -> int:
    """Dawne zrzuty 10–15 (wariant „rekordy w XML”); wymagają zasobów 40250 i wykazu z tamtego uruchomienia."""
    xml_resource = os.environ.get("AED_XML_RESOURCE", "40250")
    main_resource = int(os.environ.get("AED_OLD_MAIN_RESOURCE", "40252"))
    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="msedge", args=["--host-resolver-rules=MAP *.mcod.local 127.0.0.1, MAP mcod.local 127.0.0.1"]
        )
        page = browser.new_context(viewport={"width": 1440, "height": 900}, ignore_https_errors=True, locale="pl-PL").new_page()

        def shot(name, url=None, full_page=False, wait=None):
            if url:
                page.goto(url, wait_until="networkidle", timeout=120000)
            if wait:
                page.wait_for_selector(wait, timeout=60000)
            page.wait_for_timeout(3000)
            page.screenshot(path=str(z.OUT / name), full_page=full_page)
            print(name, page.url)

        head = "\n".join(provider_get("aed.xml")[1].decode("utf-8").splitlines()[:34]) + "\n  …"
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
        shot("12_zasob_xml_w_panelu.png", f"{z.ADMIN}/resources/resource/{xml_resource}/change/", full_page=True)
        lines = result_lines("komenda_create_main_aed_resource_xml.txt")
        log = "\n".join(line for line in lines if not NOISE.match(line) and (
            "AED" in line or line.startswith(("Zbiór", "Zasób", "Wiersze"))))
        page.set_content(z.text_page("Terminal: python manage.py create_main_aed_resource --eager (wybrane linie)", log))
        shot("13_komenda_wykaz_z_xml.png", full_page=True)
        shot("14_wykaz_z_xml_tabela.png", f"{z.FRONT}/dataset/{MAIN_DATASET}/resource/{main_resource}/table", full_page=True)
        shot("15_wykaz_z_xml_mapa.png", f"{z.FRONT}/dataset/{MAIN_DATASET}/resource/{main_resource}/map",
             wait="#resourceMap .leaflet-marker-icon, #resourceMap .leaflet-interactive")
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(old="--stare" in sys.argv[1:]))
