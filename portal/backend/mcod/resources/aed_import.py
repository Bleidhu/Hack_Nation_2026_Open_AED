"""
Import zewnętrznych danych AED do portalu: opis zbioru w XML → walidacja XSD → CSV → zgodność md5 → zbiór i zasób.

Warstwa portalu (ORM) nad czystą logiką z `aed_opis.py`. Zbiór rozpoznajemy po `customfields` (bez migracji):
`standard = AED`, `opis_xml` = adres opisu, `md5` = suma CSV z ostatniego importu. Powtórny import tego samego opisu
nic nie zmienia, gdy md5 jest takie samo; gdy się zmieniło, zasób CSV jest zastępowany nowym.
"""

import datetime
import logging
from typing import Any, Dict, List, Optional

import requests
from django.apps import apps
from django.db import transaction

from mcod.resources.aed_constants import (
    AED_CUSTOMFIELD_STANDARD_KEY,
    AED_CUSTOMFIELD_STANDARD_VALUE,
)
from mcod.resources.aed_opis import AEDCsvInvalid, inspect_csv, md5_hex, parse_opis, verify_md5
from mcod.resources.aed_xml import AEDXmlInvalid
from mcod.resources.dga_utils import request_remote_dga

logger = logging.getLogger("mcod")
CUSTOMFIELD_OPIS = "opis_xml"
CUSTOMFIELD_MD5 = "md5"


class AEDImportError(Exception):
    """Import odrzucony; nic nie zostało zapisane w portalu."""


def fetch_bytes(url: str, what: str) -> bytes:
    """Pobranie pliku od dostawcy: wymagany https i kod 200, brak odpowiedzi to błąd z powodem, a nie wyjątek sieciowy."""
    if not url.startswith("https://"):
        raise AEDImportError(f"{what}: portal przyjmuje tylko adresy https ({url})")
    try:
        response = request_remote_dga(url)
    except requests.exceptions.RequestException as exc:
        raise AEDImportError(f"{what}: serwer dostawcy nie odpowiada ({exc})") from exc
    if response.status_code != 200:
        raise AEDImportError(f"{what}: serwer dostawcy zwrócił kod {response.status_code}")
    return response.content


def prepare_import(opis_url: str, aggregated_at: Optional[str] = None) -> Dict[str, Any]:
    """Kroki bez zapisu: opis, XSD, CSV, md5, kontrola kolumn i duplikatów. Zwraca opis, CSV i raport kontroli."""
    try:
        opis = parse_opis(fetch_bytes(opis_url, "opis zbioru"))
    except AEDXmlInvalid as exc:
        raise AEDImportError(f"opis zbioru niezgodny z XSD: {exc}") from exc
    resource = opis["zasob"]
    csv_content = fetch_bytes(resource["link_csv"], "plik CSV")
    if not verify_md5(csv_content, resource["md5"]):
        raise AEDImportError(f"suma md5 pliku CSV ({md5_hex(csv_content)}) różni się od sumy w opisie ({resource['md5']})")
    source = {
        "institution_id": 0,
        "publisher": opis["dysponent_nazwa"],
        "license": opis["licencja"],
        "resource_id": 0,
        "url": opis_url,
        "data_date": opis["data_aktualizacji"][:10],
        "personal_data": False,
    }
    try:
        report = inspect_csv(csv_content, source, aggregated_at or datetime.datetime.now().replace(microsecond=0).isoformat())
    except AEDCsvInvalid as exc:
        raise AEDImportError(str(exc)) from exc
    return {"opis": opis, "md5": resource["md5"], "kontrola": report}


def _find_dataset(opis_url: str):
    Dataset = apps.get_model("datasets", "Dataset")
    return Dataset.objects.filter(customfields__contains={CUSTOMFIELD_OPIS: opis_url}).first()


