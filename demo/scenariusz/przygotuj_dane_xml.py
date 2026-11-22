"""Scenariusz ręczny: zewnętrzny dostawca XML w lokalnym portalu (zasób z linkiem do zewnętrznego serwera).

Wymaga uruchomionego serwera dostawcy (`python demo/serwer_zewnetrzny.py`) i portalu w Dockerze.

    docker cp demo/scenariusz/przygotuj_dane_xml.py mcod-admin:/tmp/
    docker exec mcod-admin python -c "import django; django.setup(); exec(open('/tmp/przygotuj_dane_xml.py').read())"

Adres serwera można zmienić zmienną AED_XML_URL (np. adres z ngroka). Skrypt tworzy przez ORM to samo, co dostawca robi
w panelu: zbiór z `standard = AED` i zasób z linkiem. Link sprawdza i pobiera standardowy potok portalu (Celery).
Idempotentny: istniejące obiekty o tych samych tytułach są pomijane.
"""
import os

from mcod.categories.models import Category
from mcod.datasets.models import Dataset
from mcod.organizations.models import Organization
from mcod.resources.models import Resource
from mcod.users.models import User

URL = os.environ.get("AED_XML_URL", "https://host.docker.internal:8099/aed.xml")
BAD_URL = URL.replace("aed.xml", "aed_bledny.xml")
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


dostawca = provider("Miejski Zakład Przykład (dostawca zewnętrzny, dane fikcyjne)", "mz-przyklad", "Olsztyn")
xml_resource(dostawca, "Defibrylatory AED – zewnętrzny serwer XML", "Wykaz AED (XML, link do serwera dostawcy)", URL, {"standard": "AED"})
xml_resource(dostawca, "Defibrylatory AED – XML niezgodny z XSD", "Wykaz AED (XML z błędami)", BAD_URL, {"standard": "AED"})
print("gotowe")
