"""
Reguły budowy zasobu zbiorczego „Zestawienie AED”.

Moduł nie importuje Django ani ORM portalu: przyjmuje `DataFrame` i słownik metadanych zasobu,
dzięki czemu da się go testować i uruchamiać poza portalem (`demo/agreguj.py`).
Implementacja referencyjna reguł: `format_danych/zrodla_wzorca/generuj_dane.py`
(`_norm`, `id_aed`, `wymaga_przegladu`, `powod_pominiecia`, `zestaw`).
"""

import csv
import datetime
import hashlib
import io
import re
import unicodedata
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

import pandas as pd

from mcod.resources.aed_constants import (
    AED_HEADER_ALIASES,
    AED_ID_PREFIX,
    AED_MINIMUM_COLUMNS,
    AED_TEMPLATE_COLUMNS,
    DEFAULT_STATUS,
    DEFAULT_VERIFICATION,
    LAT_RANGE,
    LON_RANGE,
    MAIN_AED_COLUMNS,
    OSM_SOURCE_VALUE,
    PROCESSING_AXES,
    PROCESSING_CODES_ORDER,
    PROCESSING_CONTACT_REMOVED,
    PROCESSING_DEFAULTS,
    PROCESSING_HEADERS,
    PROCESSING_OPERATOR_FROM_PUBLISHER,
)

LAT = "szerokosc_geograficzna"
LON = "dlugosc_geograficzna"
_COORDINATE_RE = re.compile(r"^-?\d+(\.\d+)?$")


def _strip_accents(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value).replace("ł", "l").replace("Ł", "L"))
    return "".join(c for c in value if not unicodedata.combining(c))


def _norm(value: str) -> str:
    return " ".join(_strip_accents(value).lower().split())


def normalize_header(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", _strip_accents(name).lower()).strip("_")


def rename_with_aliases(df: pd.DataFrame) -> Tuple[pd.DataFrame, Set[str]]:
    """
    Zwraca ramkę z kolumnami przemianowanymi na nazwy wzorca (kolumny spoza wzorca są pomijane)
    oraz zbiór oryginalnych nazw kolumn, których nazwa się zmieniła.

    Nazwa wzorca po normalizacji ma pierwszeństwo przed aliasem; przy dwóch kolumnach źródła
    mapowanych na ten sam cel wygrywa pierwsza od lewej.
    """
    normalized = [normalize_header(col) for col in df.columns]
    targets: Dict[int, str] = {}
    taken: Set[str] = set()
    for i, n in enumerate(normalized):
        if n in AED_TEMPLATE_COLUMNS and n not in taken:
            targets[i] = n
            taken.add(n)
    for i, n in enumerate(normalized):
        alias = AED_HEADER_ALIASES.get(n)
        if i not in targets and alias and alias not in taken:
            targets[i] = alias
            taken.add(alias)

    positions = sorted(targets)
    renamed = df.iloc[:, positions].copy()
    renamed.columns = [targets[i] for i in positions]
    changed = {str(df.columns[i]) for i in positions if str(df.columns[i]) != targets[i]}
    return renamed, changed


def missing_minimum_columns(columns: Iterable[str]) -> List[str]:
    present = set(columns)
    return [c for c in AED_MINIMUM_COLUMNS if c not in present]


def to_text(value: Any) -> str:
    if value is None or value is pd.NaT:
        return ""
    if pd.api.types.is_bool(value):
        return "true" if value else "false"
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    if isinstance(value, float) and value != value:
        return ""
    return str(value).strip()


def _parse_coordinate(value: str) -> Optional[float]:
    return float(value) if _COORDINATE_RE.match(value or "") else None


def fix_swapped_axes(row: Dict[str, str]) -> bool:
    lat, lon = _parse_coordinate(row.get(LAT, "")), _parse_coordinate(row.get(LON, ""))
    if lat is None or lon is None:
        return False
    lat_ok = LAT_RANGE[0] <= lat <= LAT_RANGE[1]
    if not lat_ok and LAT_RANGE[0] <= lon <= LAT_RANGE[1] and LON_RANGE[0] <= lat <= LON_RANGE[1]:
        row[LAT], row[LON] = row[LON], row[LAT]
        return True
    return False


def skip_reason(row: Dict[str, str]) -> Optional[str]:
    if (row.get("zrodlo_danych") or "").strip().lower() == OSM_SOURCE_VALUE:
        return "licencja ODbL (OpenStreetMap)"
    empty = [c for c in AED_MINIMUM_COLUMNS if not row.get(c)]
    if empty:
        return f"brak wartości: {', '.join(empty)}"
    lat, lon = _parse_coordinate(row[LAT]), _parse_coordinate(row[LON])
    if lat is None or lon is None:
        return "nieprawidłowe współrzędne"
    if not (LAT_RANGE[0] <= lat <= LAT_RANGE[1] and LON_RANGE[0] <= lon <= LON_RANGE[1]):
        return "współrzędne poza Polską"
    return None


def compute_id_aed(institution_id: int, row: Dict[str, str]) -> str:
    if row.get("id_zrodlowe"):
        key = f"{institution_id}|{row['id_zrodlowe']}"
    else:
        key = f"{institution_id}|{_norm(row['nazwa_lokalizacji'])}|{float(row[LAT]):.5f}|{float(row[LON]):.5f}"
    return AED_ID_PREFIX + hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]


