"""Weryfikator maszynowy rozwiązania „Wykaz AED”: jedno polecenie, bez Dockera i bazy.

    python demo/sprawdz.py

Sprawdza wymagania zadania na plikach z repozytorium, uruchamiając ten sam kod co portal
(`portal/backend/mcod/resources/aed_xml.py`, `aed_aggregation.py`). Wynik: `demo/wynik/weryfikacja.txt`
(do przeczytania) i `demo/wynik/weryfikacja.json` (do odczytu maszynowego); kod wyjścia 0 = wszystko PASS.
Bez zainstalowanych pandas i lxml skrypt sam uruchamia się przez `uv` (https://docs.astral.sh/uv/).
"""
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

try:
    import pandas as pd
    from lxml import etree  # noqa: F401
except ImportError:
    uv = shutil.which("uv")
    if not uv or os.environ.get("SPRAWDZ_UV"):
        sys.exit("Brak pandas/lxml. Uruchom: uv run --python 3.11 --with lxml --with pandas==1.5.3 --with 'numpy<2' python demo/sprawdz.py")
    os.environ["SPRAWDZ_UV"] = "1"
    os.execvp(uv, [uv, "run", "--python", "3.11", "--with", "lxml", "--with", "pandas==1.5.3", "--with", "numpy<2",
                   "python", __file__])

ROOT = Path(__file__).resolve().parent.parent
RESOURCES = ROOT / "portal" / "backend" / "mcod" / "resources"
SCHEMA = ROOT / "format_danych" / "schemat"
XML_DIR = ROOT / "format_danych" / "przyklady" / "xml"
OUT = ROOT / "demo" / "wynik"
ORIGINAL_COMMIT = "a1adc22"
AGGREGATED_AT = "2026-11-22T04:15:00"  # stała data: wynik jest powtarzalny


def load(name):
    spec = importlib.util.spec_from_file_location(f"mcod.resources.{name}", RESOURCES / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


constants = load("aed_constants")
aed_xml = load("aed_xml")
aggregation = load("aed_aggregation")

GOOD = (XML_DIR / "aed_poprawny.xml").read_bytes()
BAD = (XML_DIR / "aed_bledny.xml").read_bytes()
CHECKS = []


def check(cid, requirement, evidence):
    def decorator(func):
        try:
            ok, detail = func()
        except Exception as exc:  # błąd samej kontroli też jest FAIL
            ok, detail = False, f"wyjątek: {type(exc).__name__}: {exc}"
        CHECKS.append({"id": cid, "wymaganie": requirement, "status": "PASS" if ok else "FAIL", "szczegoly": detail,
                       "dowod": evidence})
        return func

    return decorator


def git(*args):
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True, encoding="utf-8").stdout


def table_schema(name):
    return json.loads((SCHEMA / name).read_text(encoding="utf-8"))


@check("xsd-zgodny-ze-wzorcem", "Schemat XSD odpowiada wzorcowi (41 kolumn, pola wymagane)",
       "format_danych/schemat/aed_punkty.xsd, aed_punkty.tableschema.json")
def _():
    ts = table_schema("aed_punkty.tableschema.json")
    names = [f["name"] for f in ts["fields"]]
    xsd = (SCHEMA / "aed_punkty.xsd").read_text(encoding="utf-8")
    required = {f["name"] for f in ts["fields"] if f.get("constraints", {}).get("required")}
    xsd_required = {n for n in names if f'<xs:element name="{n}" minOccurs="1">' in xsd}
    same_copy = (RESOURCES / "aed_punkty.xsd").read_bytes() == (SCHEMA / "aed_punkty.xsd").read_bytes()
    ok = names == constants.AED_TEMPLATE_COLUMNS and required == xsd_required and same_copy
    return ok, f"{len(names)} pól, wymaganych {len(required)}, kopia w portalu identyczna: {same_copy}"


@check("xml-poprawny", "Poprawny plik XML od zewnętrznego dostawcy przechodzi walidację XSD", "format_danych/przyklady/xml/aed_poprawny.xml")
def _():
    report = aed_xml.validate_aed_xml(GOOD)
    return report["valid"] and report["records"] == 6, f"rekordów: {report['records']}, błędów: {len(report['errors'])}"


@check("xml-bledny", "Niepoprawny XML jest odrzucany z wskazaniem linii i pola", "demo/wynik/walidacja_xml.json")
def _():
    report = aed_xml.validate_aed_xml(BAD)
    fields = sorted(e["field"] for e in report["errors"])
    return (not report["valid"] and fields == ["status_urzadzenia", "szerokosc_geograficzna", "typ_dostepu"],
            "; ".join(f"linia {e['line']} {e['field']}" for e in report["errors"]))


