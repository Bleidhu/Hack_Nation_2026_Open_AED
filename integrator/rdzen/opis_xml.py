"""Opis zbioru AED (XML) z sumą md5 pliku CSV: wejście do portalu.

Struktura zgodna z format_danych/schemat/aed_opis_zbioru.xsd. Tylko biblioteka standardowa.
Suma md5 jest liczona z bajtów pliku CSV, dokładnie tych, które dostawca opublikuje pod `link_csv`.
"""
from __future__ import annotations

import csv
import hashlib
import io
import re
from datetime import datetime
from xml.sax.saxutils import escape

from .wzorzec import HEADER_ALIASES, MINIMUM, normalize_header

LICENCJE = ("CC0 1.0", "CC BY 4.0")
CZESTOTLIWOSCI = ("daily", "weekly", "monthly", "quarterly", "everyHalfYear", "yearly", "irregular")
MAX_TEKST = 2000


class OpisBlad(ValueError):
    """Dane wejściowe nie pozwalają zbudować poprawnego opisu zbioru."""


def suma_md5(dane: bytes) -> str:
    return hashlib.md5(dane).hexdigest()  # suma kontrolna wymagana przez portal, nie zabezpieczenie


def _tekst(nazwa: str, wartosc) -> str:
    w = (wartosc or "").strip()
    if not w:
        raise OpisBlad(f"pole „{nazwa}” jest wymagane")
    if len(w) > MAX_TEKST:
        raise OpisBlad(f"pole „{nazwa}” przekracza {MAX_TEKST} znaków")
    return w


def _kolumny_csv(dane: bytes) -> tuple:
    """Zwraca (kolumny po normalizacji, liczba rekordów) z bajtów CSV (UTF-8, opcjonalny BOM)."""
    try:
        tekst = dane.decode("utf-8-sig")
    except UnicodeDecodeError as e:
        raise OpisBlad("plik CSV musi być w UTF-8") from e
    wiersze = list(csv.reader(io.StringIO(tekst, newline="")))
    if not wiersze:
        raise OpisBlad("plik CSV jest pusty")
    kolumny = []
    for h in wiersze[0]:
        n = normalize_header(h)
        kolumny.append(HEADER_ALIASES.get(n, n))
    liczba = sum(1 for w in wiersze[1:] if any(c.strip() for c in w))
    return kolumny, liczba


def sprawdz_csv(dane: bytes) -> int:
    """Sprawdza minimum kolumn wzorca; zwraca liczbę rekordów."""
    kolumny, liczba = _kolumny_csv(dane)
    brak = [k for k in MINIMUM if k not in kolumny]
    if brak:
        raise OpisBlad("w pliku CSV brakuje kolumn minimum wzorca: " + ", ".join(brak))
    return liczba


def zbuduj_opis(csv_bajty: bytes, *, link_csv: str, tytul: str, opis: str, dysponent: str, licencja: str,
                czestotliwosc: str, regon: str = None, email: str = None, tytul_zasobu: str = None,
                data_aktualizacji: datetime = None) -> str:
    """Buduje tekst XML opisu zbioru. `csv_bajty` to dokładnie plik publikowany pod `link_csv`."""
    if licencja not in LICENCJE:
        raise OpisBlad(f"licencja „{licencja}” niedozwolona; dopuszczone: {', '.join(LICENCJE)} (ODbL i CC BY-SA odrzucane)")
    if czestotliwosc not in CZESTOTLIWOSCI:
        raise OpisBlad(f"częstotliwość „{czestotliwosc}” niedozwolona; dopuszczone: {', '.join(CZESTOTLIWOSCI)}")
    link = (link_csv or "").strip()
    if not re.fullmatch(r"https://[^\s]+", link):
        raise OpisBlad("link do CSV musi zaczynać się od https:// i nie zawierać spacji")
    if regon is not None and not re.fullmatch(r"(\d{9}|\d{14})", regon):
        raise OpisBlad("REGON musi mieć 9 lub 14 cyfr")
    liczba = sprawdz_csv(csv_bajty)
    teraz = (data_aktualizacji or datetime.now()).replace(microsecond=0)

    def e(n, v):
        return escape(_tekst(n, v))

    linie = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        "<opis_zbioru>",
        f"  <tytul>{e('tytul', tytul)}</tytul>",
        f"  <opis>{e('opis', opis)}</opis>",
        f"  <dysponent_nazwa>{e('dysponent', dysponent)}</dysponent_nazwa>",
    ]
    if regon:
        linie.append(f"  <dysponent_regon>{regon}</dysponent_regon>")
    if email:
        linie.append(f"  <kontakt_email>{e('email', email)}</kontakt_email>")
    linie += [
        f"  <licencja>{licencja}</licencja>",
        f"  <czestotliwosc_aktualizacji>{czestotliwosc}</czestotliwosc_aktualizacji>",
        f"  <data_aktualizacji>{teraz.strftime('%Y-%m-%dT%H:%M:%S')}</data_aktualizacji>",
        "  <zasob>",
        f"    <tytul>{e('tytul zasobu', tytul_zasobu or 'Lokalizacje AED (CSV)')}</tytul>",
        f"    <link_csv>{escape(link)}</link_csv>",
        "    <format>csv</format>",
        f"    <md5>{suma_md5(csv_bajty)}</md5>",
        f"    <liczba_rekordow>{liczba}</liczba_rekordow>",
        "  </zasob>",
        "</opis_zbioru>",
        "",
    ]
    return "\n".join(linie)
