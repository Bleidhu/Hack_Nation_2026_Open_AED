from io import StringIO
from unittest.mock import MagicMock, patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from mcod.datasets.models import Dataset
from mcod.organizations.factories import OrganizationFactory
from mcod.resources.models import Resource
from mcod.resources.tests.test_aed_xml import make_xml

REMOTE = "mcod.resources.management.commands.import_aed_xml.request_remote_dga"
URL = "https://dostawca.example.pl/aed.xml"


def response(content: bytes, status_code: int = 200) -> MagicMock:
    return MagicMock(status_code=status_code, content=content)


def run(*args, remote=None):
    out = StringIO()
    with patch(REMOTE, **(remote or {"return_value": response(make_xml({}))})):
        call_command("import_aed_xml", *args, stdout=out, stderr=StringIO())
    return out.getvalue()


@pytest.mark.feat_main_aed
def test_creates_aed_dataset_and_link_resource():
    organization = OrganizationFactory.create()

    output = run(URL, f"--organizacja={organization.pk}")

    dataset = Dataset.objects.get(organization=organization)
    resource = Resource.objects.get(dataset=dataset)
    assert dataset.customfields == {"standard": "AED"}
    assert dataset.license_name == "CC BY 4.0"
    assert resource.link == URL
    assert "rekordów: 6" in run(
        URL, "--dry-run", remote={"return_value": response(make_xml(*[{"id_zrodlowe": str(i)} for i in range(6)]))}
    )
    assert f"Zbiór: {dataset.pk}" in output


@pytest.mark.feat_main_aed
def test_dry_run_saves_nothing():
    run(URL, "--dry-run")

    assert not Dataset.objects.filter(customfields={"standard": "AED"}).exists()


@pytest.mark.feat_main_aed
def test_invalid_xml_creates_nothing():
    organization = OrganizationFactory.create()

    with pytest.raises(CommandError, match="niezgodny"):
        run(URL, f"--organizacja={organization.pk}", remote={"return_value": response(make_xml({}, drop=("miejscowosc",)))})

    assert not Dataset.objects.filter(organization=organization).exists()


@pytest.mark.feat_main_aed
@pytest.mark.parametrize(
    ("args", "remote", "message"),
    [
        (["http://dostawca.example.pl/aed.xml"], None, "https"),
        ([URL], {"return_value": response(b"", 500)}, "kod 500"),
        ([URL], None, "--organizacja"),
        ([URL, "--organizacja=999999999"], None, "Nie ma instytucji"),
    ],
)
def test_command_errors(args, remote, message):
    with pytest.raises(CommandError, match=message):
        run(*args, remote=remote)
