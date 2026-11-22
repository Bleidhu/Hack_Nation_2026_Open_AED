"""Źródło XML (link do zewnętrznego serwera) w wykazie AED: wybór zasobów, odczyt, pominięcia i pełny przepływ."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from mcod.datasets.factories import DatasetFactory
from mcod.datasets.models import Dataset
from mcod.resources.aed_utils import (
    AEDSourceReadError,
    create_main_aed_df,
    get_aed_source_df,
    get_aed_source_resources,
    is_aed_xml_resource,
)
from mcod.resources.factories import ResourceFactory
from mcod.resources.models import Resource
from mcod.resources.tests.test_aed_sources import AGGREGATED_AT, LEGIONOWO_ROWS
from mcod.resources.tests.test_aed_xml import make_xml

REMOTE = "mcod.resources.aed_utils.request_remote_dga"


def response(content: bytes, status_code: int = 200) -> MagicMock:
    return MagicMock(status_code=status_code, headers={"Content-Type": "application/xml"}, content=content)


@pytest.fixture
def xml_resource_factory(aed_dataset):
    """Zasób z linkiem do zewnętrznego serwera: portal klasyfikuje go jako `api`, bez pliku i bez statusu zadań plikowych."""

    def create(**kwargs) -> Resource:
        params = {
            "dataset": aed_dataset,
            "type": "api",
            "format": "xml",
            "link": "https://dostawca.example.pl/aed.xml",
            "status": "published",
            "link_tasks_last_status": "SUCCESS",
            "file_tasks_last_status": "",
            "main_file": None,
        }
        params.update(kwargs)
        return ResourceFactory.create(**params)

    return create


@pytest.mark.feat_main_aed
def test_xml_link_resource_is_selected_without_file_status(xml_resource_factory):
    xml = xml_resource_factory()

    assert is_aed_xml_resource(xml)
    assert get_aed_source_resources() == [xml]


@pytest.mark.feat_main_aed
def test_xml_resource_filters(xml_resource_factory):
    xml_resource_factory(link_tasks_last_status="FAILURE")
    xml_resource_factory(status="draft")
    xml_resource_factory(dataset=DatasetFactory.create(status="published", customfields={"inne": "pole"}))
    xml_resource_factory(
        dataset=DatasetFactory.create(
            status="published", customfields={"standard": "AED"}, license_chosen=Dataset.LICENSE_CC_BY_SA
        )
    )

    assert get_aed_source_resources() == []


@pytest.mark.feat_main_aed
def test_xml_is_read_from_link_and_validated_with_xsd(xml_resource_factory):
    resource = xml_resource_factory()

    with patch(REMOTE, return_value=response(make_xml({}, {"id_zrodlowe": "T-2"}))) as remote:
        df = get_aed_source_df(resource)

    remote.assert_called_once_with(resource.link)
    assert len(df) == 2 and df.loc[0, "miejscowosc"] == "Olsztyn"


@pytest.mark.feat_main_aed
@pytest.mark.parametrize(
    ("remote_kwargs", "message"),
    [
        ({"return_value": response(make_xml({}, drop=("typ_dostepu",)))}, "niezgodny z XSD"),
        ({"return_value": response(b"", 404)}, "kod 404"),
        ({"side_effect": requests.exceptions.ConnectionError("brak")}, "nie odpowiada"),
    ],
)
def test_xml_source_errors_become_read_errors(xml_resource_factory, remote_kwargs, message):
    with patch(REMOTE, **remote_kwargs), pytest.raises(AEDSourceReadError, match=message):
        get_aed_source_df(xml_resource_factory())


@pytest.mark.feat_main_aed
def test_aggregation_merges_xml_and_csv_and_skips_invalid_xml(xml_resource_factory, aed_resource_factory):
    csv_resource = aed_resource_factory()
    good = xml_resource_factory()
    bad = xml_resource_factory(link="https://dostawca.example.pl/aed_bledny.xml")
    responses = {
        good.link: response(make_xml({}, {"id_zrodlowe": "T-2"})),
        bad.link: response(make_xml({}, drop=("miejscowosc",))),
    }

    with patch(REMOTE, side_effect=lambda url: responses[url]):
        df, stats = create_main_aed_df([csv_resource, good, bad], AGGREGATED_AT)

    assert stats["zasoby_przyjete"] == 2
    assert [item["resource_id"] for item in stats["zasoby_pominiete"]] == [bad.pk]
    assert "niezgodny z XSD" in stats["zasoby_pominiete"][0]["powod"]
    assert len(df) == LEGIONOWO_ROWS + 2
    assert set(df["id_zasobu_zrodlowego"]) == {str(csv_resource.pk), str(good.pk)}