@check("xml-bezpieczenstwo", "Plik z zewnątrz nie może wczytywać zewnętrznych encji (XXE)", "portal/backend/mcod/resources/aed_xml.py")
def _():
    xxe = b'<?xml version="1.0"?><!DOCTYPE x [<!ENTITY e SYSTEM "file:///etc/passwd">]><wykaz><aed><id_zrodlowe>&e;</id_zrodlowe></aed></wykaz>'
    report = aed_xml.validate_aed_xml(xxe)
    return not report["valid"] and "root:" not in json.dumps(report), report["errors"][0]["message"]


def build_aggregate():
    """XML jednego dostawcy (CC BY 4.0) i CSV drugiego (CC0) scalone funkcją agregacji portalu."""
    xml_df = aed_xml.aed_xml_to_df(GOOD)
    csv_df = aggregation.read_tabular_bytes((ROOT / "format_danych/przyklady/aed_punkty_przyklad.csv").read_bytes(), "csv")
    source_xml = {"institution_id": 2001, "publisher": "Miejski Zakład Przykład (dostawca zewnętrzny, dane fikcyjne)",
                  "license": "CC BY 4.0", "resource_id": 900101, "url": "https://dostawca.example.pl/aed.xml",
                  "data_date": "2026-11-20", "personal_data": False}
    source_csv = {"institution_id": 2002, "publisher": "Gmina Przykładowa (dane fikcyjne)", "license": "CC0 1.0",
                  "resource_id": 900102, "url": "https://dane.gov.pl/pl/dataset/2/resource/900102",
                  "data_date": "2026-11-19", "personal_data": False}
    parts, skipped = [], []
    for df, source in ((xml_df, source_xml), (csv_df, source_csv)):
        rows, skips = aggregation.build_aggregate_rows(df, source, AGGREGATED_AT)
        parts.append(rows)
        skipped += skips
    return pd.concat(parts, ignore_index=True), skipped, len(xml_df), len(csv_df)


MERGED, SKIPPED, N_XML, N_CSV = build_aggregate()


@check("agregacja-dwoch-dostawcow", "Dane dwóch dostawców i dwóch formatów (XML i CSV) scalone w jeden wykaz",
       "demo/wynik/wykaz_xml_i_csv.csv")
def _():
    return len(MERGED) + len(SKIPPED) == N_XML + N_CSV and len(MERGED) >= N_XML, \
        f"XML: {N_XML}, CSV: {N_CSV}, w wykazie: {len(MERGED)}, pominiętych wierszy: {len(SKIPPED)}"


@check("kolumny-wykazu", "Wykaz ma 51 kolumn zgodnych z Table Schema, unikalne id_aed i pochodzenie każdego wiersza",
       "format_danych/schemat/aed_zestawienie.tableschema.json")
def _():
    names = [f["name"] for f in table_schema("aed_zestawienie.tableschema.json")["fields"]]
    provenance = ["wydawca_zasobu", "licencja_zasobu", "id_zasobu_zrodlowego", "url_zasobu_zrodlowego", "data_agregacji"]
    ok = (list(MERGED.columns) == names and len(names) == 51 and MERGED["id_aed"].is_unique
          and all((MERGED[c].astype(str).str.strip() != "").all() for c in provenance))
    return ok, f"kolumn: {len(MERGED.columns)}, unikalnych id_aed: {MERGED['id_aed'].nunique()}/{len(MERGED)}"


@check("licencje", "Do wykazu trafiają tylko CC0 i CC BY 4.0; ODbL (OpenStreetMap) jest wykluczona",
       "portal/backend/mcod/resources/aed_constants.py")
def _():
    allowed = set(constants.AED_ALLOWED_LICENSES)
    return (allowed == {"CC0 1.0", "CC BY 4.0"} and set(MERGED["licencja_zasobu"]) <= allowed,
            f"dozwolone: {sorted(allowed)}; w wykazie: {sorted(set(MERGED['licencja_zasobu']))}")


@check("nic-nie-usunieto", "Portal rozszerzono, a nie przepisano: w diffie względem oryginału nic nie usunięto",
       f"git diff --name-status {ORIGINAL_COMMIT} -- portal/backend")
def _():
    status = git("diff", "--name-status", ORIGINAL_COMMIT, "--", "portal/backend")
    if not status.strip():
        return False, "brak danych z gita (repozytorium bez historii?)"
    letters = [line.split("\t")[0][0] for line in status.splitlines()]
    return "D" not in letters, f"dodane pliki: {letters.count('A')}, zmienione istniejące: {letters.count('M')}, usunięte: {letters.count('D')}"


@check("zero-migracji", "Zero migracji: żaden plik migracji nie został dodany ani zmieniony", f"git diff {ORIGINAL_COMMIT} -- '*/migrations/*'")
def _():
    names = git("diff", "--name-only", ORIGINAL_COMMIT, "--", "portal/backend").splitlines()
    touched = [n for n in names if "/migrations/" in n]
    return not touched and bool(names), f"zmienionych plików migracji: {len(touched)} (wszystkich zmienionych plików: {len(names)})"


