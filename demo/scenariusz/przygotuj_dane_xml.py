"""Scenariusz ręczny: zewnętrzny dostawca (opis zbioru XML + CSV, wariant dodatkowy: rekordy w XML) w lokalnym portalu.

Wymaga uruchomionego serwera dostawcy (`python demo/serwer_zewnetrzny.py --https`) i portalu w Dockerze.

    docker cp demo/scenariusz/przygotuj_dane_xml.py mcod-admin:/tmp/
    docker exec mcod-admin python manage.py shell -c "exec(open('/tmp/przygotuj_dane_xml.py').read(), {'__name__': 'x'})"

Co robi (przez ORM, tak jak dostawca w panelu; idempotentnie):

1. Instytucja „Miejski Zakład Przykład” (dostawca zewnętrzny, dane fikcyjne).
2. Wariant „rekordy w XML”: zbiory z `standard = AED` i zasobami z linkiem do `aed.xml` i `aed_bledny.xml`.
3. Nowa wersja pliku „Punkty AED – wzorzec v2” (wzorzec 2.1 z kolumną `numer_seryjny`), tak jak dostawca wgrywa
   nowy plik w panelu (`ResourceFile` z `is_main = True` i walidacja w Celery). Urządzenie CT-01 z tego pliku jest
   tym samym AED co BYD-HALA-A w CSV dostawcy z opisu XML (ten sam producent i numer seryjny), co pokazuje deduplikację.

Sam import opisu zbioru XML (opis → XSD → CSV → md5 → zbiór i zasób) robi komenda portalu, nie ten skrypt:

    docker exec mcod-admin python manage.py import_aed_xml https://host.docker.internal:8099/opis.xml --organizacja <ID>

albo całość z czekaniem na Celery: `python demo/wymus_harvest.py https://host.docker.internal:8099/opis.xml --organizacja <ID>`.
Adres serwera można zmienić zmienną AED_PROVIDER_URL (np. https://host.docker.internal:8098 albo adres z ngroka).
"""
import hashlib
import os

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from mcod.categories.models import Category
from mcod.datasets.models import Dataset
from mcod.organizations.models import Organization
from mcod.resources.models import Resource, ResourceFile
from mcod.resources.tasks import entrypoint_process_resource_file_validation_task
from mcod.users.models import User

BASE = os.environ.get("AED_PROVIDER_URL", "https://host.docker.internal:8099").rstrip("/")
SAMPLES = os.path.join(str(settings.ROOT_DIR), "data", "test_samples", "aed")
admin = User.objects.get(email="admin@mcod.local")
zdrowie = Category.objects.filter(title="Zdrowie").first()


def provider(title, slug, city):
    obj, _ = Organization.objects.get_or_create(
        title=title,
        defaults=dict(
            slug=slug, institution_type="local", city=city, postal_code="10-001", street="Testowa", street_number="1",
            email=f"{slug}@mcod.local", status="published", created_by=admin,
        ),
    )
    return obj


def xml_resource(org, dataset_title, resource_title, url, customfields):
    ds, _ = Dataset.objects.get_or_create(
        title=dataset_title,
        organization=org,
        defaults=dict(
            slug=dataset_title.lower().replace(" ", "-")[:50], notes=dataset_title, category=zdrowie, status="published",
            customfields=customfields, license_chosen=Dataset.LICENSE_CC_BY, update_frequency="daily", created_by=admin,
        ),
    )
    if zdrowie:
        ds.categories.add(zdrowie)
    if Resource.objects.filter(dataset=ds, title=resource_title).exists():
        return None
    res = Resource.objects.create(
        title=resource_title, description=resource_title, dataset=ds, link=url, type="file", status="published",
        has_dynamic_data=False, has_high_value_data=False, has_high_value_data_from_ec_list=False,
        has_research_data=False, created_by=admin,
    )
    print("zasób", res.pk, resource_title, url)
    return res


def new_file_version(resource_title, file_name):
    """Nowa wersja pliku zasobu (jak „Zmień plik” w panelu), tylko gdy treść różni się od obecnej."""
    res = Resource.objects.filter(title=resource_title, dataset__customfields__has_key="standard").order_by("pk").first()
    if res is None:
        print("brak zasobu", resource_title, "(najpierw demo/scenariusz/przygotuj_dane.py)")
        return
    with open(os.path.join(SAMPLES, file_name), "rb") as f:
        content = f.read()
    current = res.files.filter(is_main=True).first()
    if current and current.file and hashlib.md5(current.file.read()).hexdigest() == hashlib.md5(content).hexdigest():
        print("zasób", res.pk, resource_title, "ma już aktualny plik")
        return
    rf, _ = ResourceFile.objects.update_or_create(
        resource=res, is_main=True,
        defaults={"file": SimpleUploadedFile(name=file_name, content=content, content_type="text/csv")},
    )
    entrypoint_process_resource_file_validation_task.apply_async(args=(rf.id,), kwargs={"update_file_archive": True})
    print("zasób", res.pk, resource_title, "nowa wersja pliku", rf.file.name, "(walidacja w Celery)")


dostawca = provider("Miejski Zakład Przykład (dostawca zewnętrzny, dane fikcyjne)", "mz-przyklad", "Olsztyn")
print("instytucja dostawcy", dostawca.pk)
xml_resource(dostawca, "Defibrylatory AED – zewnętrzny serwer XML", "Wykaz AED (XML, link do serwera dostawcy)",
             f"{BASE}/aed.xml", {"standard": "AED"})
xml_resource(dostawca, "Defibrylatory AED – XML niezgodny z XSD", "Wykaz AED (XML z błędami)",
             f"{BASE}/aed_bledny.xml", {"standard": "AED"})
new_file_version("Punkty AED – wzorzec v2", "aed_punkty_przyklad.csv")
print("gotowe; import opisu: manage.py import_aed_xml", f"{BASE}/opis.xml", "--organizacja", dostawca.pk)
