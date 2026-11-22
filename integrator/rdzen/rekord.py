"""Dopisywanie pojedynczych rekordów AED do pliku CSV zgodnego ze wzorcem v2.

Dla małych dostawców, którzy nie mają własnego systemu. Układ pól i nazwy stanów pochodzą
z aplikacji „AED podstawowy” (`../AED/aed_mobile/lib/models/aed.dart`), zmapowane na słownik
`status_urzadzenia` wzorca v2 (enum: sprawny / niesprawny / w_serwisie / wycofany / nieznany):

- `sprawny` → `sprawny`,
- `uzyty` → `niesprawny` (użyty AED czeka na wymianę elektrod i baterii),
- `w_serwisie` → `w_serwisie`,
- `wymaga_serwisu` → `w_serwisie` (urządzenie niedostępne do czasu serwisu).

Zasad z README projektu „AED” (data/manual) trzymamy się dalej: nie zgadujemy stanu
(puste = `nieznany`), import nie jest weryfikacją (`poziom_weryfikacji` = `niezweryfikowany`).
Zapis jest atomowy (plik tymczasowy + podmiana) i nie zmienia pozostałych wierszy.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from .duplikaty import znajdz_kandydatow
from .normalizacja import norm_value
from .walidacja import validate
from .wejscie import read_input
from .wzorzec import FIELDS, FIELD
from .zapis import to_csv

ALIASY_STATUSU = {"sprawny": "sprawny", "uzyty": "niesprawny",
                  "w_serwisie": "w_serwisie", "wymaga_serwisu": "w_serwisie"}

# pola, których util nie zgaduje: puste oznaczałoby kłamstwo o dostępności urządzenia
POLA_OBWIAZKOWE = ("nazwa_lokalizacji", "miejscowosc", "szerokosc_geograficzna", "dlugosc_geograficzna",
                   "opis_lokalizacji", "typ_dostepu", "dostepny_24_7")


class RekordBlad(ValueError):
    """Błąd danych wejściowych rekordu (nieznane pole, zły format)."""


def propozycja_id(prefiks: str, istniejace_id) -> str:
    """Kolejny wolny numer w pliku z prefiksem dostawcy, a nie losowy identyfikator."""
    p = (prefiks or "AED").strip() or "AED"
    n = 1
    while f"{p}-{n:04d}" in istniejace_id:
        n += 1
    return f"{p}-{n:04d}"


def zbuduj(pola: dict, *, prefiks: str = "AED", istniejace_id=None, teraz: str = None) -> dict:
    """Rekord v2 z pól użytkownika: normalizacja wartości, domyślne zgodne z zasadami,
    propozycja `id_zrodlowe` gdy dostawca go nie podał."""
    nieznane = [k for k in pola if k not in FIELD]
    if nieznane:
        raise RekordBlad("nieznane pola (używaj nazw kolumn wzorca v2): " + ", ".join(sorted(nieznane)))
    warnings: list = []
    rec = {f: "" for f in FIELDS}
    for f in FIELDS:
        if f in pola and pola[f] is not None and str(pola[f]).strip() != "":
            rec[f] = norm_value(f, pola[f], warnings)
    if rec["status_urzadzenia"] in ALIASY_STATUSU:
        rec["status_urzadzenia"] = ALIASY_STATUSU[rec["status_urzadzenia"]]
    # brak wiedzy nie oznacza „sprawny”; import nie jest weryfikacją
    rec["status_urzadzenia"] = rec["status_urzadzenia"] or "nieznany"
    rec["poziom_weryfikacji"] = rec["poziom_weryfikacji"] or "niezweryfikowany"
    rec["data_aktualizacji"] = rec["data_aktualizacji"] or (
        teraz or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"))
    if not rec["id_zrodlowe"]:
        rec["id_zrodlowe"] = propozycja_id(prefiks, istniejace_id or set())
        warnings.append(("id_zrodlowe", f"nadano kolejny numer w pliku z prefiksem {prefiks or 'AED'}"))
    rec["__ostrzezenia"] = [{"pole": f, "komunikat": m} for f, m in warnings]
    return rec


def wczytaj_istniejace(sciezka: Path) -> list:
    """Wiersze pliku CSV (słowniki, wartości bez zmian) albo [] gdy pliku nie ma."""
    if not sciezka.exists():
        return []
    _, rows, _ = read_input(sciezka.read_bytes(), sciezka.name)
    return rows


def sprawdz_rekord(rec: dict, istniejace: list) -> dict:
    """Walidacja wzorcem + kontrola kandydatów na duplikaty względem istniejących wierszy.

    Zwraca {bledy, kandydaci, ostrzezenia}. Niczego nie zapisuje.
    """
    kopia = dict(rec)
    kopia.setdefault("__wiersz", len(istniejace) + 2)  # przyszła pozycja nowego wiersza w pliku (nagłówek + 1)
    rap = validate([kopia])
    bledy = list(rap["bledy"])
    if any(r.get("id_zrodlowe") == rec["id_zrodlowe"] and rec["id_zrodlowe"] for r in istniejace):
        bledy.append({"wiersz": None, "pole": "id_zrodlowe", "komunikat": "identyfikator już istnieje w pliku",
                      "wartosc": rec["id_zrodlowe"]})
    kandydaci = []
    if istniejace:
        for p in znajdz_kandydatow(list(istniejace) + [rec])["pary"]:
            if p["indeks_b"] == len(istniejace):  # nowy rekord jest ostatni
                kandydaci.append(p)
    return {"bledy": bledy, "kandydaci": kandydaci, "ostrzezenia": rap["ostrzezenia"]}


def dopisz(sciezka: Path, rec: dict) -> None:
    """Atomowe dopisanie jednego wiersza: CRLF, UTF-8, pozostałe wiersze bez zmian."""
    fragment = to_csv([dict(rec)])
    if sciezka.exists():
        stare = sciezka.read_bytes().decode("utf-8")
        if stare and not stare.endswith("\r\n"):
            stare += "\r\n"
        tekst = stare + fragment.split("\r\n", 1)[1]
    else:
        tekst = fragment
    tmp = sciezka.with_name(sciezka.name + ".tmp")
    tmp.write_text(tekst, "utf-8", newline="")
    os.replace(tmp, sciezka)
