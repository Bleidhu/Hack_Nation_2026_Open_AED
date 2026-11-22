"""Czytanie wejścia: CSV/TSV (UTF-8, CP1250), XLSX, GeoJSON, Overpass JSON."""
from __future__ import annotations

import csv
import io
import json
import re
import zipfile


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
