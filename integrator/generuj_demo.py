"""Generuje przykładowe wyniki integratora do `demo/integrator/` (jedno polecenie, offline).

Uruchomienie z katalogu głównego repo:

    python integrator/generuj_demo.py

Powstaje `demo/integrator/`:
- `warszawa_wzorcowy_v2.csv` – odpowiedź API m.st. Warszawy (przykład z dokumentacji) jako CSV wzorca v2;
- `raport_warszawa.json`    – raport walidacji tego importu (licencja CC BY 4.0, cel: portal);
- `raport_duplikatow.json`  – kandydaci na duplikaty we wzorcowym pliku przykładowym v2;
- `raport_porownania_osm.json` – porównanie wykazu AED z portalu z OSM (Kraków; oznaczenie ODbL);
- `statystyka_gdansk.json`  – baza pojazdów ZTM: statystyka i powód braku wierszy punktowych.

Wszystkie pliki są deterministyczne: pochodzą z plików w repo, bez sieci.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

INTEGRATOR = Path(__file__).resolve().parent
sys.path.insert(0, str(INTEGRATOR))

import importer  # noqa: E402
from adaptery.osm import wczytaj as osm_wczytaj  # noqa: E402
from rdzen.duplikaty import znajdz_kandydatow  # noqa: E402
from rdzen.mapowanie import PRESETS, apply_mapping  # noqa: E402
from rdzen.porownanie import porownaj  # noqa: E402
from rdzen.wejscie import read_input  # noqa: E402
from rdzen.wzorzec import SCHEMA  # noqa: E402

ROOT = INTEGRATOR.parent
OUT = ROOT / "demo" / "integrator"
REFERENCES = ROOT / "references" / "dane_gov_pl_aed"


def zapisz(nazwa: str, tresc: str) -> None:
    (OUT / nazwa).write_text(tresc, "utf-8", newline="")
    print(f"zapisano demo/integrator/{nazwa}")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    # 1. Warszawa: odpowiedź API z dokumentacji → CSV zgodny ze wzorcem v2 (CC BY 4.0, cel portal)
    dane = (REFERENCES / "warszawa_api" / "przyklad_wywolania.json").read_bytes()
    res = importer.run(dane, "przyklad_wywolania.json", preset="warszawa", cel="portal")
    dobre = [rec for rec in res["rekordy"] if rec.get("__status") != "odrzucony"]
    assert res["raport"]["poprawne"] == 1 and res["pochodzenie"]["do_publikacji"]
    zapisz("warszawa_wzorcowy_v2.csv", importer.to_csv(dobre))
    raport = res["raport"]
    for rec in res["rekordy"]:
        rec.pop("__bledy", None)
        rec.pop("__status", None)
        rec.pop("__ostrzezenia", None)
    zapisz("raport_warszawa.json", json.dumps(raport, ensure_ascii=False, indent=2))

    # 2. Duplikaty: wzorcowy plik przykładowy v2 (8 wierszy, 1 kandydat w tym samym punkcie)
    przyklad = (ROOT / "format_danych" / "przyklady" / "aed_punkty_przyklad.csv").read_bytes()
    res2 = importer.run(przyklad, "aed_punkty_przyklad.csv", preset="wzorzec", licencja="CC0 1.0", cel="portal")
    dobre2 = [rec for rec in res2["rekordy"] if rec.get("__status") != "odrzucony"]
    dup = znajdz_kandydatow(dobre2)
    zapisz("raport_duplikatow.json", json.dumps(dup, ensure_ascii=False, indent=2))

    # 3. Porównanie wykazu z OSM (lokalnie, ODbL): wykaz z portalu + próbka OSM Kraków
    wykaz = (ROOT / "demo" / "wynik" / "zestawienie_aed.csv").read_bytes()
    osm = (INTEGRATOR / "dane_przykladowe" / "01_integrator_osm" / "osm_overpass_krakow.json").read_bytes()
    _, wykaz_rows, _ = read_input(wykaz, "zestawienie_aed.csv")
    osm_rows, _ = osm_wczytaj(osm, "osm_overpass_krakow.json")
    por = porownaj(wykaz_rows, apply_mapping(osm_rows, PRESETS["osm"]))
    zapisz("raport_porownania_osm.json", json.dumps(por, ensure_ascii=False, indent=2))

    # 4. Gdańsk: baza pojazdów ZTM – statystyka zamiast wierszy punktowych
    ztm = (REFERENCES / "gdansk_ztm" / "zasob_31843_baza_pojazdow.json").read_bytes()
    res3 = importer.run(ztm, "zasob_31843_baza_pojazdow.json", preset="gdansk", cel="portal")
    zapisz("statystyka_gdansk.json", json.dumps(res3["raport"]["gdansk"], ensure_ascii=False, indent=2))

    podsumowanie = {
        "warszawa": {"wiersze": 1, "licencja": res["pochodzenie"]["licencja"]},
        "duplikaty": res2["raport"]["liczba_wierszy"] and dup["podsumowanie"],
        "porownanie_osm": por["podsumowanie"],
        "gdansk": res3["raport"]["gdansk"],
    }
    print(json.dumps(podsumowanie, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
