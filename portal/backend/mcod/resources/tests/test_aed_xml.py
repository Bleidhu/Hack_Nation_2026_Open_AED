"""Czyste testy (bez bazy) źródła XML wykazu AED: walidacja XSD i zamiana na ramkę."""

import json
from pathlib import Path

import pytest

from mcod.resources.aed_constants import AED_TEMPLATE_COLUMNS
from mcod.resources.aed_xml import XSD_PATH, AEDXmlInvalid, aed_xml_to_df, validate_aed_xml

REPO_SCHEMA = Path(__file__).resolve().parents[5] / "format_danych" / "schemat"  # poza kontenerem portalu może nie istnieć

RECORD = {
    "id_zrodlowe": "T-1",
    "nazwa_lokalizacji": "Test – hol",
    "miejscowosc": "Olsztyn",
    "szerokosc_geograficzna": "53.778420",
    "dlugosc_geograficzna": "20.480120",
    "opis_lokalizacji": "Parter, hol",
    "typ_dostepu": "publiczny",
    "dostepny_24_7": "true",
    "data_aktualizacji": "2026-11-20T08:00:00",
}


def make_xml(*records, drop=(), **override):
    def one(rec):
        fields = {**RECORD, **rec, **override}
        for name in drop:
            fields.pop(name, None)
        return "<aed>" + "".join(f"<{k}>{v}</{k}>" for k, v in fields.items()) + "</aed>"

    return ('<?xml version="1.0" encoding="UTF-8"?><wykaz>' + "".join(one(r) for r in records) + "</wykaz>").encode("utf-8")


def test_valid_file():
    report = validate_aed_xml(make_xml({}, {"id_zrodlowe": "T-2"}))
    assert report == {"valid": True, "records": 2, "errors": []}


def test_missing_required_field_names_the_field():
    report = validate_aed_xml(make_xml({}, drop=("typ_dostepu",)))
    assert not report["valid"]
    assert report["errors"][0]["field"] == "typ_dostepu"
    assert "brak wymaganego pola" in report["errors"][0]["message"]


def test_value_outside_dictionary_and_wrong_type():
    report = validate_aed_xml(
        make_xml({"id_zrodlowe": "A", "status_urzadzenia": "dziala"}, {"id_zrodlowe": "B", "szerokosc_geograficzna": "abc"})
    )
    assert sorted(e["field"] for e in report["errors"]) == ["status_urzadzenia", "szerokosc_geograficzna"]
    assert all(e["line"] >= 1 for e in report["errors"])


def test_coordinates_outside_poland_rejected():
    assert not validate_aed_xml(make_xml({}, szerokosc_geograficzna="10.0"))["valid"]


def test_duplicate_source_id_rejected():
    assert not validate_aed_xml(make_xml({}, {}))["valid"]


@pytest.mark.parametrize("content", [b"", b"   ", b"<wykaz><aed>", b"nie xml"])
def test_broken_or_empty_input(content):
    report = validate_aed_xml(content)
    assert not report["valid"] and report["errors"]


def test_external_entities_are_not_resolved(tmp_path):
    secret = tmp_path / "secret.txt"
    secret.write_text("TAJNE")
    doctype = f'<!DOCTYPE x [<!ENTITY e SYSTEM "file://{secret.as_posix()}">]>'
    xml = f'<?xml version="1.0"?>{doctype}<wykaz><aed><id_zrodlowe>&e;</id_zrodlowe></aed></wykaz>'
    report = validate_aed_xml(xml.encode())
    assert not report["valid"] and "TAJNE" not in json.dumps(report)


def test_dataframe_has_template_columns_and_text_values():
    df = aed_xml_to_df(make_xml({}, kondygnacja="0"))
    assert list(df.columns) == AED_TEMPLATE_COLUMNS
    assert df.loc[0, "kondygnacja"] == "0" and df.loc[0, "powiat"] == ""


def test_dataframe_rejects_invalid_xml():
    with pytest.raises(AEDXmlInvalid) as exc:
        aed_xml_to_df(make_xml({}, drop=("miejscowosc",)))
    assert exc.value.errors[0]["field"] == "miejscowosc"


def test_xsd_matches_template_columns():
    names = XSD_PATH.read_text(encoding="utf-8")
    assert all(f'name="{col}"' in names for col in AED_TEMPLATE_COLUMNS)


@pytest.mark.skipif(not (REPO_SCHEMA / "aed_punkty.xsd").exists(), reason="brak katalogu format_danych w kontenerze")
def test_portal_xsd_is_copy_of_repo_xsd_and_matches_table_schema():
    assert XSD_PATH.read_bytes() == (REPO_SCHEMA / "aed_punkty.xsd").read_bytes()
    schema = json.loads((REPO_SCHEMA / "aed_punkty.tableschema.json").read_text(encoding="utf-8"))
    assert [f["name"] for f in schema["fields"]] == AED_TEMPLATE_COLUMNS
    required = {f["name"] for f in schema["fields"] if f.get("constraints", {}).get("required")}
    xsd = XSD_PATH.read_text(encoding="utf-8")
    assert required == {c for c in AED_TEMPLATE_COLUMNS if f'<xs:element name="{c}" minOccurs="1">' in xsd}