def _create_resource(dataset, opis: Dict[str, Any], user):
    Resource = apps.get_model("resources", "Resource")
    zasob = opis["zasob"]
    return Resource.objects.create(
        title=zasob["tytul"],
        description=f"{zasob['tytul']}. Plik CSV zgodny ze wzorcem AED, suma md5 {zasob['md5']} sprawdzona przy imporcie.",
        dataset=dataset,
        link=zasob["link_csv"],
        type="file",
        status="published",
        data_date=datetime.date.fromisoformat(opis["data_aktualizacji"][:10]),
        has_dynamic_data=False,
        has_high_value_data=False,
        has_high_value_data_from_ec_list=False,
        has_research_data=False,
        created_by=user,
    )


def import_dataset(opis_url: str, organization, user=None) -> Dict[str, Any]:
    """Pełny import. Zwraca {"status": utworzono|zaktualizowano|bez_zmian, "zbior", "zasob", "kontrola"}."""
    Dataset = apps.get_model("datasets", "Dataset")
    Category = apps.get_model("categories", "Category")
    prepared = prepare_import(opis_url)
    opis, md5 = prepared["opis"], prepared["md5"]
    customfields = {
        AED_CUSTOMFIELD_STANDARD_KEY: AED_CUSTOMFIELD_STANDARD_VALUE,
        CUSTOMFIELD_OPIS: opis_url,
        CUSTOMFIELD_MD5: md5,
    }
    license_chosen = Dataset.LICENSE_CC0 if opis["licencja"] == "CC0 1.0" else Dataset.LICENSE_CC_BY
    with transaction.atomic():
        dataset = _find_dataset(opis_url)
        if dataset is not None and (dataset.customfields or {}).get(CUSTOMFIELD_MD5) == md5:
            current = dataset.resources.order_by("-pk").values_list("pk", flat=True).first()
            return {"status": "bez_zmian", "zbior": dataset.pk, "zasob": current, "kontrola": prepared["kontrola"]}
        status = "zaktualizowano" if dataset is not None else "utworzono"
        if dataset is None:
            dataset = Dataset.objects.create(
                title=opis["tytul"],
                notes=opis["opis"],
                organization=organization,
                customfields=customfields,
                license_chosen=license_chosen,
                update_frequency=opis["czestotliwosc_aktualizacji"],
                status="published",
                created_by=user,
            )
            category = Category.objects.filter(title="Zdrowie").first()
            if category:
                dataset.categories.add(category)
        else:
            for old in dataset.resources.all():
                old.delete()
            dataset.title, dataset.notes, dataset.license_chosen = opis["tytul"], opis["opis"], license_chosen
            dataset.update_frequency = opis["czestotliwosc_aktualizacji"]
            dataset.customfields = customfields
            dataset.save()
        resource = _create_resource(dataset, opis, user)
    logger.info("Import AED %s: zbiór %s, zasób %s, md5 %s", status, dataset.pk, resource.pk, md5)
    return {"status": status, "zbior": dataset.pk, "zasob": resource.pk, "kontrola": prepared["kontrola"]}


def refresh_imported_datasets() -> List[Dict[str, Any]]:
    """
    Ponowny import wszystkich zbiorów zaczytanych wcześniej z opisu XML (`customfields.opis_xml`): opis, XSD, CSV, md5.
    Ta sama suma md5 nic nie zmienia, nowa zastępuje zasób; odrzucony import zostawia zbiór bez zmian.
    Wspólna logika komendy `import_aed_xml --odswiez` i nocnego zadania `refresh_aed_opis_task`.
    Zwraca listę {"url", "status", "zbior", "zasob"}; przy odrzuceniu status to „odrzucono”, a powód jest w "blad".
    """
    Dataset = apps.get_model("datasets", "Dataset")
    results = []
    for dataset in Dataset.objects.filter(customfields__has_key=CUSTOMFIELD_OPIS).order_by("pk"):
        url = dataset.customfields[CUSTOMFIELD_OPIS]
        try:
            result = import_dataset(url, dataset.organization)
        except AEDImportError as exc:
            logger.warning("Odświeżenie opisu AED %s odrzucone, zbiór %s bez zmian: %s", url, dataset.pk, exc)
            results.append({"url": url, "status": "odrzucono", "zbior": dataset.pk, "zasob": None, "blad": str(exc)})
            continue
        results.append({"url": url, "status": result["status"], "zbior": result["zbior"], "zasob": result["zasob"]})
    return results
