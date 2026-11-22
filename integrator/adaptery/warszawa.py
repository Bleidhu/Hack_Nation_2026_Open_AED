"""Wejście z API Warszawy (POST get_scb_lokalizacja_defibrylatorow): odpowiedź zapisana w pliku.

API wymaga tokenu użytkownika, dlatego adapter czyta **plik z odpowiedzią** zapisany przez
dostawcę albo przykład odpowiedzi wycięty z dokumentacji
(`references/dane_gov_pl_aed/warszawa_api/przyklad_wywolania.json`). Żadnych połączeń
sieciowych i żadnych tokenów w repo. Pole `attachment` (zdjęcie Base64) jest pomijane:
nie ma odpowiednika we wzorcu v2.
"""
from __future__ import annotations

import json
import re

from rdzen.wejscie import decode, geometry_point


def _features_z_dokumentacji(obj: list) -> list:
    """Plik z sekcjami dokumentacji: przykład odpowiedzi jest w treści sekcji „Przykład odpowiedzi”."""
    for sec in obj:
        if not isinstance(sec, dict) or sec.get("section_name") != "Przykład odpowiedzi":
            continue
        for el in sec.get("section_elements") or []:
            c = str(el.get("content", ""))
            i = c.find("[")
            if i < 0:
                continue
            # przykład kończy się „}, ...]” – wielokropek z przecinkiem usuwamy przed parsowaniem
            try:
                features = json.loads(re.sub(r",\s*\.\.\.", "", c[i:]).replace("...", ""))
            except ValueError:
                continue
            if isinstance(features, list) and features:
                return features
    return []


def _wiersz(f: dict) -> dict:
    p = {k: ("" if v is None else str(v)) for k, v in (f.get("properties") or {}).items()}
    p.pop("attachment", None)
    lat, lon = geometry_point(f.get("geometry"))
    p["__lat"], p["__lon"] = lat, lon
    return p


def wczytaj(data: bytes, filename: str = "") -> tuple:
    """(wiersze, meta). Rozpoznaje odpowiedź API (lista obiektów z `geometry`/`properties`)
    albo plik dokumentacji z przykładem odpowiedzi."""
    obj = json.loads(decode(data))
    if isinstance(obj, list) and obj and isinstance(obj[0], dict) and "geometry" in obj[0]:
        features = obj
    elif isinstance(obj, list) and obj and isinstance(obj[0], dict) and "section_name" in obj[0]:
        features = _features_z_dokumentacji(obj)
    else:
        features = None
    if features is None:
        raise ValueError("Nierozpoznany plik: oczekiwano odpowiedzi API (lista z geometry/properties) "
                          "lub dokumentacji z przykładem odpowiedzi")
    rows = [_wiersz(f) for f in features if isinstance(f, dict)]
    bez_wspolrzednych = sum(1 for r in rows if not r["__lat"])
    meta = {"format": "warszawa-api", "elementy": len(rows), "bez_wspolrzednych": bez_wspolrzednych}
    return rows, meta