@check("testy-portalu", "Testy portalu (nowe i DGA) przechodzą, makemigrations --check: brak zmian", "demo/wynik/testy.txt")
def _():
    log = (OUT / "testy.txt").read_text(encoding="utf-8")
    passed = re.findall(r"(\d+) passed", log)
    return bool(passed) and " failed" not in log and "No changes detected" in log, \
        f"{passed[-1] if passed else '?'} passed; makemigrations: No changes detected"


@check("odpornosc-na-realne-dane", "Realne wadliwe dane z dane.gov.pl nie psują wykazu: pominięcia mają powód", "demo/wynik/raport_agregacji.txt")
def _():
    report = (OUT / "raport_agregacji.txt").read_text(encoding="utf-8")
    return "POMINIĘTY:" in report and "przyjęty" in report, f"{report.count('POMINIĘTY:')} zasobów pominiętych z powodem"


@check("xlsx-wzorcowy-zakres", "Wzorcowy zakres danych w XLSX (5 arkuszy)", "format_danych/wzorcowy_zakres_danych.xlsx")
def _():
    with zipfile.ZipFile(ROOT / "format_danych/wzorcowy_zakres_danych.xlsx") as z:
        sheets = re.findall(r'<sheet [^>]*name="([^"]+)"', z.read("xl/workbook.xml").decode("utf-8"))
    return len(sheets) == 5, ", ".join(sheets)


@check("prototyp-offline", "Prototyp działa offline: strona nie ładuje nic z innych domen", "demo/index.html")
def _():
    html = (ROOT / "demo/index.html").read_text(encoding="utf-8")
    external = sorted(set(re.findall(r'(?:src|href)=["\'](https?://[^"\']+)', html)))
    return not external, f"rozmiar {len(html) // 1024} kB; zewnętrzne zasoby: {external or 'brak'}"


@check("proces-maszynowy", "Prototyp ma opis procesu w JSON: każdy krok wskazuje istniejące pliki dowodowe i zrzuty", "demo/proces.json")
def _():
    proces = json.loads((ROOT / "demo/proces.json").read_text(encoding="utf-8"))
    paths = [d for k in proces["kroki"] for d in k["dowody"] + k["zrzuty"]]
    missing = [d for d in paths if not (ROOT / d).exists()]
    html = (ROOT / "demo/index.html").read_text(encoding="utf-8")
    sections = len(re.findall(r'<section class="krok"', html))
    embedded = '<script type="application/json" id="proces">' in html
    return (not missing and sections == len(proces["kroki"]) and embedded,
            f"kroków: {len(proces['kroki'])} (sekcji na stronie: {sections}), plików: {len(paths)}, brakuje: {missing or 'nic'}")


@check("pliki-do-zgloszenia", "Obecne są wszystkie pliki z §4: opis, prezentacja, logotypy, księga znaku, instrukcja", "patrz szczegóły")
def _():
    needed = ["README.md", "ZMIANY_W_PORTALU.md", "INSTRUKCJA_DLA_JURY.md", "prezentacja/dane_przezycie_prezentacja.pdf",
              "branding/ksiega_znaku.pdf", "branding/logo/dane-przezycie_logo_poziome.jpg",
              "branding/logo/dane-przezycie_logo_poziome.png", "branding/logo/dane-przezycie_logo_poziome.pdf",
              "branding/logo/dane-przezycie_logo_poziome.svg"]
    missing = [p for p in needed if not (ROOT / p).exists()]
    return not missing, f"brakuje: {missing}" if missing else f"{len(needed)} plików jest"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "walidacja_xml.json").write_text(
        json.dumps({"aed_poprawny.xml": aed_xml.validate_aed_xml(GOOD), "aed_bledny.xml": aed_xml.validate_aed_xml(BAD)},
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    (OUT / "wykaz_xml_i_csv.csv").write_bytes(aggregation.to_csv_bytes(MERGED))
    failed = [c for c in CHECKS if c["status"] != "PASS"]
    (OUT / "weryfikacja.json").write_text(
        json.dumps({"wynik": "PASS" if not failed else "FAIL", "kontrole": CHECKS}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8", newline="\n")
    lines = [f"Weryfikacja maszynowa Wykazu AED: {len(CHECKS) - len(failed)}/{len(CHECKS)} PASS", ""]
    for c in CHECKS:
        lines += [f"[{c['status']}] {c['wymaganie']}", f"       {c['szczegoly']}", f"       dowód: {c['dowod']}"]
    text = "\n".join(lines) + "\n"
    (OUT / "weryfikacja.txt").write_text(text, encoding="utf-8", newline="\n")
    sys.stdout.reconfigure(encoding="utf-8")
    print(text, end="")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
