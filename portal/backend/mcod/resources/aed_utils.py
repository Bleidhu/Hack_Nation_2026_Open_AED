import datetime
import json
import logging
import os
from mimetypes import guess_all_extensions
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Set, Tuple

import pandas as pd
import requests
import sentry_sdk
from cache_memoize import cache_memoize
from django.apps import apps
from django.conf import settings
from django.core.cache import caches
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction

from mcod.resources.aed_aggregation import (
    LAT,
    LON,
    TABULAR_EXTENSIONS,
    build_aggregate_rows,
    read_tabular_bytes,
    to_csv_bytes,
    to_text,
)
from mcod.resources.aed_constants import (
    AED_ALLOWED_LICENSES,
    AED_CUSTOMFIELD_AGGREGATE_KEY,
    AED_CUSTOMFIELD_AGGREGATE_VALUE,
    AED_CUSTOMFIELD_STANDARD_KEY,
    AED_CUSTOMFIELD_STANDARD_VALUE,
    MAIN_AED_COLUMNS,
)
from mcod.resources.dga_utils import request_remote_dga

if TYPE_CHECKING:
    from mcod.categories.models import Category
    from mcod.datasets.models import Dataset
    from mcod.resources.models import Resource
    from mcod.tags.models import Tag

logger = logging.getLogger("mcod")


class AEDSourceReadError(Exception):
    """Zasobu źródłowego AED nie da się odczytać jako tabeli."""


def _customfields(dataset: "Dataset") -> Dict[str, str]:
    """Pola niestandardowe zbioru z kluczami po `strip().lower()`; `customfields` bywa None, słownikiem lub napisem JSON."""
    value = getattr(dataset, "customfields", None)
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            return {}
    if not isinstance(value, dict):
        return {}
    return {str(key).strip().lower(): str(val).strip() for key, val in value.items() if val is not None}


def is_aed_dataset(dataset: "Dataset") -> bool:
    value = _customfields(dataset).get(AED_CUSTOMFIELD_STANDARD_KEY, "").upper()
    return value == AED_CUSTOMFIELD_STANDARD_VALUE or value.startswith(AED_CUSTOMFIELD_STANDARD_VALUE + " ")


def is_main_aed_dataset(dataset: "Dataset") -> bool:
    value = _customfields(dataset).get(AED_CUSTOMFIELD_AGGREGATE_KEY, "")
    return value.lower() == AED_CUSTOMFIELD_AGGREGATE_VALUE.lower()


def get_aed_source_resources() -> List["Resource"]:
    """
    Zasoby źródłowe wykazu AED: opublikowane, po udanej walidacji portalu, ze zbiorów oznaczonych
    `standard = AED` (poza zbiorem zbiorczym), z licencją CC0 lub CC BY 4.0 i w formacie tabelarycznym.
    """
    Resource = apps.get_model("resources", "Resource")
    candidates = (
        Resource.objects.filter(
            status="published",
            dataset__status="published",
            data_tasks_last_status="SUCCESS",
            file_tasks_last_status="SUCCESS",
            link_tasks_last_status="SUCCESS",
            dataset__customfields__isnull=False,
        )
        .select_related("dataset__organization")
        .order_by("dataset__organization__title", "pk")
    )
    selected: List["Resource"] = []
    for resource in candidates:
        dataset = resource.dataset
        if not is_aed_dataset(dataset) or is_main_aed_dataset(dataset):
            continue
        reason: Optional[str] = None
        if dataset.license_name not in AED_ALLOWED_LICENSES:
            reason = f"licencja {dataset.license_name} nie pozwala na włączenie do wykazu"
        elif not resource.has_tabular_format():
            reason = f"format {resource.format} nie jest tabelaryczny"
        if reason:
            logger.info("Pomijam zasób %s zbioru AED %s: %s", resource.pk, dataset.pk, reason)
            continue
        selected.append(resource)
    return selected


def get_source_meta(resource: "Resource") -> Dict[str, Any]:
    return {
        "institution_id": resource.institution.pk,
        "publisher": resource.institution.title,
        "license": resource.dataset.license_name,
        "resource_id": resource.pk,
        "url": resource.frontend_absolute_url,
        "data_date": resource.data_date.isoformat() if resource.data_date else "",
        "personal_data": bool(resource.dataset.license_condition_personal_data),
    }


def _remote_tabular_extension(response: requests.models.Response) -> Optional[str]:
    content_type = response.headers.get("Content-Type", "").split(";")[0].strip()
    extensions = [ext.lstrip(".") for ext in guess_all_extensions(content_type)] if content_type else []
    return next((ext for ext in TABULAR_EXTENSIONS if ext in extensions), None)