def _parse_date(value: str) -> Optional[datetime.date]:
    try:
        return datetime.date.fromisoformat(value[:10])
    except (TypeError, ValueError):
        return None


def needs_inspection(row: Dict[str, str], today: datetime.date) -> str:
    electrodes, battery, inspection = (
        _parse_date(row.get(k) or "") for k in ("data_waznosci_elektrod", "data_waznosci_baterii", "data_ostatniego_przegladu")
    )
    if not (electrodes or battery or inspection):
        return ""
    overdue = (
        (electrodes is not None and electrodes < today)
        or (battery is not None and battery < today)
        or (inspection is not None and inspection < today - datetime.timedelta(days=365))
    )
    return "true" if overdue else "false"


def _processing(codes: Set[str]) -> str:
    return ";".join(code for code in PROCESSING_CODES_ORDER if code in codes)


def build_aggregate_rows(
    df: pd.DataFrame, source: Dict[str, Any], aggregated_at: str
) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Zamienia ramkę zasobu dostawcy na wiersze zasobu zbiorczego (kolumny `MAIN_AED_COLUMNS`).

    `source`: institution_id, publisher, license, resource_id, url, data_date, personal_data.
    Zwraca też listę pominięć `{"wiersz": nr, "powod": ...}`; wiersz 0 oznacza cały zasób.
    """
    renamed, changed_headers = rename_with_aliases(df)
    missing = missing_minimum_columns(renamed.columns)
    if missing:
        return pd.DataFrame(columns=MAIN_AED_COLUMNS), [{"wiersz": 0, "powod": f"brak kolumn: {', '.join(missing)}"}]

    today = datetime.date.fromisoformat(aggregated_at[:10])
    provenance = {
        "wydawca_zasobu": to_text(source.get("publisher")),
        "licencja_zasobu": to_text(source.get("license")),
        "id_zasobu_zrodlowego": to_text(source.get("resource_id")),
        "url_zasobu_zrodlowego": to_text(source.get("url")),
        "data_danych_zasobu": to_text(source.get("data_date")),
        "data_agregacji": aggregated_at,
    }
    rows: List[Dict[str, str]] = []
    skipped: List[Dict[str, Any]] = []
    for number, record in enumerate(renamed.to_dict("records"), start=2):
        row = {c: to_text(record.get(c)) for c in AED_TEMPLATE_COLUMNS}
        codes: Set[str] = {PROCESSING_HEADERS} if changed_headers else set()
        if fix_swapped_axes(row):
            codes.add(PROCESSING_AXES)
        reason = skip_reason(row)
        if reason:
            skipped.append({"wiersz": number, "powod": reason})
            continue

        aed_id = compute_id_aed(source["institution_id"], row)
        for column, default in (("status_urzadzenia", DEFAULT_STATUS), ("poziom_weryfikacji", DEFAULT_VERIFICATION)):
            if not row[column]:
                row[column] = default
                codes.add(PROCESSING_DEFAULTS)
        operator_from_publisher = not row["dysponent_nazwa"]
        if operator_from_publisher:
            row["dysponent_nazwa"] = provenance["wydawca_zasobu"]
            codes.add(PROCESSING_OPERATOR_FROM_PUBLISHER)
        if source.get("personal_data") and (row["telefon_kontaktowy"] or row["email_kontaktowy"]):
            row["telefon_kontaktowy"] = row["email_kontaktowy"] = ""
            codes.add(PROCESSING_CONTACT_REMOVED)

        row.update(
            id_aed=aed_id,
            wymaga_przegladu=needs_inspection(row, today),
            dysponent_z_wydawcy="true" if operator_from_publisher else "false",
            przetworzenie=_processing(codes),
            **provenance,
        )
        rows.append(row)

    return pd.DataFrame(rows, columns=MAIN_AED_COLUMNS), skipped


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    """CSV wg RFC 4180: przecinek, CRLF, jeden nagłówek, UTF-8 bez BOM."""
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL, lineterminator="\r\n")
    writer.writerow(list(df.columns))
    for values in df.itertuples(index=False, name=None):
        writer.writerow([to_text(v) for v in values])
    return buffer.getvalue().encode("utf-8")
