"""Licencja źródła jest jawna, nigdy domyślna. Dla portalu przechodzą tylko licencje z konfiguracji."""
from __future__ import annotations

import json
import re
from pathlib import Path

KONFIGURACJA = Path(__file__).resolve().parent.parent / "konfiguracja.json"


class LicencjaBlad(ValueError):
    """Licencji brakuje albo nie pozwala na publikację w portalu."""


def wczytaj_konfiguracje(sciezka=None) -> dict:
    return json.loads(Path(sciezka or KONFIGURACJA).read_text("utf-8"))


def kanoniczna(licencja, konfiguracja: dict) -> str:
    """„CC0-1.0”, „cc0 1.0”, „ODbL-1.0” → postać z konfiguracji („CC0 1.0”, „ODbL 1.0”); nieznana zostaje bez zmian."""
    n = re.sub(r"[\s_-]+", " ", (licencja or "").strip())
    znane = list(konfiguracja.get("dozwolone_licencje", [])) + list(konfiguracja.get("atrybucje", {}))
    return next((z for z in znane if z.lower() == n.lower()), n)


def sprawdz(licencja, cel: str, konfiguracja: dict) -> dict:
    """Zwraca {licencja, atrybucja, do_publikacji, ostrzezenie}; dla celu `portal` rzuca LicencjaBlad."""
    if cel not in ("portal", "lokalny"):
        raise ValueError(f"nieznany cel: {cel}")
    dozwolone = konfiguracja.get("dozwolone_licencje", [])
    lic = kanoniczna(licencja, konfiguracja)
    if not lic:
        if cel == "portal":
            raise LicencjaBlad("Brak licencji źródła. Podaj ją jawnie (--licencja), np. „CC0 1.0” albo „CC BY 4.0”.")
        return {"licencja": "", "atrybucja": "", "do_publikacji": False,
                "ostrzezenie": "Brak licencji źródła: wynik nie nadaje się do publikacji."}
    ok = lic in dozwolone
    info = {"licencja": lic, "atrybucja": konfiguracja.get("atrybucje", {}).get(lic, ""), "do_publikacji": ok, "ostrzezenie": ""}
    if not ok:
        msg = (f"Licencja „{lic}” nie jest na liście dozwolonych ({', '.join(dozwolone)}). "
               "Dane na tej licencji nie trafiają do zbioru dla portalu.")
        if cel == "portal":
            raise LicencjaBlad(msg)
        info["ostrzezenie"] = msg + " Wynik tylko do użytku lokalnego i porównań."
    return info
