"""
Opis zbioru AED w XML (struktura opisu datasetu + link do CSV + suma md5): walidacja, parsowanie i kontrola pliku CSV.

Moduł nie importuje Django ani ORM, więc działa też w `demo/sprawdz.py`. Kolejność importu (wykonuje ją
komenda `import_aed_xml`): opis → walidacja XSD → pobranie CSV → zgodność md5 → kontrola kolumn i duplikatów → zapis.
Schemat `aed_opis_zbioru.xsd` jest kopią `format_danych/schemat/aed_opis_zbioru.xsd` (pilnuje tego test).
"""

import hashlib
from pathlib import Path
from typing import Any, Dict

from mcod.resources.aed_aggregation import (
    build_aggregate_rows,
    missing_minimum_columns,
    read_tabular_bytes,
    rename_with_aliases,
)
from mcod.resources.aed_dedup import deduplicate_rows
from mcod.resources.aed_xml import AEDXmlInvalid, _parse, validate_aed_xml

OPIS_XSD_PATH = Path(__file__).resolve().parent / "aed_opis_zbioru.xsd"


class AEDCsvInvalid(Exception):
    pass


def validate_opis_xml(content: bytes) -> Dict[str, Any]:
    """Raport walidacji opisu: {"valid", "errors": [{"line", "field", "message"}]} (pola jak w `validate_aed_xml`)."""
    report = validate_aed_xml(content, str(OPIS_XSD_PATH))
    report["records"] = 1 if report["valid"] else 0
    return report


def parse_opis(content: bytes) -> Dict[str, Any]:
    """Wartości opisu jako słownik (`zasob` zagnieżdżony). Niezgodny z XSD: AEDXmlInvalid."""
    report = validate_opis_xml(content)
    if not report["valid"]:
        raise AEDXmlInvalid(report["errors"])
    root = _parse(content).getroot()
    result: Dict[str, Any] = {}
    for child in root:
        if child.tag == "zasob":
            result["zasob"] = {item.tag: (item.text or "").strip() for item in child}
        else:
            result[child.tag] = (child.text or "").strip()
    result["zasob"]["md5"] = result["zasob"]["md5"].lower()
    return result


def md5_hex(content: bytes) -> str:
    return hashlib.md5(content).hexdigest()  # noqa: S303 suma kontrolna pliku, nie zabezpieczenie kryptograficzne


def verify_md5(content: bytes, expected: str) -> bool:
    return md5_hex(content) == expected.strip().lower()


def inspect_csv(content: bytes, source: Dict[str, Any], aggregated_at: str) -> Dict[str, Any]:
    """
    Kontrola CSV przed zapisem: czy ma kolumny minimum wzorca i ile wierszy przejdzie agregację oraz deduplikację.
    Zwraca {"wiersze", "przyjete", "pominiete", "duplikaty": [...]}; brak kolumn minimum: AEDCsvInvalid.
    """
    try:
        df = read_tabular_bytes(content, "csv")
    except Exception as exc:
        raise AEDCsvInvalid(f"nie można odczytać CSV: {exc}") from exc
    missing = missing_minimum_columns(rename_with_aliases(df)[0].columns)
    if missing:
        raise AEDCsvInvalid(f"w CSV brakuje kolumn: {', '.join(missing)}")
    rows, skipped = build_aggregate_rows(df, source, aggregated_at)
    deduplicated, duplicates = deduplicate_rows(rows)
    return {"wiersze": len(df), "przyjete": len(deduplicated), "pominiete": len(skipped), "duplikaty": duplicates}
