from pathlib import Path
from typing import Optional
from unittest import mock
from unittest.mock import MagicMock, call

import pandas as pd
import pytest
from django.conf import settings

from mcod.categories.factories import CategoryFactory
from mcod.categories.models import Category
from mcod.datasets.factories import DatasetFactory
from mcod.datasets.models import Dataset
from mcod.lib.model_sanitization import sanitize_html
from mcod.organizations.models import Organization
from mcod.resources.aed_constants import MAIN_AED_COLUMNS
from mcod.resources.aed_utils import (
    build_aed_tabular_schema,
    clean_up_after_main_aed_resource_creation,
    create_main_aed_dataset,
    create_main_aed_file,
    create_main_aed_resource_with_dataset,
    get_main_aed_dataset,
    get_main_aed_resource,
    replace_old_main_aed_resource,
)
from mcod.resources.factories import ResourceFactory
from mcod.resources.models import Resource, ResourceFile
from mcod.resources.tasks import (
    process_resource_file_data_task,
    process_resource_res_file_task,
    update_resource_has_table_has_map_task,
)


@pytest.fixture
def small_main_aed_csv(tmp_path: Path) -> Path:
    """Nagłówek i dwa wiersze z referencyjnego przykładu zasobu zbiorczego."""
    lines = Path(settings.TEST_SAMPLES_PATH, "aed", "aed_zestawienie_przyklad.csv").read_bytes().split(b"\r\n")
    path = tmp_path / "wykaz_aed.csv"
    path.write_bytes(b"\r\n".join(lines[:3]) + b"\r\n")
    return path


@pytest.mark.feat_main_aed
def test_build_aed_tabular_schema():
    schema = build_aed_tabular_schema(MAIN_AED_COLUMNS)

    assert len(schema["fields"]) == 51
    assert all(field["type"] == "string" for field in schema["fields"])
    assert schema["missingValues"] == []
    for geo_type, column in (("b", "szerokosc_geograficzna"), ("l", "dlugosc_geograficzna"), ("label", "nazwa_lokalizacji")):
        index = MAIN_AED_COLUMNS.index(column)
        assert schema["geo"][geo_type] == {"col_name": column, "col_index": index}
        assert schema["fields"][index]["geo"] == geo_type
    assert sum("geo" in field for field in schema["fields"]) == 3


@pytest.mark.feat_main_aed
def test_create_main_aed_dataset(main_aed_owner_organization: Organization):
    if not Category.objects.filter(title="Zdrowie").exists():
        CategoryFactory.create(title="Zdrowie")

    dataset = Dataset.objects.get(pk=create_main_aed_dataset())

    assert dataset.title == settings.MAIN_AED_DATASET_DEFAULT_TITLE
    assert dataset.notes == sanitize_html(settings.MAIN_AED_DATASET_DEFAULT_DESC)
    assert dataset.organization == main_aed_owner_organization
    assert dataset.customfields == {"standard": "AED", "zestawienie": "AED-krajowe"}
    assert dataset.license_name == "CC BY 4.0"
    assert dataset.status == "published"
    assert dataset.update_frequency == "daily"
    assert dataset.update_notification_recipient_email == settings.MAIN_AED_DATASET_UPDATE_NOTIFICATION_EMAIL
    assert {category.title for category in dataset.categories.all()} == {"Zdrowie"}
    assert sorted(tag.name for tag in dataset.tags.all()) == sorted(settings.MAIN_AED_DATASET_TAGS_NAMES)
    assert get_main_aed_dataset() == dataset


@pytest.mark.feat_main_aed
def test_create_main_aed_dataset_without_category(main_aed_owner_organization: Organization, settings):
    settings.MAIN_AED_DATASET_CATEGORIES_TITLES = ["Kategoria spoza bazy AED"]

    with mock.patch("mcod.resources.aed_utils.logger") as logger:
        dataset = Dataset.objects.get(pk=create_main_aed_dataset())

    assert dataset.categories.count() == 0
    logger.warning.assert_called_once_with("No category with title Kategoria spoza bazy AED found.")