def _get_ckan_aed_source_df(resource: "Resource") -> pd.DataFrame:
    if not resource.link:
        raise AEDSourceReadError("zasób z CKAN nie ma linku")
    try:
        response = request_remote_dga(resource.link)
    except requests.exceptions.RequestException as exc:
        raise AEDSourceReadError(f"serwer dostawcy nie odpowiada: {exc}") from exc
    extension = _remote_tabular_extension(response) if response.status_code == 200 else None
    if extension is None:
        raise AEDSourceReadError("zasób nie jest plikiem tabelarycznym")
    try:
        return read_tabular_bytes(response.content, extension)
    except Exception as exc:
        raise AEDSourceReadError(f"nie można odczytać pliku {extension}: {exc}") from exc


def get_aed_source_df(resource: "Resource") -> pd.DataFrame:
    """Dane zasobu jako tekst; zasoby z CKAN pobierane spod `resource.link`, pozostałe z danych tabelarycznych portalu."""
    if resource.is_imported_from_ckan:
        return _get_ckan_aed_source_df(resource)
    tabular_data = resource.tabular_data
    if tabular_data is None:
        raise AEDSourceReadError("zasób nie ma danych tabelarycznych w portalu")
    try:
        rows = tabular_data.table.read(keyed=True, cast=False)
    except Exception as exc:
        raise AEDSourceReadError(f"nie można odczytać danych tabelarycznych: {exc}") from exc
    return pd.DataFrame(rows).applymap(to_text)


