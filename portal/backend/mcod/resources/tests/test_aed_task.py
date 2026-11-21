from io import StringIO
from pathlib import Path
from unittest import mock
from unittest.mock import MagicMock

import pytest
from celery.schedules import crontab
from django.core.management import call_command
from django.test import override_settings

import mcod.resources.tasks as resources_tasks
from mcod.celeryapp import get_beat_schedule
from mcod.resources.dga_utils import FailedValidationException, PendingValidationException
from mcod.resources.tasks import create_main_aed_resource_task

COMMAND_MODULE = "mcod.resources.management.commands.create_main_aed_resource"


@pytest.mark.feat_main_aed
class TestMainAEDResourceCreationTask:

    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        self.resource_mock = MagicMock()
        self.resource_objects_get_mock = MagicMock()
        self.resource_mock.objects = MagicMock(get=self.resource_objects_get_mock)
        with mock.patch("mcod.resources.tasks.aed.apps.get_model", return_value=self.resource_mock), mock.patch(
            "mcod.resources.tasks.aed.create_main_aed_file"
        ) as self.mock_create_file, mock.patch(
            "mcod.resources.tasks.aed.create_main_aed_resource_with_dataset"
        ) as self.mock_create_resource, mock.patch(
            "mcod.resources.tasks.aed.check_all_resource_validations_status"
        ) as self.mock_check_status, mock.patch(
            "mcod.resources.tasks.aed.replace_old_main_aed_resource"
        ) as self.mock_replace, mock.patch(
            "mcod.resources.tasks.aed.clean_up_after_main_aed_resource_creation"
        ) as self.mock_clean_up:
            self.mock_create_file.return_value = "/path/to/wykaz_aed.csv"
            self.mock_create_resource.return_value = (10, 2)
            yield

    def test_main_aed_resource_creation_task(self):
        manager = MagicMock()
        for name in ("mock_create_file", "mock_create_resource", "mock_check_status", "mock_replace", "mock_clean_up"):
            manager.attach_mock(getattr(self, name), name)

        create_main_aed_resource_task()

        new_resource = self.resource_objects_get_mock.return_value
        self.resource_objects_get_mock.assert_called_once_with(pk=10)
        assert manager.mock_calls == [
            mock.call.mock_create_file(),
            mock.call.mock_create_resource(file_path="/path/to/wykaz_aed.csv"),
            mock.call.mock_check_status(new_resource),
            mock.call.mock_replace(new_resource),
            mock.call.mock_clean_up(exception_occurred=False),
        ]

    def test_file_creation_exception(self):
        self.mock_create_file.side_effect = Exception()

        with pytest.raises(Exception):
            create_main_aed_resource_task()

        self.mock_create_resource.assert_not_called()
        self.mock_clean_up.assert_called_once_with(exception_occurred=True)

    def test_resource_creation_exception(self):
        self.mock_create_resource.side_effect = Exception()

        with pytest.raises(Exception):
            create_main_aed_resource_task()

        self.mock_create_resource.assert_called_once_with(file_path="/path/to/wykaz_aed.csv")
        self.mock_replace.assert_not_called()
        self.mock_clean_up.assert_called_once_with(exception_occurred=True)

    @pytest.mark.parametrize("exception", [Exception, PendingValidationException, FailedValidationException])
    def test_validations_exception(self, exception):
        self.mock_check_status.side_effect = exception

        with pytest.raises(exception):
            create_main_aed_resource_task()

        self.mock_check_status.assert_called_once_with(self.resource_objects_get_mock.return_value)
        self.mock_replace.assert_not_called()
        if exception is PendingValidationException:
            self.mock_clean_up.assert_not_called()
        else:
            self.mock_clean_up.assert_called_once_with(exception_occurred=True)

    def test_replace_exception(self):
        self.mock_replace.side_effect = Exception()

        with pytest.raises(Exception):
            create_main_aed_resource_task()

        self.mock_clean_up.assert_called_once_with(exception_occurred=True)

    @override_settings(AED_AGGREGATION_ENABLED=False)
    def test_disabled_does_nothing(self):
        create_main_aed_resource_task()

        for mocked in (self.mock_create_file, self.mock_create_resource, self.mock_check_status, self.mock_replace):
            mocked.assert_not_called()
        self.mock_clean_up.assert_not_called()


@pytest.mark.feat_main_aed
def test_beat_schedule_has_aed_entry_when_enabled():
    schedule = get_beat_schedule(
        enable_monthly_reports=False, enable_create_xml_metadata_report=True, enable_aed_aggregation=True
    )

    entry = schedule["aed_main_resource_creation"]
    assert entry["task"] == "mcod.resources.tasks.create_main_aed_resource_task"
    assert entry["options"] == {"queue": "periodic"}
    assert entry["schedule"] == crontab(minute=15, hour=4)


