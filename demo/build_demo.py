"""Składa demo/index.html: jeden plik HTML działający offline (file://), bez zasobów z innych domen.

Uruchomienie z katalogu głównego repo (tylko biblioteka standardowa i git):

    python demo/build_demo.py

Wejście: demo/szablon.html, wyniki z demo/wynik/ (agregacja i portal lokalny), kontur Polski z demo/dane/,
logo i fonty z branding/, przykład wzorca z format_danych/ i lista zmian portalu z `git diff` względem oryginału.
Zrzuty z demo/zrzuty/ są ładowane względnie (pliki obok index.html), więc index.html zostaje mały.
"""

import base64
import csv
import io
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEMO = ROOT / "demo"
ORIGINAL_COMMIT = "a1adc22"

PORTAL_FILE_NOTES = {
    "CHANGELOG.md": "wpisy zmian AED-01…AED-10",
    "data/test_samples/aed/": "próbki testowe: realne pliki z dane.gov.pl i przykład wzorca",
    "mcod/celeryapp.py": "wpis harmonogramu: zadanie nocne Wykazu AED o 4:15 (tylko gdy włączone); "
    "sygnatura get_beat_schedule dostała parametr opcjonalny, stąd jedna linia zamieniona",
    "mcod/core/api/utils/views.py": "opis /aed-aggregated w specyfikacji OpenAPI",
    "mcod/core/tests/fixtures/__init__.py": "rejestracja fikstur AED",
    "mcod/core/tests/fixtures/aed.py": "fikstury testów AED",
    "mcod/datasets/forms.py": "podpowiedź (help_text) przy „Polach niestandardowych” zbioru",
    "mcod/datasets/tests/test_aed_customfields_help.py": "testy podpowiedzi formularza",
    "mcod/resources/aed_aggregation.py": "logika ramek danych bez ORM: kolumny, aliasy, normalizacja, id_aed, pochodzenie",
    "mcod/resources/aed_constants.py": "kontrakt kolumn wzorca i zasobu zbiorczego, licencje, nazwy",
    "mcod/resources/aed_utils.py": "wybór zbiorów standard = AED, odczyt zasobów, budowa zasobu zbiorczego (wzór: dga_utils.py)",
    "mcod/resources/management/commands/create_main_aed_resource.py": "komenda ręcznego uruchomienia (--dry-run, --eager)",
    "mcod/resources/serializers.py": "serializer odpowiedzi /aed-aggregated",
    "mcod/resources/tasks/__init__.py": "eksport zadania Celery",
    "mcod/resources/tasks/aed.py": "zadanie Celery tworzące zasób zbiorczy (wzór: zadanie DGA)",
    "mcod/resources/views.py": "widok API /aed-aggregated (wzór: /dga-aggregated)",
    "mcod/routes.py": "trasa /aed-aggregated",
    "mcod/settings/base.py": "wyłącznik dodatku AED_AGGREGATION_ENABLED i ustawienia MAIN_AED_*",
    "mcod/settings/test.py": "ustawienia testowe AED",
    "mcod/templates/docs/resources/aggregated_aed_info_view.yml": "dokumentacja endpointu",
}

PORTAL_RESOURCE_NAMES = {
    40209: "AED Marki (plik z dane.gov.pl)",
    40210: "AED Krosno (plik z dane.gov.pl)",
}

SAMPLE_COLUMNS = [
    "id_zrodlowe",
    "nazwa_lokalizacji",
    "miejscowosc",
    "nazwa_ulicy",
    "numer_budynku",
    "szerokosc_geograficzna",
    "dlugosc_geograficzna",
    "typ_dostepu",
    "dostepny_24_7",
    "status_urzadzenia",
    "dysponent_nazwa",
]


def read_text(path):
    return (ROOT / path).read_text(encoding="utf-8")


def font_data_uri(name):
    data = (ROOT / "branding" / "fonty" / name).read_bytes()
    return "data:font/ttf;base64," + base64.b64encode(data).decode("ascii")


