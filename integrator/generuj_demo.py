"""Generuje przykładowe wyniki integratora do `demo/integrator/` (jedno polecenie, offline).

Uruchomienie z katalogu głównego repo:

    python integrator/generuj_demo.py

Powstaje `demo/integrator/`:
- `warszawa_wzorcowy_v2.csv` – odpowiedź API m.st. Warszawy (przykład z dokumentacji) jako CSV wzorca v2;
- `raport_warszawa.json`    – raport walidacji tego importu (licencja CC BY 4.0, cel: portal);
- `raport_duplikatow.json`  – kandydaci na duplikaty we wzorcowym pliku przykładowym v2;
- `raport_porownania_osm.json` – porównanie wykazu AED z portalu z OSM (Kraków; oznaczenie ODbL);
- `statystyka_gdansk.json`  – baza pojazdów ZTM: statystyka i powód braku wierszy punktowych;
- `README.md`               – opis tych plików z liczbami policzonymi przy generowaniu.

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


def odmiana(n: int, jeden: str, kilka: str, wiele: str) -> str:
    """Polska forma liczebnika: 1 pojazd, 2-4 pojazdy (bez 12-14), 5+ pojazdów."""
    if n == 1:
        return f"{n} {jeden}"
    return f"{n} {kilka if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14) else wiele}"


def readme(kolumny: int, dup: dict, por: dict, gdansk: dict) -> str:
    """README katalogu demo/integrator/ z liczbami policzonymi przy generowaniu (bez ręcznego przepisywania)."""
    formy = {"autobus": ("autobus", "autobusy", "autobusów"), "tramwaj": ("tramwaj", "tramwaje", "tramwajów")}
    typy = ", ".join(odmiana(v, *formy.get(k.lower(), (k.lower(),) * 3)) for k, v in gdansk["rozbicie_typow"].items())
    linie = [
        "# Przykładowe wyniki integratora",
        "",
        "Wszystkie pliki (także ten opis) generuje **jedno polecenie** z katalogu głównego repo (offline, na plikach z repozytorium):",
        "",
        "```bash",
        "python integrator/generuj_demo.py",
        "```",
        "",
        "| Plik | Co pokazuje |",
        "|---|---|",
        "| `warszawa_wzorcowy_v2.csv` | Odpowiedź API `get_scb_lokalizacja_defibrylatorow` m.st. Warszawy (przykład z dokumentacji "
        f"zbioru 39512) przepisana na {odmiana(kolumny, 'kolumnę', 'kolumny', 'kolumn')} wzorca v2. Jeden wiersz, licencja CC BY 4.0, dysponent jawny. |",
        "| `raport_warszawa.json` | Raport walidacji tego importu: 1 wiersz poprawny, pochodzenie i licencja. |",
        "| `raport_duplikatow.json` | Kandydaci na duplikaty we wzorcowym pliku przykładowym: "
        f"{dup['kandydaci']} (prawdopodobne: {dup['prawdopodobne']}, mało prawdopodobne: {dup['maloprawdopodobne']}). "
        "Para w tym samym punkcie o różnych nazwach jest oznaczona jako mało prawdopodobna (wiele AED w jednym miejscu to "
        "osobne wiersze). Integrator nic nie scala; scalanie duplikatów robi portal przy budowie Wykazu AED. |",
        "| `raport_porownania_osm.json` | Porównanie wykazu AED z portalu (`demo/wynik/zestawienie_aed.csv`, "
        f"{odmiana(por['wiersze_wykazu'], 'wiersz', 'wiersze', 'wierszy')}) z próbką OSM (Kraków, {odmiana(por['wiersze_osm'], 'element', 'elementy', 'elementów')}): `w obu {por['w_obu']} · "
        f"tylko w wykazie {por['tylko_w_wykazie']} · tylko w OSM {por['tylko_w_osm']}`. Raport ma oznaczenie ODbL: tylko do "
        "użytku lokalnego. |",
        f"| `statystyka_gdansk.json` | Baza pojazdów ZTM w Gdańsku (zasób 31843): {odmiana(gdansk['pojazdy'], 'pojazd', 'pojazdy', 'pojazdów')}, "
        f"{gdansk['pojazdy_z_aed']} z AED ({typy}). Zero wierszy punktowych z jednoznacznym powodem: dane flotowe, nie punkty. |",
        "",
        "Do samodzielnego przejścia całego przepływu (wgranie pliku, mapowanie, walidacja, duplikaty, porównanie z OSM, "
        "dopisanie rekordu) służy lokalny interfejs: `python integrator/ui/serwer.py`, adres `http://127.0.0.1:8765/` "
        "(bez internetu, pliki nie opuszczają komputera).",
        "",
        "Opis zbioru w XML z sumą md5 pliku CSV (wejście do portalu) buduje podkomenda `python integrator/importer.py opis …`; "
        "instrukcja w [`../../integrator/README.md`](../../integrator/README.md).",
        "",
    ]
    return "\n".join(linie)


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

    zapisz("README.md", readme(len(SCHEMA["fields"]), dup["podsumowanie"], por["podsumowanie"], res3["raport"]["gdansk"]))

    podsumowanie = {
        "warszawa": {"wiersze": 1, "licencja": res["pochodzenie"]["licencja"]},
        "duplikaty": res2["raport"]["liczba_wierszy"] and dup["podsumowanie"],
        "porownanie_osm": por["podsumowanie"],
        "gdansk": res3["raport"]["gdansk"],
    }
    print(json.dumps(podsumowanie, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
