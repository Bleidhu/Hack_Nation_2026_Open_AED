"""Weryfikator maszynowy rozwiązania „Wykaz AED”: jedno polecenie, bez Dockera i bazy.

    python demo/sprawdz.py

Sprawdza wymagania zadania na plikach z repozytorium, uruchamiając ten sam kod co portal
(`portal/backend/mcod/resources/aed_xml.py`, `aed_aggregation.py`, `aed_opis.py`, `aed_dedup.py`). Wynik:
`demo/wynik/weryfikacja.txt` (do przeczytania) i `demo/wynik/weryfikacja.json` (do odczytu maszynowego); kod wyjścia
0 = wszystko PASS. Wyniki importu opisu zbioru (XSD, md5, kontrola CSV, deduplikacja, serwer dostawcy) trafiają
do `demo/wynik/import_opisu.json`, z którego korzysta prototyp (`demo/build_demo.py`).
Bez zainstalowanych pandas i lxml skrypt sam uruchamia się przez `uv` (https://docs.astral.sh/uv/).
"""
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
import zipfile
from pathlib import Path
from urllib.parse import urlsplit

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
OPIS_DIR = ROOT / "format_danych" / "przyklady" / "opis"
OUT = ROOT / "demo" / "wynik"
ORIGINAL_COMMIT = "a1adc22"
AGGREGATED_AT = "2026-11-22T04:15:00"  # stała data: wynik jest powtarzalny
TEMPLATE_COLUMNS = 42  # wzorzec dostawcy v2 (docs/06_DECYZJE_STRUKTURA_DANYCH_AED.md, z kolumną numer_seryjny)
AGGREGATE_COLUMNS = 52  # zasób zbiorczy: kolumny wzorca + id_aed i kolumny pochodzenia
SERVER_MAX_SECONDS = 1.0


def load(name, path=None):
    path = path or RESOURCES / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name if path.parent != RESOURCES else f"mcod.resources.{name}", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# Kolejność ma znaczenie: moduły portalu importują się nawzajem przez `mcod.resources.*` (bez Django).
constants = load("aed_constants")
aed_xml = load("aed_xml")
aggregation = load("aed_aggregation")
dedup = load("aed_dedup")
opis = load("aed_opis")
supplier_server = load("serwer_zewnetrzny", ROOT / "demo" / "serwer_zewnetrzny.py")

GOOD = (XML_DIR / "aed_poprawny.xml").read_bytes()
BAD = (XML_DIR / "aed_bledny.xml").read_bytes()
OPIS_FILES = {name: (OPIS_DIR / name).read_bytes() for name in ("opis_poprawny.xml", "opis_bledny_md5.xml", "opis_bledny_xsd.xml")}
SUPPLIER_CSV = (OPIS_DIR / "aed_dostawcy.csv").read_bytes()
TEMPLATE_CSV = (ROOT / "format_danych/przyklady/aed_punkty_przyklad.csv").read_bytes()
CHECKS = []
IMPORT = {}  # wyniki dla demo/wynik/import_opisu.json


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


@check("xsd-zgodny-ze-wzorcem", f"Schemat XSD odpowiada wzorcowi ({TEMPLATE_COLUMNS} kolumny, pola wymagane)",
       "format_danych/schemat/aed_punkty.xsd, aed_punkty.tableschema.json")
def _():
    ts = table_schema("aed_punkty.tableschema.json")
    names = [f["name"] for f in ts["fields"]]
    xsd = (SCHEMA / "aed_punkty.xsd").read_text(encoding="utf-8")
    required = {f["name"] for f in ts["fields"] if f.get("constraints", {}).get("required")}
    xsd_required = {n for n in names if f'<xs:element name="{n}" minOccurs="1">' in xsd}
    same_copy = (RESOURCES / "aed_punkty.xsd").read_bytes() == (SCHEMA / "aed_punkty.xsd").read_bytes()
    ok = (names == constants.AED_TEMPLATE_COLUMNS and len(names) == TEMPLATE_COLUMNS and required == xsd_required
          and same_copy and "numer_seryjny" in names)
    return ok, f"{len(names)} pól (w tym numer_seryjny), wymaganych {len(required)}, kopia w portalu identyczna: {same_copy}"


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


# --- Opis zbioru w XML: XSD, md5, kontrola CSV (kroki komendy import_aed_xml bez zapisu w bazie) ---


