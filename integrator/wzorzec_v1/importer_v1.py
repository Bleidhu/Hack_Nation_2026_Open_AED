#!/usr/bin/env python3
"""
ARCHIWUM v1: importer do wzorca v1 (44 kolumny + rozszerzenia). Aktualny: importer.py (v2).

Wspólny silnik dla: API (server.py → /api/v1/importy), CLI i paczki deliverable.
Tylko biblioteka standardowa Pythona.

Wejście:   CSV/TSV (dowolny separator, UTF-8 lub CP1250), XLSX (pierwszy arkusz),
           GeoJSON, Overpass JSON (OSM).
Mapowanie: plik JSON (format opisany w deliverable/01_FORMAT_DANYCH.md, §6) lub preset:
           "wzorzec" (plik już w naszym formacie), "osm" (tagi OpenStreetMap).
Wyjście:   rekordy we wzorcu + raport walidacji + CSV RFC 4180 gotowy dla dane.gov.pl.

CLI:
    python importer.py plik.csv --mapowanie mapowanie.json --organizacja org.json --wyjscie wynik.csv
    python importer.py eksport_osm.geojson --preset osm --wyjscie osm_wzorzec.csv
    python importer.py plik.csv --podpowiedz            # tylko podpowiedź mapowania kolumn
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
import unicodedata
import zipfile
from datetime import date, datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent  # archiwum: skrypt leży w wzorzec_v1/
ROOT = HERE.parent
BASE_SCHEMA = HERE / "wzorzec_v1" / "schemat_tableschema.json"  # shortcut: zamrożony wzorzec v1; przepiąć na v2 w kroku 2
DICTS = HERE / "wzorzec_v1" / "slowniki_wartosci.json"

PL_LAT = (49.0, 54.9)
PL_LON = (14.1, 24.2)

# --------------------------------------------------------------------------- #
# Schemat: wzorzec v1, 44 kolumny (integrator/wzorzec_v1) + rozszerzenia
# --------------------------------------------------------------------------- #
EXTENSION_FIELDS = [
    {"name": "organizacja_id", "type": "string", "x-wymagalnosc": "O", "x-grupa": "Rozszerzenia",
     "description": "Identyfikator organizacji z tabeli organizacji (logo, strona www) – np. sieć placówek firmy",
     "constraints": {"pattern": "^[a-z0-9][a-z0-9-]{1,62}$"}},
    {"name": "id_obszaru", "type": "string", "x-wymagalnosc": "O", "x-grupa": "Rozszerzenia",
     "description": "Powiązanie z AED obszarowym/mobilnym (tabela aed_obszarowe), np. flota tramwajów",
     "constraints": {"pattern": "^PL-AEDO-\\d{5}$"}},
    {"name": "id_pojazdu", "type": "string", "x-wymagalnosc": "O", "x-grupa": "Rozszerzenia",
     "description": "Numer taborowy pojazdu, w którym zamontowano AED (AED mobilne)"},
]

AREA_FIELDS = [
    ("id_obszaru", "string", "W", "Identyfikator obszaru: PL-AEDO-NNNNN", "PL-AEDO-00001"),
    ("nazwa_obszaru", "string", "W", "Nazwa obszaru lub floty", "Tramwaje MZK – linie 1–12"),
    ("typ_obszaru", "string", "W", "Słownik typ_obszaru", "flota_pojazdow"),
    ("organizacja_id", "string", "Z", "Organizacja odpowiedzialna (tabela organizacji)", "mzk-przyklad"),
    ("dysponent_nazwa", "string", "W", "Dysponent urządzeń", "Miejski Zakład Komunikacji Przykład"),
    ("dysponent_regon", "string", "Z", "REGON 9 lub 14 cyfr", "012345678"),
    ("liczba_aed", "integer", "W", "Liczba AED w obszarze / flocie", "69"),
    ("liczba_pojazdow", "integer", "O", "Liczba pojazdów floty (gdy AED tylko w części)", "120"),
    ("geometria_wkt", "string", "W", "Zasięg: WKT w WGS84 (POLYGON, MULTIPOLYGON, LINESTRING, MULTILINESTRING) – lon lat", "POLYGON((14.50 53.40, …))"),
    ("bufor_m", "integer", "O", "Bufor wokół linii (trasy) w metrach", "300"),
    ("gtfs_url", "string", "O", "Rozkład GTFS przewoźnika (zasięg tras i przystanków)", "https://…/gtfs.zip"),
    ("gtfs_rt_url", "string", "O", "Pozycje pojazdów na żywo (GTFS-RT VehiclePositions lub API JSON)", "https://…/VehiclePositions.pb"),
    ("typy_pojazdow", "string", "O", "Lista oddzielona |: tramwaj|autobus|karetka|patrol_pieszy|rower|lodz", "tramwaj"),
    ("linie", "string", "O", "Numery linii oddzielone |", "1|2|3"),
    ("godziny_dostepnosci", "string", "Z", "opening_hours (OSM), np. Mo-Su 05:00-23:00", "Mo-Su 05:00-23:30"),
    ("jak_uzyskac_dostep", "string", "W", "Instrukcja dla świadka zdarzenia", "Zatrzymaj tramwaj, poproś motorniczego – AED w kabinie"),
    ("status_programu", "string", "W", "Słownik status_programu", "aktywny"),
    ("aktywny_od", "date", "O", "Od kiedy (yyyy-mm-dd)", "2026-12-01"),
    ("aktywny_do", "date", "O", "Do kiedy – dla wydarzeń (yyyy-mm-dd)", ""),
    ("telefon_kontaktowy", "string", "Z", "9 cyfr / +48…", "914800000"),
    ("strona_www", "string", "O", "Strona programu (https)", "https://example.org/aed"),
    ("zrodlo_danych", "string", "W", "Słownik zrodlo_danych", "dysponent"),
    ("data_aktualizacji", "datetime", "W", "ISO 8601", "2026-11-21T10:00:00"),
    ("uwagi", "string", "O", "", ""),
]
AREA_ENUMS = {
    "typ_obszaru": ["flota_pojazdow", "patrol_mobilny", "wydarzenie", "teren_obiektu", "trasa", "inne"],
    "status_programu": ["aktywny", "w_realizacji", "planowany", "zakonczony"],
}

ORG_FIELDS = [
    ("organizacja_id", "string", "W", "Krótki identyfikator: małe litery, cyfry, '-'", "bank-przyklad"),
    ("nazwa", "string", "W", "Pełna nazwa organizacji", "Bank Przykład S.A."),
    ("typ_organizacji", "string", "W", "Słownik typ_organizacji", "firma"),
    ("regon", "string", "Z", "REGON 9 lub 14 cyfr", "012345678"),
    ("nip", "string", "O", "NIP 10 cyfr", "5250000000"),
    ("strona_www", "string", "Z", "Strona organizacji (https)", "https://bank-przyklad.example"),
    ("logo_url", "string", "O", "Logo: https, PNG lub SVG, min. 128 px, przezroczyste tło", "https://bank-przyklad.example/logo.svg"),
    ("logo_alt", "string", "O", "Tekst alternatywny logo (WCAG) – wymagany, gdy jest logo", "Logo Banku Przykład"),
    ("email_kontaktowy", "string", "Z", "Kontakt instytucjonalny w sprawie AED", "aed@bank-przyklad.example"),
    ("telefon_kontaktowy", "string", "O", "9 cyfr / +48…", "225550000"),
    ("liczba_aed", "integer", "O", "Deklarowana liczba AED (kontrola kompletności)", "120"),
    ("licencja_danych", "string", "W", "CC0-1.0 (zalecana) lub CC-BY-4.0", "CC0-1.0"),
    ("uwagi", "string", "O", "Logo i nazwa są znakami towarowymi – nie podlegają licencji danych", ""),
]
ORG_ENUMS = {
    "typ_organizacji": ["jst", "administracja", "firma", "przewoznik", "uczelnia", "szkola", "ngo", "sluzby", "inne"],
    "licencja_danych": ["CC0-1.0", "CC-BY-4.0"],
}


def load_schema() -> dict:
    base = json.loads(BASE_SCHEMA.read_text("utf-8"))
    base = dict(base)
    base["fields"] = base["fields"] + EXTENSION_FIELDS
    base["name"] = "aed-punkty"
    base["version"] = "1.1.0"
    return base


SCHEMA = load_schema()
FIELDS = [f["name"] for f in SCHEMA["fields"]]
FIELD = {f["name"]: f for f in SCHEMA["fields"]}
DICT_VALUES = {k: [w if isinstance(w, str) else w.get("wartosc") for w in v.get("wartosci", [])]
               for k, v in json.loads(DICTS.read_text("utf-8")).items()} if DICTS.exists() else {}

# --------------------------------------------------------------------------- #
# Pomocnicze
# --------------------------------------------------------------------------- #
def fold(s: str) -> str:
    s = (s or "").lower().replace("ł", "l")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def decode(b: bytes) -> str:
    for enc in ("utf-8-sig", "cp1250"):
        try:
            return b.decode(enc)
        except UnicodeDecodeError:
            pass
    return b.decode("latin-1")


# --------------------------------------------------------------------------- #
# Odczyt plików
# --------------------------------------------------------------------------- #
def read_xlsx(b: bytes) -> list[list[str]]:
    """Minimalny odczyt pierwszego arkusza XLSX (bez zależności)."""
    z = zipfile.ZipFile(io.BytesIO(b))
    shared = []
    if "xl/sharedStrings.xml" in z.namelist():
        xml = z.read("xl/sharedStrings.xml").decode("utf-8")
        for si in re.findall(r"<si>(.*?)</si>", xml, re.S):
            shared.append(unescape_xml("".join(re.findall(r"<t[^>]*>(.*?)</t>", si, re.S))))
    sheet = sorted(n for n in z.namelist() if n.startswith("xl/worksheets/sheet"))[0]
    xml = z.read(sheet).decode("utf-8")
    rows = []
    for row in re.findall(r"<row[^>]*>(.*?)</row>", xml, re.S):
        cells = {}
        for attrs, body in re.findall(r"<c([^>]*?)(?:/>|>(.*?)</c>)", row, re.S):
            ref = re.search(r'r="([A-Z]+)\d+"', attrs)
            col = 0
            for ch in ref.group(1) if ref else "A":
                col = col * 26 + ord(ch) - 64
            v = re.search(r"<v>(.*?)</v>", body or "", re.S)
            t = re.search(r'\bt="(\w+)"', attrs)
            if t and t.group(1) == "s" and v:
                val = shared[int(v.group(1))]
            elif t and t.group(1) == "inlineStr":
                val = unescape_xml("".join(re.findall(r"<t[^>]*>(.*?)</t>", body or "", re.S)))
            else:
                val = unescape_xml(v.group(1)) if v else ""
            cells[col - 1] = val
        if cells:
            rows.append([cells.get(i, "") for i in range(max(cells) + 1)])
    return rows


def unescape_xml(s: str) -> str:
    return s.replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"').replace("&apos;", "'").replace("&amp;", "&")


def read_input(data: bytes, filename: str = "") -> tuple[list[str], list[dict], str]:
    """Zwraca (kolumny, wiersze jako słowniki, rozpoznany format)."""
    name = filename.lower()
    if name.endswith(".xlsx") or data[:2] == b"PK":
        rows = [r for r in read_xlsx(data) if any(str(c).strip() for c in r)]
        header = [str(h).strip() for h in rows[0]]
        return header, [dict(zip(header, [str(c) for c in r] + [""] * (len(header) - len(r)))) for r in rows[1:]], "xlsx"
    text = decode(data)
    stripped = text.lstrip()
    if stripped.startswith("{") or stripped.startswith("["):
        obj = json.loads(text)
        if isinstance(obj, dict) and obj.get("type") == "FeatureCollection":
            out = []
            for f in obj.get("features", []):
                props = {k: ("" if v is None else str(v)) for k, v in (f.get("properties") or {}).items()}
                lat, lon = geometry_point(f.get("geometry"))
                props["__lat"], props["__lon"] = lat, lon
                out.append(props)
            cols = sorted({k for r in out for k in r})
            return cols, out, "geojson"
        if isinstance(obj, dict) and "elements" in obj:  # Overpass JSON
            out = []
            for el in obj["elements"]:
                tags = {k: str(v) for k, v in (el.get("tags") or {}).items()}
                c = el.get("center") or el
                tags["__lat"], tags["__lon"] = str(c.get("lat", "")), str(c.get("lon", ""))
                tags["@id"] = f"{el.get('type')}/{el.get('id')}"
                out.append(tags)
            cols = sorted({k for r in out for k in r})
            return cols, out, "osm"
        raise ValueError("Nierozpoznany JSON – oczekiwano GeoJSON FeatureCollection lub Overpass JSON")
    first = text.splitlines()[0] if text else ""
    delim = max([",", ";", "\t", "|"], key=first.count)
    rd = csv.reader(io.StringIO(text), delimiter=delim)
    rows = [r for r in rd if any(c.strip() for c in r)]
    if not rows:
        return [], [], "csv"
    header = [h.strip() for h in rows[0]]
    return header, [dict(zip(header, r + [""] * (len(header) - len(r)))) for r in rows[1:]], "csv"


def geometry_point(g) -> tuple[str, str]:
    if not g:
        return "", ""
    c = g.get("coordinates")
    while isinstance(c, list) and c and isinstance(c[0], list):
        c = c[0]
    return (str(c[1]), str(c[0])) if isinstance(c, list) and len(c) >= 2 else ("", "")


# --------------------------------------------------------------------------- #
# Mapowanie
# --------------------------------------------------------------------------- #
SYNONYMS = {
    "id_zrodlowe": ["id", "identyfikator", "numer id", "nr", "kod placowki", "id placowki", "ref", "@id", "defibrillator id"],
    "nazwa_lokalizacji": ["nazwa", "name", "obiekt", "placowka", "oddzial", "nazwa obiektu", "lokalizacja", "location object name"],
    "miejscowosc": ["miasto", "miejscowosc", "city", "addr city", "location city"],
    "kod_pocztowy": ["kod", "kod pocztowy", "postcode", "addr postcode", "zip", "pna"],
    "nazwa_ulicy": ["ulica", "street", "addr street", "nazwa ulicy", "location street"],
    "numer_budynku": ["nr budynku", "numer", "numer domu", "housenumber", "addr housenumber", "building", "home number"],
    "szerokosc_geograficzna": ["lat", "latitude", "szerokosc", "szerokosc geograficzna", "y", "__lat", "wsp y"],
    "dlugosc_geograficzna": ["lon", "lng", "long", "longitude", "dlugosc", "dlugosc geograficzna", "x", "__lon", "wsp x"],
    "opis_lokalizacji": ["opis", "opis lokalizacji", "miejsce", "gdzie", "defibrillator location", "defibrillator location pl", "description"],
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
    "zdjecie_url": ["zdjecie", "foto", "image", "photo"],
    "uwagi": ["uwagi", "note", "notes", "komentarz"],
    "id_pojazdu": ["nr taborowy", "pojazd", "vehicle", "vehicle number"],
}

PRESETS: dict[str, dict] = {
    "wzorzec": {"opis": "Plik już we wzorcowym formacie (nagłówki = nazwy kolumn wzorca)",
                "kolumny": {f: {"z": f} for f in FIELDS}},
    "osm": {
        "opis": "OpenStreetMap: GeoJSON z OpenAEDMap/Overpass (tag emergency=defibrillator). Licencja ODbL!",
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
            "zdjecie_url": {"z": "image"},
            "zrodlo_danych": {"stala": "baza_zewnetrzna"},
            "poziom_weryfikacji": {"stala": "niezweryfikowany"},
        },
    },
}


def suggest_mapping(headers: list[str]) -> dict:
    """Podpowiedź mapowania: dokładna nazwa kolumny wzorca → synonimy → początek nazwy."""
    fh = {h: fold(h) for h in headers}
    used, cols = set(), {}
    for f in FIELDS:
        hit = next((h for h in headers if h not in used and fold(h) == fold(f)), None)
        if not hit:
            for syn in SYNONYMS.get(f, []):
                hit = next((h for h in headers if h not in used and (fh[h] == fold(syn) or fold(h) == syn)), None)
                if hit:
                    break
        if not hit:
            for syn in SYNONYMS.get(f, []):
                if len(syn) > 4:
                    hit = next((h for h in headers if h not in used and fh[h].startswith(fold(syn))), None)
                    if hit:
                        break
        if hit:
            used.add(hit)
            cols[f] = {"z": hit}
    return {"wersja": "1.0", "kolumny": cols, "niezmapowane_kolumny_zrodla": [h for h in headers if h not in used]}


TRUE = {"true", "tak", "t", "yes", "y", "1", "24/7", "24h", "calodobowo", "całodobowo", "x"}
FALSE = {"false", "nie", "n", "no", "0", "-"}


def norm_value(field: str, v: str, warnings: list) -> str:
    v = "" if v is None else str(v).strip()
    if not v:
        return ""
    t = FIELD.get(field, {}).get("type")
    if t == "number":
        v = v.replace(" ", "")
        if v.count(",") == 1 and "." not in v:
            v = v.replace(",", ".")
    elif t == "boolean":
        lv = v.lower()
        v = "true" if lv in TRUE else "false" if lv in FALSE else v
    elif t == "date":
        m = re.fullmatch(r"(\d{1,2})[./-](\d{1,2})[./-](\d{4})", v)
        if m:
            v = f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
            warnings.append((field, "data przekształcona do ISO 8601"))
        v = v[:10] if re.match(r"\d{4}-\d{2}-\d{2}", v) else v
    elif t == "datetime":
        v = v.replace(" ", "T", 1) if re.match(r"\d{4}-\d{2}-\d{2} \d", v) else v
    if field == "kod_pocztowy" and re.fullmatch(r"\d{5}", v):
        v = f"{v[:2]}-{v[2:]}"
    if field in ("telefon_kontaktowy",):
        digits = re.sub(r"[^\d+]", "", v)
        if digits.startswith("+48"):
            digits = "+48" + digits[3:]
        elif digits.startswith("48") and len(digits) == 11:
            digits = "+" + digits
        v = digits
    if field in ("dysponent_regon",):
        v = re.sub(r"\D", "", v)
    return v


def pick(row: dict, spec) -> str:
    srcs = spec if isinstance(spec, list) else [spec]
    for s in srcs:
        val = row.get(s, "")
        if str(val).strip():
            return str(val)
    return ""


def make_id(*parts) -> str:
    h = hashlib.sha1("|".join(str(p) for p in parts).encode()).hexdigest()
    return f"PL-AED-{int(h[:12], 16) % 10_000_000:07d}"


def apply_mapping(rows: list[dict], mapping: dict, *, organizacja_id: str = "", defaults: dict | None = None) -> list[dict]:
    cols = mapping.get("kolumny", {})
    defaults = {**(mapping.get("domyslne") or {}), **(defaults or {})}
    out = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
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
        if organizacja_id and not rec["organizacja_id"]:
            rec["organizacja_id"] = organizacja_id
        # zamienione współrzędne
        try:
            la, lo = float(rec["szerokosc_geograficzna"]), float(rec["dlugosc_geograficzna"])
            if not (PL_LAT[0] <= la <= PL_LAT[1]) and PL_LAT[0] <= lo <= PL_LAT[1] and PL_LON[0] <= la <= PL_LON[1]:
                rec["szerokosc_geograficzna"], rec["dlugosc_geograficzna"] = rec["dlugosc_geograficzna"], rec["szerokosc_geograficzna"]
                warnings.append(("szerokosc_geograficzna", "zamieniono szerokość z długością geograficzną"))
        except ValueError:
            pass
        if rec["godziny_dostepnosci"].strip() == "24/7" and not rec["dostepny_24_7"]:
            rec["dostepny_24_7"] = "true"
        if not rec["data_aktualizacji"]:
            rec["data_aktualizacji"] = now
        if not rec["id_aed"]:
            rec["id_aed"] = make_id(rec["organizacja_id"], rec["id_zrodlowe"] or i, rec["szerokosc_geograficzna"], rec["dlugosc_geograficzna"])
        rec["__wiersz"] = i + 2  # numer wiersza w pliku (z nagłówkiem)
        rec["__ostrzezenia"] = [{"pole": f, "komunikat": m} for f, m in warnings]
        out.append(rec)
    return out


# --------------------------------------------------------------------------- #
# Walidacja (Table Schema + reguły dodatkowe)
# --------------------------------------------------------------------------- #
def validate_value(field: dict, v: str) -> str | None:
    c = field.get("constraints", {})
    if not v:
        return "pole wymagane" if c.get("required") else None
    t = field.get("type")
    if t == "number":
        try:
            n = float(v)
        except ValueError:
            return "oczekiwano liczby z kropką dziesiętną"
        if "minimum" in c and n < c["minimum"] or "maximum" in c and n > c["maximum"]:
            return f"poza zakresem {c.get('minimum')}–{c.get('maximum')}"
    elif t == "integer":
        if not re.fullmatch(r"-?\d+", v):
            return "oczekiwano liczby całkowitej"
    elif t == "boolean":
        if v not in ("true", "false"):
            return "oczekiwano true/false"
    elif t == "date":
        try:
            date.fromisoformat(v)
        except ValueError:
            return "oczekiwano daty yyyy-mm-dd"
    elif t == "datetime":
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?(Z|[+-]\d{2}:\d{2})?", v):
            return "oczekiwano daty i czasu ISO 8601"
    if "enum" in c and v not in c["enum"]:
        return f"wartość spoza słownika: {', '.join(c['enum'])}"
    if "pattern" in c and not re.fullmatch(c["pattern"], v):
        return f"niezgodne z wzorcem {c['pattern']}"
    return None


def validate(recs: list[dict], *, strict_required: bool = True) -> dict:
    """Raport: rekordy poprawne / z ostrzeżeniami / odrzucone (brak pól W lub błędy typów)."""
    seen_ids: set = set()
    report = {"liczba_wierszy": len(recs), "poprawne": 0, "z_ostrzezeniami": 0, "odrzucone": 0, "bledy": [], "ostrzezenia": [],
              "kompletnosc": {}}
    for r in recs:
        errs = []
        for f in SCHEMA["fields"]:
            msg = validate_value(f, r.get(f["name"], ""))
            if msg:
                level = "blad" if (f.get("constraints", {}).get("required") and strict_required) or msg != "pole wymagane" else "ostrzezenie"
                (errs if level == "blad" else r["__ostrzezenia"]).append({"pole": f["name"], "komunikat": msg})
        today = date.today().isoformat()
        for f, label in (("data_waznosci_elektrod", "elektrody"), ("data_waznosci_baterii", "bateria")):
            v = r.get(f, "")
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", v) and v < today:
                r["__ostrzezenia"].append({"pole": f, "komunikat": f"{label} po terminie ważności – AED wymaga serwisu"})
        if r["id_aed"] in seen_ids:
            errs.append({"pole": "id_aed", "komunikat": "zduplikowany identyfikator"})
        seen_ids.add(r["id_aed"])
        r["__status"] = "odrzucony" if errs else ("ostrzezenie" if r["__ostrzezenia"] else "ok")
        r["__bledy"] = errs
        report["odrzucone" if errs else ("z_ostrzezeniami" if r["__ostrzezenia"] else "poprawne")] += 1
        for e in errs:
            report["bledy"].append({"wiersz": r["__wiersz"], **e, "wartosc": r.get(e["pole"], "")})
        for w in r["__ostrzezenia"]:
            report["ostrzezenia"].append({"wiersz": r["__wiersz"], **w})
    n = max(1, len(recs))
    report["kompletnosc"] = {f: round(100 * sum(1 for r in recs if r.get(f)) / n) for f in FIELDS}
    return report


def to_csv(recs: list[dict], fields: list[str] | None = None, *, only_valid: bool = True) -> str:
    fields = fields or FIELDS
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\r\n")
    w.writerow(fields)
    for r in recs:
        if only_valid and r.get("__status") == "odrzucony":
            continue
        w.writerow([r.get(f, "") for f in fields])
    return buf.getvalue()


def to_geojson(recs: list[dict]) -> dict:
    feats = []
    for r in recs:
        if r.get("__status") == "odrzucony":
            continue
        try:
            la, lo = float(r["szerokosc_geograficzna"]), float(r["dlugosc_geograficzna"])
        except ValueError:
            continue
        props = {k: v for k, v in r.items() if not k.startswith("__") and v != ""}
        feats.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [lo, la]}, "properties": props})
    return {"type": "FeatureCollection", "features": feats}


# --------------------------------------------------------------------------- #
# AED obszarowe i organizacje
# --------------------------------------------------------------------------- #
def wkt_to_geojson(wkt: str) -> dict | None:
    """WKT (POINT, LINESTRING, POLYGON, MULTI*) → GeoJSON geometry. Kolejność: lon lat."""
    m = re.match(r"\s*(MULTIPOLYGON|POLYGON|MULTILINESTRING|LINESTRING|POINT)\s*\((.*)\)\s*$", wkt or "", re.I | re.S)
    if not m:
        return None
    kind, body = m.group(1).upper(), m.group(2)

    def ring(s):
        return [[float(a), float(b)] for a, b in (p.split()[:2] for p in s.split(",") if p.strip())]

    if kind == "POINT":
        return {"type": "Point", "coordinates": ring(body)[0]}
    if kind == "LINESTRING":
        return {"type": "LineString", "coordinates": ring(body)}
    if kind == "MULTILINESTRING":
        return {"type": "MultiLineString", "coordinates": [ring(x) for x in re.findall(r"\(([^()]*)\)", body)]}
    if kind == "POLYGON":
        return {"type": "Polygon", "coordinates": [ring(x) for x in re.findall(r"\(([^()]*)\)", "(" + body + ")")]}
    polys = re.findall(r"\(\s*(\([^()]*\)(?:\s*,\s*\([^()]*\))*)\s*\)", body)
    return {"type": "MultiPolygon", "coordinates": [[ring(x) for x in re.findall(r"\(([^()]*)\)", p)] for p in polys]}


def _validate_table(rows: list[dict], spec: list[tuple], enums: dict) -> dict:
    report = {"liczba_wierszy": len(rows), "poprawne": 0, "odrzucone": 0, "bledy": []}
    for i, r in enumerate(rows):
        errs = []
        for name, typ, req, _, _ in spec:
            v = str(r.get(name, "") or "").strip()
            fdef = {"type": typ, "constraints": {"required": req == "W"}}
            if name in enums:
                fdef["constraints"]["enum"] = enums[name]
            msg = validate_value(fdef, v)
            if msg:
                errs.append({"wiersz": i + 2, "pole": name, "komunikat": msg, "wartosc": v})
        if "geometria_wkt" in r and r.get("geometria_wkt") and not wkt_to_geojson(r["geometria_wkt"]):
            errs.append({"wiersz": i + 2, "pole": "geometria_wkt", "komunikat": "niepoprawny WKT", "wartosc": r["geometria_wkt"][:60]})
        if r.get("logo_url") and not str(r.get("logo_alt", "")).strip():
            errs.append({"wiersz": i + 2, "pole": "logo_alt", "komunikat": "brak tekstu alternatywnego logo (WCAG)", "wartosc": ""})
        for url_f in ("logo_url", "strona_www", "gtfs_url", "gtfs_rt_url"):
            if r.get(url_f) and not str(r[url_f]).startswith("https://"):
                errs.append({"wiersz": i + 2, "pole": url_f, "komunikat": "adres musi zaczynać się od https://", "wartosc": r[url_f]})
        report["bledy"] += errs
        report["odrzucone" if errs else "poprawne"] += 1
    return report


def validate_areas(rows: list[dict]) -> dict:
    return _validate_table(rows, AREA_FIELDS, AREA_ENUMS)


def validate_orgs(rows: list[dict]) -> dict:
    rep = _validate_table(rows, ORG_FIELDS, ORG_ENUMS)
    for i, r in enumerate(rows):
        if r.get("organizacja_id") and not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,62}", r["organizacja_id"]):
            rep["bledy"].append({"wiersz": i + 2, "pole": "organizacja_id", "komunikat": "tylko małe litery, cyfry i '-'", "wartosc": r["organizacja_id"]})
    return rep


def areas_to_geojson(rows: list[dict]) -> dict:
    feats = []
    for r in rows:
        g = wkt_to_geojson(r.get("geometria_wkt", ""))
        if g:
            feats.append({"type": "Feature", "geometry": g, "properties": {k: v for k, v in r.items() if k != "geometria_wkt" and v not in ("", None)}})
    return {"type": "FeatureCollection", "features": feats}


# --------------------------------------------------------------------------- #
def run(data: bytes, filename: str, mapping: dict | None, *, preset: str | None = None, organizacja_id: str = "",
        defaults: dict | None = None) -> dict:
    headers, rows, fmt = read_input(data, filename)
    if mapping is None:
        mapping = PRESETS[preset] if preset else (PRESETS["osm"] if fmt == "osm" else suggest_mapping(headers))
    recs = apply_mapping(rows, mapping, organizacja_id=organizacja_id, defaults=defaults)
    report = validate(recs)
    return {"format": fmt, "kolumny_zrodla": headers, "mapowanie": mapping, "rekordy": recs, "raport": report,
            "licencja_zrodla": mapping.get("licencja_zrodla", "")}


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plik", type=Path)
    ap.add_argument("--mapowanie", type=Path)
    ap.add_argument("--preset", choices=sorted(PRESETS))
    ap.add_argument("--organizacja", default="", help="organizacja_id przypisywany wszystkim rekordom")
    ap.add_argument("--domyslne", type=Path, help="JSON z wartościami domyślnymi pól")
    ap.add_argument("--wyjscie", type=Path, help="CSV wynikowy (tylko poprawne rekordy)")
    ap.add_argument("--raport", type=Path, help="raport walidacji JSON")
    ap.add_argument("--podpowiedz", action="store_true", help="wypisz podpowiedź mapowania i zakończ")
    a = ap.parse_args()
    data = a.plik.read_bytes()
    if a.podpowiedz:
        h, _, fmt = read_input(data, a.plik.name)
        print(json.dumps(PRESETS["osm"] if fmt == "osm" else suggest_mapping(h), ensure_ascii=False, indent=2))
        return
    mapping = json.loads(a.mapowanie.read_text("utf-8")) if a.mapowanie else None
    defaults = json.loads(a.domyslne.read_text("utf-8")) if a.domyslne else None
    res = run(data, a.plik.name, mapping, preset=a.preset, organizacja_id=a.organizacja, defaults=defaults)
    r = res["raport"]
    print(f"format: {res['format']} · wiersze: {r['liczba_wierszy']} · poprawne: {r['poprawne']} · "
          f"z ostrzeżeniami: {r['z_ostrzezeniami']} · odrzucone: {r['odrzucone']}")
    for e in r["bledy"][:15]:
        print(f"  ✗ wiersz {e['wiersz']}: {e['pole']} – {e['komunikat']} ({e['wartosc']!r})")
    if a.wyjscie:
        a.wyjscie.write_text(to_csv(res["rekordy"]), "utf-8", newline="")
        print(f"zapisano {a.wyjscie}")
    if a.raport:
        a.raport.write_text(json.dumps(r, ensure_ascii=False, indent=2), "utf-8")


if __name__ == "__main__":
    main()
