"""Zrzuty ekranu Wykazu AED z portalu uruchomionego lokalnie (zadanie 15).

    uv run --with playwright python demo/scenariusz/zrzuty.py

Używa zainstalowanej przeglądarki Edge; nazwy *.mcod.local kieruje na nginx portalu (127.0.0.1)
regułą --host-resolver-rules, więc nie wymaga wpisów w pliku hosts. Mapa we froncie uruchomionym przez
`ng serve` wymaga "prebundle": false w konfiguracji serve (inaczej `require('leaflet')` w LeafletService
kończy się błędem „Dynamic require of "leaflet" is not supported”). Dane logowania: konto
administratora środowiska lokalnego z portal/backend/README.md (zmienne AED_ADMIN_EMAIL, AED_ADMIN_PASSWORD).
"""

import html
import json
import os
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "demo" / "zrzuty"
RESULTS = ROOT / "demo" / "wynik"

SOURCE_DATASET = int(os.environ.get("AED_SOURCE_DATASET", "4211"))
MAIN_DATASET = int(os.environ.get("AED_MAIN_DATASET", "4216"))
MAIN_RESOURCE = int(os.environ.get("AED_MAIN_RESOURCE", "40247"))
EMAIL = os.environ.get("AED_ADMIN_EMAIL", "admin@mcod.local")
PASSWORD = os.environ.get("AED_ADMIN_PASSWORD", "testadmin123!")

ADMIN = "https://admin.mcod.local"
API = "https://api.mcod.local/1.4"
FRONT = "https://mcod.local/pl"


def text_page(title: str, text: str) -> str:
    return (
        "<!doctype html><meta charset='utf-8'><title>{0}</title>"
        "<body style='margin:0;background:#1e1e1e;color:#e6e6e6;font:14px/1.45 Consolas,monospace'>"
        "<div style='padding:12px 20px;background:#333;color:#fff;font:600 15px Segoe UI,sans-serif'>{0}</div>"
        "<pre style='margin:0;padding:16px 20px;white-space:pre-wrap'>{1}</pre></body>"
    ).format(html.escape(title), html.escape(text))


def command_log() -> str:
    noise = re.compile(r"^(\[\w+\] sender:|NoneType: None|.*UserWarning: Overriding|\s+warnings\.warn)")
    lines = (RESULTS / "komenda_create_main_aed_resource.txt").read_text(encoding="utf-8").splitlines()
    return "\n".join(line for line in lines if not noise.match(line))


def tests_log() -> str:
    lines = (RESULTS / "testy.txt").read_text(encoding="utf-8").splitlines()
    summary = [line for line in lines if re.search(r"passed|failed|No changes detected|makemigrations", line)]
    per_file = {}
    for line in lines:
        match = re.match(r"(mcod/\S+\.py)::\S+ (PASSED|FAILED|ERROR)", line)
        if match:
            counts = per_file.setdefault(match.group(1), {})
            counts[match.group(2)] = counts.get(match.group(2), 0) + 1
    rows = [f"{path:<60} {' '.join(f'{k} {v}' for k, v in counts.items())}" for path, counts in per_file.items()]
    return "\n".join(rows + [""] + summary)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="msedge", args=["--host-resolver-rules=MAP *.mcod.local 127.0.0.1, MAP mcod.local 127.0.0.1"]
        )
        context = browser.new_context(viewport={"width": 1440, "height": 900}, ignore_https_errors=True, locale="pl-PL")
        page = context.new_page()

        def shot(name: str, url: str = None, full_page: bool = False, wait: str = None):
            if url:
                page.goto(url, wait_until="networkidle", timeout=120000)
            close_privacy_dialog = page.get_by_role("button", name="Zamknij")
            if close_privacy_dialog.count():
                close_privacy_dialog.first.click()
            if wait:
                page.wait_for_selector(wait, timeout=60000)
                page.locator(wait).first.scroll_into_view_if_needed()
            page.wait_for_timeout(3000)
            page.screenshot(path=str(OUT / name), full_page=full_page)
            print(name, page.url, "|", page.title())

        page.goto(f"{ADMIN}/login/", wait_until="networkidle")
        page.fill("input[name=username]", EMAIL)
        page.fill("input[name=password]", PASSWORD)
        page.click("[type=submit]")
        page.wait_for_load_state("networkidle")

        page.goto(f"{ADMIN}/datasets/dataset/{SOURCE_DATASET}/change/", wait_until="networkidle")
        field = page.locator(".field-customfields, [class*=customfields]").first
        field.scroll_into_view_if_needed()
        page.evaluate("window.scrollBy(0, -250)")
        shot("01_formularz_zbioru_standard_aed.png")

        shot("02_zasoby_dostawcow.png", f"{ADMIN}/resources/resource/?q=AED", full_page=True)

        page.set_content(text_page("Terminal: python manage.py create_main_aed_resource", command_log()))
        shot("03_komenda_wykaz_statystyki.png", full_page=True)

        shot("04_wykaz_tabela.png", f"{FRONT}/dataset/{MAIN_DATASET}/resource/{MAIN_RESOURCE}/table", full_page=True)
        shot(
            "05_wykaz_mapa.png",
            f"{FRONT}/dataset/{MAIN_DATASET}/resource/{MAIN_RESOURCE}/map",
            wait="#resourceMap .leaflet-marker-icon, #resourceMap .leaflet-interactive",
        )

        url = f"{API}/aed-aggregated"
        page.goto(url, wait_until="networkidle")
        body = json.loads(page.inner_text("body"))
        page.set_content(text_page(f"GET {url}  (odpowiedź API, sformatowana)", json.dumps(body, indent=2, ensure_ascii=False)))
        shot("06_api_aed_aggregated.png")

        url = f"{API}/resources/{MAIN_RESOURCE}/data?per_page=1"
        page.goto(url, wait_until="networkidle")
        body = json.loads(page.inner_text("body"))
        headers = body["meta"]["headers_map"]
        first_row = {headers[col]: value["val"] for col, value in body["data"][0]["attributes"].items() if col in headers}
        excerpt = {
            "meta.count": body["meta"]["count"],
            "meta.data_schema.geo": body["meta"]["data_schema"]["geo"],
            "data[0] (kolumny wg meta.headers_map)": {column: first_row.get(column) for column in headers.values()},
        }
        page.set_content(
            text_page(
                f"GET {url}  (wybrane pola odpowiedzi API, sformatowane)", json.dumps(excerpt, indent=2, ensure_ascii=False)
            )
        )
        shot("07_api_dane_zasobu.png", full_page=True)

        if (RESULTS / "testy.txt").exists():
            page.set_content(text_page("Testy portalu: Wykaz AED i regresja DGA (pytest w kontenerze)", tests_log()))
            shot("09_testy.png", full_page=True)
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