@pytest.mark.feat_main_aed
def test_beat_schedule_without_aed_entry_when_disabled():
    enabled = get_beat_schedule(enable_monthly_reports=False, enable_create_xml_metadata_report=True, enable_aed_aggregation=True)
    disabled = get_beat_schedule(enable_monthly_reports=False, enable_create_xml_metadata_report=True)

    assert "aed_main_resource_creation" not in disabled
    enabled.pop("aed_main_resource_creation")
    assert enabled == disabled
    assert disabled["dga_main_resource_creation"]["schedule"] == crontab(minute=30, hour=3)


@pytest.mark.feat_main_aed
def test_task_exported():
    assert resources_tasks.create_main_aed_resource_task is create_main_aed_resource_task
    assert "create_main_aed_resource_task" in resources_tasks.__all__
    assert create_main_aed_resource_task.name == "mcod.resources.tasks.create_main_aed_resource_task"


def run_command(*args) -> str:
    out = StringIO()
    call_command("create_main_aed_resource", *args, stdout=out)
    return out.getvalue()


@pytest.fixture
def csv_with_two_rows(tmp_path) -> Path:
    path = tmp_path / "wykaz_aed.csv"
    path.write_bytes('id_aed,nazwa_lokalizacji\r\nPL-AED-1,"Ratusz\r\nparter"\r\nPL-AED-2,Szkoła\r\n'.encode("utf-8"))
    return path


@pytest.mark.feat_main_aed
def test_command_delay():
    with mock.patch(f"{COMMAND_MODULE}.create_main_aed_resource_task") as task:
        output = run_command()

    task.delay.assert_called_once_with()
    assert "Zlecono zadanie" in output


@pytest.mark.feat_main_aed
def test_command_eager(csv_with_two_rows):
    resource = MagicMock(dataset_id=5)
    with mock.patch(f"{COMMAND_MODULE}.create_main_aed_file", return_value=csv_with_two_rows), mock.patch(
        f"{COMMAND_MODULE}.create_main_aed_resource_with_dataset", return_value=(77, None)
    ) as create_resource, mock.patch(f"{COMMAND_MODULE}.Resource.objects.get", return_value=resource) as get, mock.patch(
        f"{COMMAND_MODULE}.clean_up_after_main_aed_resource_creation"
    ) as clean_up:
        output = run_command("--eager")

    create_resource.assert_called_once_with(file_path=csv_with_two_rows)
    get.assert_called_once_with(pk=77)
    clean_up.assert_called_once_with(exception_occurred=False)
    assert "Zbiór: 5\n" in output
    assert "Zasób: 77" in output
    assert "Wiersze: 2" in output


@pytest.mark.feat_main_aed
def test_command_eager_cleans_up_on_error(csv_with_two_rows):
    with mock.patch(f"{COMMAND_MODULE}.create_main_aed_file", return_value=csv_with_two_rows), mock.patch(
        f"{COMMAND_MODULE}.create_main_aed_resource_with_dataset", side_effect=RuntimeError("błąd")
    ), mock.patch(f"{COMMAND_MODULE}.clean_up_after_main_aed_resource_creation") as clean_up:
        with pytest.raises(RuntimeError):
            run_command("--eager")

    clean_up.assert_called_once_with(exception_occurred=True)


@pytest.mark.feat_main_aed
def test_command_dry_run(csv_with_two_rows):
    with mock.patch(f"{COMMAND_MODULE}.create_main_aed_file", return_value=csv_with_two_rows), mock.patch(
        f"{COMMAND_MODULE}.create_main_aed_resource_with_dataset"
    ) as create_resource, mock.patch(f"{COMMAND_MODULE}.caches") as caches:
        output = run_command("--dry-run")

    create_resource.assert_not_called()
    caches.__getitem__.return_value.delete.assert_called_once_with("main_aed_csv_path_to_clean")
    assert f"Plik CSV: {csv_with_two_rows}" in output
    assert "Wiersze: 2" in output
    assert csv_with_two_rows.exists()


@pytest.mark.feat_main_aed
@override_settings(AED_AGGREGATION_ENABLED=False)
def test_command_disabled():
    with mock.patch(f"{COMMAND_MODULE}.create_main_aed_file") as create_file, mock.patch(
        f"{COMMAND_MODULE}.create_main_aed_resource_task"
    ) as task:
        output = run_command("--eager")

    create_file.assert_not_called()
    task.delay.assert_not_called()
    assert "Wykaz AED wyłączony" in output
