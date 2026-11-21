from pathlib import Path
from typing import Callable

import factory
import pytest
from django.conf import settings

from mcod.datasets.factories import DatasetFactory
from mcod.datasets.models import Dataset
from mcod.organizations.factories import OrganizationFactory
from mcod.organizations.models import Organization
from mcod.resources.factories import ResourceFactory
from mcod.resources.models import Resource


@pytest.fixture
def aed_dataset() -> Dataset:
    return DatasetFactory.create(customfields={"standard": "AED"}, status="published", license_chosen=Dataset.LICENSE_CC0)


@pytest.fixture
def aed_resource_factory(aed_dataset: Dataset) -> Callable[..., Resource]:
    """Tworzy opublikowany zasób AED po udanej walidacji z pliku z `data/test_samples/aed/`."""

    def create(file_name: str = "legionowo_2625221.csv", **kwargs) -> Resource:
        params = {
            "dataset": aed_dataset,
            "type": "file",
            "format": "csv",
            "status": "published",
            "data_tasks_last_status": "SUCCESS",
            "file_tasks_last_status": "SUCCESS",
            "link_tasks_last_status": "SUCCESS",
            "main_file__file": factory.django.FileField(
                from_path=Path(settings.TEST_SAMPLES_PATH, "aed", file_name),
                filename=file_name,
            ),
        }
        params.update(kwargs)
        return ResourceFactory.create(**params)

    return create


@pytest.fixture
def main_aed_owner_organization() -> Organization:
    return OrganizationFactory.create(pk=settings.MAIN_AED_DATASET_OWNER_ORGANIZATION_PK)


@pytest.fixture
def main_aed_dataset(main_aed_owner_organization: Organization) -> Dataset:
    return DatasetFactory.create(
        organization=main_aed_owner_organization,
        title=settings.MAIN_AED_DATASET_DEFAULT_TITLE,
        customfields={"standard": "AED", "zestawienie": "AED-krajowe"},
        license_chosen=Dataset.LICENSE_CC_BY,
        status="published",
    )
