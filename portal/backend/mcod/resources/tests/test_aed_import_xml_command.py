"""Import zewnętrznych danych AED (opis XML → XSD → CSV → md5 → zbiór i zasób): komenda `import_aed_xml`."""

from io import StringIO
from unittest.mock import MagicMock, patch

import pytest
import requests
from django.core.management import call_command
from django.core.management.base import CommandError

from mcod.datasets.models import Dataset
from mcod.organizations.factories import OrganizationFactory
from mcod.resources.aed_import import refresh_imported_datasets
from mcod.resources.aed_opis import md5_hex
from mcod.resources.models import Resource
from mcod.resources.tests.test_aed_opis import make_csv, make_opis

REMOTE = "mcod.resources.aed_import.request_remote_dga"
OPIS_URL = "https://dostawca.example.pl/opis.xml"
CSV_URL = "https://dostawca.example.pl/aed.csv"
CSV = make_csv({"producent": "Zoll", "numer_seryjny": "ZP-0001"}, {})


def response(content: bytes, status_code: int = 200) -> MagicMock:
    return MagicMock(status_code=status_code, content=content)


def server(files):
    def get(url):
        value = files[url]
        if isinstance(value, Exception):
            raise value
        return value if isinstance(value, MagicMock) else response(value)

    return get


def run(files, *args):
    out = StringIO()
    with patch(REMOTE, side_effect=server(files)):
        call_command("import_aed_xml", *args, stdout=out, stderr=StringIO())
    return out.getvalue()


def good(csv=CSV):
    return {OPIS_URL: make_opis(md5=md5_hex(csv), link=CSV_URL), CSV_URL: csv}


@pytest.mark.feat_main_aed
def test_import_creates_dataset_and_csv_resource_after_md5_check():
    organization = OrganizationFactory.create()

    output = run(good(), OPIS_URL, f"--organizacja={organization.pk}")

    dataset = Dataset.objects.get(organization=organization)
    resource = Resource.objects.get(dataset=dataset)
    assert dataset.customfields == {"standard": "AED", "opis_xml": OPIS_URL, "md5": md5_hex(CSV)}
    assert dataset.license_name == "CC BY 4.0" and dataset.title == "Defibrylatory AED"
    assert resource.link == CSV_URL
    assert "Wynik: utworzono" in output and "zgodna z opisem" in output


@pytest.mark.feat_main_aed
def test_second_import_with_same_md5_changes_nothing_and_new_md5_replaces_resource():
    organization = OrganizationFactory.create()
    run(good(), OPIS_URL, f"--organizacja={organization.pk}")
    first = Resource.objects.get(dataset__organization=organization)

    assert "bez_zmian" in run(good(), OPIS_URL, f"--organizacja={organization.pk}")
    assert list(Resource.objects.filter(dataset__organization=organization)) == [first]

    new_csv = make_csv({"producent": "Zoll", "numer_seryjny": "ZP-0002"})
    assert "zaktualizowano" in run(good(new_csv), OPIS_URL, f"--organizacja={organization.pk}")
    resources = Resource.objects.filter(dataset__organization=organization)
    assert resources.count() == 1 and resources.get().pk != first.pk
    assert Dataset.objects.get(organization=organization).customfields["md5"] == md5_hex(new_csv)


@pytest.mark.feat_main_aed
def test_wrong_md5_rejects_import_and_saves_nothing():
    organization = OrganizationFactory.create()
    files = {OPIS_URL: make_opis(md5="0" * 32, link=CSV_URL), CSV_URL: CSV}

    with pytest.raises(CommandError, match="md5"):
        run(files, OPIS_URL, f"--organizacja={organization.pk}")

    assert not Dataset.objects.filter(organization=organization).exists()


