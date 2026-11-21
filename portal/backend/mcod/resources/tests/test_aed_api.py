from typing import Any, Dict

import pytest
from django.test import override_settings
from falcon import HTTP_NOT_FOUND, HTTP_OK
from falcon.testing import TestClient

from mcod.datasets.models import Dataset
from mcod.resources.factories import ResourceFactory


@pytest.mark.feat_main_aed
def test_api_aed_aggregated_ok(client: TestClient, main_aed_dataset: Dataset):
    resource = ResourceFactory.create(dataset=main_aed_dataset, status="published")

    resp = client.simulate_get("/aed-aggregated/")

    assert resp.status == HTTP_OK, resp.json
    assert resp.json == {
        "dataset_id": main_aed_dataset.id,
        "dataset_slug": main_aed_dataset.slug,
        "resource_id": resource.id,
        "resource_slug": resource.slug,
    }


@pytest.mark.feat_main_aed
def test_api_aed_aggregated_returns_newest_resource(client: TestClient, main_aed_dataset: Dataset):
    ResourceFactory.create(dataset=main_aed_dataset, status="published")
    newest = ResourceFactory.create(dataset=main_aed_dataset, status="published")

    resp = client.simulate_get("/aed-aggregated/")

    assert resp.status == HTTP_OK, resp.json
    assert resp.json["resource_id"] == newest.id


@pytest.mark.feat_main_aed
def test_api_aed_aggregated_not_found_without_dataset(client: TestClient):
    resp = client.simulate_get("/aed-aggregated/")

    assert resp.status == HTTP_NOT_FOUND, resp.json


@pytest.mark.feat_main_aed
def test_api_aed_aggregated_not_found_without_resource(client: TestClient, main_aed_dataset: Dataset):
    resp = client.simulate_get("/aed-aggregated/")

    assert resp.status == HTTP_NOT_FOUND, resp.json


@pytest.mark.feat_main_aed
@pytest.mark.parametrize(
    "resource_params, status_code",
    [
        (dict(is_removed=True), HTTP_NOT_FOUND),
        (dict(is_removed=False), HTTP_OK),
        (dict(status="draft"), HTTP_NOT_FOUND),
        (dict(status="published"), HTTP_OK),
    ],
)
def test_api_aed_aggregated_draft_or_removed(
    client: TestClient, main_aed_dataset: Dataset, resource_params: Dict[str, Any], status_code: str
):
    ResourceFactory.create(dataset=main_aed_dataset, **{"status": "published", **resource_params})

    resp = client.simulate_get("/aed-aggregated/")

    assert resp.status == status_code, resp.json


@pytest.mark.feat_main_aed
def test_api_aed_aggregated_disabled(client: TestClient, main_aed_dataset: Dataset):
    ResourceFactory.create(dataset=main_aed_dataset, status="published")

    with override_settings(AED_AGGREGATION_ENABLED=False):
        resp = client.simulate_get("/aed-aggregated/")

    assert resp.status == HTTP_NOT_FOUND, resp.json


@pytest.mark.feat_main_aed
def test_openapi_spec_documents_aed_aggregated(client: TestClient):
    resp = client.simulate_get("/spec", headers={"X-API-VERSION": "1.4"})

    assert resp.status == HTTP_OK
    assert resp.json["paths"]["/aed-aggregated"]["get"]["responses"]["200"]["content"]["application/vnd.api+json"]["schema"] == {
        "$ref": "#/components/schemas/AggregatedAEDInfo"
    }
    assert "AggregatedAEDInfo" in resp.json["components"]["schemas"]