def portal_changes():
    def git(*args):
        return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout

    name_status = git("diff", "--name-status", ORIGINAL_COMMIT, "HEAD", "--", "portal/").splitlines()
    statuses = {path: status for status, path in (line.split("\t", 1) for line in name_status)}
    changes = []
    for line in git("diff", "--numstat", ORIGINAL_COMMIT, "HEAD", "--", "portal/").splitlines():
        added, removed, path = line.split("\t")
        short = path.replace("portal/backend/", "", 1)
        note = PORTAL_FILE_NOTES.get(short) or next((v for k, v in PORTAL_FILE_NOTES.items() if short.startswith(k)), "")
        changes.append({"status": statuses[path], "sciezka": path, "dodane": int(added), "usuniete": int(removed), "opis": note})
    return changes


def sample_rows():
    rows = list(csv.DictReader(io.StringIO(read_text("format_danych/przyklady/aed_punkty_przyklad.csv"))))
    return {"naglowki": SAMPLE_COLUMNS, "wiersze": [[row[c] for c in SAMPLE_COLUMNS] for row in rows[:3]], "liczba": len(rows)}


def integrator_summary():
    """Wyniki dodatkowego integratora (demo/integrator/, generuje integrator/generuj_demo.py)."""
    out = DEMO / "integrator"

    def wczytaj(nazwa):
        return json.loads((out / nazwa).read_text(encoding="utf-8"))

    raport_warszawa = wczytaj("raport_warszawa.json")
    return {
        "warszawa": {"poprawne": raport_warszawa["poprawne"], "licencja": raport_warszawa["pochodzenie"]["licencja"]},
        "duplikaty": wczytaj("raport_duplikatow.json")["podsumowanie"],
        "osm": wczytaj("raport_porownania_osm.json")["podsumowanie"],
        "gdansk": wczytaj("statystyka_gdansk.json"),
    }


def main():
    csv_text = (DEMO / "wynik" / "zestawienie_aed.csv").read_bytes().decode("utf-8")
    table = list(csv.reader(io.StringIO(csv_text, newline="")))
    stats = json.loads(read_text("demo/wynik/statystyki_agregacji.json"))
    for skipped in stats["zasoby_pominiete"]:
        skipped["nazwa"] = PORTAL_RESOURCE_NAMES.get(skipped["resource_id"], "")
    data = {
        "naglowki": table[0],
        "wiersze": table[1:],
        "csv": csv_text,
        "statystyki": stats,
        "api": json.loads(read_text("demo/wynik/api_aed_aggregated.json")),
        "kontur": json.loads(read_text("demo/dane/kontur_polski.json")),
        "slowniki": json.loads(read_text("format_danych/schemat/slowniki.json")),
        "raport": read_text("demo/wynik/raport_agregacji.txt"),
        "przyklad": sample_rows(),
        "zmiany": portal_changes(),
        "integrator": integrator_summary(),
        "xml": {
            "poprawny": read_text("format_danych/przyklady/xml/aed_poprawny.xml"),
            "bledny": read_text("format_danych/przyklady/xml/aed_bledny.xml"),
            "raport": json.loads(read_text("demo/wynik/walidacja_xml.json")),
        },
    }
    data_json = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    logo = read_text("branding/logo/dane-przezycie_logo_poziome.svg").strip()
    logo = logo.replace('aria-labelledby="t d"', 'aria-labelledby="logo-t"').replace('id="t"', 'id="logo-t"')
    logo = logo.replace('<desc id="d">', "<desc>")

    html = read_text("demo/szablon.html")
    for key, value in {
        "{{FONT_REGULAR}}": font_data_uri("AtkinsonHyperlegible-Regular.ttf"),
        "{{FONT_BOLD}}": font_data_uri("AtkinsonHyperlegible-Bold.ttf"),
        "{{LOGO_SVG}}": logo,
        "{{DANE_JSON}}": data_json,
        "{{PROCES_JSON}}": json.dumps(json.loads(read_text("demo/proces.json")), ensure_ascii=False, separators=(",", ":")).replace("<", "\u003c"),
    }.items():
        if key not in html:
            raise SystemExit(f"brak {key} w demo/szablon.html")
        html = html.replace(key, value)
    out = DEMO / "index.html"
    out.write_text(html, encoding="utf-8", newline="\n")
    print(f"{out.relative_to(ROOT)}: {len(html.encode('utf-8')) / 1024:.0f} kB, wiersze wykazu: {len(table) - 1}")


if __name__ == "__main__":
    main()
