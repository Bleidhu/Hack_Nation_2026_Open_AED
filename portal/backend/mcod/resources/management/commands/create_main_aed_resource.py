import csv

from django.conf import settings
from django.core.cache import caches
from django.core.management.base import BaseCommand

from mcod.resources.aed_utils import (
    clean_up_after_main_aed_resource_creation,
    create_main_aed_file,
    create_main_aed_resource_with_dataset,
    key_generator_for_create_main_aed_file,
    replace_old_main_aed_resource,
)
from mcod.resources.models import Resource
from mcod.resources.tasks import create_main_aed_resource_task


def count_csv_rows(file_path) -> int:
    with open(file_path, encoding="utf-8", newline="") as file:
        return max(sum(1 for _ in csv.reader(file)) - 1, 0)


class Command(BaseCommand):
    help = (
        "Buduje zasób zbiorczy Wykazu AED. Bez opcji zleca zadanie Celery; --eager tworzy plik i zasób od razu "
        "i wycofuje poprzedni zasób zbiorczy (walidację dokończą workery portalu); --dry-run tylko zapisuje CSV, "
        "bez obiektów w bazie."
    )

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group()
        group.add_argument("--eager", action="store_true", help="Utwórz plik CSV i zasób zbiorczy synchronicznie.")
        group.add_argument("--dry-run", action="store_true", help="Utwórz tylko plik CSV, bez obiektów w bazie.")

    def handle(self, *args, **options):
        if not settings.AED_AGGREGATION_ENABLED:
            self.stdout.write("Wykaz AED wyłączony (AED_AGGREGATION_ENABLED=False).")
            return

        if options["dry_run"]:
            file_path = create_main_aed_file()
            # Plik zostaje do wglądu; zwolnienie klucza cache, żeby nocne zadanie zbudowało świeży plik.
            caches["default"].delete(key_generator_for_create_main_aed_file())
            self.stdout.write(f"Plik CSV: {file_path}")
            self.stdout.write(f"Wiersze: {count_csv_rows(file_path)}")
            return

        if options["eager"]:
            try:
                file_path = create_main_aed_file()
                rows = count_csv_rows(file_path)
                resource_pk, created_dataset_pk = create_main_aed_resource_with_dataset(file_path=file_path)
            except Exception:
                clean_up_after_main_aed_resource_creation(exception_occurred=True)
                raise
            clean_up_after_main_aed_resource_creation(exception_occurred=False)
            resource = Resource.objects.get(pk=resource_pk)
            replace_old_main_aed_resource(resource)
            self.stdout.write(f"Zbiór: {resource.dataset_id}{' (utworzony)' if created_dataset_pk else ''}")
            self.stdout.write(f"Zasób: {resource_pk}")
            self.stdout.write(f"Wiersze: {rows}")
            return

        create_main_aed_resource_task.delay()
        self.stdout.write("Zlecono zadanie create_main_aed_resource_task.")