def describe_opis(name, content, csv_content):
    """Kroki `prepare_import` (aed_import.py) bez sieci i bazy: XSD opisu, md5 pliku CSV, kontrola CSV."""
    report = opis.validate_opis_xml(content)
    result = {"plik": f"format_danych/przyklady/opis/{name}", "xsd": report, "md5_w_opisie": None,
              "md5_csv": opis.md5_hex(csv_content), "md5_zgodne": None, "kontrola_csv": None}
    if not report["valid"]:
        result.update(wynik="odrzucony", powod=f"opis zbioru niezgodny z XSD ({len(report['errors'])} błędy)")
        return result
    parsed = opis.parse_opis(content)
    result["md5_w_opisie"] = parsed["zasob"]["md5"]
    result["md5_zgodne"] = opis.verify_md5(csv_content, parsed["zasob"]["md5"])
    if not result["md5_zgodne"]:
        result.update(wynik="odrzucony", powod="suma md5 pliku CSV różni się od sumy w opisie")
        return result
    source = {"institution_id": 0, "publisher": parsed["dysponent_nazwa"], "license": parsed["licencja"], "resource_id": 0,
              "url": parsed["zasob"]["link_csv"], "data_date": parsed["data_aktualizacji"][:10], "personal_data": False}
    result["kontrola_csv"] = opis.inspect_csv(csv_content, source, AGGREGATED_AT)
    result["opis"] = {k: v for k, v in parsed.items() if k != "zasob"}
    result["zasob"] = parsed["zasob"]
    result.update(wynik="przyjęty", powod="")
    return result


IMPORT["opisy"] = {name: describe_opis(name, content, SUPPLIER_CSV) for name, content in OPIS_FILES.items()}


@check("opis-xsd", "Opis zbioru w XML jest sprawdzany schematem XSD: poprawny przechodzi, błędny jest odrzucany z linią i polem",
       "format_danych/schemat/aed_opis_zbioru.xsd, portal/backend/mcod/resources/aed_opis.py")
def _():
    good = IMPORT["opisy"]["opis_poprawny.xml"]["xsd"]
    bad = IMPORT["opisy"]["opis_bledny_xsd.xml"]["xsd"]
    same_copy = (RESOURCES / "aed_opis_zbioru.xsd").read_bytes() == (SCHEMA / "aed_opis_zbioru.xsd").read_bytes()
    fields = {e["field"] for e in bad["errors"]}
    ok = good["valid"] and not good["errors"] and not bad["valid"] and {"tytul", "licencja", "link_csv"} <= fields and same_copy
    return ok, (f"opis_poprawny.xml: zgodny, błędów {len(good['errors'])}; opis_bledny_xsd.xml: odrzucony, "
                + "; ".join(f"linia {e['line']} {e['field']}" for e in bad["errors"]) + f"; kopia XSD w portalu identyczna: {same_copy}")


@check("opis-md5", "Suma md5 z opisu musi pasować do pobranego CSV; niezgodna suma odrzuca import",
       "format_danych/przyklady/opis/opis_poprawny.xml, opis_bledny_md5.xml, aed_dostawcy.csv")
def _():
    good = IMPORT["opisy"]["opis_poprawny.xml"]
    bad = IMPORT["opisy"]["opis_bledny_md5.xml"]
    ok = (good["md5_zgodne"] is True and good["wynik"] == "przyjęty" and bad["xsd"]["valid"]
          and bad["md5_zgodne"] is False and bad["wynik"] == "odrzucony")
    return ok, (f"md5 CSV {good['md5_csv']}; opis_poprawny.xml: {good['md5_w_opisie']} (zgodne, przyjęty); "
                f"opis_bledny_md5.xml: {bad['md5_w_opisie']} (zgodny z XSD, md5 niezgodne, odrzucony)")


@check("opis-kontrola-csv", "Przed zapisem portal sprawdza CSV z opisu: kolumny minimum, wiersze przyjęte i pominięte",
       "portal/backend/mcod/resources/aed_opis.py (inspect_csv)")
def _():
    good = IMPORT["opisy"]["opis_poprawny.xml"]
    report = good["kontrola_csv"]
    declared = int(good["zasob"].get("liczba_rekordow") or -1)
    ok = report["wiersze"] == declared and report["przyjete"] == declared and report["pominiete"] == 0 and not report["duplikaty"]
    return ok, (f"wierszy w CSV: {report['wiersze']} (w opisie liczba_rekordow: {declared}), przyjętych: {report['przyjete']}, "
                f"pominiętych: {report['pominiete']}, duplikatów w pliku: {len(report['duplikaty'])}")


# --- Deduplikacja: to samo urządzenie od dwóch dostawców ---