@pytest.mark.feat_main_aed
def test_get_main_aed_dataset_and_resource(main_aed_dataset: Dataset):
    DatasetFactory.create(organization=main_aed_dataset.organization, status="published", customfields={"standard": "AED"})
    ResourceFactory.create(dataset=main_aed_dataset, status="published")
    newest = ResourceFactory.create(dataset=main_aed_dataset, status="published")
    ResourceFactory.create(dataset=main_aed_dataset, status="draft")

    assert get_main_aed_dataset() == main_aed_dataset
    assert get_main_aed_resource() == newest


@pytest.mark.feat_main_aed
def test_get_main_aed_dataset_none_without_aggregate_marker(main_aed_owner_organization: Organization):
    DatasetFactory.create(organization=main_aed_owner_organization, status="published", customfields={"standard": "AED"})
    assert get_main_aed_dataset() is None
    assert get_main_aed_resource() is None


@pytest.mark.feat_main_aed
def test_create_main_aed_file():
    row = {column: "" for column in MAIN_AED_COLUMNS}
    row.update(id_aed="PL-AED-000000000001", nazwa_lokalizacji="Ratusz, parter")
    main_df = pd.DataFrame([row], columns=MAIN_AED_COLUMNS)
    stats = {"zasoby_przyjete": 1, "zasoby_pominiete": [], "wiersze": 1, "wiersze_pominiete": 0}

    with mock.patch("mcod.resources.aed_utils.get_aed_source_resources", return_value=[]), mock.patch(
        "mcod.resources.aed_utils.create_main_aed_df", return_value=(main_df, stats)
    ) as create_df:
        file_path = create_main_aed_file()

    try:
        content = Path(file_path).read_bytes()
        assert Path(file_path).name.startswith(settings.MAIN_AED_CSV_FILE_NAME_PREFIX)
        assert Path(file_path).suffix == ".csv"
        assert not content.startswith(b"\xef\xbb\xbf")
        header, first_row = content.split(b"\r\n")[:2]
        assert header.decode("utf-8").split(",") == MAIN_AED_COLUMNS
        assert b'"Ratusz, parter"' in first_row
        assert create_df.call_args[0][0] == []
    finally:
        Path(file_path).unlink()


@pytest.mark.feat_main_aed
def test_create_main_aed_resource_with_dataset(main_aed_owner_organization: Organization, small_main_aed_csv: Path):
    resource_pk, dataset_pk = create_main_aed_resource_with_dataset(small_main_aed_csv)

    assert dataset_pk
    resource = Resource.objects.get(pk=resource_pk)
    assert resource.title == settings.MAIN_AED_RESOURCE_DEFAULT_TITLE
    assert resource.description == sanitize_html(settings.MAIN_AED_RESOURCE_DEFAULT_DESC)
    assert resource.dataset.pk == dataset_pk
    assert resource.dataset.institution == main_aed_owner_organization
    assert resource.contains_protected_data is False
    assert resource.status == "published"
    assert set(resource.tabular_data_schema["geo"]) == {"b", "l", "label"}

    resource_files = ResourceFile.objects.filter(resource=resource)
    assert resource_files.count() == 1
    assert resource_files.first().is_main is True


@pytest.mark.feat_main_aed
def test_create_main_aed_resource_reuses_dataset_and_metadata(main_aed_dataset: Dataset, small_main_aed_csv: Path):
    old = ResourceFactory.create(dataset=main_aed_dataset, status="published", title="Wykaz AED (edytowany)")

    resource_pk, dataset_pk = create_main_aed_resource_with_dataset(small_main_aed_csv)

    assert dataset_pk is None
    resource = Resource.objects.get(pk=resource_pk)
    assert resource.dataset == main_aed_dataset
    assert resource.title == old.title
    assert Resource.objects.filter(pk=old.pk, status="published").exists()


