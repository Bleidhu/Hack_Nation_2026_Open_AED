import logging
from pathlib import Path

from django.apps import apps
from django.conf import settings

from mcod.core.tasks import extended_shared_task
from mcod.resources.aed_utils import (
    clean_up_after_main_aed_resource_creation,
    create_main_aed_file,
    create_main_aed_resource_with_dataset,
    replace_old_main_aed_resource,
)
from mcod.resources.dga_utils import (
    FailedValidationException,
    PendingValidationException,
    check_all_resource_validations_status,
)

logger = logging.getLogger("mcod")


@extended_shared_task(
    max_retries=5,
    atomic=False,
    retry_countdown=20,
    retry_on_errors=(PendingValidationException,),
    bind=True,
    name="mcod.resources.tasks.create_main_aed_resource_task",
)
def create_main_aed_resource_task(self) -> None:
    """
    Buduje zasób zbiorczy Wykazu AED (wzór: `create_main_dga_resource_task`):

    1. CSV z zasobów zbiorów oznaczonych `standard = AED`.
    2. Nowy zasób z plikiem (i zbiór zbiorczy, jeśli go brak).
    3. Sprawdzenie walidacji zasobu; przy walidacji w toku zadanie jest ponawiane.
    4. Usunięcie poprzedniego zasobu zbiorczego.

    Przy błędzie albo walidacji niezakończonej w ostatniej próbie utworzone obiekty są usuwane.
    Przy `AED_AGGREGATION_ENABLED = False` zadanie nic nie robi.
    """
    if not settings.AED_AGGREGATION_ENABLED:
        logger.info("Wykaz AED wyłączony (AED_AGGREGATION_ENABLED=False).")
        return

    logger.info("Starting main AED resource creation.")
    Resource = apps.get_model("resources", "Resource")

    try:
        logger.info("Step 1/4: Creating Main AED csv file.")
        file_path: Path = create_main_aed_file()

        logger.info("Step 2/4: Creating Main AED resource with files.")
        new_resource_pk, _ = create_main_aed_resource_with_dataset(file_path=file_path)
        new_resource = Resource.objects.get(pk=new_resource_pk)

        logger.info("Step 3/4: Checking resource validations.")
        check_all_resource_validations_status(new_resource)

        logger.info("Step 4/4: Deleting previous Main AED resource.")
        replace_old_main_aed_resource(new_resource)

        logger.info("Main AED Resource successfully created.")
        clean_up_after_main_aed_resource_creation(exception_occurred=False)

    except PendingValidationException:
        if self.request.retries == self.max_retries:
            logger.info("Cleaning after main AED resource creation task due to still pending resource validation(s).")
            clean_up_after_main_aed_resource_creation(exception_occurred=True)
        raise

    except FailedValidationException:
        clean_up_after_main_aed_resource_creation(exception_occurred=True)
        raise

    except Exception as exc:
        logger.error(f"Cleaning after main AED resource creation task due to unexpected error: {exc}")
        clean_up_after_main_aed_resource_creation(exception_occurred=True)
        raise
