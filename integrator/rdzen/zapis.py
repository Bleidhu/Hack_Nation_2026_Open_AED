"""Zapis: CSV RFC 4180 (UTF-8, CRLF, jeden nagłówek, kolumny w kolejności wzorca) i GeoJSON."""
from __future__ import annotations

import csv
import io

from .wzorzec import FIELDS


def to_csv(recs: list, *, only_valid: bool = True) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\r\n")
    w.writerow(FIELDS)
    for r in recs:
        if only_valid and r.get("__status") == "odrzucony":
            continue
        w.writerow([r.get(f, "") for f in FIELDS])
    return buf.getvalue()


def to_geojson(recs: list) -> dict:
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
