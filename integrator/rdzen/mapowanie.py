"""Mapowanie kolumn źródła na wzorzec v2: podpowiedź, presety, zastosowanie pliku mapowania."""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone

from .normalizacja import norm_value
from .wzorzec import FIELDS, HEADER_ALIASES, PL_LAT, PL_LON, normalize_header

SYNONYMS = {
    "id_zrodlowe": ["id", "identyfikator", "numer id", "nr", "kod placowki", "id placowki", "ref", "@id", "defibrillator id"],
    "nazwa_lokalizacji": ["nazwa", "name", "obiekt", "placowka", "oddzial", "nazwa obiektu", "lokalizacja"],
    "miejscowosc": ["miasto", "miejscowosc", "city", "addr city", "location city"],
    "kod_pocztowy": ["kod", "kod pocztowy", "postcode", "addr postcode", "zip", "pna"],
    "nazwa_ulicy": ["ulica", "street", "addr street", "nazwa ulicy", "location street"],
    "numer_budynku": ["nr budynku", "numer", "numer domu", "housenumber", "addr housenumber", "building", "home number"],
    "szerokosc_geograficzna": ["lat", "latitude", "szerokosc", "szerokosc geograficzna", "y", "__lat", "wsp y"],
    "dlugosc_geograficzna": ["lon", "lng", "long", "longitude", "dlugosc", "dlugosc geograficzna", "x", "__lon", "wsp x"],
    "opis_lokalizacji": ["opis", "opis lokalizacji", "miejsce", "gdzie", "defibrillator location", "description"],
    "godziny_dostepnosci": ["godziny", "godziny otwarcia", "opening hours", "godziny dostepnosci", "godziny pracy"],
    "typ_dostepu": ["dostep", "typ dostepu", "access", "public access"],
    "dostepny_24_7": ["24 7", "24h", "calodobowo", "dostepny 24 7", "aed 24h"],
    "telefon_kontaktowy": ["telefon", "tel", "phone", "nr telefonu"],
    "email_kontaktowy": ["email", "e mail", "mail"],
    "dysponent_nazwa": ["dysponent", "operator", "wlasciciel", "zarzadca"],
    "dysponent_regon": ["regon"],
    "producent": ["producent", "manufacturer"],
    "model": ["model"],
    "kondygnacja": ["pietro", "kondygnacja", "level"],
    "wewnatrz_budynku": ["wewnatrz", "indoor", "w budynku"],
    "data_waznosci_elektrod": ["waznosc elektrod", "elektrody do", "pads expiry"],
    "data_waznosci_baterii": ["waznosc baterii", "bateria do", "battery expiry"],
    "data_ostatniego_przegladu": ["przeglad", "ostatni przeglad", "data przegladu"],
    "data_weryfikacji": ["data weryfikacji", "check date", "zweryfikowano"],
    "status_urzadzenia": ["status", "stan"],
}

PRESETS = {
    "wzorzec": {"opis": "Plik już we wzorcu v2 (nagłówki = nazwy kolumn)", "kolumny": {f: {"z": f} for f in FIELDS}},
    "osm": {
        "opis": "OpenStreetMap (emergency=defibrillator). Licencja ODbL: tylko tryb lokalny i porównania.",
        "licencja_zrodla": "ODbL-1.0",
        "kolumny": {
            "id_zrodlowe": {"z": "@id"},
            "nazwa_lokalizacji": {"z": ["name", "description", "operator"]},
            "opis_lokalizacji": {"z": ["defibrillator:location:pl", "defibrillator:location", "description"]},
            "szerokosc_geograficzna": {"z": "__lat"},
            "dlugosc_geograficzna": {"z": "__lon"},
            "miejscowosc": {"z": "addr:city"},
            "kod_pocztowy": {"z": "addr:postcode"},
            "nazwa_ulicy": {"z": "addr:street"},
            "numer_budynku": {"z": "addr:housenumber"},
            "wewnatrz_budynku": {"z": "indoor", "mapa": {"yes": "true", "no": "false"}},
            "kondygnacja": {"z": "level"},
            "typ_dostepu": {"z": "access", "mapa": {"yes": "publiczny", "permissive": "publiczny", "customers": "ograniczony",
                                                    "permit": "ograniczony", "private": "prywatny", "no": "prywatny"}},
            "godziny_dostepnosci": {"z": "opening_hours"},
            "dostepny_24_7": {"z": "opening_hours", "mapa": {"24/7": "true", "*": "false"}},
            "dysponent_nazwa": {"z": "operator"},
            "telefon_kontaktowy": {"z": ["phone", "emergency:phone"]},
            "producent": {"z": "manufacturer"},
            "model": {"z": "model"},
            "data_weryfikacji": {"z": "check_date"},
            "zrodlo_danych": {"stala": "openstreetmap"},
            "poziom_weryfikacji": {"stala": "niezweryfikowany"},
        },
    },
}


