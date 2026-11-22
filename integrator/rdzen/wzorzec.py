"""Wzorzec v2 (41 kolumn): kolumny, typy, słowniki i minimum czytane z ../format_danych/schemat/."""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SCHEMAT = ROOT / "format_danych" / "schemat"

SCHEMA = json.loads((SCHEMAT / "aed_punkty.tableschema.json").read_text("utf-8"))
FIELDS = [f["name"] for f in SCHEMA["fields"]]
FIELD = {f["name"]: f for f in SCHEMA["fields"]}
MINIMUM = list(SCHEMA["x-minimum-agregacji"])
SLOWNIKI = json.loads((SCHEMAT / "slowniki.json").read_text("utf-8"))

PL_LAT = (49.0, 54.9)
PL_LON = (14.1, 24.2)

# Kopia AED_HEADER_ALIASES z portal/backend/mcod/resources/aed_constants.py (test_rdzen_v2 pilnuje zgodności).
HEADER_ALIASES = {
    "nazwa": "nazwa_lokalizacji", "name": "nazwa_lokalizacji",
    "nr_budynku": "numer_budynku", "numer_domu": "numer_budynku", "home_number": "numer_budynku",
    "nr_lokalu": "numer_lokalu",
    "szerokosc": "szerokosc_geograficzna", "lat": "szerokosc_geograficzna", "latitude": "szerokosc_geograficzna",
    "dlugosc": "dlugosc_geograficzna", "lon": "dlugosc_geograficzna", "lng": "dlugosc_geograficzna",
    "longitude": "dlugosc_geograficzna",
    "miasto": "miejscowosc", "city": "miejscowosc",
    "ulica": "nazwa_ulicy", "street": "nazwa_ulicy",
    "kod": "kod_pocztowy", "postcode": "kod_pocztowy",
    "telefon": "telefon_kontaktowy", "phone": "telefon_kontaktowy",
    "email": "email_kontaktowy", "e_mail": "email_kontaktowy",
    "id": "id_zrodlowe", "numer_id": "id_zrodlowe",
}


def normalize_header(name: str) -> str:
    """Ta sama reguła co aed_aggregation.normalize_header w portalu (ł→l, bez diakrytyków, reszta → _)."""
    s = (name or "").replace("ł", "l").replace("Ł", "L")
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")
