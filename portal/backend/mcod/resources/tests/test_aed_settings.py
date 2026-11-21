import pytest
from django.conf import settings

from mcod.settings import base as base_settings


@pytest.mark.feat_main_aed
def test_aed_settings_defaults():
    assert isinstance(settings.AED_AGGREGATION_ENABLED, bool)
    assert isinstance(settings.MAIN_AED_DATASET_OWNER_ORGANIZATION_PK, int)
    assert settings.MAIN_AED_RESOURCE_CSV_CREATION_ROOT.endswith("main_aed")
    assert settings.MAIN_AED_DATASET_DEFAULT_TITLE == "Wykaz defibrylatorów AED – wykaz zbiorczy"
    assert settings.MAIN_AED_RESOURCE_DEFAULT_TITLE == "Wykaz defibrylatorów AED"
    assert "standard = AED" in settings.MAIN_AED_DATASET_DEFAULT_DESC
    assert "standard = AED" in settings.MAIN_AED_RESOURCE_DEFAULT_DESC
    assert settings.MAIN_AED_DATASET_CATEGORIES_TITLES == ["Zdrowie"]
    assert "AED" in settings.MAIN_AED_DATASET_TAGS_NAMES
    assert settings.MAIN_AED_DATASET_UPDATE_NOTIFICATION_EMAIL


@pytest.mark.feat_main_aed
def test_aed_aggregation_enabled_by_default():
    assert base_settings.AED_AGGREGATION_ENABLED is True


@pytest.mark.feat_main_aed
def test_aed_task_route_registered():
    # test.py nadpisuje CELERY_TASK_ROUTES pustym słownikiem, więc trasę sprawdzamy w ustawieniach bazowych.
    route = base_settings.CELERY_TASK_ROUTES["mcod.resources.tasks.create_main_aed_resource_task"]
    assert route == {"queue": "resources"}
