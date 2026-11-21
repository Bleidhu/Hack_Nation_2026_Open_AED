import json
import logging
from mimetypes import guess_all_extensions
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd
import requests
import sentry_sdk
from django.apps import apps

from mcod.resources.aed_aggregation import (
    TABULAR_EXTENSIONS,
    build_aggregate_rows,
    read_tabular_bytes,
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
    from mcod.datasets.models import Dataset
    from mcod.resources.models import Resource

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
