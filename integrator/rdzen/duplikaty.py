"""Kandydaci na duplikaty: pary wierszy w promieniu o podobnej nazwie lub opisie lokalizacji.

Raport tylko flaguje pary; niczego nie scala i nie usuwa (docs/06 §3: wiele AED w jednym
miejscu to osobne wiersze). Funkcja czyta wiersze i nie modyfikuje ich. Siatka po współrzędnych
zamiast porównań każdy z każdym, żeby kilkadziesiąt tysięcy wierszy liczyło się w sekundach.
"""
from __future__ import annotations

import difflib
import math
from collections import defaultdict

from .wzorzec import PL_LAT, PL_LON, normalize_header

PROMIEN_DOMYSLNY = 25.0
PROG_PODOBIENSTWA = 0.6
META = 111320.0  # metry na stopę szerokości geograficznej


def wspolrzedne(r: dict):
    """(lat, lon) w granicach Polski albo None (wiersz bez współrzędnych nie bierze udziału)."""
    try:
        la = float(r.get("szerokosc_geograficzna", ""))
        lo = float(r.get("dlugosc_geograficzna", ""))
    except (TypeError, ValueError):
        return None
    if not (PL_LAT[0] <= la <= PL_LAT[1] and PL_LON[0] <= lo <= PL_LON[1]):
        return None
    return la, lo


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371008.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _text(r: dict) -> str:
    return normalize_header(" ".join([str(r.get("nazwa_lokalizacji", "")), str(r.get("opis_lokalizacji", ""))])).strip()


def podobienstwo(a: dict, b: dict) -> float:
    """Podobieństwo nazwy i opisu lokalizacji (SequenceMatcher, 2 miejsca po kropce)."""
    ta, tb = _text(a), _text(b)
    if not ta or not tb:
        return 0.0
    return round(difflib.SequenceMatcher(None, ta, tb).ratio(), 2)


def _zrodlo(r: dict) -> str:
    return str(r.get("zrodlo_danych", "") or r.get("zrodlo_url", ""))


def _pochodzenie(r: dict, i: int) -> dict:
    return {"wiersz": r.get("__wiersz") or i + 1, "zrodlo_danych": r.get("zrodlo_danych", ""),
            "id_zrodlowe": r.get("id_zrodlowe", ""), "dysponent_nazwa": r.get("dysponent_nazwa", "")}


def znajdz_kandydatow(rekordy: list, *, promien: float = PROMIEN_DOMYSLNY,
                      prog_podobienstwa: float = PROG_PODOBIENSTWA) -> dict:
    """Raport par kandydatów na duplikaty. Reguły:

    1. Odległość haversine ≤ `promien` (domyślnie 25 m).
    2. Para z tym samym `id_zrodlowe` w tym samym źródle to ten sam rekord, nie duplikat.
    3. Kondygnacja lub opis się różnią → mniejsza pewność; różna kondygnacja → „mało prawdopodobny”.
    """
    cell_lat = promien / META
    cell_lon = promien / (META * math.cos(math.radians(52.0)))
    grid = defaultdict(list)
    punkty = 0
    for i, r in enumerate(rekordy):
        c = wspolrzedne(r)
        if c:
            punkty += 1
            grid[(int(c[0] // cell_lat), int(c[1] // cell_lon))].append(i)

    kandydaci = set()
    for (cy, cx), members in grid.items():
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                for j in grid.get((cy + dy, cx + dx), ()):
                    for i in members:
                        if i != j:
                            kandydaci.add((i, j) if i < j else (j, i))

    pary = []
    for i, j in sorted(kandydaci):
        a, b = rekordy[i], rekordy[j]
        if _zrodlo(a) == _zrodlo(b) and a.get("id_zrodlowe") and a.get("id_zrodlowe") == b.get("id_zrodlowe"):
            continue
        ca, cb = wspolrzedne(a), wspolrzedne(b)
        d = haversine(ca[0], ca[1], cb[0], cb[1])
        if d > promien:
            continue
        sim = podobienstwo(a, b)
        ta_sama = (a.get("dysponent_nazwa") and a.get("dysponent_nazwa") == b.get("dysponent_nazwa"))
        pewnosc, powody = "prawdopodobny", []
        if a.get("kondygnacja") and b.get("kondygnacja") and normalize_header(a["kondygnacja"]) != normalize_header(b["kondygnacja"]):
            pewnosc = "maloprawdopodobny"
            powody.append("różna kondygnacja")
        if sim < prog_podobienstwa:
            pewnosc = "maloprawdopodobny"
            powody.append(f"podobieństwo {sim} < {prog_podobienstwa}")
        pary.append({"indeks_a": i, "indeks_b": j,
                     "pochodzenie_a": _pochodzenie(a, i), "pochodzenie_b": _pochodzenie(b, j),
                     "odleglosc_m": round(d, 1), "podobienstwo": sim,
                     "przyczyna": "ta_sama_instytucja" if ta_sama else "rozne_instytucje",
                     "pewnosc": pewnosc, "powody_niskiej_pewnosci": powody})

    podsumowanie = {"kandydaci": len(pary),
                    "prawdopodobne": sum(1 for p in pary if p["pewnosc"] == "prawdopodobny"),
                    "maloprawdopodobne": sum(1 for p in pary if p["pewnosc"] == "maloprawdopodobny"),
                    "ta_sama_instytucja": sum(1 for p in pary if p["przyczyna"] == "ta_sama_instytucja"),
                    "rozne_instytucje": sum(1 for p in pary if p["przyczyna"] == "rozne_instytucje")}
    return {"promien_m": promien, "prog_podobienstwa": prog_podobienstwa,
            "liczba_wierszy": len(rekordy), "wiersze_ze_wspolrzednymi": punkty,
            "pary": pary, "podsumowanie": podsumowanie,
            "uwaga": "Raport tylko flaguje kandydatów na duplikaty; niczego nie scala i nie usuwa."}
