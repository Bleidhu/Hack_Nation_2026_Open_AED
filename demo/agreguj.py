"""
Weryfikacja agregacji Wykazu AED bez Dockera i bazy danych.

Uruchamia te same funkcje co portal (`portal/backend/mcod/resources/aed_aggregation.py` i deduplikację
`aed_dedup.deduplicate_rows`, którą wywołuje `create_main_aed_df` w `aed_utils.py`) na migawce realnych zasobów AED
z dane.gov.pl (`references/dane_gov_pl_aed/`), na przykładzie wzorca (`format_danych/przyklady/`) i na pliku CSV
dostawcy zewnętrznego z opisem zbioru w XML (`format_danych/przyklady/opis/`). Zapisuje w `demo/wynik/`:
`zestawienie_aed.csv` (zasób zbiorczy), `raport_agregacji.txt` i `statystyki_agreguj.json` (statystyki w układzie
`create_main_aed_df`, z deduplikacją).

    uv run --python 3.11 --with "pandas==1.5.3" --with "numpy<2" --with openpyxl python demo/agreguj.py
"""

import datetime
import importlib.util
import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
MCOD_RESOURCES = ROOT / "portal" / "backend" / "mcod" / "resources"
REFERENCES = ROOT / "references" / "dane_gov_pl_aed"
METADATA = REFERENCES / "metadane_api"
EXAMPLES = ROOT / "format_danych" / "przyklady"
OUTPUT = ROOT / "demo" / "wynik"

# Wartości z testu zgodności portalu (test_aed_aggregation.py::test_golden_matches_reference).
EXAMPLE_AGGREGATED_AT = "2026-11-22T04:15:00"
EXAMPLE_SOURCES = {
    "gmina": {
        "institution_id": 1001,
        "publisher": "Gmina Przykładowa (PRZYKŁAD)",
        "license": "CC0 1.0",
        "resource_id": 900001,
        "url": "https://dane.gov.pl/pl/dataset/1/resource/900001",
        "data_date": "2026-11-20",
        "personal_data": False,
    },
    "powiat": {
        "institution_id": 1002,
        "publisher": "Starostwo Powiatowe Przykład (PRZYKŁAD)",
        "license": "CC BY 4.0",
        "resource_id": 900002,
        "url": "https://dane.gov.pl/pl/dataset/2/resource/900002",
        "data_date": "2026-11-19",
        "personal_data": True,
    },
}


