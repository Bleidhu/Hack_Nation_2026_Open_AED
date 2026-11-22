"""Wejście z Gdańska: baza pojazdów ZTM (zasób 31843 z dane.gov.pl) – dane flotowe, nie punkty.

AED ma 278 z 503 pojazdów (autobusy i tramwaje), ale wzorzec v2 opisuje **punkty**
(`docs/06_DECYZJE_STRUKTURA_DANYCH_AED.md`: kolumny `id_pojazdu` nie ma). Adapter nie tworzy
wierszy punktowych – zwraca statystykę i jednoznaczny powód. Do zasobu zbiorczego trafiają
punkty, a nie flota.
"""
from __future__ import annotations

import json
from collections import Counter

from rdzen.wejscie import decode

POWOD = ("Baza pojazdów ZTM to dane flotowe (AED w autobusach i tramwajach), a nie punkty; "
         "wzorzec v2 nie ma kolumny pojazdu, więc te dane nie trafiają do wykazu punktów. "
         "Punkty AED w Gdańsku trzeba zgłosić osobnym zasobem.")


def wczytaj(data: bytes, filename: str = "") -> tuple:
    """([], meta). meta: format, pojazdy, pojazdy_z_aed, rozbicie_typow, powód."""
    obj = json.loads(decode(data))
    results = obj.get("results") if isinstance(obj, dict) else obj
    if not isinstance(results, list) or not results or not isinstance(results[0], dict):
        raise ValueError("Nierozpoznany plik: oczekiwano bazy pojazdów ZTM (lista `results`)")
    z_aed = [v for v in results if v.get("aed")]
    rozbicie = dict(sorted(Counter(str(v.get("transportationType") or "nieznany") for v in z_aed).items()))
    meta = {"format": "gdansk-ztm-pojazdy", "pojazdy": len(results), "pojazdy_z_aed": len(z_aed),
            "rozbicie_typow": rozbicie, "powod": POWOD, "wiersze": 0}
    return [], meta
