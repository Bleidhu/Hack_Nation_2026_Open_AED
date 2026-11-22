"""Porównanie wykazu AED (CSV z portalu) z rekordami OSM: w obu, tylko w wykazie, tylko w OSM.

Czyste funkcje na dwóch listach słowników o kolumnach wzorca v2 (wykaz z portalu może mieć
kolumny dodatkowe, np. `id_aed`). Dopasowanie reuse'uje logikę z `duplikaty.py` (promień,
podobieństwo nazwy i opisu), bez jej kopiowania. Raport służy dostawcom i dyspozytorom do
sprawdzenia kompletności; danych OSM nie publikujemy (oznaczenie licencyjne w każdym raporcie).
"""
from __future__ import annotations

import math
from collections import defaultdict

from .duplikaty import (META, PROMIEN_DOMYSLNY, PROG_PODOBIENSTWA, haversine, podobienstwo, wspolrzedne)
from .wzorzec import normalize_header

OZNACZENIE = ("Raport zawiera dane z OpenStreetMap (ODbL): tylko do użytku lokalnego, "
              "nie do publikacji w portalu jako CC0 / CC BY.")


def _kondygnacje_rozne(a: dict, b: dict) -> bool:
    ka = normalize_header(str(a.get("kondygnacja", "") or ""))
    kb = normalize_header(str(b.get("kondygnacja", "") or ""))
    return bool(ka) and bool(kb) and ka != kb


def _strona_wykazu(r: dict, i: int) -> dict:
    return {"wiersz": r.get("__wiersz") or i + 1, "id_aed": r.get("id_aed", ""), "id_zrodlowe": r.get("id_zrodlowe", ""),
            "nazwa_lokalizacji": r.get("nazwa_lokalizacji", ""),
            "szerokosc_geograficzna": r.get("szerokosc_geograficzna", ""), "dlugosc_geograficzna": r.get("dlugosc_geograficzna", ""),
            "zrodlo_danych": r.get("zrodlo_danych", "")}


def _strona_osm(r: dict) -> dict:
    """Minimum potrzebne do sprawdzenia: identyfikator OSM i współrzędne, bez pełnych rekordów."""
    return {"id_zrodlowe": r.get("id_zrodlowe", ""), "zrodlo_url": r.get("zrodlo_url", ""),
            "szerokosc_geograficzna": r.get("szerokosc_geograficzna", ""), "dlugosc_geograficzna": r.get("dlugosc_geograficzna", "")}


def porownaj(wykaz: list, osm: list, *, promien: float = PROMIEN_DOMYSLNY,
             prog_podobienstwa: float = PROG_PODOBIENSTWA) -> dict:
    """Dopasowanie jedno-do-jednego po najmniejszej odległości w promieniu `promien` metrów.

    Para w promieniu z różną kondygnacją to prawdopodobnie różne urządzenia (docs/06 §3):
    trafia do `pary_do_sprawdzenia`, a nie do `w_obu`.
    """
    cell_lat = promien / META
    cell_lon = promien / (META * math.cos(math.radians(52.0)))
    grid = defaultdict(list)
    wspolrzedne_wykaz = {}
    for j, r in enumerate(wykaz):
        c = wspolrzedne(r)
        if c:
            wspolrzedne_wykaz[j] = c
            grid[(int(c[0] // cell_lat), int(c[1] // cell_lon))].append(j)

    kandydaci = []
    for i, r in enumerate(osm):
        c = wspolrzedne(r)
        if not c:
            continue
        cy, cx = int(c[0] // cell_lat), int(c[1] // cell_lon)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                for j in grid.get((cy + dy, cx + dx), ()):
                    d = haversine(c[0], c[1], *wspolrzedne_wykaz[j])
                    if d <= promien:
                        kandydaci.append((round(d, 6), i, j))

    w_obu, pary_do_sprawdzenia = [], []
    uzyte_wykaz, uzyte_osm = set(), set()
    bez_wspolrzednych = {"wykaz": len(wykaz) - len(wspolrzedne_wykaz)}
    for d, i, j in sorted(kandydaci):
        if i in uzyte_osm or j in uzyte_wykaz:
            continue
        a, b = wykaz[j], osm[i]
        if _kondygnacje_rozne(a, b):
            pary_do_sprawdzenia.append({"wykaz": _strona_wykazu(a, j), "osm": _strona_osm(b),
                                        "odleglosc_m": round(d, 1), "powod": "różna kondygnacja"})
            continue
        uzyte_osm.add(i)
        uzyte_wykaz.add(j)
        sim = podobienstwo(a, b)
        w_obu.append({"wykaz": _strona_wykazu(a, j), "osm": _strona_osm(b), "odleglosc_m": round(d, 1),
                      "podobienstwo": sim, "pewnosc": "duza" if sim >= prog_podobienstwa else "niska"})

    tylko_w_wykazie = [_strona_wykazu(wykaz[j], j) for j in range(len(wykaz)) if j not in uzyte_wykaz]
    tylko_w_osm = [_strona_osm(osm[i]) for i in range(len(osm)) if i not in uzyte_osm]
    bez_wspolrzednych["osm"] = sum(1 for r in osm if not wspolrzedne(r))
    podsumowanie = {"wiersze_wykazu": len(wykaz), "wiersze_osm": len(osm), "w_obu": len(w_obu),
                    "tylko_w_wykazie": len(tylko_w_wykazie), "tylko_w_osm": len(tylko_w_osm),
                    "pary_do_sprawdzenia": len(pary_do_sprawdzenia),
                    "bez_wspolrzednych": bez_wspolrzednych}
    return {"oznaczenie": OZNACZENIE, "promien_m": promien, "prog_podobienstwa": prog_podobienstwa,
            "podsumowanie": podsumowanie, "w_obu": w_obu,
            "tylko_w_wykazie": tylko_w_wykazie, "tylko_w_osm": tylko_w_osm,
            "pary_do_sprawdzenia": pary_do_sprawdzenia}
