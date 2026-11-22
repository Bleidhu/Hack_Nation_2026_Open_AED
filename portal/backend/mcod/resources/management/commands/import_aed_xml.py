from django.core.management.base import BaseCommand, CommandError

from mcod.organizations.models import Organization
from mcod.resources.aed_import import (
    AEDImportError,
    import_dataset,
    prepare_import,
    refresh_imported_datasets,
)
from mcod.users.models import User


class Command(BaseCommand):
    help = (
        "Zaczytuje zewnętrzne dane AED: pobiera opis zbioru w XML (kod 200), waliduje go schematem XSD, pobiera CSV "
        "spod linku z opisu, sprawdza sumę md5 i kontroluje kolumny oraz duplikaty. Dopiero potem tworzy zbiór "
        "(standard = AED) i zasób CSV. Przy niezgodności nic nie zapisuje. --dry-run tylko sprawdza, "
        "--odswiez ponawia import wszystkich zbiorów zaczytanych wcześniej z opisu XML (to samo robi co noc "
        "zadanie refresh_aed_opis_task przed budową wykazu)."
    )

    def add_arguments(self, parser):
        parser.add_argument("url", nargs="?", help="Adres https opisu zbioru (XML).")
        parser.add_argument("--organizacja", type=int, help="Identyfikator instytucji dostawcy (wymagany bez --dry-run).")
        parser.add_argument("--uzytkownik", help="E-mail użytkownika zapisanego jako autor (opcjonalnie).")
        parser.add_argument("--dry-run", action="store_true", help="Tylko pobierz i sprawdź, bez zapisu w bazie.")
        parser.add_argument("--odswiez", action="store_true", help="Ponów import wszystkich zbiorów z polem opis_xml.")

    def handle(self, *args, **options):
        if options["odswiez"]:
            return self.refresh_all()
        if not options["url"]:
            raise CommandError("Podaj adres opisu zbioru (XML) albo użyj --odswiez.")
        url = options["url"]
        try:
            prepared = prepare_import(url)
        except AEDImportError as exc:
            raise CommandError(f"Import odrzucony, nic nie zapisano: {exc}")
        self.report(prepared["md5"], prepared["kontrola"])
        if options["dry_run"]:
            return
        if not options["organizacja"]:
            raise CommandError("Podaj --organizacja (identyfikator instytucji dostawcy).")
        try:
            organization = Organization.objects.get(pk=options["organizacja"])
        except Organization.DoesNotExist:
            raise CommandError(f"Nie ma instytucji o identyfikatorze {options['organizacja']}.")
        user = User.objects.filter(email=options["uzytkownik"]).first() if options["uzytkownik"] else None
        result = import_dataset(url, organization, user)
        self.stdout.write(f"Wynik: {result['status']}, zbiór: {result['zbior']}, zasób: {result['zasob']}")

    def report(self, md5, control):
        self.stdout.write("Opis zbioru: zgodny z XSD.")
        self.stdout.write(f"Suma md5 pliku CSV zgodna z opisem: {md5}.")
        self.stdout.write(
            f"CSV: wiersze {control['wiersze']}, do wykazu {control['przyjete']}, pominięte {control['pominiete']}, "
            f"duplikaty w pliku {len(control['duplikaty'])}."
        )

    def refresh_all(self):
        results = refresh_imported_datasets()
        for result in results:
            if result["status"] == "odrzucono":
                self.stderr.write(f"{result['url']}: odrzucono, zbiór {result['zbior']} bez zmian ({result['blad']})")
            else:
                self.stdout.write(f"{result['url']}: {result['status']}, zbiór: {result['zbior']}, zasób: {result['zasob']}")
        if not results:
            self.stdout.write("Brak zbiorów zaczytanych z opisu XML (pole opis_xml).")