def build_dedup():
    """Przykład wzorca (CT-01) i CSV dostawcy z opisu (BYD-HALA-A: ten sam producent i numer seryjny)."""
    parsed = opis.parse_opis(OPIS_FILES["opis_poprawny.xml"])
    sources = [
        ({"institution_id": 2002, "publisher": "Gmina Przykładowa (dane fikcyjne)", "license": "CC0 1.0", "resource_id": 900102,
          "url": "https://dane.gov.pl/pl/dataset/2/resource/900102", "data_date": "2026-11-19", "personal_data": False},
         TEMPLATE_CSV, "format_danych/przyklady/aed_punkty_przyklad.csv"),
        ({"institution_id": 2003, "publisher": parsed["dysponent_nazwa"], "license": parsed["licencja"], "resource_id": 900103,
          "url": parsed["zasob"]["link_csv"], "data_date": parsed["data_aktualizacji"][:10], "personal_data": False},
         SUPPLIER_CSV, "format_danych/przyklady/opis/aed_dostawcy.csv"),
    ]
    parts, described = [], []
    for source, content, path in sources:
        rows, skipped = aggregation.build_aggregate_rows(aggregation.read_tabular_bytes(content, "csv"), source, AGGREGATED_AT)
        parts.append(rows)
        described.append({"plik": path, "wydawca": source["publisher"], "licencja": source["license"],
                          "id_zasobu": source["resource_id"], "wiersze": len(rows), "pominiete": len(skipped)})
    merged = pd.concat(parts, ignore_index=True)
    deduplicated, duplicates = dedup.deduplicate_rows(merged)
    by_id = merged.set_index("id_aed")
    columns = ["id_aed", "id_zrodlowe", "nazwa_lokalizacji", "miejscowosc", "producent", "model", "numer_seryjny",
               "poziom_weryfikacji", "wydawca_zasobu", "licencja_zasobu"]
    pairs = [{"powod": d["powod"],
              "zachowany": {c: str(by_id.loc[d["zachowany"]].get(c, "")) if c != "id_aed" else d["zachowany"] for c in columns},
              "pominiety": {c: str(by_id.loc[d["pominiety"]].get(c, "")) if c != "id_aed" else d["pominiety"] for c in columns}}
             for d in duplicates]
    return {"zrodla": described, "wiersze_przed": len(merged), "wiersze_po": len(deduplicated), "duplikaty": pairs,
            "unikalne_id_aed": bool(deduplicated["id_aed"].is_unique), "kolumny": len(deduplicated.columns)}


IMPORT["deduplikacja"] = build_dedup()


@check("deduplikacja", "To samo urządzenie zgłoszone przez dwóch dostawców trafia do wykazu raz (numer seryjny + producent)",
       "portal/backend/mcod/resources/aed_dedup.py, format_danych/przyklady/opis/aed_dostawcy.csv")
def _():
    d = IMPORT["deduplikacja"]
    pair = d["duplikaty"][0] if len(d["duplikaty"]) == 1 else None
    ok = (pair is not None and pair["powod"] == "numer_seryjny" and pair["zachowany"]["id_zrodlowe"] == "CT-01"
          and pair["pominiety"]["id_zrodlowe"] == "BYD-HALA-A" and d["wiersze_po"] == d["wiersze_przed"] - 1
          and d["unikalne_id_aed"] and d["kolumny"] == AGGREGATE_COLUMNS)
    if not pair:
        return False, f"oczekiwano 1 pary duplikatów, wykryto {len(d['duplikaty'])}"
    return ok, (f"wierszy przed: {d['wiersze_przed']}, po: {d['wiersze_po']}; zachowany {pair['zachowany']['id_zrodlowe']} "
                f"({pair['zachowany']['wydawca_zasobu']}), pominięty {pair['pominiety']['id_zrodlowe']} "
                f"({pair['pominiety']['wydawca_zasobu']}), powód: {pair['powod']} {pair['zachowany']['numer_seryjny']}")


# --- Serwer dostawcy: demo/serwer_zewnetrzny.py w wątku na wolnym porcie ---


def fetch(url, headers=None):
    request = urllib.request.Request(url, headers=headers or {})
    started = time.perf_counter()
    with urllib.request.urlopen(request, timeout=5) as response:  # noqa: S310 adres lokalny 127.0.0.1
        body = response.read()
        return response.status, body, time.perf_counter() - started


