#!/usr/bin/env python3
"""
Integrator danych AED do wzorca v2 (41 kolumn). Cienka powłoka CLI nad `rdzen/`; tylko biblioteka standardowa.

    python integrator/importer.py plik.csv --mapowanie mapowanie.json --wyjscie wynik.csv --raport raport.json
    python integrator/importer.py plik.csv --podpowiedz       # propozycja mapowania kolumn

Wejście: CSV/TSV (UTF-8, CP1250), XLSX, GeoJSON, Overpass JSON. Presety: wzorzec, osm.
Wersja dla wzorca v1: wzorzec_v1/importer_v1.py (archiwum).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rdzen.mapowanie import PRESETS, apply_mapping, suggest_mapping  # noqa: E402
from rdzen.walidacja import validate  # noqa: E402
from rdzen.wejscie import read_input  # noqa: E402
from rdzen.zapis import to_csv, to_geojson  # noqa: E402,F401


def run(data: bytes, filename: str, mapping: dict = None, *, preset: str = None, defaults: dict = None) -> dict:
    headers, rows, fmt = read_input(data, filename)
    if mapping is None:
        mapping = PRESETS[preset] if preset else (PRESETS["osm"] if fmt == "osm" else suggest_mapping(headers))
    recs = apply_mapping(rows, mapping, defaults=defaults)
    return {"format": fmt, "kolumny_zrodla": headers, "mapowanie": mapping, "rekordy": recs, "raport": validate(recs),
            "licencja_zrodla": mapping.get("licencja_zrodla", "")}


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plik", type=Path)
    ap.add_argument("--mapowanie", type=Path)
    ap.add_argument("--preset", choices=sorted(PRESETS))
    ap.add_argument("--domyslne", type=Path, help="JSON z wartościami domyślnymi pól")
    ap.add_argument("--wyjscie", type=Path, help="CSV wynikowy (tylko poprawne rekordy)")
    ap.add_argument("--raport", type=Path, help="raport walidacji JSON")
    ap.add_argument("--podpowiedz", action="store_true", help="wypisz podpowiedź mapowania i zakończ")
    a = ap.parse_args()
    data = a.plik.read_bytes()
    if a.podpowiedz:
        h, _, fmt = read_input(data, a.plik.name)
        print(json.dumps(PRESETS["osm"] if fmt == "osm" else suggest_mapping(h), ensure_ascii=False, indent=2))
        return
    mapping = json.loads(a.mapowanie.read_text("utf-8")) if a.mapowanie else None
    defaults = json.loads(a.domyslne.read_text("utf-8")) if a.domyslne else None
    res = run(data, a.plik.name, mapping, preset=a.preset, defaults=defaults)
    r = res["raport"]
    print(f"format: {res['format']} · wiersze: {r['liczba_wierszy']} · poprawne: {r['poprawne']} · "
          f"z ostrzeżeniami: {r['z_ostrzezeniami']} · odrzucone: {r['odrzucone']}")
    for e in r["bledy"][:15]:
        print(f"  ✗ wiersz {e['wiersz']}: {e['pole']} – {e['komunikat']} ({e['wartosc']!r})")
    if a.wyjscie:
        a.wyjscie.write_text(to_csv(res["rekordy"]), "utf-8", newline="")
        print(f"zapisano {a.wyjscie}")
    if a.raport:
        a.raport.write_text(json.dumps(r, ensure_ascii=False, indent=2), "utf-8")


if __name__ == "__main__":
    main()
