"""Wejście w formacie OSM: Overpass JSON, GeoJSON i OSM XML. Zwraca wiersze (tagi + __lat/__lon/@id/__url/__data) i metadane."""
from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from rdzen.wejscie import decode, geometry_point

MAPOWANIE = Path(__file__).resolve().parent / "osm_mapowanie.json"


def wczytaj_mapowanie() -> dict:
    return json.loads(MAPOWANIE.read_text("utf-8"))


def _url(typ: str, oid) -> str:
    return f"https://www.openstreetmap.org/{typ}/{oid}"


def _wiersz(tags: dict, typ: str, oid, lat, lon, data: str) -> dict:
    row = {k: str(v) for k, v in tags.items()}
    row["@id"] = f"osm:{typ}/{oid}"
    row["__lat"], row["__lon"] = str(lat), str(lon)
    row["__url"] = _url(typ, oid)
    row["__data"] = data
    return row


def _czas(ts) -> str:
    """„2026-11-21T06:00:00Z” → „2026-11-21T06:00:00” (format kolumny data_aktualizacji); brak = pusty (będzie data importu)."""
    return (ts or "").rstrip("Z")[:19]


def _elementy(elements, data: str):
    rows, pominiete = [], []
    for el in elements:
        typ, oid, tags = el.get("type"), el.get("id"), el.get("tags") or {}
        c = el if typ == "node" else el.get("center")
        if not c or c.get("lat") is None or c.get("lon") is None:
            pominiete.append({"id": f"{typ}/{oid}", "powod": "brak środka geometrii (użyj `out center` w Overpass)"})
            continue
        rows.append(_wiersz(tags, typ, oid, c["lat"], c["lon"], data))
    return rows, pominiete


def wczytaj(data: bytes, filename: str = "") -> tuple:
    """(wiersze, meta). meta: format, timestamp_osm_base, pominiete [{id, powod}]."""
    text = decode(data)
    s = text.lstrip()
    if s.startswith("<"):
        root = ET.fromstring(text)
        ts = (root.find("meta") is not None and root.find("meta").get("osm_base")) or root.get("timestamp") or ""
        els = []
        for e in root:
            if e.tag not in ("node", "way", "relation"):
                continue
            ctr = e if e.tag == "node" else e.find("center")
            els.append({"type": e.tag, "id": e.get("id"), "tags": {t.get("k"): t.get("v") for t in e.findall("tag")},
                        "lat": ctr.get("lat") if ctr is not None else None, "lon": ctr.get("lon") if ctr is not None else None,
                        "center": {"lat": ctr.get("lat"), "lon": ctr.get("lon")} if ctr is not None and e.tag != "node" else None})
        rows, pominiete = _elementy(els, _czas(ts))
        return rows, {"format": "osm-xml", "timestamp_osm_base": _czas(ts), "pominiete": pominiete}
    obj = json.loads(text)
    if isinstance(obj, dict) and "elements" in obj:
        ts = _czas((obj.get("osm3s") or {}).get("timestamp_osm_base"))
        rows, pominiete = _elementy(obj["elements"], ts)
        return rows, {"format": "overpass-json", "timestamp_osm_base": ts, "pominiete": pominiete}
    if isinstance(obj, dict) and obj.get("type") == "FeatureCollection":
        rows, pominiete = [], []
        for i, f in enumerate(obj.get("features", [])):
            p = f.get("properties") or {}
            lat, lon = geometry_point(f.get("geometry"))
            typ = p.get("@osm_type") or (str(f.get("id", "")).split("/")[0] if "/" in str(f.get("id", "")) else "node")
            oid = p.get("@osm_id") or (str(f.get("id", "")).split("/")[-1] if f.get("id") else f"geojson-{i + 1}")
            if not lat:
                pominiete.append({"id": f"{typ}/{oid}", "powod": "brak geometrii punktowej"})
                continue
            tags = {k: v for k, v in p.items() if not k.startswith("@")}
            rows.append(_wiersz(tags, typ, oid, lat, lon, ""))
        return rows, {"format": "geojson", "timestamp_osm_base": "", "pominiete": pominiete}
    raise ValueError("Nierozpoznany format OSM: oczekiwano Overpass JSON, GeoJSON FeatureCollection lub OSM XML")


def tagi_bez_odpowiednika(rows: list, mapowanie: dict) -> dict:
    """Licznik tagów, których nie czyta żadna kolumna mapowania (bez zgadywania; informacja do raportu)."""
    uzyte = set(mapowanie.get("ignorowane_tagi", []))
    for spec in mapowanie["kolumny"].values():
        z = spec.get("z")
        uzyte.update(z if isinstance(z, list) else [z] if z else [])
    licznik: dict = {}
    for r in rows:
        for k in r:
            if k not in uzyte and not k.startswith("__") and not k.startswith("@"):
                licznik[k] = licznik.get(k, 0) + 1
    return dict(sorted(licznik.items(), key=lambda kv: (-kv[1], kv[0])))
