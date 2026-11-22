import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
import requests
from django.conf import settings

from mcod.datasets.factories import DatasetFactory
from mcod.datasets.models import Dataset
from mcod.resources.aed_utils import (
    create_main_aed_df,
    get_aed_source_df,
    get_aed_source_resources,
    get_source_meta,
    is_aed_dataset,
    is_main_aed_dataset,
)
from mcod.resources.models import Resource
from mcod.resources.tasks import process_resource_file_data_task

AGGREGATED_AT = "2026-11-22T04:15:00"
LEGIONOWO_ROWS = 24


def legionowo_bytes() -> bytes:
    return Path(settings.TEST_SAMPLES_PATH, "aed", "legionowo_2625221.csv").read_bytes()


def make_resource(pk: int, rows=None, read_error: Exception = None, ckan: bool = False) -> MagicMock:
    resource = MagicMock(spec_set=Resource)
    resource.pk = pk
    resource.is_imported_from_ckan = ckan
    resource.link = f"https://ckan.example.com/{pk}.csv"
    resource.institution.pk = 100 + pk
    resource.institution.title = f"Gmina {pk}"
    resource.dataset.license_name = "CC0 1.0"
    resource.dataset.license_condition_personal_data = None
    resource.frontend_absolute_url = f"https://dane.gov.pl/pl/dataset/1/resource/{pk}"
    resource.data_date = datetime.date(2026, 11, 20)
    if read_error:
        resource.tabular_data.table.read.side_effect = read_error
    else:
        resource.tabular_data.table.read.return_value = rows
    return resource


def remote_response(content_type: str, content: bytes = b"", status_code: int = 200) -> MagicMock:
    return MagicMock(status_code=status_code, headers={"Content-Type": content_type}, content=content)


@pytest.mark.feat_main_aed
@pytest.mark.parametrize(
    ("customfields", "expected"),
    [
        ({"standard": "AED"}, True),
        ({"Standard": "aed 1.1"}, True),
        ({" standard ": " AED "}, True),
        ('{"standard": "AED"}', True),
        ({"standard": "AEDX"}, False),
        ({"standard": "DGA"}, False),
        (None, False),
        ({}, False),
        ("nie-json", False),
    ],
)
def test_is_aed_dataset(customfields, expected):
    assert is_aed_dataset(SimpleNamespace(customfields=customfields)) is expected


@pytest.mark.feat_main_aed
@pytest.mark.parametrize(
    ("customfields", "expected"),
    [
        ({"zestawienie": "AED-krajowe"}, True),
        ({"Zestawienie": "aed-krajowe", "standard": "AED"}, True),
        ({"standard": "AED"}, False),
        (None, False),
    ],
)
def test_is_main_aed_dataset(customfields, expected):
    assert is_main_aed_dataset(SimpleNamespace(customfields=customfields)) is expected


@pytest.mark.feat_main_aed
def test_get_aed_source_resources_filters(aed_resource_factory):
    selected = aed_resource_factory()

    aed_resource_factory(dataset=DatasetFactory.create(status="published", customfields={"inne": "pole"}))
    aed_resource_factory(
        dataset=DatasetFactory.create(status="published", customfields={"standard": "AED", "zestawienie": "AED-krajowe"})
    )
    aed_resource_factory(file_tasks_last_status="FAILURE")
    aed_resource_factory(link_tasks_last_status="FAILURE")
    aed_resource_factory(status="draft")
    aed_resource_factory(
        dataset=DatasetFactory.create(
            status="published", customfields={"standard": "AED"}, license_chosen=Dataset.LICENSE_CC_BY_SA
        )
    )
    aed_resource_factory(format="json")

    assert get_aed_source_resources() == [selected]


@pytest.mark.feat_main_aed
def test_get_aed_source_resources_ignores_portal_data_validation(aed_resource_factory):
    # Plik zgodny ze wzorcem może nie przejść walidacji typów zgadywanych przez portal
    # (np. "5A" w numer_budynku, puste pole w kolumnie uznanej za liczbę); zgodność sprawdza agregacja.
    failed_type_inference = aed_resource_factory("aed_punkty_przyklad.csv", data_tasks_last_status="FAILURE")
    pending = aed_resource_factory(data_tasks_last_status="PENDING")

    assert get_aed_source_resources() == [failed_type_inference, pending]


@pytest.mark.feat_main_aed
def test_get_source_meta_personal_data(aed_resource_factory):
    dataset = DatasetFactory.create(
        status="published",
        customfields={"standard": "AED"},
        license_condition_personal_data="Dane kontaktowe nie są przetwarzane dalej.",
    )
    resource = aed_resource_factory(dataset=dataset)

    meta = get_source_meta(resource)

    assert meta["personal_data"] is True
    assert meta["institution_id"] == dataset.organization.pk
    assert meta["publisher"] == dataset.organization.title
    assert meta["license"] == dataset.license_name
    assert meta["resource_id"] == resource.pk
    assert meta["url"] == resource.frontend_absolute_url
    assert meta["data_date"] == resource.data_date.isoformat()