def create_main_aed_df(resources: Iterable["Resource"], aggregated_at: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Buduje ramkę zasobu zbiorczego AED. Zasób, którego nie da się odczytać lub który nie ma kolumn minimum,
    jest pomijany z powodem w `stats` i nie przerywa agregacji.
    """
    stats: Dict[str, Any] = {"zasoby_przyjete": 0, "zasoby_pominiete": [], "wiersze": 0, "wiersze_pominiete": 0}
    parts: List[pd.DataFrame] = []
    for resource in resources:
        try:
            df = get_aed_source_df(resource)
        except AEDSourceReadError as exc:
            sentry_sdk.api.capture_exception(exc)
            logger.error("Pomijam zasób źródłowy AED %s, bo nie da się go odczytać: %s", resource.pk, exc)
            stats["zasoby_pominiete"].append({"resource_id": resource.pk, "powod": str(exc)})
            continue

        rows, skipped = build_aggregate_rows(df, get_source_meta(resource), aggregated_at)
        resource_skips = [skip for skip in skipped if skip["wiersz"] == 0]
        if resource_skips:
            reason = resource_skips[0]["powod"]
            logger.warning("Pomijam zasób źródłowy AED %s: %s", resource.pk, reason)
            stats["zasoby_pominiete"].append({"resource_id": resource.pk, "powod": reason})
            continue

        for skip in skipped:
            logger.info("Pomijam wiersz %s zasobu AED %s: %s", skip["wiersz"], resource.pk, skip["powod"])
        stats["zasoby_przyjete"] += 1
        stats["wiersze_pominiete"] += len(skipped)
        parts.append(rows)

    main_df = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=MAIN_AED_COLUMNS)
    stats["wiersze"] = len(main_df)
    logger.info(
        "Wykaz AED: przyjęte zasoby %s, pominięte %s, wiersze %s, pominięte wiersze %s.",
        stats["zasoby_przyjete"],
        len(stats["zasoby_pominiete"]),
        stats["wiersze"],
        stats["wiersze_pominiete"],
    )
    return main_df, stats


def get_main_aed_dataset() -> Optional["Dataset"]:
    Dataset = apps.get_model("datasets", "Dataset")
    datasets = Dataset.objects.filter(
        organization_id=settings.MAIN_AED_DATASET_OWNER_ORGANIZATION_PK,
        status="published",
        is_removed=False,
    ).order_by("-pk")
    return next((dataset for dataset in datasets if is_main_aed_dataset(dataset)), None)


def get_main_aed_resource() -> Optional["Resource"]:
    dataset = get_main_aed_dataset()
    if dataset is None:
        return None
    return dataset.resources.filter(status="published", is_removed=False).order_by("-pk").first()


def key_generator_for_create_main_aed_file(*args, **kwargs) -> str:
    return "main_aed_csv_path_to_clean"


def get_or_create_main_aed_path() -> Path:
    directory = Path(settings.MAIN_AED_RESOURCE_CSV_CREATION_ROOT)
    directory.mkdir(parents=True, exist_ok=True)
    today_date = datetime.datetime.now().strftime("%Y%m%d")
    return directory / f"{settings.MAIN_AED_CSV_FILE_NAME_PREFIX} {today_date}.csv"


@cache_memoize(
    timeout=settings.MAIN_AED_RESOURCE_CSV_CREATION_CACHE_TIMEOUT,
    hit_callable=lambda *args, **kwargs: logger.info("Using cache for main AED file path."),
    key_generator_callable=key_generator_for_create_main_aed_file,
)
def create_main_aed_file() -> Path:
    """Zapisuje CSV zasobu zbiorczego AED (51 kolumn, RFC 4180) i zwraca ścieżkę pliku."""
    aggregated_at = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    main_df, stats = create_main_aed_df(get_aed_source_resources(), aggregated_at)
    file_path = get_or_create_main_aed_path()
    file_path.write_bytes(to_csv_bytes(main_df))
    logger.info("Created main AED file %s; stats: %s", file_path, stats)
    return file_path


def build_aed_tabular_schema(columns: List[str]) -> Dict[str, Any]:
    """
    Schemat Table Schema zasobu zbiorczego: wszystkie kolumny tekstowe (wartości literalne) i mapowanie mapy
    w formacie `ResourceMapsAndPlotsWidget`. `missingValues` = [] (zasób bez znaków specjalnych), więc potok
    `process_resource_file_data_task` nie nadpisuje schematu.
    """
    fields: List[Dict[str, Any]] = [{"name": column, "type": "string", "format": "default"} for column in columns]
    geo: Dict[str, Dict[str, Any]] = {}
    for geo_type, column in (("b", LAT), ("l", LON), ("label", "nazwa_lokalizacji")):
        index = columns.index(column)
        fields[index]["geo"] = geo_type
        geo[geo_type] = {"col_name": column, "col_index": index}
    return {"fields": fields, "missingValues": [], "geo": geo}


def get_default_main_aed_dataset_categories() -> List["Category"]:
    Category = apps.get_model("categories", "Category")
    titles: List[str] = settings.MAIN_AED_DATASET_CATEGORIES_TITLES
    found = list(Category.objects.filter(title__in=titles))
    missing: Set[str] = set(titles) - {category.title for category in found}
    for title in missing:
        logger.warning(f"No category with title {title} found.")
    return found


def get_or_create_default_main_aed_dataset_tags() -> List["Tag"]:
    Tag = apps.get_model("tags", "Tag")
    pl_lang = settings.LANGUAGES[0][0]
    tags = []
    for name in settings.MAIN_AED_DATASET_TAGS_NAMES:
        tag, created = Tag.objects.get_or_create(name=name, language=pl_lang)
        if created:
            logger.info(f"Created Tag with name {name}.")
        tags.append(tag)
    return tags


def create_main_aed_dataset() -> int:
    """Tworzy zbiór zbiorczy Wykazu AED rozpoznawany po polach niestandardowych (bez nowego modelu)."""
    Organization = apps.get_model("organizations", "Organization")
    Dataset = apps.get_model("datasets", "Dataset")

    organization_pk: int = settings.MAIN_AED_DATASET_OWNER_ORGANIZATION_PK
    try:
        institution = Organization.objects.get(pk=organization_pk)
    except Organization.DoesNotExist:
        logger.error(f"Can't create main AED dataset. Institution with pk {organization_pk} not found.")
        raise ObjectDoesNotExist("Main AED Owner Institution not found.")

    with transaction.atomic():
        dataset = Dataset.objects.create(
            title=settings.MAIN_AED_DATASET_DEFAULT_TITLE,
            notes=settings.MAIN_AED_DATASET_DEFAULT_DESC,
            organization=institution,
            customfields={
                AED_CUSTOMFIELD_STANDARD_KEY: AED_CUSTOMFIELD_STANDARD_VALUE,
                AED_CUSTOMFIELD_AGGREGATE_KEY: AED_CUSTOMFIELD_AGGREGATE_VALUE,
            },
            license_chosen=Dataset.LICENSE_CC_BY,
            update_notification_recipient_email=settings.MAIN_AED_DATASET_UPDATE_NOTIFICATION_EMAIL,
            has_dynamic_data=False,
            has_high_value_data=False,
            has_high_value_data_from_ec_list=False,
            has_research_data=False,
            update_frequency="daily",
            status="published",
        )
        dataset.categories.set(get_default_main_aed_dataset_categories())
        dataset.tags.set(get_or_create_default_main_aed_dataset_tags())
        dataset.save()

    logger.info(f"Created main AED dataset {dataset.pk}.")
    return dataset.pk


def key_generator_for_create_main_aed_resource(*args, **kwargs) -> str:
    return "main_aed_to_clean"


@cache_memoize(
    timeout=settings.MAIN_AED_RESOURCE_CREATION_CACHE_TIMEOUT,
    hit_callable=lambda *args, **kwargs: logger.info("AED objects get from cache."),
    key_generator_callable=key_generator_for_create_main_aed_resource,
)
def create_main_aed_resource_with_dataset(file_path: Path) -> Tuple[int, Optional[int]]:
    """
    Tworzy nowy zasób zbiorczy AED z plikiem CSV (i zbiór zbiorczy, jeśli go brak). Poprzedni zasób zostaje
    do czasu udanej walidacji nowego (`replace_old_main_aed_resource`).

    Returns:
        int: klucz nowego zasobu.
        Optional[int]: klucz zbioru, jeśli został utworzony.
    """
    Resource = apps.get_model("resources", "Resource")
    ResourceFile = apps.get_model("resources", "ResourceFile")
    Dataset = apps.get_model("datasets", "Dataset")

    old_resource = get_main_aed_resource()
    dataset = get_main_aed_dataset()

    if not os.path.exists(file_path):
        caches["default"].delete(key_generator_for_create_main_aed_file())
        logger.warning("Main AED file %s does not exist anymore. Regenerating it before resource creation.", file_path)
        file_path = create_main_aed_file()

    if not os.path.exists(file_path):
        raise FileNotFoundError(file_path)

    dataset_created = False
    with transaction.atomic():
        if dataset is None:
            dataset = Dataset.objects.get(pk=create_main_aed_dataset())
            dataset_created = True

        resource = Resource.objects.create(
            title=old_resource.title if old_resource else settings.MAIN_AED_RESOURCE_DEFAULT_TITLE,
            description=old_resource.description if old_resource else settings.MAIN_AED_RESOURCE_DEFAULT_DESC,
            dataset=dataset,
            has_dynamic_data=False,
            has_high_value_data=False,
            has_high_value_data_from_ec_list=False,
            has_research_data=False,
            status="published",
            data_date=datetime.date.today(),
            tabular_data_schema=build_aed_tabular_schema(MAIN_AED_COLUMNS),
        )
        logger.debug(f"Created Main AED resource {resource.pk}")

        with open(file_path, "rb") as file:
            django_file = SimpleUploadedFile(name=os.path.basename(file.name), content=file.read(), content_type="text/csv")
        # post_save pliku uruchamia walidację zasobu
        resource_file = ResourceFile.objects.create(resource=resource, is_main=True, file=django_file)
        logger.debug(f"Created Main AED resource file {resource_file.pk}")

    return resource.pk, dataset.pk if dataset_created else None


def replace_old_main_aed_resource(new_resource: "Resource") -> None:
    """Usuwa pozostałe opublikowane zasoby zbioru zbiorczego, tak żeby aktualny był tylko `new_resource`."""
    Resource = apps.get_model("resources", "Resource")
    with transaction.atomic():
        old_resources = Resource.objects.filter(dataset_id=new_resource.dataset_id, status="published").exclude(
            pk=new_resource.pk
        )
        for old_resource in old_resources:
            old_resource.delete()
            logger.info(f"Previous Main AED Resource {old_resource.pk} deleted.")


def clean_up_after_main_aed_resource_creation(exception_occurred: bool) -> None:
    """
    Po błędzie usuwa zasób i zbiór utworzone przez zadanie; zawsze usuwa tymczasowy plik CSV
    i zwalnia klucze cache.
    """
    logger.info("Starting clean up process after main AED Resource creation.")

    cache = caches["default"]
    clean_objects_key = key_generator_for_create_main_aed_resource()
    clean_file_path_key = key_generator_for_create_main_aed_file()

    resource_created, dataset_created = cache.get(clean_objects_key, (None, None))
    file_path: Optional[str] = cache.get(clean_file_path_key, None)

    try:
        if exception_occurred and resource_created:
            Resource = apps.get_model("resources", "Resource")
            Resource.raw.filter(pk=resource_created).delete()

        if exception_occurred and dataset_created:
            Dataset = apps.get_model("datasets", "Dataset")
            Dataset.raw.filter(pk=dataset_created).delete()

        cache.delete(clean_objects_key)

    except Exception as exc:
        logger.error(f"Clean up failed. Reason: {exc}")
        sentry_sdk.api.capture_exception(exc)

    try:
        if file_path:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"File {file_path} has been deleted successfully.")
            else:
                logger.warning(f"Main AED temp file {file_path} was already missing during cleanup.")

    except Exception as e:
        logger.error(f"An error occurred while deleting the file {file_path}: {e}")
    finally:
        cache.delete(clean_file_path_key)

    logger.info("Clean up completed.")