@pytest.mark.feat_main_aed
def test_replace_old_main_aed_resource(main_aed_dataset: Dataset):
    old = ResourceFactory.create(dataset=main_aed_dataset, status="published")
    other_dataset_resource = ResourceFactory.create(status="published")
    new = ResourceFactory.create(dataset=main_aed_dataset, status="published")

    replace_old_main_aed_resource(new)

    old.refresh_from_db()
    new.refresh_from_db()
    other_dataset_resource.refresh_from_db()
    assert old.is_removed is True
    assert new.is_removed is False
    assert other_dataset_resource.is_removed is False
    assert get_main_aed_resource() == new


@pytest.mark.feat_main_aed
@pytest.mark.parametrize(
    ("resource_id", "dataset_id", "exc_occurred", "file_exists"),
    [
        (123, 456, False, True),
        (123, 456, True, True),
        (123, None, False, True),
        (123, None, True, True),
        (None, None, True, True),
        (None, None, False, True),
        (None, None, False, False),
    ],
)
@mock.patch("mcod.resources.aed_utils.sentry_sdk.api.capture_exception")
@mock.patch("mcod.resources.aed_utils.os.remove")
@mock.patch("mcod.resources.aed_utils.caches")
def test_clean_up_after_main_aed_resource_creation(
    mock_caches: MagicMock,
    mock_os_remove: MagicMock,
    mock_sentry: MagicMock,
    resource_id: Optional[int],
    dataset_id: Optional[int],
    exc_occurred: bool,
    file_exists: bool,
):
    dataset: Optional[Dataset] = DatasetFactory.create(pk=dataset_id) if dataset_id else None
    if resource_id:
        ResourceFactory.create(pk=resource_id, dataset=dataset) if dataset else ResourceFactory.create(pk=resource_id)

    values = {"main_aed_to_clean": (resource_id, dataset_id), "main_aed_csv_path_to_clean": "/tmp/wykaz_aed.csv"}
    mock_cache = MagicMock()
    mock_cache.get.side_effect = lambda key, default=None: values.get(key, default)
    mock_caches.__getitem__.return_value = mock_cache

    with mock.patch("mcod.resources.aed_utils.os.path.exists", return_value=file_exists):
        clean_up_after_main_aed_resource_creation(exc_occurred)

    if exc_occurred:
        assert Resource.raw.filter(pk=resource_id).exists() is False
        assert Dataset.raw.filter(pk=dataset_id).exists() is False
    else:
        assert bool(resource_id) is Resource.raw.filter(pk=resource_id).exists()
        assert bool(dataset_id) is Dataset.raw.filter(pk=dataset_id).exists()

    if file_exists:
        mock_os_remove.assert_called_once_with("/tmp/wykaz_aed.csv")
    else:
        mock_os_remove.assert_not_called()
    mock_cache.delete.assert_has_calls([call("main_aed_to_clean"), call("main_aed_csv_path_to_clean")])
    mock_sentry.assert_not_called()


@pytest.mark.elasticsearch
@pytest.mark.feat_main_aed
def test_main_aed_resource_has_map_after_processing(main_aed_owner_organization: Organization, small_main_aed_csv: Path):
    resource_pk, _ = create_main_aed_resource_with_dataset(small_main_aed_csv)
    resource_file = ResourceFile.objects.get(resource_id=resource_pk, is_main=True)

    process_resource_res_file_task.apply(args=(resource_file.pk,), kwargs={"update_link": False})
    process_resource_file_data_task.apply(args=(resource_pk,))
    update_resource_has_table_has_map_task(resource_pk)

    resource = Resource.objects.get(pk=resource_pk)
    assert set(resource.tabular_data_schema["geo"]) == {"b", "l", "label"}
    assert resource.has_table is True
    assert resource.has_map is True
    rows = resource.tabular_data.table.read(keyed=True, cast=False)
    expected = pd.read_csv(small_main_aed_csv, dtype=str, keep_default_na=False).to_dict("records")
    assert len(rows) == 2
    for column in ("id_aed", "kod_simc", "kod_terc", "szerokosc_geograficzna", "dlugosc_geograficzna"):
        assert rows[0][column] == expected[0][column]