def _fold(s: str) -> str:
    return normalize_header(s).replace("_", " ")


def suggest_mapping(headers: list) -> dict:
    """Podpowiedź: nazwa wzorca, alias portalu, synonim, początek nazwy."""
    fh = {h: _fold(h) for h in headers}
    used, cols = set(), {}
    for f in FIELDS:
        free = [h for h in headers if h not in used]
        hit = next((h for h in free if fh[h] == _fold(f)), None)
        if not hit:
            hit = next((h for h in free if HEADER_ALIASES.get(normalize_header(h)) == f), None)
        if not hit:
            for syn in SYNONYMS.get(f, []):
                hit = next((h for h in free if fh[h] == syn), None)
                if hit:
                    break
        if not hit:
            for syn in SYNONYMS.get(f, []):
                if len(syn) > 4:
                    hit = next((h for h in free if fh[h].startswith(syn)), None)
                    if hit:
                        break
        if hit:
            used.add(hit)
            cols[f] = {"z": hit}
    return {"wersja": "2.0", "kolumny": cols, "niezmapowane_kolumny_zrodla": [h for h in headers if h not in used]}


def pick(row: dict, spec) -> str:
    for s in spec if isinstance(spec, list) else [spec]:
        val = row.get(s, "")
        if str(val).strip():
            return str(val)
    return ""


def stable_id(*parts) -> str:
    return "auto-" + hashlib.sha1("|".join(str(p) for p in parts).encode("utf-8")).hexdigest()[:10]


def apply_mapping(rows: list, mapping: dict, *, defaults: dict = None, now: str = None) -> list:
    cols = mapping.get("kolumny", {})
    defaults = {**(mapping.get("domyslne") or {}), **(defaults or {})}
    now = now or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    out = []
    for i, row in enumerate(rows):
        warnings: list = []
        rec = {f: "" for f in FIELDS}
        for f, spec in cols.items():
            if f not in rec:
                continue
            if "stala" in spec:
                val = str(spec["stala"])
            else:
                val = pick(row, spec.get("z"))
                if "regex" in spec and val:
                    m = re.search(spec["regex"], val)
                    val = m.group(1) if m and m.groups() else (m.group(0) if m else "")
                if "mapa" in spec and val:
                    mp = spec["mapa"]
                    val = mp.get(val, mp.get(val.lower(), mp.get("*", val)))
            rec[f] = norm_value(f, val, warnings)
        for f, v in defaults.items():
            if f in rec and not rec[f]:
                rec[f] = str(v)
        try:
            la, lo = float(rec["szerokosc_geograficzna"]), float(rec["dlugosc_geograficzna"])
            if not (PL_LAT[0] <= la <= PL_LAT[1]) and PL_LAT[0] <= lo <= PL_LAT[1] and PL_LON[0] <= la <= PL_LON[1]:
                rec["szerokosc_geograficzna"], rec["dlugosc_geograficzna"] = rec["dlugosc_geograficzna"], rec["szerokosc_geograficzna"]
                warnings.append(("szerokosc_geograficzna", "zamieniono szerokość z długością geograficzną"))
        except ValueError:
            pass
        if rec["godziny_dostepnosci"].strip() == "24/7":
            rec["dostepny_24_7"] = rec["dostepny_24_7"] or "true"
            rec["godziny_dostepnosci"] = ""
        # Brak wiedzy nie oznacza „sprawny”; import nie jest weryfikacją.
        rec["status_urzadzenia"] = rec["status_urzadzenia"] or "nieznany"
        rec["poziom_weryfikacji"] = rec["poziom_weryfikacji"] or "niezweryfikowany"
        rec["data_aktualizacji"] = rec["data_aktualizacji"] or now
        if not rec["id_zrodlowe"]:
            rec["id_zrodlowe"] = stable_id(rec["nazwa_lokalizacji"], rec["szerokosc_geograficzna"], rec["dlugosc_geograficzna"])
            warnings.append(("id_zrodlowe", "brak identyfikatora źródła, nadano identyfikator z nazwy i współrzędnych"))
        rec["__wiersz"] = i + 2
        rec["__ostrzezenia"] = [{"pole": f, "komunikat": m} for f, m in warnings]
        out.append(rec)
    return out
