"""Normalizacja wartości do postaci wzorca v2 (przecinek dziesiętny, TAK/NIE, daty ISO, kod, telefon, REGON)."""
from __future__ import annotations

import re

from .wzorzec import FIELD

TRUE = {"true", "tak", "t", "yes", "y", "1", "24/7", "24h", "calodobowo", "całodobowo", "x"}
FALSE = {"false", "nie", "n", "no", "0", "-"}


def norm_value(field: str, v, warnings: list) -> str:
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
        v = v[:19] if re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[.,]\d+", v) else v
    if field == "kod_pocztowy" and re.fullmatch(r"\d{5}", v):
        v = f"{v[:2]}-{v[2:]}"
    if field == "telefon_kontaktowy":
        d = re.sub(r"[^\d+]", "", v)
        v = "+" + d if d.startswith("48") and len(d) == 11 else d
    if field == "dysponent_regon":
        v = re.sub(r"\D", "", v)
    return v
