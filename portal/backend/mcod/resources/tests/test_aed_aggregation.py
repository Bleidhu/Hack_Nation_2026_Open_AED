import datetime
import io
from pathlib import Path

import pandas as pd
import pytest
from django.conf import settings

from mcod.resources.aed_aggregation import (
    build_aggregate_rows,
    compute_id_aed,
    fix_swapped_axes,
    missing_minimum_columns,
    needs_inspection,
    normalize_header,
    read_tabular_bytes,
    rename_with_aliases,
    skip_reason,
    to_csv_bytes,
    to_text,
)
from mcod.resources.aed_constants import MAIN_AED_COLUMNS

AGGREGATED_AT = "2026-11-22T04:15:00"
SOURCE_MUNICIPALITY = {
    "institution_id": 1001,
    "publisher": "Gmina Przykładowa (PRZYKŁAD)",
    "license": "CC0 1.0",
    "resource_id": 900001,
    "url": "https://dane.gov.pl/pl/dataset/1/resource/900001",
    "data_date": "2026-11-20",
    "personal_data": False,
}
SOURCE_COUNTY = {
    "institution_id": 1002,
    "publisher": "Starostwo Powiatowe Przykład (PRZYKŁAD)",
    "license": "CC BY 4.0",
    "resource_id": 900002,
    "url": "https://dane.gov.pl/pl/dataset/2/resource/900002",
    "data_date": "2026-11-19",
    "personal_data": True,
}


@pytest.fixture
def aed_samples() -> Path:
    return Path(settings.TEST_SAMPLES_PATH, "aed")


def read_sample(path: Path, **kwargs) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False, **kwargs)


def minimal_row(**values) -> dict:
    row = {
        "id_zrodlowe": "A-1",
        "nazwa_lokalizacji": "Ratusz",
        "miejscowosc": "Legionowo",
        "szerokosc_geograficzna": "52.400000",
        "dlugosc_geograficzna": "20.930000",
        "status_urzadzenia": "sprawny",
        "poziom_weryfikacji": "zweryfikowany_w_terenie",
        "dysponent_nazwa": "Urząd Miasta",
    }
    row.update(values)
    return row


@pytest.mark.feat_main_aed
@pytest.mark.parametrize(
    ("header", "expected"),
    [
        ("Długość geograficzna", "dlugosc_geograficzna"),
        (" Nr_Budynku ", "nr_budynku"),
        ("Łódź", "lodz"),
        ("\ufeffnazwa", "nazwa"),
        (" Numer Id", "numer_id"),
    ],
)
def test_normalize_header(header, expected):
    assert normalize_header(header) == expected


@pytest.mark.feat_main_aed
@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, ""),
        (True, "true"),
        (False, "false"),
        (datetime.date(2026, 1, 2), "2026-01-02"),
        (float("nan"), ""),
        (" x ", "x"),
        (52.5, "52.5"),
    ],
)
def test_to_text(value, expected):
    assert to_text(value) == expected


@pytest.mark.feat_main_aed
def test_compute_id_aed_deterministic():
    row = {"id_zrodlowe": "A"}
    assert compute_id_aed(1, row) == compute_id_aed(1, dict(row))
    assert compute_id_aed(1, row).startswith("PL-AED-")
    assert len(compute_id_aed(1, row)) == len("PL-AED-") + 12


@pytest.mark.feat_main_aed
def test_compute_id_aed_fallback_without_source_id():
    row = {
        "id_zrodlowe": "",
        "nazwa_lokalizacji": "Ratusz  Łódź",
        "szerokosc_geograficzna": "51.7",
        "dlugosc_geograficzna": "19.4",
    }
    assert compute_id_aed(1, row) == compute_id_aed(1, dict(row, nazwa_lokalizacji="ratusz lodz"))
    assert compute_id_aed(1, row) != compute_id_aed(1, dict(row, szerokosc_geograficzna="51.8"))


@pytest.mark.feat_main_aed
def test_compute_id_aed_differs_by_institution():
    assert compute_id_aed(1, {"id_zrodlowe": "A"}) != compute_id_aed(2, {"id_zrodlowe": "A"})


