"""Czyste testy (bez bazy) opisu zbioru AED w XML: walidacja XSD, md5, kontrola CSV."""

import csv
import hashlib
import io
import json
from pathlib import Path

import pytest

from mcod.resources.aed_constants import AED_TEMPLATE_COLUMNS
from mcod.resources.aed_opis import (
    OPIS_XSD_PATH,
    AEDCsvInvalid,
    inspect_csv,
    md5_hex,
    parse_opis,
    validate_opis_xml,
    verify_md5,
)
from mcod.resources.aed_xml import AEDXmlInvalid

REPO_SCHEMA = Path(__file__).resolve().parents[5] / "format_danych" / "schemat"
SOURCE = {
    "institution_id": 1,
    "publisher": "Dostawca",
    "license": "CC BY 4.0",
    "resource_id": 1,
    "url": "https://dostawca.example.pl/opis.xml",
    "data_date": "2026-11-22",
    "personal_data": False,
}


def make_csv(*rows, columns=None):
    columns = columns or AED_TEMPLATE_COLUMNS
    buf = io.StringIO(newline="")
    writer = csv.DictWriter(buf, fieldnames=columns, lineterminator="\r\n")
    writer.writeheader()
    for index, row in enumerate(rows, 1):
        base = {
            "id_zrodlowe": f"X-{index}",
            "nazwa_lokalizacji": f"Hala {index}",
            "miejscowosc": "Olsztyn",
            "szerokosc_geograficzna": f"53.{index}000",
            "dlugosc_geograficzna": f"20.{index}000",
        }
        base.update(row)
        writer.writerow({k: base.get(k, "") for k in columns})
    return buf.getvalue().encode("utf-8")


def make_opis(
    md5="0" * 32, link="https://dostawca.example.pl/aed.csv", license_name="CC BY 4.0", title="Defibrylatory AED", **extra
):
    parts = {
        "tytul": title,
        "opis": "Opis zbioru",
        "dysponent_nazwa": "Dostawca",
        "licencja": license_name,
        "czestotliwosc_aktualizacji": "daily",
        "data_aktualizacji": "2026-11-22T06:00:00",
    }
    parts.update(extra)
    body = "".join(f"<{k}>{v}</{k}>" for k, v in parts.items() if v is not None)
    zasob = f"<zasob><tytul>CSV</tytul><link_csv>{link}</link_csv><format>csv</format><md5>{md5}</md5></zasob>"
    return f'<?xml version="1.0" encoding="UTF-8"?><opis_zbioru>{body}{zasob}</opis_zbioru>'.encode("utf-8")


def test_valid_opis_is_parsed():
    opis = parse_opis(make_opis(md5="ABCDEF0123456789ABCDEF0123456789"))
    assert opis["tytul"] == "Defibrylatory AED" and opis["licencja"] == "CC BY 4.0"
    assert opis["zasob"]["link_csv"] == "https://dostawca.example.pl/aed.csv"
    assert opis["zasob"]["md5"] == "abcdef0123456789abcdef0123456789"


@pytest.mark.parametrize(
    ("content", "field"),
    [
        (make_opis(title=None), "tytul"),
        (make_opis(link="http://dostawca.example.pl/aed.csv"), "link_csv"),
        (make_opis(license_name="CC BY-SA 4.0"), "licencja"),
        (make_opis(md5="xyz"), "md5"),
        (make_opis(czestotliwosc_aktualizacji="co_godzine"), "czestotliwosc_aktualizacji"),
        (make_opis(data_aktualizacji="wczoraj"), "data_aktualizacji"),
    ],
)
def test_invalid_opis_points_to_the_field(content, field):
    report = validate_opis_xml(content)
    assert not report["valid"] and field in [e["field"] for e in report["errors"]]
    with pytest.raises(AEDXmlInvalid):
        parse_opis(content)


@pytest.mark.parametrize("content", [b"", b"<opis_zbioru>", b"nie xml"])
def test_broken_opis(content):
    assert not validate_opis_xml(content)["valid"]


def test_doctype_is_rejected():
    xml = b'<?xml version="1.0"?><!DOCTYPE x [<!ENTITY e SYSTEM "file:///etc/passwd">]><opis_zbioru>&e;</opis_zbioru>'
    report = validate_opis_xml(xml)
    assert not report["valid"] and "root:" not in json.dumps(report)


def test_md5_is_verified_case_insensitively():
    data = make_csv({})
    assert md5_hex(data) == hashlib.md5(data).hexdigest()
    assert verify_md5(data, md5_hex(data).upper()) and not verify_md5(data, "0" * 32)
    assert not verify_md5(data + b"x", md5_hex(data))


def test_inspect_csv_counts_rows_and_duplicates():
    data = make_csv(
        {"producent": "Zoll", "numer_seryjny": "ZP-0001", "szerokosc_geograficzna": "53.1", "dlugosc_geograficzna": "20.1"},
        {"producent": "Zoll", "numer_seryjny": "zp 0001", "szerokosc_geograficzna": "53.2", "dlugosc_geograficzna": "20.2"},
        {},
    )
    report = inspect_csv(data, SOURCE, "2026-11-22T04:15:00")
    assert (report["wiersze"], report["przyjete"], len(report["duplikaty"])) == (3, 2, 1)
    assert report["duplikaty"][0]["powod"] == "numer_seryjny"


def test_inspect_csv_without_minimum_columns_is_rejected():
    with pytest.raises(AEDCsvInvalid, match="brakuje kolumn"):
        inspect_csv(make_csv({}, columns=["id_zrodlowe", "producent"]), SOURCE, "2026-11-22T04:15:00")


@pytest.mark.skipif(not (REPO_SCHEMA / "aed_opis_zbioru.xsd").exists(), reason="brak katalogu format_danych w kontenerze")
def test_portal_xsd_is_copy_of_repo_xsd():
    assert OPIS_XSD_PATH.read_bytes() == (REPO_SCHEMA / "aed_opis_zbioru.xsd").read_bytes()
