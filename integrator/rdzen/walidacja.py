"""Walidacja wg Table Schema wzorca v2 i reguł dodatkowych; raport z numerami wierszy."""
from __future__ import annotations

import re
from datetime import date

from .wzorzec import FIELDS, SCHEMA


def validate_value(field: dict, v: str):
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
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", v):
            return "oczekiwano daty i czasu yyyy-mm-ddThh:mm:ss"
    if "enum" in c and v not in c["enum"]:
        return f"wartość spoza słownika: {', '.join(c['enum'])}"
    if "pattern" in c and not re.fullmatch(c["pattern"], v):
        return f"niezgodne z wzorcem {c['pattern']}"
    return None


def validate(recs: list, *, today: str = None) -> dict:
    """Błąd (odrzucenie wiersza): naruszenie schematu lub zduplikowane id_zrodlowe. Ostrzeżenie: reguły dodatkowe."""
    today = today or date.today().isoformat()
    seen: set = set()
    rep = {"liczba_wierszy": len(recs), "poprawne": 0, "z_ostrzezeniami": 0, "odrzucone": 0,
           "bledy": [], "ostrzezenia": [], "kompletnosc": {}}
    for r in recs:
        errs = []
        warns = r.setdefault("__ostrzezenia", [])
        for f in SCHEMA["fields"]:
            msg = validate_value(f, r.get(f["name"], ""))
            if msg:
                errs.append({"pole": f["name"], "komunikat": msg})
        for f, label in (("data_waznosci_elektrod", "elektrody"), ("data_waznosci_baterii", "bateria")):
            v = r.get(f, "")
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", v) and v < today:
                warns.append({"pole": f, "komunikat": f"{label} po terminie ważności: AED wymaga przeglądu"})
        if r.get("dostepny_24_7") == "true" and r.get("godziny_dostepnosci"):
            warns.append({"pole": "godziny_dostepnosci", "komunikat": "dostepny_24_7=true: godziny powinny być puste"})
        if r.get("dostepny_24_7") == "false" and not r.get("godziny_dostepnosci"):
            warns.append({"pole": "godziny_dostepnosci", "komunikat": "dostepny_24_7=false: godziny zalecane"})
        if r.get("id_zrodlowe") in seen:
            errs.append({"pole": "id_zrodlowe", "komunikat": "zduplikowany identyfikator"})
        seen.add(r.get("id_zrodlowe"))
        r["__bledy"] = errs
        r["__status"] = "odrzucony" if errs else ("ostrzezenie" if warns else "ok")
        rep["odrzucone" if errs else ("z_ostrzezeniami" if warns else "poprawne")] += 1
        rep["bledy"] += [{"wiersz": r["__wiersz"], **e, "wartosc": r.get(e["pole"], "")} for e in errs]
        rep["ostrzezenia"] += [{"wiersz": r["__wiersz"], **w} for w in warns]
    n = max(1, len(recs))
    rep["kompletnosc"] = {f: round(100 * sum(1 for r in recs if r.get(f)) / n) for f in FIELDS}
    return rep