@pytest.mark.feat_main_aed
@pytest.mark.parametrize(
    ("row", "expected"),
    [
        ({}, ""),
        ({"data_waznosci_elektrod": "2026-11-21"}, "true"),
        ({"data_ostatniego_przegladu": "2025-11-21"}, "true"),
        ({"data_ostatniego_przegladu": "2025-11-23", "data_waznosci_baterii": "2027-01-01"}, "false"),
    ],
)
def test_needs_inspection(row, expected):
    assert needs_inspection(row, datetime.date(2026, 11, 22)) == expected


@pytest.mark.feat_main_aed
def test_needs_inspection_ignores_unparseable_dates():
    assert needs_inspection({"data_waznosci_baterii": "31.12.2020"}, datetime.date(2026, 11, 22)) == ""


@pytest.mark.feat_main_aed
def test_skip_reason_osm():
    assert skip_reason(minimal_row(zrodlo_danych="openstreetmap")).startswith("licencja ODbL")


@pytest.mark.feat_main_aed
def test_skip_reason_missing_minimum():
    assert skip_reason(minimal_row(miejscowosc="")) == "brak wartości: miejscowosc"


@pytest.mark.feat_main_aed
@pytest.mark.parametrize("latitude", ["52,4", "abc", "52.4N"])
def test_skip_reason_bad_coordinates(latitude):
    assert skip_reason(minimal_row(szerokosc_geograficzna=latitude)) == "nieprawidłowe współrzędne"


@pytest.mark.feat_main_aed
def test_skip_reason_outside_poland():
    assert skip_reason(minimal_row(szerokosc_geograficzna="48.1")) == "współrzędne poza Polską"


@pytest.mark.feat_main_aed
def test_skip_reason_valid_row():
    assert skip_reason(minimal_row()) is None


@pytest.mark.feat_main_aed
def test_fix_swapped_axes():
    row = minimal_row(szerokosc_geograficzna="21.1", dlugosc_geograficzna="52.3")
    assert fix_swapped_axes(row) is True
    assert (row["szerokosc_geograficzna"], row["dlugosc_geograficzna"]) == ("52.3", "21.1")
    assert fix_swapped_axes(row) is False

    df = pd.DataFrame([minimal_row(szerokosc_geograficzna="21.1", dlugosc_geograficzna="52.3")])
    result, skipped = build_aggregate_rows(df, SOURCE_MUNICIPALITY, AGGREGATED_AT)
    assert skipped == []
    assert result.loc[0, "szerokosc_geograficzna"] == "52.3"
    assert result.loc[0, "przetworzenie"] == "osie"


@pytest.mark.feat_main_aed
def test_defaults_operator_contacts():
    df = pd.DataFrame(
        [minimal_row(status_urzadzenia="", poziom_weryfikacji="", dysponent_nazwa="", telefon_kontaktowy="123456789")]
    )
    result, skipped = build_aggregate_rows(df, dict(SOURCE_MUNICIPALITY, personal_data=True), AGGREGATED_AT)
    row = result.iloc[0]
    assert skipped == []
    assert row["status_urzadzenia"] == "nieznany"
    assert row["poziom_weryfikacji"] == "niezweryfikowany"
    assert row["dysponent_nazwa"] == SOURCE_MUNICIPALITY["publisher"]
    assert row["dysponent_z_wydawcy"] == "true"
    assert row["telefon_kontaktowy"] == ""
    assert row["przetworzenie"] == "domyslne;dysponent_z_wydawcy;kontakt_usuniety"


@pytest.mark.feat_main_aed
def test_contacts_kept_without_personal_data():
    df = pd.DataFrame([minimal_row(telefon_kontaktowy="123456789")])
    result, _ = build_aggregate_rows(df, SOURCE_MUNICIPALITY, AGGREGATED_AT)
    assert result.loc[0, "telefon_kontaktowy"] == "123456789"


