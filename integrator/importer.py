#!/usr/bin/env python3
"""
Integrator danych AED do wzorca v2 (42 kolumny). Cienka powłoka CLI nad `rdzen/`; tylko biblioteka standardowa.

    python integrator/importer.py plik.csv --licencja "CC0 1.0" --mapowanie mapowanie.json --wyjscie wynik.csv --raport raport.json
    python integrator/importer.py plik.csv --podpowiedz       # propozycja mapowania kolumn
    python integrator/importer.py opis aed.csv --link-csv https://... --tytul ... --opis ... --dysponent ... --licencja "CC BY 4.0" --czestotliwosc daily
                                                               # opis zbioru XML z md5 pliku CSV (wejście do portalu)

Wejście: CSV/TSV (UTF-8, CP1250), XLSX, GeoJSON, Overpass JSON. Presety: wzorzec, osm, warszawa (odpowiedź API um.warszawa.pl z pliku), gdansk (baza pojazdów ZTM – tylko statystyka).
Licencja źródła jest jawna (--licencja); ODbL (preset osm) tylko z --cel lokalny.
Wersja dla wzorca v1: archive/integrator/wzorzec_v1/importer_v1.py (archiwum, niedostępna z tego katalogu).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from adaptery.gdansk import wczytaj as gdansk_wczytaj  # noqa: E402
from adaptery.osm import tagi_bez_odpowiednika, wczytaj as osm_wczytaj  # noqa: E402
from adaptery.warszawa import wczytaj as warszawa_wczytaj  # noqa: E402
from rdzen.duplikaty import PROMIEN_DOMYSLNY, znajdz_kandydatow  # noqa: E402
from rdzen.licencje import LicencjaBlad, sprawdz, wczytaj_konfiguracje  # noqa: E402
from rdzen.opis_xml import OpisBlad, suma_md5, zbuduj_opis  # noqa: E402
from rdzen.mapowanie import PRESETS, apply_mapping, suggest_mapping  # noqa: E402
from rdzen.porownanie import porownaj  # noqa: E402
from rdzen.rekord import RekordBlad, dopisz, sprawdz_rekord, wczytaj_istniejace, zbuduj  # noqa: E402
from rdzen.walidacja import validate  # noqa: E402
from rdzen.wejscie import read_input  # noqa: E402
from rdzen.wzorzec import SCHEMA  # noqa: E402
from rdzen.zapis import to_csv, to_geojson  # noqa: E402,F401

ADAPTERY = {"osm": osm_wczytaj, "warszawa": warszawa_wczytaj, "gdansk": gdansk_wczytaj}


def run(data: bytes, filename: str, mapping: dict = None, *, preset: str = None, defaults: dict = None,
        licencja: str = None, cel: str = "portal", konfiguracja: dict = None) -> dict:
    """cel=portal: wymaga jawnej, dozwolonej licencji (inaczej LicencjaBlad); cel=lokalny: licencja spoza listy to ostrzeżenie."""
    typ = preset or (mapping or {}).get("typ_zrodla") or ""
    adapter = ADAPTERY.get(typ)
    osm = typ == "osm" or (mapping or {}).get("typ_zrodla") == "osm"
    if adapter:
        mapping = mapping or PRESETS[typ]
        rows, meta = adapter(data, filename)
        headers, fmt = sorted({k for r in rows for k in r}), meta["format"]
    else:
        headers, rows, fmt = read_input(data, filename)
        if mapping is None:
            mapping = PRESETS[preset] if preset else (PRESETS["osm"] if fmt == "osm" else suggest_mapping(headers))
        osm = osm or fmt == "osm" or (mapping or {}).get("typ_zrodla") == "osm"
        if osm:
            rows, meta = osm_wczytaj(data, filename)
    pochodzenie = sprawdz(licencja or mapping.get("licencja_zrodla", ""), cel, konfiguracja or wczytaj_konfiguracje())
    recs = apply_mapping(rows, mapping, defaults=defaults)
    raport = validate(recs, luzna=cel == "lokalny" and mapping.get("walidacja") == "luzna")
    if osm:
        raport["osm"] = {"format": meta["format"], "elementy": len(rows) + len(meta["pominiete"]), "przyjete": len(rows),
                         "timestamp_osm_base": meta["timestamp_osm_base"], "pominiete": meta["pominiete"],
                         "tagi_bez_odpowiednika": tagi_bez_odpowiednika(rows, mapping)}
    if fmt == "gdansk-ztm-pojazdy":
        raport["gdansk"] = {"pojazdy": meta["pojazdy"], "pojazdy_z_aed": meta["pojazdy_z_aed"],
                            "rozbicie_typow": meta["rozbicie_typow"], "powod": meta["powod"]}
    raport["pochodzenie"] = {**pochodzenie, "cel": cel, "zrodlo_danych": sorted({r["zrodlo_danych"] for r in recs if r["zrodlo_danych"]})}
    return {"format": fmt, "kolumny_zrodla": headers, "mapowanie": mapping, "rekordy": recs, "raport": raport,
            "licencja_zrodla": pochodzenie["licencja"], "pochodzenie": raport["pochodzenie"]}


def _dodaj(argv) -> None:
    """Podkomenda `dodaj`: dopisz jeden rekord AED do pliku CSV zgodnego ze wzorcem v2."""
    ap = argparse.ArgumentParser(prog="importer.py dodaj",
                                 description="Dopisz jeden rekord AED do pliku CSV wzorca v2 "
                                             "(dla dostawców bez własnego systemu). Pola = kolumny wzorca.")
    ap.add_argument("plik", type=Path)
    for f in SCHEMA["fields"]:
        opis = (f.get("description") or "").split("–")[0].strip()
        ap.add_argument("--" + f["name"], help=opis or None)
    ap.add_argument("--prefiks-id", default="AED", help="prefiks propozycji id_zrodlowe, gdy --id_zrodlowe puste")
    ap.add_argument("--tak", action="store_true", help="zapisz mimo kandydatów na duplikaty (raport i tak ich nie scala)")
    a = ap.parse_args(argv)
    sciezka = a.plik
    istniejace = wczytaj_istniejace(sciezka)
    pola = {f["name"]: getattr(a, f["name"]) for f in SCHEMA["fields"] if getattr(a, f["name"]) is not None}
    try:
        rec = zbuduj(pola, prefiks=a.prefiks_id, istniejace_id={r.get("id_zrodlowe", "") for r in istniejace})
    except RekordBlad as e:
        sys.exit(f"Błąd: {e}")
    wynik = sprawdz_rekord(rec, istniejace)
    for e in wynik["bledy"]:
        print(f"  ✗ {e['pole']}: {e['komunikat']} ({e['wartosc']!r})")
    for p in wynik["kandydaci"]:
        q = p["pochodzenie_a"]
        print(f"  ? możliwy duplikat: {q['id_zrodlowe'] or ('wiersz ' + str(q['wiersz']))} "
              f"({p['odleglosc_m']} m, podobieństwo {p['podobienstwo']}, pewność: {p['pewnosc']})")
    if wynik["bledy"]:
        sys.exit("rekord odrzucony – popraw pola i uruchom ponownie")
    if wynik["kandydaci"] and not a.tak:
        sys.exit("sprawdź kandydatów powyżej; aby zapisać mimo to, dodaj --tak")
    nowy_plik = not sciezka.exists()
    dopisz(sciezka, rec)
    print(f"dopisano {rec['id_zrodlowe']} do {sciezka}" + (" (plik utworzony z nagłówkiem)" if nowy_plik else ""))


def _opis(argv) -> None:
    """Podkomenda `opis`: opis zbioru XML z sumą md5 pliku CSV (wejście do portalu)."""
    ap = argparse.ArgumentParser(prog="importer.py opis",
                                 description="Zbuduj opis zbioru XML (schemat format_danych/schemat/aed_opis_zbioru.xsd) "
                                             "dla pliku CSV zgodnego ze wzorcem. Plik CSV i opis.xml należy wystawić "
                                             "pod https bez zmian (md5 liczone z bajtów CSV).")
    ap.add_argument("plik", type=Path, help="CSV zgodny ze wzorcem")
    ap.add_argument("--link-csv", required=True, help="docelowy adres https pliku CSV")
    ap.add_argument("--tytul", required=True)
    ap.add_argument("--opis", required=True)
    ap.add_argument("--dysponent", required=True, help="nazwa dysponenta danych")
    ap.add_argument("--licencja", required=True, help="'CC0 1.0' lub 'CC BY 4.0'")
    ap.add_argument("--czestotliwosc", required=True,
                    help="daily, weekly, monthly, quarterly, everyHalfYear, yearly, irregular")
    ap.add_argument("--regon")
    ap.add_argument("--email")
    ap.add_argument("--tytul-zasobu", help="tytuł zasobu CSV (domyślnie „Lokalizacje AED (CSV)”)")
    ap.add_argument("--wyjscie", type=Path, help="katalog zapisu opis.xml (domyślnie katalog pliku CSV)")
    a = ap.parse_args(argv)
    dane = a.plik.read_bytes()
    try:
        xml = zbuduj_opis(dane, link_csv=a.link_csv, tytul=a.tytul, opis=a.opis, dysponent=a.dysponent,
                          licencja=a.licencja, czestotliwosc=a.czestotliwosc, regon=a.regon, email=a.email,
                          tytul_zasobu=a.tytul_zasobu)
    except OpisBlad as e:
        sys.exit(f"Błąd: {e}")
    katalog = a.wyjscie or a.plik.parent
    katalog.mkdir(parents=True, exist_ok=True)
    cel = katalog / "opis.xml"
    cel.write_text(xml, "utf-8", newline="")
    print(f"zapisano {cel} (md5 {suma_md5(dane)}); opublikuj {a.plik.name} pod {a.link_csv} bez zmian")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    if len(sys.argv) > 1 and sys.argv[1] == "dodaj":
        return _dodaj(sys.argv[2:])
    if len(sys.argv) > 1 and sys.argv[1] == "opis":
        return _opis(sys.argv[2:])
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
    ap.add_argument("--porownaj-z-osm", type=Path, metavar="PLIK",
                    help="porównaj `plik` (wykaz AED z portalu) z PLIKiem OSM; raport JSON wymaga --raport")
    ap.add_argument("--promien", type=float, default=PROMIEN_DOMYSLNY, help="promień dopasowania w metrach (do --duplikaty)")
    ap.add_argument("--podpowiedz", action="store_true", help="wypisz podpowiedź mapowania i zakończ")
    a = ap.parse_args()
    data = a.plik.read_bytes()
    if a.porownaj_z_osm:
        if not a.raport:
            sys.exit("--porownaj-z-osm wymaga --raport (ścieżka raportu porównania JSON)")
        _, wykaz_rows, _ = read_input(data, a.plik.name)
        osm_rows, _ = osm_wczytaj(a.porownaj_z_osm.read_bytes(), a.porownaj_z_osm.name)
        rap = porownaj(wykaz_rows, apply_mapping(osm_rows, PRESETS["osm"]), promien=a.promien)
        a.raport.write_text(json.dumps(rap, ensure_ascii=False, indent=2), "utf-8")
        s = rap["podsumowanie"]
        print(f"porównanie z OSM ({a.porownaj_z_osm.name}, promień {rap['promien_m']} m): "
              f"w obu {s['w_obu']} · tylko w wykazie {s['tylko_w_wykazie']} · tylko w OSM {s['tylko_w_osm']}")
        if s["pary_do_sprawdzenia"]:
            print(f"  pary do sprawdzenia (różna kondygnacja): {s['pary_do_sprawdzenia']}")
        print(f"  ! {rap['oznaczenie']}")
        print(f"zapisano {a.raport}")
        return
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
    if "gdansk" in r:
        g = r["gdansk"]
        rozbicie = ", ".join(f"{k}: {v}" for k, v in g["rozbicie_typow"].items())
        print(f"  Gdańsk ZTM: pojazdy {g['pojazdy']}, z AED {g['pojazdy_z_aed']} ({rozbicie}); wierszy punktowych: 0")
        print(f"  ! {g['powod']}")
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