@pytest.mark.feat_main_aed
@pytest.mark.parametrize(
    ("files", "message"),
    [
        ({OPIS_URL: make_opis(title=None)}, "niezgodny z XSD"),
        ({OPIS_URL: response(b"", 503)}, "kod 503"),
        ({OPIS_URL: requests.exceptions.ConnectTimeout("limit czasu")}, "nie odpowiada"),
        ({OPIS_URL: make_opis(md5=md5_hex(CSV), link=CSV_URL), CSV_URL: response(b"", 404)}, "kod 404"),
        ({OPIS_URL: make_opis(md5=md5_hex(b"a\r\n"), link=CSV_URL), CSV_URL: b"a\r\n"}, "brakuje kolumn"),
    ],
)
def test_import_is_rejected_with_reason(files, message):
    organization = OrganizationFactory.create()

    with pytest.raises(CommandError, match=message):
        run(files, OPIS_URL, f"--organizacja={organization.pk}")

    assert not Dataset.objects.filter(organization=organization).exists()


@pytest.mark.feat_main_aed
def test_dry_run_checks_but_saves_nothing_and_reports_duplicates():
    csv = make_csv({"producent": "Zoll", "numer_seryjny": "ZP-0001"}, {"producent": "Zoll", "numer_seryjny": "ZP-0001"})

    output = run(good(csv), OPIS_URL, "--dry-run")

    assert "duplikaty w pliku 1" in output
    assert not Dataset.objects.filter(customfields__contains={"standard": "AED"}).exists()


@pytest.mark.feat_main_aed
@pytest.mark.parametrize(
    ("args", "message"),
    [
        (["http://dostawca.example.pl/opis.xml"], "https"),
        ([OPIS_URL], "--organizacja"),
        ([OPIS_URL, "--organizacja=999999999"], "Nie ma instytucji"),
        ([], "Podaj adres"),
    ],
)
def test_command_errors(args, message):
    with pytest.raises(CommandError, match=message):
        run(good(), *args)


@pytest.mark.feat_main_aed
def test_refresh_reimports_known_datasets():
    organization = OrganizationFactory.create()
    run(good(), OPIS_URL, f"--organizacja={organization.pk}")
    resource = Resource.objects.get(dataset__organization=organization)

    output = run(good(), "--odswiez")

    assert f"{OPIS_URL}: bez_zmian, zbiór: {resource.dataset_id}, zasób: {resource.pk}" in output


@pytest.mark.feat_main_aed
def test_same_md5_reports_current_resource():
    organization = OrganizationFactory.create()
    run(good(), OPIS_URL, f"--organizacja={organization.pk}")
    resource = Resource.objects.get(dataset__organization=organization)

    output = run(good(), OPIS_URL, f"--organizacja={organization.pk}")

    assert f"Wynik: bez_zmian, zbiór: {resource.dataset_id}, zasób: {resource.pk}" in output


@pytest.mark.feat_main_aed
def test_refresh_imported_datasets_replaces_changed_and_keeps_rejected():
    first, second = OrganizationFactory.create(), OrganizationFactory.create()
    other_url, other_csv_url = "https://inny.example.pl/opis.xml", "https://inny.example.pl/aed.csv"
    other = {other_url: make_opis(md5=md5_hex(CSV), link=other_csv_url, title="Inne AED"), other_csv_url: CSV}
    run(good(), OPIS_URL, f"--organizacja={first.pk}")
    run(other, other_url, f"--organizacja={second.pk}")
    kept = Resource.objects.get(dataset__organization=second)
    new_csv = make_csv({"producent": "Zoll", "numer_seryjny": "ZP-0003"})
    files = {**good(new_csv), other_url: make_opis(md5="0" * 32, link=other_csv_url, title="Inne AED"), other_csv_url: CSV}

    with patch(REMOTE, side_effect=server(files)):
        results = refresh_imported_datasets()

    by_url = {r["url"]: r for r in results}
    assert by_url[OPIS_URL]["status"] == "zaktualizowano"
    assert by_url[OPIS_URL]["zasob"] == Resource.objects.get(dataset__organization=first).pk
    assert by_url[other_url]["status"] == "odrzucono" and "md5" in by_url[other_url]["blad"]
    assert list(Resource.objects.filter(dataset__organization=second)) == [kept]
    assert Dataset.objects.get(organization=second).customfields["md5"] == md5_hex(CSV)


@pytest.mark.feat_main_aed
def test_refresh_without_imported_datasets():
    assert "Brak zbiorów" in run({}, "--odswiez")