def run_server_check():
    server = supplier_server.make_server("127.0.0.1", 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        # X-Forwarded-Proto: https tak jak za ngrokiem: serwer wpisuje do opisu link https, który przechodzi XSD.
        status_opis, body_opis, time_opis = fetch(base + "/opis.xml", {"X-Forwarded-Proto": "https"})
        parsed = opis.parse_opis(body_opis)
        link = parsed["zasob"]["link_csv"]
        status_csv, body_csv, time_csv = fetch(base + urlsplit(link).path)
        status_bad, body_bad, time_bad = fetch(base + "/opis_bledny_md5.xml", {"X-Forwarded-Proto": "https"})
        status_xsd, body_xsd, time_xsd = fetch(base + "/opis_bledny_xsd.xml", {"X-Forwarded-Proto": "https"})
    finally:
        server.shutdown()
        server.server_close()
    return {
        "adres": "http://127.0.0.1:<port>",
        "zadania": [
            {"sciezka": "/opis.xml", "kod": status_opis, "czas_ms": round(time_opis * 1000, 1), "bajty": len(body_opis)},
            {"sciezka": urlsplit(link).path, "kod": status_csv, "czas_ms": round(time_csv * 1000, 1), "bajty": len(body_csv)},
            {"sciezka": "/opis_bledny_md5.xml", "kod": status_bad, "czas_ms": round(time_bad * 1000, 1), "bajty": len(body_bad)},
            {"sciezka": "/opis_bledny_xsd.xml", "kod": status_xsd, "czas_ms": round(time_xsd * 1000, 1), "bajty": len(body_xsd)},
        ],
        "link_csv_z_opisu": link.replace(f":{urlsplit(link).port}", ":<port>") if urlsplit(link).port else link,
        "link_na_ten_sam_serwer": urlsplit(link).hostname == "127.0.0.1" and urlsplit(link).port == urlsplit(base).port,
        "md5_w_opisie": parsed["zasob"]["md5"],
        "md5_pobranego_csv": opis.md5_hex(body_csv),
        "md5_zgodne": opis.verify_md5(body_csv, parsed["zasob"]["md5"]),
        "csv_identyczny_z_repo": body_csv == SUPPLIER_CSV,
        "opis_bledny_md5_odrzucony": not opis.verify_md5(body_csv, opis.parse_opis(body_bad)["zasob"]["md5"]),
        "opis_bledny_xsd_odrzucony": not opis.validate_opis_xml(body_xsd)["valid"],
    }


IMPORT["serwer"] = run_server_check()


@check("serwer-dostawcy", f"Serwer dostawcy odpowiada 200 w < {SERVER_MAX_SECONDS:g} s, a md5 z opisu = md5 pobranego CSV",
       "demo/serwer_zewnetrzny.py (make_server)")
def _():
    s = IMPORT["serwer"]
    slowest = max(r["czas_ms"] for r in s["zadania"])
    ok = (all(r["kod"] == 200 for r in s["zadania"]) and slowest < SERVER_MAX_SECONDS * 1000 and s["md5_zgodne"]
          and s["link_na_ten_sam_serwer"] and s["csv_identyczny_z_repo"] and s["opis_bledny_md5_odrzucony"]
          and s["opis_bledny_xsd_odrzucony"])
    return ok, ("; ".join(f"{r['sciezka']} {r['kod']} w {r['czas_ms']:.0f} ms" for r in s["zadania"])
                + f"; md5 z opisu = md5 CSV: {s['md5_zgodne']}; błędne opisy odrzucone: "
                f"{s['opis_bledny_md5_odrzucony'] and s['opis_bledny_xsd_odrzucony']}")


def build_aggregate():
    """XML jednego dostawcy (CC BY 4.0) i CSV drugiego (CC0) scalone funkcją agregacji portalu."""
    xml_df = aed_xml.aed_xml_to_df(GOOD)
    csv_df = aggregation.read_tabular_bytes(TEMPLATE_CSV, "csv")
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


@check("kolumny-wykazu", f"Wykaz ma {AGGREGATE_COLUMNS} kolumny zgodne z Table Schema, unikalne id_aed i pochodzenie każdego wiersza",
       "format_danych/schemat/aed_zestawienie.tableschema.json")
def _():
    names = [f["name"] for f in table_schema("aed_zestawienie.tableschema.json")["fields"]]
    provenance = ["wydawca_zasobu", "licencja_zasobu", "id_zasobu_zrodlowego", "url_zasobu_zrodlowego", "data_agregacji"]
    ok = (list(MERGED.columns) == names and len(names) == AGGREGATE_COLUMNS and MERGED["id_aed"].is_unique
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


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    write_json(OUT / "walidacja_xml.json",
               {"aed_poprawny.xml": aed_xml.validate_aed_xml(GOOD), "aed_bledny.xml": aed_xml.validate_aed_xml(BAD)})
    (OUT / "wykaz_xml_i_csv.csv").write_bytes(aggregation.to_csv_bytes(MERGED))
    write_json(OUT / "import_opisu.json", {
        "opis": "Wynik demo/sprawdz.py: kroki importu opisu zbioru (XSD, md5, kontrola CSV) wykonane funkcjami portalu "
                "z aed_opis.py, deduplikacja funkcją aed_dedup.deduplicate_rows i odpowiedzi serwera dostawcy "
                "demo/serwer_zewnetrzny.py. Czasy odpowiedzi zależą od komputera.",
        "data_agregacji": AGGREGATED_AT,
        **IMPORT,
    })
    failed = [c for c in CHECKS if c["status"] != "PASS"]
    write_json(OUT / "weryfikacja.json", {"wynik": "PASS" if not failed else "FAIL", "kontrole": CHECKS})
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