@pytest.mark.feat_main_aed
def test_unchanged_row_has_empty_processing():
    result, skipped = build_aggregate_rows(pd.DataFrame([minimal_row()]), SOURCE_MUNICIPALITY, AGGREGATED_AT)
    assert skipped == []
    assert result.loc[0, "przetworzenie"] == ""
    assert result.loc[0, "dysponent_z_wydawcy"] == "false"
    assert list(result.columns) == MAIN_AED_COLUMNS


@pytest.mark.feat_main_aed
def test_provenance_columns():
    result, _ = build_aggregate_rows(pd.DataFrame([minimal_row()]), SOURCE_COUNTY, AGGREGATED_AT)
    row = result.iloc[0]
    assert row["wydawca_zasobu"] == SOURCE_COUNTY["publisher"]
    assert row["licencja_zasobu"] == "CC BY 4.0"
    assert row["id_zasobu_zrodlowego"] == "900002"
    assert row["url_zasobu_zrodlowego"] == SOURCE_COUNTY["url"]
    assert row["data_danych_zasobu"] == "2026-11-19"
    assert row["data_agregacji"] == AGGREGATED_AT


@pytest.mark.feat_main_aed
def test_skipped_rows_are_reported_with_row_number():
    df = pd.DataFrame([minimal_row(), minimal_row(id_zrodlowe="A-2", zrodlo_danych="openstreetmap"), minimal_row(miejscowosc="")])
    result, skipped = build_aggregate_rows(df, SOURCE_MUNICIPALITY, AGGREGATED_AT)
    assert len(result) == 1
    assert skipped == [
        {"wiersz": 3, "powod": "licencja ODbL (OpenStreetMap)"},
        {"wiersz": 4, "powod": "brak wartości: miejscowosc"},
    ]


@pytest.mark.feat_main_aed
def test_golden_matches_reference(aed_samples):
    df = read_sample(aed_samples / "aed_punkty_przyklad.csv")
    parts = []
    for _, record in df.iterrows():
        source = SOURCE_COUNTY if record["id_zrodlowe"] == "UNI-B-3" else SOURCE_MUNICIPALITY
        rows, skipped = build_aggregate_rows(record.to_frame().T, source, AGGREGATED_AT)
        assert skipped == []
        parts.append(rows)

    result = to_csv_bytes(pd.concat(parts, ignore_index=True))

    assert result == (aed_samples / "aed_zestawienie_przyklad.csv").read_bytes()


@pytest.mark.feat_main_aed
def test_to_csv_bytes_format():
    data = to_csv_bytes(pd.DataFrame([{"a": "x, y", "b": "z"}]))
    assert data == b'a,b\r\n"x, y",z\r\n'
    assert not data.startswith(b"\xef\xbb\xbf")


@pytest.mark.feat_main_aed
def test_legionowo_aliases(aed_samples):
    df = read_sample(aed_samples / "legionowo_2625221.csv", encoding="utf-8-sig")
    result, skipped = build_aggregate_rows(df, SOURCE_MUNICIPALITY, AGGREGATED_AT)
    assert skipped == []
    assert len(result) == 24
    assert result["przetworzenie"].str.split(";").map(lambda codes: "naglowki" in codes).all()
    assert (result["nazwa_lokalizacji"] != "").all()
    assert (result["numer_budynku"] != "").all()
    assert result.loc[0, "nazwa_lokalizacji"] == "Urząd Miasta Legionowo"
    assert result.loc[0, "szerokosc_geograficzna"] == "52.395198"


@pytest.mark.feat_main_aed
def test_krosno_skipped_missing_minimum(aed_samples):
    df = read_sample(aed_samples / "krosno_54632.csv")
    result, skipped = build_aggregate_rows(df, SOURCE_MUNICIPALITY, AGGREGATED_AT)
    assert result.empty
    assert list(result.columns) == MAIN_AED_COLUMNS
    assert skipped == [{"wiersz": 0, "powod": "brak kolumn: miejscowosc"}]