@pytest.mark.feat_main_aed
def test_create_main_aed_df_with_mocks():
    rows = [
        {
            "nazwa": "Ratusz",
            "miejscowosc": "Legionowo",
            "szerokosc_geograficzna": "52.4",
            "dlugosc_geograficzna": "20.9",
            "kod_simc": "0920806",
        },
        {"nazwa": "Bez współrzędnych", "miejscowosc": "Legionowo", "szerokosc_geograficzna": "", "dlugosc_geograficzna": ""},
    ]
    readable = make_resource(1, rows=rows)
    unreadable = make_resource(2, read_error=ValueError("uszkodzony plik"))
    no_minimum = make_resource(3, rows=[{"nazwa": "X"}])

    df, stats = create_main_aed_df([readable, unreadable, no_minimum], AGGREGATED_AT)

    assert len(df) == 1
    assert df.loc[0, "nazwa_lokalizacji"] == "Ratusz"
    assert df.loc[0, "kod_simc"] == "0920806"
    assert df.loc[0, "wydawca_zasobu"] == "Gmina 1"
    assert df.loc[0, "data_danych_zasobu"] == "2026-11-20"
    assert stats == {
        "zasoby_przyjete": 1,
        "zasoby_pominiete": [
            {"resource_id": 2, "powod": "nie można odczytać danych tabelarycznych: uszkodzony plik"},
            {"resource_id": 3, "powod": "brak kolumn: miejscowosc, szerokosc_geograficzna, dlugosc_geograficzna"},
        ],
        "wiersze": 1,
        "wiersze_pominiete": 1,
        "wiersze_zdeduplikowane": 0,
        "duplikaty": [],
    }


@pytest.mark.feat_main_aed
def test_missing_tabular_data_is_skipped():
    resource = make_resource(1)
    resource.tabular_data = None
    resource.main_file = ""
    _, stats = create_main_aed_df([resource], AGGREGATED_AT)
    assert stats["zasoby_pominiete"] == [{"resource_id": 1, "powod": "zasób nie ma danych tabelarycznych w portalu"}]


@pytest.mark.feat_main_aed
@pytest.mark.parametrize(
    "response",
    [
        remote_response("text/html; charset=utf-8", b"<html></html>"),
        remote_response("text/csv", b"nazwa\r\nX\r\n", status_code=404),
    ],
    ids=["html-page", "not-found"],
)
def test_ckan_html_link_skipped(response):
    resource = make_resource(7, ckan=True)
    with patch("mcod.resources.aed_utils.request_remote_dga", return_value=response):
        df, stats = create_main_aed_df([resource], AGGREGATED_AT)
    assert df.empty
    assert stats["zasoby_pominiete"] == [{"resource_id": 7, "powod": "zasób nie jest plikiem tabelarycznym"}]


@pytest.mark.feat_main_aed
def test_ckan_connection_error_skipped():
    resource = make_resource(7, ckan=True)
    with patch("mcod.resources.aed_utils.request_remote_dga", side_effect=requests.exceptions.ConnectTimeout("timeout")):
        _, stats = create_main_aed_df([resource], AGGREGATED_AT)
    assert stats["zasoby_pominiete"][0]["powod"].startswith("serwer dostawcy nie odpowiada")


@pytest.mark.feat_main_aed
def test_ckan_csv_read_as_text():
    resource = make_resource(7, ckan=True)
    with patch(
        "mcod.resources.aed_utils.request_remote_dga", return_value=remote_response("text/csv; charset=utf-8", legionowo_bytes())
    ):
        df, stats = create_main_aed_df([resource], AGGREGATED_AT)
    assert stats["zasoby_przyjete"] == 1
    assert len(df) == LEGIONOWO_ROWS
    assert df.loc[0, "kod_simc"] == "0920806"


@pytest.mark.elasticsearch
@pytest.mark.feat_main_aed
def test_template_file_read_without_portal_tabular_data(aed_resource_factory):
    # Walidacja danych portalu odrzuca "5A" w numer_budynku, więc portal nie ma danych tabelarycznych;
    # wykaz czyta wtedy plik zasobu wprost, jako tekst.
    resource = aed_resource_factory("aed_punkty_przyklad.csv", data_tasks_last_status="FAILURE")
    assert resource.tabular_data is None

    df = get_aed_source_df(resource)

    assert len(df) == 8
    assert "5A" in df["numer_budynku"].tolist()
    assert df.loc[0, "kod_terc"] == "0461011"


@pytest.mark.elasticsearch
@pytest.mark.feat_main_aed
def test_real_legionowo_csv_read(aed_resource_factory):
    resource = aed_resource_factory("legionowo_2625221.csv")
    process_resource_file_data_task(resource.pk)
    resource.refresh_from_db()

    df = get_aed_source_df(resource)

    assert "nazwa" in df.columns
    assert len(df) == LEGIONOWO_ROWS
    assert df.loc[0, "kod_simc"] == "0920806"
