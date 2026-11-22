import requests
from django.core.management.base import BaseCommand, CommandError

from mcod.categories.models import Category
from mcod.datasets.models import Dataset
from mcod.organizations.models import Organization
from mcod.resources.aed_constants import AED_CUSTOMFIELD_STANDARD_KEY, AED_CUSTOMFIELD_STANDARD_VALUE
from mcod.resources.aed_xml import validate_aed_xml
from mcod.resources.dga_utils import request_remote_dga
from mcod.resources.models import Resource
from mcod.users.models import User


class Command(BaseCommand):
    help = (
        "Zaczytuje zewnętrzne dane AED w XML: pobiera plik z podanego adresu https, sprawdza go schematem XSD "
        "i tworzy zbiór z `standard = AED` oraz zasób z linkiem do zewnętrznego serwera. Dalej działa zwykły potok "
        "portalu, a nocne zadanie Wykazu AED pobiera XML i włącza go do wykazu. --dry-run tylko waliduje."
    )

    def add_arguments(self, parser):
        parser.add_argument("url", help="Adres https pliku XML dostawcy.")
        parser.add_argument("--organizacja", type=int, help="Identyfikator instytucji (dostawcy). Wymagany bez --dry-run.")
        parser.add_argument("--tytul", help="Tytuł zbioru (domyślnie: Defibrylatory AED – <instytucja>).")
        parser.add_argument("--uzytkownik", help="E-mail użytkownika zapisanego jako autor (opcjonalnie).")
        parser.add_argument("--dry-run", action="store_true", help="Tylko pobierz i zwaliduj plik, bez zapisu w bazie.")

    def fetch_valid_xml(self, url):
        if not url.startswith("https://"):
            raise CommandError("Portal przyjmuje tylko adresy https.")
        try:
            response = request_remote_dga(url)
        except requests.exceptions.RequestException as exc:
            raise CommandError(f"Serwer dostawcy nie odpowiada: {exc}")
        if response.status_code != 200:
            raise CommandError(f"Serwer dostawcy zwrócił kod {response.status_code}.")
        report = validate_aed_xml(response.content)
        if not report["valid"]:
            for error in report["errors"]:
                self.stderr.write(f"linia {error['line']}, pole {error['field'] or '-'}: {error['message']}")
            raise CommandError(f"Plik XML jest niezgodny ze schematem XSD ({len(report['errors'])} błędów). Nic nie zapisano.")
        return report

    def handle(self, *args, **options):
        url = options["url"]
        report = self.fetch_valid_xml(url)
        self.stdout.write(f"XML zgodny z XSD, rekordów: {report['records']}.")
        if options["dry_run"]:
            return

        if not options["organizacja"]:
            raise CommandError("Podaj --organizacja (identyfikator instytucji dostawcy).")
        try:
            organization = Organization.objects.get(pk=options["organizacja"])
        except Organization.DoesNotExist:
            raise CommandError(f"Nie ma instytucji o identyfikatorze {options['organizacja']}.")
        user = User.objects.filter(email=options["uzytkownik"]).first() if options["uzytkownik"] else None

        title = options["tytul"] or f"Defibrylatory AED – {organization.title}"
        category = Category.objects.filter(title="Zdrowie").first()
        dataset = Dataset.objects.create(
            title=title,
            notes=f"{title}. Dane zaczytane z zewnętrznego serwera dostawcy w formacie XML (schemat XSD wzorca AED).",
            organization=organization,
            customfields={AED_CUSTOMFIELD_STANDARD_KEY: AED_CUSTOMFIELD_STANDARD_VALUE},
            license_chosen=Dataset.LICENSE_CC_BY,
            update_frequency="daily",
            status="published",
            created_by=user,
        )
        if category:
            dataset.categories.add(category)
        resource = Resource.objects.create(
            title="Wykaz AED (XML, link do serwera dostawcy)",
            description="Plik XML zgodny ze schematem XSD wzorca AED, pobierany z serwera dostawcy.",
            dataset=dataset,
            link=url,
            type="file",
            status="published",
            has_dynamic_data=False,
            has_high_value_data=False,
            has_high_value_data_from_ec_list=False,
            has_research_data=False,
            created_by=user,
        )
        self.stdout.write(f"Zbiór: {dataset.pk}")
        self.stdout.write(f"Zasób: {resource.pk} (link sprawdzi i pobierze potok portalu)")