@pytest.mark.feat_main_aed
def test_przemysl_skipped_missing_coordinates(aed_samples):
    df = read_sample(aed_samples / "przemysl_62095.csv", sep=";", encoding="utf-8-sig")
    assert "geometry" in df.columns
    result, skipped = build_aggregate_rows(df, SOURCE_MUNICIPALITY, AGGREGATED_AT)
    assert result.empty
    assert skipped == [{"wiersz": 0, "powod": "brak kolumn: szerokosc_geograficzna, dlugosc_geograficzna"}]


@pytest.mark.feat_main_aed
def test_marki_single_column_skipped(aed_samples):
    df = read_sample(aed_samples / "marki_68353.csv")
    assert len(df.columns) == 1
    result, skipped = build_aggregate_rows(df, SOURCE_MUNICIPALITY, AGGREGATED_AT)
    assert result.empty
    assert len(skipped) == 1
    assert skipped[0]["powod"].startswith("brak kolumn")


@pytest.mark.feat_main_aed
def test_exact_name_wins_over_alias():
    df = pd.DataFrame([{"nazwa": "Alias", "nazwa_lokalizacji": "Oryginał"}])
    renamed, changed = rename_with_aliases(df)
    assert list(renamed.columns) == ["nazwa_lokalizacji"]
    assert renamed.loc[0, "nazwa_lokalizacji"] == "Oryginał"
    assert changed == set()


@pytest.mark.feat_main_aed
def test_first_alias_from_left_wins():
    df = pd.DataFrame([{"lat": "52.1", "latitude": "52.2"}])
    renamed, changed = rename_with_aliases(df)
    assert list(renamed.columns) == ["szerokosc_geograficzna"]
    assert renamed.loc[0, "szerokosc_geograficzna"] == "52.1"
    assert changed == {"lat"}


@pytest.mark.feat_main_aed
@pytest.mark.parametrize(
    ("file_name", "shape", "first_column"),
    [
        ("legionowo_2625221.csv", (24, 11), "nazwa"),
        ("krosno_54632.csv", (21, 6), "Długość geograficzna"),
        ("przemysl_62095.csv", (21, 17), "id"),
        ("marki_68353.csv", (8, 1), "Długość geograficzna,Szerokość geograficzna, Nazwa, Lokalizacja, Adres, Numer Id"),
    ],
)
def test_read_tabular_bytes_real_csv(aed_samples, file_name, shape, first_column):
    df = read_tabular_bytes((aed_samples / file_name).read_bytes(), "csv")
    assert df.shape == shape
    assert df.columns[0] == first_column


@pytest.mark.feat_main_aed
def test_read_tabular_bytes_keeps_literal_values(aed_samples):
    df = read_tabular_bytes((aed_samples / "legionowo_2625221.csv").read_bytes(), "csv")
    assert df.loc[0, "kod_simc"] == "0920806"
    assert df.loc[0, "nr_lokalu"] == ""
    assert df.loc[0, "szerokosc_geograficzna"] == "52.395198"


@pytest.mark.feat_main_aed
def test_read_tabular_bytes_cp1250_fallback():
    df = read_tabular_bytes("nazwa;miasto\r\nŁódź;Łódź\r\n".encode("cp1250"), "csv")
    assert df.to_dict("records") == [{"nazwa": "Łódź", "miasto": "Łódź"}]


@pytest.mark.feat_main_aed
def test_read_tabular_bytes_xlsx_as_text():
    buffer = io.BytesIO()
    pd.DataFrame({"kod_simc": ["0920806"], "lat": [52.39], "pusta": [None]}).to_excel(buffer, index=False)
    df = read_tabular_bytes(buffer.getvalue(), "xlsx")
    assert df.to_dict("records") == [{"kod_simc": "0920806", "lat": "52.39", "pusta": ""}]


@pytest.mark.feat_main_aed
def test_read_tabular_bytes_rejects_other_formats():
    with pytest.raises(ValueError):
        read_tabular_bytes(b"{}", "json")


@pytest.mark.feat_main_aed
def test_missing_minimum_columns():
    assert missing_minimum_columns(["nazwa_lokalizacji", "miejscowosc"]) == ["szerokosc_geograficzna", "dlugosc_geograficzna"]
