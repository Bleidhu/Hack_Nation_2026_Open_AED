"""Generuje format_danych/schemat/aed_punkty.xsd z aed_punkty.tableschema.json (tylko biblioteka standardowa).

Struktura płaska: <wykaz><aed><id_zrodlowe>…</id_zrodlowe>…</aed>…</wykaz>.
Jedno pole wzorca = jeden element o nazwie kolumny. Pola wymagane (constraints.required) mają minOccurs=1,
pozostałe są pomijane, gdy nie ma wartości. Kolejność elementów dowolna (xs:all), id_zrodlowe unikalne.
Uruchomienie: python format_danych/narzedzia/generuj_xsd.py
"""
import json
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

KATALOG = Path(__file__).resolve().parent.parent / "schemat"
DATETIME_PATTERN = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"


def _restriction(base, facets):
    body = "".join(f"<xs:{k} value={quoteattr(str(v))}/>" for k, v in facets)
    return f'<xs:restriction base="xs:{base}">{body}</xs:restriction>'


def _type_xml(field):
    c = field.get("constraints", {})
    t = field["type"]
    if t == "number":
        facets = [("minInclusive", c["minimum"]), ("maxInclusive", c["maximum"])] if "minimum" in c else []
        return _restriction("decimal", facets)
    if t == "integer":
        return _restriction("integer", [])
    if t == "boolean":
        return '<xs:restriction base="xs:boolean"/>'
    if t == "date":
        return '<xs:restriction base="xs:date"/>'
    if t == "datetime":
        return _restriction("string", [("pattern", DATETIME_PATTERN)])
    facets = [("enumeration", v) for v in c.get("enum", [])]
    if "pattern" in c:
        facets.append(("pattern", c["pattern"].lstrip("^").rstrip("$")))  # w XSD wzorce są domyślnie zakotwiczone
    return _restriction("string", facets)


def build_xsd(schema):
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" elementFormDefault="qualified">',
        f"  <!-- {escape(schema['title'])}, wersja {escape(str(schema['version']))}. "
        "Plik generowany z aed_punkty.tableschema.json przez format_danych/narzedzia/generuj_xsd.py. -->",
        '  <xs:element name="wykaz">',
        "    <xs:complexType><xs:sequence>",
        '      <xs:element name="aed" minOccurs="1" maxOccurs="unbounded">',
        "        <xs:complexType><xs:all>",
    ]
    for f in schema["fields"]:
        required = f.get("constraints", {}).get("required", False)
        lines.append(
            f'          <xs:element name="{f["name"]}" minOccurs="{1 if required else 0}">'
            f"<xs:simpleType>{_type_xml(f)}</xs:simpleType></xs:element>"
        )
    lines += [
        "        </xs:all></xs:complexType>",
        "      </xs:element>",
        "    </xs:sequence></xs:complexType>",
        '    <xs:unique name="unikalny_id_zrodlowe"><xs:selector xpath="aed"/><xs:field xpath="id_zrodlowe"/></xs:unique>',
        "  </xs:element>",
        "</xs:schema>",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    schema = json.loads((KATALOG / "aed_punkty.tableschema.json").read_text(encoding="utf-8"))
    xsd = build_xsd(schema)
    # Kopia w pakiecie portalu: kontener portalu nie widzi katalogu format_danych/.
    for cel in (KATALOG / "aed_punkty.xsd", KATALOG.parent.parent / "portal/backend/mcod/resources/aed_punkty.xsd"):
        cel.write_text(xsd, encoding="utf-8", newline="\n")
        print("Zapisano", cel)