def load_portal_module(name: str):
    # `import mcod.resources...` wykonałby `mcod/resources/__init__.py`, który wymaga Django,
    # więc moduły agregacji ładujemy wprost z plików pod ich nazwami z portalu.
    spec = importlib.util.spec_from_file_location(f"mcod.resources.{name}", MCOD_RESOURCES / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


constants = load_portal_module("aed_constants")
aed_xml = load_portal_module("aed_xml")
aggregation = load_portal_module("aed_aggregation")
dedup = load_portal_module("aed_dedup")
opis = load_portal_module("aed_opis")
OPIS_DIR = EXAMPLES / "opis"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def local_copies() -> dict:
    copies = {}
    for path in REFERENCES.glob("zasob_*_zbior_*.*"):
        match = re.match(r"zasob_(\d+)_zbior_(\d+)\.(\w+)$", path.name)
        if match:
            copies[match.group(1)] = path
    return copies


def source_resources():
    """Zasoby zbiorów AED z migawki API w kolejności: zbiór, zasób."""
    copies = local_copies()
    for listing in sorted(METADATA.glob("resources_*.json"), key=lambda p: int(p.stem.split("_")[1])):
        dataset_id = listing.stem.split("_")[1]
        dataset = read_json(METADATA / f"dataset_{dataset_id}.json")["data"]["attributes"]
        institution = read_json(METADATA / f"inst_{dataset_id}.json")["data"]
        for resource in sorted(read_json(listing)["data"], key=lambda r: int(r["id"])):
            attributes = resource["attributes"]
            yield {
                "dataset_id": dataset_id,
                "dataset_title": dataset["title"],
                "resource_title": attributes["title"],
                "format": (attributes.get("format") or "").lower(),
                "path": copies.get(resource["id"]),
                "source": {
                    "institution_id": int(institution["id"]),
                    "publisher": institution["attributes"]["title"],
                    "license": dataset["license_name"],
                    "resource_id": int(resource["id"]),
                    "url": f"https://dane.gov.pl/pl/dataset/{dataset_id}/resource/{resource['id']}",
                    "data_date": attributes.get("data_date") or "",
                    "personal_data": bool(dataset.get("license_condition_personal_data")),
                },
            }


def resource_skip_reason(resource: dict):
    if resource["source"]["license"] not in constants.AED_ALLOWED_LICENSES:
        return f"licencja {resource['source']['license']} nie pozwala na włączenie do wykazu"
    if resource["format"] not in aggregation.TABULAR_EXTENSIONS:
        return f"format nietabelaryczny ({resource['format'] or 'brak'})"
    if resource["path"] is None:
        return "brak lokalnej kopii pliku w references/dane_gov_pl_aed/"
    return None


def aggregate_real_sources(aggregated_at: str):
    report, parts = [], []
    for resource in source_resources():
        entry = {
            "zbior": f"{resource['dataset_id']} {resource['dataset_title']}",
            "zasob": resource["source"]["resource_id"],
            "format": resource["format"],
            "przyjete": 0,
            "pominiete": 0,
            "powod": resource_skip_reason(resource),
            "pominiete_wiersze": [],
        }
        report.append(entry)
        if entry["powod"]:
            continue
        try:
            df = aggregation.read_tabular_bytes(resource["path"].read_bytes(), resource["format"])
        except Exception as exc:
            entry["powod"] = f"nie można odczytać pliku {resource['format']}: {exc}"
            continue
        rows, skipped = aggregation.build_aggregate_rows(df, resource["source"], aggregated_at)
        resource_skips = [skip for skip in skipped if skip["wiersz"] == 0]
        if resource_skips:
            entry["powod"] = resource_skips[0]["powod"]
            continue
        entry.update(przyjete=len(rows), pominiete=len(skipped), pominiete_wiersze=skipped)
        parts.append(rows)
    return report, parts


def aggregate_example():
    df = aggregation.read_tabular_bytes((EXAMPLES / "aed_punkty_przyklad.csv").read_bytes(), "csv")
    parts = []
    for _, record in df.iterrows():
        source = EXAMPLE_SOURCES["powiat" if record["id_zrodlowe"] == "UNI-B-3" else "gmina"]
        rows, _ = aggregation.build_aggregate_rows(record.to_frame().T, source, EXAMPLE_AGGREGATED_AT)
        parts.append(rows)
    result = pd.concat(parts, ignore_index=True)
    matches = aggregation.to_csv_bytes(result) == (EXAMPLES / "aed_zestawienie_przyklad.csv").read_bytes()
    return result, matches


def aggregate_supplier(aggregated_at: str):
    """CSV dostawcy zewnętrznego: źródło (wydawca, licencja, link) z opisu zbioru, jak w komendzie import_aed_xml."""
    parsed = opis.parse_opis((OPIS_DIR / "opis_poprawny.xml").read_bytes())
    content = (OPIS_DIR / "aed_dostawcy.csv").read_bytes()
    if not opis.verify_md5(content, parsed["zasob"]["md5"]):
        raise SystemExit("suma md5 aed_dostawcy.csv różni się od sumy w opis_poprawny.xml")
    source = {
        "institution_id": 2003,
        "publisher": parsed["dysponent_nazwa"],
        "license": parsed["licencja"],
        "resource_id": 900103,
        "url": parsed["zasob"]["link_csv"],
        "data_date": parsed["data_aktualizacji"][:10],
        "personal_data": False,
    }
    rows, skipped = aggregation.build_aggregate_rows(aggregation.read_tabular_bytes(content, "csv"), source, aggregated_at)
    return rows, skipped


def format_report(report, example_rows: int, matches: bool, total_rows: int, aggregated_at: str, stats: dict) -> str:
    lines = [f"Wykaz AED: weryfikacja agregacji bez bazy (data agregacji {aggregated_at})", ""]
    lines.append(f"{'zasób':>8}  {'format':<8} {'przyjęte':>8} {'pominięte':>9}  zbiór / powód pominięcia zasobu")
    for entry in report:
        status = f"POMINIĘTY: {entry['powod']}" if entry["powod"] else "przyjęty"
        lines.append(
            f"{entry['zasob']:>8}  {entry['format']:<8} {entry['przyjete']:>8} {entry['pominiete']:>9}  {entry['zbior']}"
        )
        lines.append(f"{'':>39}{status}")
        for skip in entry["pominiete_wiersze"]:
            lines.append(f"{'':>39}  wiersz {skip['wiersz']}: {skip['powod']}")
    accepted = sum(1 for entry in report if not entry["powod"])
    lines += [
        "",
        f"Przykład wzorca (format_danych/przyklady/aed_punkty_przyklad.csv): {example_rows} wierszy, "
        f"zgodność z aed_zestawienie_przyklad.csv: {'TAK' if matches else 'NIE'}",
        f"Dostawca zewnętrzny z opisem XML (format_danych/przyklady/opis/aed_dostawcy.csv, md5 zgodne z opisem): "
        f"{stats['wiersze_dostawcy']} wierszy",
        f"Zasoby realne: przyjęte {accepted}, pominięte {len(report) - accepted}.",
        f"Deduplikacja (aed_dedup.deduplicate_rows): wierszy przed {stats['wiersze_przed_deduplikacja']}, "
        f"pominięte duplikaty {stats['wiersze_zdeduplikowane']}.",
    ]
    for duplicate in stats["duplikaty"]:
        lines.append(f"  duplikat {duplicate['pominiety']} pominięty, bo to samo urządzenie co {duplicate['zachowany']} ({duplicate['powod']})")
    lines.append(f"Wiersze w demo/wynik/zestawienie_aed.csv: {total_rows} (kolumn: {stats['kolumny']}).")
    return "\n".join(lines) + "\n"


def main() -> int:
    aggregated_at = datetime.datetime.now().replace(microsecond=0).isoformat()
    report, parts = aggregate_real_sources(aggregated_at)
    example, matches = aggregate_example()
    supplier, supplier_skipped = aggregate_supplier(aggregated_at)
    merged = pd.concat(parts + [example, supplier], ignore_index=True)
    result, duplicates = dedup.deduplicate_rows(merged)
    accepted = [entry for entry in report if not entry["powod"]]
    stats = {
        "zrodlo": "demo/agreguj.py (bez bazy): migawka dane.gov.pl, przykład wzorca i plik dostawcy z opisem XML",
        "data_agregacji": aggregated_at,
        "zasoby_przyjete": len(accepted) + 2,
        "zasoby_pominiete": [{"resource_id": entry["zasob"], "powod": entry["powod"]} for entry in report if entry["powod"]],
        "wiersze": len(result),
        "wiersze_pominiete": sum(entry["pominiete"] for entry in accepted) + len(supplier_skipped),
        "wiersze_zdeduplikowane": len(duplicates),
        "duplikaty": duplicates,
        "wiersze_przed_deduplikacja": len(merged),
        "wiersze_dostawcy": len(supplier),
        "kolumny": len(result.columns),
    }

    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "zestawienie_aed.csv").write_bytes(aggregation.to_csv_bytes(result))
    (OUTPUT / "statystyki_agreguj.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    text = format_report(report, len(example), matches, len(result), aggregated_at, stats)
    (OUTPUT / "raport_agregacji.txt").write_text(text, encoding="utf-8", newline="\n")
    sys.stdout.reconfigure(encoding="utf-8")
    print(text, end="")
    return 0 if matches else 1


if __name__ == "__main__":
    sys.exit(main())
