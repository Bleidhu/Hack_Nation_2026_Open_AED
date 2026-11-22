from typing import Dict, List, Tuple

# Stałe dodatku „Zestawienie AED”. Plik importuje wyłącznie `typing`, bo korzysta z niego
# również czysta logika agregacji (`aed_aggregation.py`) uruchamiana poza Django.
#
# Kolejność kolumn jest kontraktem: wzorzec dostawcy v2 (42 kolumny) i zasób zbiorczy (52 kolumny)
# muszą odpowiadać schematom `format_danych/schemat/aed_punkty.tableschema.json`
# i `format_danych/schemat/aed_zestawienie.tableschema.json`.

AED_TEMPLATE_COLUMNS: List[str] = [
    "id_zrodlowe",
    "nazwa_lokalizacji",
    "wojewodztwo",
    "powiat",
    "gmina",
    "kod_terc",
    "miejscowosc",
    "kod_simc",
    "kod_pocztowy",
    "cecha_ulicy",
    "nazwa_ulicy",
    "kod_ulic",
    "numer_budynku",
    "numer_lokalu",
    "adres_uniwersalny",
    "szerokosc_geograficzna",
    "dlugosc_geograficzna",
    "opis_lokalizacji",
    "wewnatrz_budynku",
    "kondygnacja",
    "typ_dostepu",
    "dostepny_24_7",
    "godziny_dostepnosci",
    "zabezpieczenie",
    "instrukcja_dostepu",
    "status_urzadzenia",
    "producent",
    "model",
    "numer_seryjny",
    "elektrody_pediatryczne",
    "data_waznosci_elektrod",
    "data_waznosci_baterii",
    "data_ostatniego_przegladu",
    "poziom_weryfikacji",
    "data_weryfikacji",
    "dysponent_nazwa",
    "dysponent_regon",
    "telefon_kontaktowy",
    "email_kontaktowy",
    "zrodlo_danych",
    "zrodlo_url",
    "data_aktualizacji",
]

AED_COMPUTED_COLUMNS: List[str] = ["wymaga_przegladu", "dysponent_z_wydawcy", "przetworzenie"]

AED_PROVENANCE_COLUMNS: List[str] = [
    "wydawca_zasobu",
    "licencja_zasobu",
    "id_zasobu_zrodlowego",
    "url_zasobu_zrodlowego",
    "data_danych_zasobu",
    "data_agregacji",
]

MAIN_AED_COLUMNS: List[str] = ["id_aed"] + AED_TEMPLATE_COLUMNS + AED_COMPUTED_COLUMNS + AED_PROVENANCE_COLUMNS

# Bez tych kolumn zasób nie trafia do zestawienia, a bez tych wartości nie trafia wiersz.
AED_MINIMUM_COLUMNS: List[str] = ["nazwa_lokalizacji", "miejscowosc", "szerokosc_geograficzna", "dlugosc_geograficzna"]

# Klucz: znormalizowany nagłówek źródła (normalize_header), wartość: kolumna wzorca.
# Tylko aliasy jednoznaczne; „lokalizacja”, „adres” czy „description” celowo pominięte.
AED_HEADER_ALIASES: Dict[str, str] = {
    "nazwa": "nazwa_lokalizacji",
    "name": "nazwa_lokalizacji",
    "nr_budynku": "numer_budynku",
    "numer_domu": "numer_budynku",
    "home_number": "numer_budynku",
    "nr_lokalu": "numer_lokalu",
    "szerokosc": "szerokosc_geograficzna",
    "lat": "szerokosc_geograficzna",
    "latitude": "szerokosc_geograficzna",
    "dlugosc": "dlugosc_geograficzna",
    "lon": "dlugosc_geograficzna",
    "lng": "dlugosc_geograficzna",
    "longitude": "dlugosc_geograficzna",
    "miasto": "miejscowosc",
    "city": "miejscowosc",
    "ulica": "nazwa_ulicy",
    "street": "nazwa_ulicy",
    "kod": "kod_pocztowy",
    "postcode": "kod_pocztowy",
    "telefon": "telefon_kontaktowy",
    "phone": "telefon_kontaktowy",
    "email": "email_kontaktowy",
    "e_mail": "email_kontaktowy",
    "id": "id_zrodlowe",
    "numer_id": "id_zrodlowe",
    "nr_seryjny": "numer_seryjny",
    "serial": "numer_seryjny",
    "serial_number": "numer_seryjny",
    "sn": "numer_seryjny",
}

# Wartości zwracane przez `Dataset.license_name`. ODbL i licencje „share-alike” nie wchodzą do zestawienia.
AED_ALLOWED_LICENSES: Tuple[str, ...] = ("CC0 1.0", "CC BY 4.0")

# Oznaczenie zbiorów przez „Pola niestandardowe” (`Dataset.customfields`) – bez migracji.
AED_CUSTOMFIELD_STANDARD_KEY = "standard"
AED_CUSTOMFIELD_STANDARD_VALUE = "AED"
AED_CUSTOMFIELD_AGGREGATE_KEY = "zestawienie"
AED_CUSTOMFIELD_AGGREGATE_VALUE = "AED-krajowe"

# Kody kolumny `przetworzenie` (art. 15 ust. 1 pkt 2 ustawy); kolejność = kolejność w kolumnie.
PROCESSING_HEADERS = "naglowki"
PROCESSING_AXES = "osie"
PROCESSING_DEFAULTS = "domyslne"
PROCESSING_OPERATOR_FROM_PUBLISHER = "dysponent_z_wydawcy"
PROCESSING_CONTACT_REMOVED = "kontakt_usuniety"
PROCESSING_CODES_ORDER: List[str] = [
    PROCESSING_HEADERS,
    PROCESSING_AXES,
    PROCESSING_DEFAULTS,
    PROCESSING_OPERATOR_FROM_PUBLISHER,
    PROCESSING_CONTACT_REMOVED,
]

# Brak wiedzy nie oznacza „sprawny”.
DEFAULT_STATUS = "nieznany"
DEFAULT_VERIFICATION = "niezweryfikowany"
OSM_SOURCE_VALUE = "openstreetmap"

LAT_RANGE: Tuple[float, float] = (49.0, 54.9)
LON_RANGE: Tuple[float, float] = (14.1, 24.2)

AED_ID_PREFIX = "PL-AED-"
