#!/usr/bin/env python3
"""
Integrator danych AED do wzorca v2 (41 kolumn). Cienka powłoka CLI nad `rdzen/`; tylko biblioteka standardowa.

    python integrator/importer.py plik.csv --licencja "CC0 1.0" --mapowanie mapowanie.json --wyjscie wynik.csv --raport raport.json
    python integrator/importer.py plik.csv --podpowiedz       # propozycja mapowania kolumn

Wejście: CSV/TSV (UTF-8, CP1250), XLSX, GeoJSON, Overpass JSON. Presety: wzorzec, osm.
Licencja źródła jest jawna (--licencja); ODbL (preset osm) tylko z --cel lokalny.
Wersja dla wzorca v1: wzorzec_v1/importer_v1.py (archiwum).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from adaptery.osm import tagi_bez_odpowiednika, wczytaj as osm_wczytaj  # noqa: E402
from rdzen.duplikaty import PROMIEN_DOMYSLNY, znajdz_kandydatow  # noqa: E402
from rdzen.licencje import LicencjaBlad, sprawdz, wczytaj_konfiguracje  # noqa: E402
from rdzen.mapowanie import PRESETS, apply_mapping, suggest_mapping  # noqa: E402
from rdzen.walidacja import validate  # noqa: E402
from rdzen.wejscie import read_input  # noqa: E402
from rdzen.zapis import to_csv, to_geojson  # noqa: E402,F401


def run(data: bytes, filename: str, mapping: dict = None, *, preset: str = None, defaults: dict = None,
        licencja: str = None, cel: str = "portal", konfiguracja: dict = None) -> dict:
    """cel=portal: wymaga jawnej, dozwolonej licencji (inaczej LicencjaBlad); cel=lokalny: licencja spoza listy to ostrzeżenie."""
    osm = preset == "osm" or (mapping or {}).get("typ_zrodla") == "osm"
    if osm:
        mapping = mapping or PRESETS["osm"]
        rows, meta = osm_wczytaj(data, filename)
        headers, fmt = sorted({k for r in rows for k in r}), meta["format"]
    else:
        headers, rows, fmt = read_input(data, filename)
        if mapping is None:
            mapping = PRESETS[preset] if preset else (PRESETS["osm"] if fmt == "osm" else suggest_mapping(headers))
            osm = fmt == "osm"
            if osm:
                rows, meta = osm_wczytaj(data, filename)
    pochodzenie = sprawdz(licencja or mapping.get("licencja_zrodla", ""), cel, konfiguracja or wczytaj_konfiguracje())
    recs = apply_mapping(rows, mapping, defaults=defaults)
    raport = validate(recs, luzna=cel == "lokalny" and mapping.get("walidacja") == "luzna")
    if osm:
        raport["osm"] = {"format": meta["format"], "elementy": len(rows) + len(meta["pominiete"]), "przyjete": len(rows),
                         "timestamp_osm_base": meta["timestamp_osm_base"], "pominiete": meta["pominiete"],
                         "tagi_bez_odpowiednika": tagi_bez_odpowiednika(rows, mapping)}
    raport["pochodzenie"] = {**pochodzenie, "cel": cel, "zrodlo_danych": sorted({r["zrodlo_danych"] for r in recs if r["zrodlo_danych"]})}
    return {"format": fmt, "kolumny_zrodla": headers, "mapowanie": mapping, "rekordy": recs, "raport": raport,
            "licencja_zrodla": pochodzenie["licencja"], "pochodzenie": raport["pochodzenie"]}


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plik", type=Path)
    ap.add_argument("--mapowanie", type=Path)
    ap.add_argument("--preset", choices=sorted(PRESETS))
    ap.add_argument("--licencja", help="licencja źródła (wymagana dla --cel portal), np. 'CC0 1.0', 'CC BY 4.0'")
    ap.add_argument("--cel", choices=("portal", "lokalny"), default="portal",
                    help="portal: tylko licencje z konfiguracja.json; lokalny: ostrzeżenie zamiast odmowy")
    ap.add_argument("--domyslne", type=Path, help="JSON z wartościami domyślnymi pól")
    ap.add_argument("--wyjscie", type=Path, help="CSV wynikowy (tylko poprawne rekordy)")
    ap.add_argument("--raport", type=Path, help="raport walidacji JSON")
    ap.add_argument("--duplikaty", type=Path, help="raport kandydatów na duplikaty JSON (tylko flaguje, bez scalania)")
    ap.add_argument("--promien", type=float, default=PROMIEN_DOMYSLNY, help="promień dopasowania w metrach (do --duplikaty)")
    ap.add_argument("--podpowiedz", action="store_true", help="wypisz podpowiedź mapowania i zakończ")
    a = ap.parse_args()
    data = a.plik.read_bytes()
    if a.podpowiedz:
        h, _, fmt = read_input(data, a.plik.name)
        print(json.dumps(PRESETS["osm"] if fmt == "osm" else suggest_mapping(h), ensure_ascii=False, indent=2))
        return
    mapping = json.loads(a.mapowanie.read_text("utf-8")) if a.mapowanie else None
    defaults = json.loads(a.domyslne.read_text("utf-8")) if a.domyslne else None
    try:
        res = run(data, a.plik.name, mapping, preset=a.preset, defaults=defaults, licencja=a.licencja, cel=a.cel)
    except LicencjaBlad as e:
        sys.exit(f"Odmowa: {e}\nDla użytku lokalnego i porównań dodaj --cel lokalny.")
    r = res["raport"]
    print(f"format: {res['format']} · wiersze: {r['liczba_wierszy']} · poprawne: {r['poprawne']} · "
          f"z ostrzeżeniami: {r['z_ostrzezeniami']} · odrzucone: {r['odrzucone']}")
    if r["pochodzenie"]["ostrzezenie"]:
        print("  ! " + r["pochodzenie"]["ostrzezenie"])
    if "osm" in r:
        o = r["osm"]
        print(f"  OSM: elementy {o['elementy']}, przyjęte {o['przyjete']}, pominięte {len(o['pominiete'])}, "
              f"tagi bez odpowiednika: {sum(o['tagi_bez_odpowiednika'].values())} ({len(o['tagi_bez_odpowiednika'])} rodzajów)")
    for e in r["bledy"][:15]:
        print(f"  ✗ wiersz {e['wiersz']}: {e['pole']} – {e['komunikat']} ({e['wartosc']!r})")
    if a.wyjscie:
        a.wyjscie.write_text(to_csv(res["rekordy"]), "utf-8", newline="")
        print(f"zapisano {a.wyjscie}")
    if a.raport:
        a.raport.write_text(json.dumps(r, ensure_ascii=False, indent=2), "utf-8")
    if a.duplikaty:
        rap = znajdz_kandydatow([rec for rec in res["rekordy"] if rec.get("__status") != "odrzucony"],
                                promien=a.promien)
        a.duplikaty.write_text(json.dumps(rap, ensure_ascii=False, indent=2), "utf-8")
        s = rap["podsumowanie"]
        print(f"kandydaci na duplikaty: {s['kandydaci']} (prawdopodobne: {s['prawdopodobne']}, "
              f"mało prawdopodobne: {s['maloprawdopodobne']}) → {a.duplikaty}")


if __name__ == "__main__":
    main()
