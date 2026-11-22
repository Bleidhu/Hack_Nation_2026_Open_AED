"""
Źródło XML dla wykazu AED: walidacja plikiem XSD i zamiana na `DataFrame` o kolumnach wzorca v2.

Moduł nie importuje Django ani ORM (jak `aed_aggregation.py`), więc działa też w `demo/sprawdz.py`.
Schemat `aed_punkty.xsd` jest kopią `format_danych/schemat/aed_punkty.xsd` (generuje je
`format_danych/narzedzia/generuj_xsd.py`; zgodność pilnuje test `test_aed_xml.py`).
"""

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from lxml import etree

from mcod.resources.aed_constants import AED_TEMPLATE_COLUMNS

XSD_PATH = Path(__file__).resolve().parent / "aed_punkty.xsd"
MAX_XML_BYTES = 20 * 1024 * 1024


class AEDXmlInvalid(Exception):
    def __init__(self, errors: List[Dict[str, Any]]):
        self.errors = errors
        first = errors[0] if errors else {}
        super().__init__(f"XML niezgodny z XSD ({len(errors)} błędów): linia {first.get('line')}: {first.get('message')}")


@lru_cache(maxsize=None)
def load_schema(path: Optional[str] = None) -> etree.XMLSchema:
    return etree.XMLSchema(etree.parse(str(path or XSD_PATH)))


def _parse(content: bytes) -> etree._ElementTree:
    # Bez DTD, zewnętrznych encji i sieci: plik pochodzi z zewnątrz i nie jest zaufany.
    parser = etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False, dtd_validation=False)
    return etree.fromstring(content, parser).getroottree()


def _required_fields(xsd_path: Optional[str] = None) -> List[str]:
    ns = {"xs": "http://www.w3.org/2001/XMLSchema"}
    tree = etree.parse(str(xsd_path or XSD_PATH))
    return tree.xpath("//xs:all/xs:element[@minOccurs='1']/@name", namespaces=ns)


def _describe(error, tree) -> Dict[str, Any]:
    path = error.path or ""
    message = error.message
    field = path.rsplit("/", 1)[-1]
    if "Missing child element" in message:
        # xs:all wymienia w komunikacie pola opcjonalne, więc wskazujemy brakujące pole wymagane.
        record = tree.xpath(path)
        present = {child.tag for child in record[0]} if record else set()
        missing = [name for name in _required_fields() if name not in present]
        if missing:
            message = f"brak wymaganego pola: {', '.join(missing)}"
            field = missing[0]
    return {"line": error.line, "field": field, "message": message}


def validate_aed_xml(content: bytes, xsd_path: Optional[str] = None) -> Dict[str, Any]:
    """Raport: {"valid": bool, "records": int, "errors": [{"line", "field", "message"}]}."""
    if not content or not content.strip():
        return {"valid": False, "records": 0, "errors": [{"line": 0, "field": "", "message": "pusty plik"}]}
    if len(content) > MAX_XML_BYTES:
        return {"valid": False, "records": 0, "errors": [{"line": 0, "field": "", "message": "plik większy niż 20 MB"}]}
    try:
        tree = _parse(content)
    except etree.XMLSyntaxError as exc:
        return {
            "valid": False,
            "records": 0,
            "errors": [{"line": exc.lineno or 0, "field": "", "message": f"niepoprawny XML: {exc.msg}"}],
        }
    if tree.docinfo.doctype or b"<!ENTITY" in content:
        return {
            "valid": False,
            "records": 0,
            "errors": [{"line": 0, "field": "", "message": "deklaracje DOCTYPE i ENTITY są niedozwolone"}],
        }
    schema = load_schema(xsd_path)
    try:
        valid = schema.validate(tree)
    except etree.XMLSchemaValidateError as exc:
        return {"valid": False, "records": 0, "errors": [{"line": 0, "field": "", "message": f"błąd walidacji: {exc}"}]}
    errors = [_describe(e, tree) for e in schema.error_log]
    return {"valid": bool(valid), "records": len(tree.getroot().findall("aed")), "errors": errors}


def aed_xml_to_df(content: bytes, xsd_path: Optional[str] = None) -> pd.DataFrame:
    """Ramka tekstowa (jak reszta agregacji) o kolumnach wzorca; brakujące pola to pusty tekst. Niezgodny XML: AEDXmlInvalid."""
    report = validate_aed_xml(content, xsd_path)
    if not report["valid"]:
        raise AEDXmlInvalid(report["errors"])
    root = _parse(content).getroot()
    rows = [{col: (record.findtext(col) or "").strip() for col in AED_TEMPLATE_COLUMNS} for record in root.findall("aed")]
    return pd.DataFrame(rows, columns=AED_TEMPLATE_COLUMNS)
