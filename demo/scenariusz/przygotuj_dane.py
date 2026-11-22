"""Scenariusz ręczny zadania 10: dane wejściowe Wykazu AED w lokalnym portalu.

Uruchomienie (portal/backend):
    docker cp ../../demo/scenariusz/przygotuj_dane.py mcod-admin:/tmp/
    docker exec mcod-admin python -c "import django; django.setup(); exec(open('/tmp/przygotuj_dane.py').read())"

Tworzy przez ORM to samo, co dostawca robi w panelu: organizacje, zbiory z polami niestandardowymi
i zasoby z plikami. Zapis pliku zasobu uruchamia zwykły potok walidacji portalu (Celery).
Skrypt jest idempotentny: istniejące obiekty o tych samych tytułach są pomijane.
"""
import os

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from mcod.categories.models import Category
from mcod.datasets.models import Dataset
from mcod.organizations.models import Organization
from mcod.resources.models import Resource, ResourceFile
from mcod.users.models import User

admin = User.objects.get(email="admin@mcod.local")
zdrowie = Category.objects.filter(title="Zdrowie").first()
SAMPLES = os.path.join(str(settings.ROOT_DIR), "data", "test_samples", "aed")


def org(title, slug, city, pk=None):
    lookup = {"pk": pk} if pk else {"title": title}
    obj, _ = Organization.objects.get_or_create(
        **lookup,
        defaults=dict(
            title=title, slug=slug, institution_type="state" if pk else "local", city=city, postal_code="00-001",
            street="Testowa", street_number="1", email=f"{slug}@mcod.local", status="published", created_by=admin,
        ),
    )
    return obj


def dataset(organization, title, customfields, license_chosen):
    obj, _ = Dataset.objects.get_or_create(
        title=title,
        organization=organization,
        defaults=dict(
            slug=title.lower().replace(" ", "-")[:50], notes=title, category=zdrowie, status="published",
            customfields=customfields, license_chosen=license_chosen, update_frequency="daily", created_by=admin,
        ),
    )
    if zdrowie:
        obj.categories.add(zdrowie)
    return obj


def resource(ds, title, file_name):
    if Resource.objects.filter(dataset=ds, title=title).exists():
        return
    res = Resource.objects.create(
        title=title, description=title, dataset=ds, type="file", format="csv", status="published",
        has_dynamic_data=False, has_high_value_data=False, has_high_value_data_from_ec_list=False,
        has_research_data=False, created_by=admin,
    )
    with open(os.path.join(SAMPLES, file_name), "rb") as f:
        ResourceFile.objects.create(
            resource=res, is_main=True,
            file=SimpleUploadedFile(name=file_name, content=f.read(), content_type="text/csv"),
        )
    print("zasób", res.pk, title)


org("Ministerstwo Cyfryzacji", "ministerstwo-cyfryzacji", "Warszawa", pk=settings.MAIN_AED_DATASET_OWNER_ORGANIZATION_PK)
legionowo = org("Urząd Miasta Legionowo", "um-legionowo", "Legionowo")
marki = org("Urząd Miasta Marki", "um-marki", "Marki")
krosno = org("Urząd Miasta Krosna", "um-krosno", "Krosno")
przyklad = org("Przykładowy dysponent AED (dane fikcyjne)", "dysponent-przyklad", "Bydgoszcz")

resource(dataset(legionowo, "Defibrylatory AED w Legionowie", {"standard": "AED"}, Dataset.LICENSE_CC0),
         "Lokalizacje AED – Legionowo", "legionowo_2625221.csv")
resource(dataset(przyklad, "Defibrylatory AED dysponenta przykładowego", {"standard": "AED 1.1"}, Dataset.LICENSE_CC_BY),
         "Punkty AED – wzorzec v2", "aed_punkty_przyklad.csv")
resource(dataset(marki, "Defibrylatory AED w Markach", {"standard": "AED"}, Dataset.LICENSE_CC_BY),
         "AED Marki (plik z dane.gov.pl)", "marki_68353.csv")
resource(dataset(krosno, "Defibrylatory AED w Krośnie", {"standard": "AED"}, Dataset.LICENSE_CC0),
         "AED Krosno (plik z dane.gov.pl)", "krosno_54632.csv")
# Zbiór bez oznaczenia standard = AED: poprawny plik, ale nie trafia do wykazu.
resource(dataset(przyklad, "Dane dysponenta bez oznaczenia AED", {}, Dataset.LICENSE_CC_BY),
         "Punkty AED bez deklaracji standardu", "aed_punkty_przyklad.csv")
print("gotowe")
