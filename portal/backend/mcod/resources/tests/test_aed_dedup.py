"""Czyste testy (bez bazy) deduplikacji Wykazu AED: numer seryjny, marka, lokalizacja."""

import pandas as pd
import pytest

from mcod.resources.aed_constants import MAIN_AED_COLUMNS
from mcod.resources.aed_dedup import deduplicate_rows, distance_m, normalize_serial

LAT, LON = 53.1500, 18.0100
ONE_METER_LAT = 1 / 111000.0


def row(aed_id, resource=1, **kwargs):
    base = {column: "" for column in MAIN_AED_COLUMNS}
    base.update(
        id_aed=aed_id,
        id_zasobu_zrodlowego=str(resource),
        nazwa_lokalizacji="Hala A",
        szerokosc_geograficzna=str(LAT),
        dlugosc_geograficzna=str(LON),
        data_aktualizacji="2026-11-01T10:00:00",
    )
    base.update(kwargs)
    return base


def run(*rows):
    result, duplicates = deduplicate_rows(pd.DataFrame(list(rows), columns=MAIN_AED_COLUMNS))
    return list(result["id_aed"]), duplicates


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("FRX-2026-0001", "frx20260001"),
        (" frx 2026 0001 ", "frx20260001"),
        ("Brak", ""),
        ("-", ""),
        ("abc", ""),
        ("0000000", ""),
        (None, ""),
    ],
)
def test_normalize_serial(value, expected):
    assert normalize_serial(value) == expected


def test_distance_is_in_meters():
    assert 95 < distance_m(LAT, LON, LAT + 100 * ONE_METER_LAT, LON) < 105


def test_same_serial_and_brand_from_two_providers_is_one_device():
    ids, duplicates = run(
        row("A", 1, producent="Philips", numer_seryjny="FRX-2026-0001"),
        row(
            "B", 2, producent="philips", numer_seryjny="frx 2026 0001", szerokosc_geograficzna="52.0", dlugosc_geograficzna="19.0"
        ),
    )
    assert ids == ["A"] and duplicates == [{"zachowany": "A", "pominiety": "B", "powod": "numer_seryjny"}]


def test_same_serial_inside_one_file_is_a_duplicate():
    assert run(row("A", 1, numer_seryjny="SN-0001"), row("B", 1, numer_seryjny="SN-0001"))[0] == ["A"]


def test_same_serial_but_different_brands_are_different_devices():
    ids, _ = run(
        row("A", 1, producent="Philips", numer_seryjny="SN-0001"),
        row("B", 2, producent="Zoll", numer_seryjny="SN-0001"),
    )
    assert ids == ["A", "B"]


def test_placeholder_serials_do_not_merge():
    assert run(
        row("A", 1, numer_seryjny="brak", szerokosc_geograficzna="51.0"),
        row("B", 2, numer_seryjny="brak", szerokosc_geograficzna="52.0"),
    )[0] == ["A", "B"]


def test_same_brand_and_place_without_serial_across_resources_is_merged():
    ids, duplicates = run(
        row("A", 1, producent="Zoll", model="AED Plus"),
        row("B", 2, producent="ZOLL", model="aed plus", szerokosc_geograficzna=str(LAT + 15 * ONE_METER_LAT)),
    )
    assert ids == ["A"] and duplicates[0]["powod"] == "marka_model_i_lokalizacja"


def test_same_brand_and_place_inside_one_resource_is_two_devices():
    assert run(row("A", 1, producent="Zoll"), row("B", 1, producent="Zoll"))[0] == ["A", "B"]


def test_different_serials_at_one_place_are_two_devices():
    ids, _ = run(
        row("A", 1, producent="Zoll", numer_seryjny="SN-0001"),
        row("B", 2, producent="Zoll", numer_seryjny="SN-0002"),
    )
    assert ids == ["A", "B"]


def test_different_floors_are_two_devices():
    assert run(row("A", 1, producent="Zoll", kondygnacja="0"), row("B", 2, producent="Zoll", kondygnacja="1"))[0] == ["A", "B"]


def test_different_models_are_two_devices():
    assert run(row("A", 1, producent="Zoll", model="AED Plus"), row("B", 2, producent="Zoll", model="AED 3"))[0] == ["A", "B"]


def test_far_apart_points_are_not_merged():
    far = str(LAT + 100 * ONE_METER_LAT)
    assert run(row("A", 1, producent="Zoll"), row("B", 2, producent="Zoll", szerokosc_geograficzna=far))[0] == ["A", "B"]


def test_without_brand_same_name_within_ten_meters_is_merged_and_other_name_is_not():
    near = str(LAT + 5 * ONE_METER_LAT)
    ids, duplicates = run(row("A", 1), row("B", 2, szerokosc_geograficzna=near))
    assert ids == ["A"] and duplicates[0]["powod"] == "nazwa_i_lokalizacja"
    assert run(row("A", 1), row("B", 2, nazwa_lokalizacji="Inna hala", szerokosc_geograficzna=near))[0] == ["A", "B"]


def test_better_verified_row_is_kept_and_gaps_are_filled():
    result, duplicates = deduplicate_rows(
        pd.DataFrame(
            [
                row("A", 1, numer_seryjny="SN-0001", poziom_weryfikacji="niezweryfikowany"),
                row(
                    "B",
                    2,
                    numer_seryjny="SN-0001",
                    poziom_weryfikacji="zweryfikowany_w_terenie",
                    producent="Zoll",
                    model="AED Plus",
                ),
            ],
            columns=MAIN_AED_COLUMNS,
        )
    )
    assert list(result["id_aed"]) == ["B"] and duplicates[0]["zachowany"] == "B"


def test_newer_record_wins_and_missing_serial_is_filled_from_duplicate():
    result, _ = deduplicate_rows(
        pd.DataFrame(
            [
                row("A", 1, producent="Zoll", numer_seryjny="SN-0001", data_aktualizacji="2026-01-01T00:00:00"),
                row("B", 2, producent="Zoll", data_aktualizacji="2026-11-01T00:00:00"),
            ],
            columns=MAIN_AED_COLUMNS,
        )
    )
    assert list(result["id_aed"]) == ["B"] and result.loc[0, "numer_seryjny"] == "SN-0001"


def test_order_of_kept_rows_is_preserved_and_empty_input_is_ok():
    ids, _ = run(
        row("A", 1, numer_seryjny="SN-0001", szerokosc_geograficzna="51.0"),
        row("B", 1, numer_seryjny="SN-0002", szerokosc_geograficzna="52.0"),
        row("C", 2, numer_seryjny="SN-0001", szerokosc_geograficzna="53.0"),
    )
    assert ids == ["A", "B"]
    assert deduplicate_rows(pd.DataFrame(columns=MAIN_AED_COLUMNS))[1] == []


def test_three_way_duplicate_collapses_to_one_row():
    ids, duplicates = run(
        row("A", 1, numer_seryjny="SN-0001", szerokosc_geograficzna="51.0"),
        row("B", 2, numer_seryjny="SN-0001", szerokosc_geograficzna="52.0"),
        row("C", 3, numer_seryjny="SN-0001", szerokosc_geograficzna="53.0"),
    )
    assert ids == ["A"] and len(duplicates) == 2
