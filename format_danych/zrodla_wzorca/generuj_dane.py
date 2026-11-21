#!/usr/bin/env python3
"""
Szkic danych „Otwórz AED” – generuje wszystkie pliki przykładowe z jednego źródła prawdy.

Tylko biblioteka standardowa (Python 3.9+). Uruchomienie:
    python generuj_dane.py

Wyniki (w tym samym folderze):
  CSV (RFC 4180: UTF-8 bez BOM, przecinek, CRLF)
    aed_wzorzec_przyklad.csv     – 8 przykładowych rekordów wg wzorca (44 kolumny)
    aed_wzorzec_szablon.csv      – pusty szablon dla dysponenta (sam nagłówek)
    slownik_kolumn.csv           – opis kolumn (dokument uzupełniający do zbioru)
    mapowanie_zrodel.csv         – jak pola z istniejących źródeł mapują się na wzorzec
  JSON
    aed_wzorzec_przyklad.json    – odpowiedź API: JSON:API + kontekst JSON-LD (schema.org)
    aed_wzorzec_przyklad.geojson – te same rekordy jako GeoJSON (WGS84)
    schemat_tableschema.json     – schemat maszynowy (Frictionless Table Schema) do walidatora
    slowniki_wartosci.json       – zamknięte słowniki wartości + mapowanie na tagi OSM
    rekord_scalony_przyklad.json – jak wygląda rekord po scaleniu 3 źródeł (referencyjność)
    metadane_zbioru_dcat.json    – metadane zbioru krajowego (DCAT-AP, JSON-LD)

UWAGA: wszystkie rekordy są FIKCYJNE (dane ilustracyjne). Współrzędne są przybliżone,
nazwy dysponentów zmyślone, numery REGON/telefony nie należą do nikogo.
"""
from __future__ import annotations

import csv
import io
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
API = "https://api.otworzaed.example/api/v1"  # adres przykładowy (domena .example – RFC 2606)
DATA_NA_DZIEN = "2026-11-21"

# ---------------------------------------------------------------------------
# 1. WZORZEC: kolumny (kolejność = kolejność w CSV/XLSX)
#    (nazwa, typ, wymagalność W/Z/O, grupa, opis, przykład, reguła jakości dane.gov.pl)
# ---------------------------------------------------------------------------
KOLUMNY = [
    # Identyfikacja
    ("id_aed", "string", "W", "Identyfikacja", "Unikalny, trwały identyfikator AED w zbiorze krajowym (nadaje agregator; dysponent może zostawić puste)", "PL-AED-0000123", ""),
    ("id_zrodlowe", "string", "Z", "Identyfikacja", "Identyfikator urządzenia w systemie dysponenta lub źródła", "BYD-AED-045", ""),
    ("nazwa_lokalizacji", "string", "W", "Identyfikacja", "Nazwa obiektu; etykieta punktu na mapie portalu", "Dworzec – hala główna", ""),
    # Adres i położenie
    ("wojewodztwo", "string", "Z", "Adres i położenie", "Nazwa województwa wg TERYT, małymi literami", "kujawsko-pomorskie", ""),
    ("powiat", "string", "Z", "Adres i położenie", "Nazwa powiatu wg TERYT", "Bydgoszcz", ""),
    ("gmina", "string", "Z", "Adres i położenie", "Nazwa gminy wg TERYT", "Bydgoszcz", ""),
    ("kod_terc", "string", "Z", "Adres i położenie", "Kod TERC gminy (7 znaków, TEKST – zera wiodące)", "0461011", ""),
    ("miejscowosc", "string", "W", "Adres i położenie", "Nazwa miejscowości wg TERYT (SIMC)", "Bydgoszcz", ""),
    ("kod_simc", "string", "Z", "Adres i położenie", "Identyfikator SIMC miejscowości (7 cyfr, TEKST)", "", ""),
    ("kod_pocztowy", "string", "W", "Adres i położenie", "Kod pocztowy PNA w formacie 00-000", "85-001", "Kod PNA"),
    ("cecha_ulicy", "enum", "Z", "Adres i położenie", "Cecha ulicy ze słownika cecha_ulicy", "ul.", "Cecha adresu"),
    ("nazwa_ulicy", "string", "Z", "Adres i położenie", "Nazwa ulicy wg TERYT (ULIC); puste, gdy miejscowość bez ulic", "Gdańska", ""),
    ("kod_ulic", "string", "O", "Adres i położenie", "Identyfikator ULIC (5 cyfr, TEKST)", "", ""),
    ("numer_budynku", "string", "W", "Adres i położenie", "Numer porządkowy budynku (tekst – bywają litery)", "187", ""),
    ("numer_lokalu", "string", "O", "Adres i położenie", "Numer lokalu", "", ""),
    ("adres_uniwersalny", "string", "O", "Adres i położenie", "Adres uniwersalny wg Standardu technicznego 3.2 (kody rozdzielone |)", "", "Adres uniwersalny"),
    ("szerokosc_geograficzna", "number", "W", "Adres i położenie", "Szerokość geograficzna WGS84, kropka dziesiętna, min. 6 miejsc po przecinku, zakres 49.0–54.9", "53.123456", "Pole numeryczne"),
    ("dlugosc_geograficzna", "number", "W", "Adres i położenie", "Długość geograficzna WGS84, kropka dziesiętna, min. 6 miejsc po przecinku, zakres 14.1–24.2", "18.012345", "Pole numeryczne"),
    ("opis_lokalizacji", "string", "W", "Adres i położenie", "Gdzie dokładnie wisi urządzenie (piętro, ściana, punkt orientacyjny)", "Parter, przy wejściu głównym, zielona szafka", ""),
    ("wewnatrz_budynku", "boolean", "Z", "Adres i położenie", "true – wewnątrz budynku; false – na zewnątrz", "true", "Pole wartości logicznych"),
    ("kondygnacja", "integer", "O", "Adres i położenie", "0 = parter, liczby ujemne = poziomy podziemne", "0", "Pole numeryczne"),
    # Dostępność
    ("typ_dostepu", "enum", "W", "Dostępność", "Kto może skorzystać – słownik typ_dostepu", "publiczny", ""),
    ("dostepny_24_7", "boolean", "W", "Dostępność", "true – dostępny całą dobę, 7 dni w tygodniu", "true", "Pole wartości logicznych"),
    ("godziny_dostepnosci", "string", "Z", "Dostępność", "Godziny w składni opening_hours (OSM); puste, gdy 24/7", "Mo-Fr 07:00-21:00; Sa 08:00-14:00", ""),
    ("zabezpieczenie", "enum", "Z", "Dostępność", "Sposób zabezpieczenia urządzenia – słownik zabezpieczenie", "szafka_z_alarmem", ""),
    ("instrukcja_dostepu", "string", "O", "Dostępność", "Jak dostać się do urządzenia. NIE wpisujemy kodów do szafek – podaje je dyspozytor", "Klucz w portierni (całodobowo)", ""),
    # Urządzenie i sprawność
    ("status_urzadzenia", "enum", "W", "Urządzenie i sprawność", "Stan urządzenia – słownik status_urzadzenia", "sprawny", ""),
    ("producent", "string", "O", "Urządzenie i sprawność", "Producent urządzenia", "", ""),
    ("model", "string", "O", "Urządzenie i sprawność", "Model urządzenia", "", ""),
    ("elektrody_pediatryczne", "boolean", "Z", "Urządzenie i sprawność", "Czy dostępne elektrody/tryb pediatryczny", "true", "Pole wartości logicznych"),
    ("data_waznosci_elektrod", "date", "Z", "Urządzenie i sprawność", "Data ważności elektrod (yyyy-mm-dd)", "2027-05-31", ""),
    ("data_waznosci_baterii", "date", "Z", "Urządzenie i sprawność", "Data ważności baterii (yyyy-mm-dd)", "2029-01-31", ""),
    ("data_ostatniego_przegladu", "date", "Z", "Urządzenie i sprawność", "Data ostatniego przeglądu/autotestu potwierdzonego przez opiekuna", "2026-10-02", ""),
    # Dysponent, źródło, referencyjność
    ("dysponent_nazwa", "string", "W", "Dysponent i źródło", "Właściciel lub zarządca urządzenia (instytucja, nie osoba fizyczna)", "Gmina Przykładowa", ""),
    ("dysponent_regon", "string", "Z", "Dysponent i źródło", "REGON dysponenta: 9 lub 14 cyfr, TEKST", "", "REGON"),
    ("telefon_kontaktowy", "string", "Z", "Dysponent i źródło", "Telefon INSTYTUCJONALNY: 9 cyfr lub +48 i 9 cyfr", "", "Numer telefonu"),
    ("email_kontaktowy", "string", "O", "Dysponent i źródło", "E-mail INSTYTUCJONALNY (np. aed@…)", "", ""),
    ("zrodlo_danych", "enum", "W", "Dysponent i źródło", "Pochodzenie rekordu – słownik zrodlo_danych", "dysponent", ""),
    ("zrodlo_url", "string", "Z", "Dysponent i źródło", "Link do zbioru źródłowego (np. zbioru dysponenta na dane.gov.pl)", "", ""),
    ("poziom_weryfikacji", "enum", "W", "Dysponent i źródło", "Jak potwierdzono dane – słownik poziom_weryfikacji", "zweryfikowany_przez_dysponenta", ""),
    ("data_weryfikacji", "date", "W", "Dysponent i źródło", "Kiedy ostatnio potwierdzono obecność i sprawność AED (yyyy-mm-dd)", "2026-11-15", ""),
    ("data_aktualizacji", "datetime", "W", "Dysponent i źródło", "Ostatnia zmiana rekordu (yyyy-mm-ddThh:mm:ss)", "2026-11-21T10:15:00", ""),
    ("zdjecie_url", "string", "O", "Dysponent i źródło", "Zdjęcie miejsca (licencja CC0/CC BY, bez wizerunku osób)", "", ""),
    ("uwagi", "string", "O", "Dysponent i źródło", "Uwagi; bez znaków nowej linii", "", ""),
]
NAZWY = [k[0] for k in KOLUMNY]
assert len(NAZWY) == 44 and len(set(NAZWY)) == 44

# ---------------------------------------------------------------------------
# 2. SŁOWNIKI (zamknięte listy wartości)
# ---------------------------------------------------------------------------
SLOWNIKI = {
    "typ_dostepu": {
        "opis": "Kto może skorzystać z urządzenia",
        "wartosci": [
            {"kod": "publiczny", "etykieta": "Publiczny – każdy, bez ograniczeń", "osm": "access=yes"},
            {"kod": "ograniczony", "etykieta": "Ograniczony – w godzinach obiektu / przez personel lub ochronę", "osm": "access=customers|permit"},
            {"kod": "prywatny", "etykieta": "Prywatny – nie publikujemy w widoku publicznym", "osm": "access=private"},
        ],
    },
    "zabezpieczenie": {
        "opis": "Sposób zabezpieczenia urządzenia",
        "wartosci": [
            {"kod": "brak", "etykieta": "Brak – urządzenie na uchwycie"},
            {"kod": "szafka_otwarta", "etykieta": "Szafka bez zamka"},
            {"kod": "szafka_z_alarmem", "etykieta": "Szafka z alarmem (otwiera każdy)"},
            {"kod": "szafka_na_kod", "etykieta": "Szafka na kod (kod podaje dyspozytor 112)"},
            {"kod": "zamkniety_na_klucz", "etykieta": "Zamknięty na klucz (klucz u personelu)"},
        ],
    },
    "status_urzadzenia": {
        "opis": "Stan urządzenia",
        "wartosci": [
            {"kod": "sprawny", "etykieta": "Sprawny"},
            {"kod": "niesprawny", "etykieta": "Niesprawny (np. błąd autotestu, przeterminowane elektrody)"},
            {"kod": "w_serwisie", "etykieta": "Czasowo zdjęty – w serwisie"},
            {"kod": "wycofany", "etykieta": "Wycofany / zdemontowany"},
            {"kod": "nieznany", "etykieta": "Nieznany – brak potwierdzenia"},
        ],
    },
    "zrodlo_danych": {
        "opis": "Pochodzenie rekordu; kolejność = priorytet referencyjności (1 najwyższy)",
        "wartosci": [
            {"kod": "dysponent", "etykieta": "Dane własne dysponenta (zbiór na dane.gov.pl, plik, formularz)", "priorytet": 1},
            {"kod": "rejestr_publiczny", "etykieta": "Rejestr publiczny / dane JST", "priorytet": 2},
            {"kod": "baza_zewnetrzna", "etykieta": "Baza zewnętrzna o zgodnej licencji", "priorytet": 3},
            {"kod": "openstreetmap", "etykieta": "OpenStreetMap / OpenAEDMap (ODbL) – tylko porównanie, nie trafia do zbioru CC0", "priorytet": 4},
            {"kod": "zgloszenie_obywatelskie", "etykieta": "Zgłoszenie obywatela – wymaga potwierdzenia", "priorytet": 5},
        ],
    },
    "poziom_weryfikacji": {
        "opis": "Jak potwierdzono dane",
        "wartosci": [
            {"kod": "zweryfikowany_w_terenie", "etykieta": "Sprawdzony na miejscu (np. zdjęcie + data)"},
            {"kod": "zweryfikowany_przez_dysponenta", "etykieta": "Potwierdzony przez dysponenta"},
            {"kod": "niezweryfikowany", "etykieta": "Niezweryfikowany"},
        ],
    },
    "cecha_ulicy": {
        "opis": "Cecha ulicy wg TERYT (reguła „Cecha adresu” w dane.gov.pl)",
        "wartosci": [{"kod": c} for c in ["ul.", "al.", "pl.", "skwer", "bulw.", "rondo", "park", "rynek", "szosa", "droga", "os.", "ogród", "wyspa", "wyb.", "inne"]],
    },
}

# ---------------------------------------------------------------------------
# 3. PRZYKŁADOWE REKORDY (FIKCYJNE). Każdy pokazuje inny przypadek z praktyki.
# ---------------------------------------------------------------------------
BAZA = dict(wojewodztwo="kujawsko-pomorskie", powiat="Bydgoszcz", gmina="Bydgoszcz",
            kod_terc="0461011", miejscowosc="Bydgoszcz", kod_simc="", kod_ulic="",
            numer_lokalu="", adres_uniwersalny="", producent="", model="", dysponent_regon="",
            telefon_kontaktowy="", email_kontaktowy="", zrodlo_url="", zdjecie_url="", uwagi="")

REKORDY = [
    dict(BAZA, id_aed="PL-AED-0000001", id_zrodlowe="CT-01", nazwa_lokalizacji="Centrum targowe – hala A, wejście główne",
         kod_pocztowy="85-001", cecha_ulicy="ul.", nazwa_ulicy="Przykładowa", numer_budynku="187",
         szerokosc_geograficzna=53.150120, dlugosc_geograficzna=18.017350,
         opis_lokalizacji="Parter, ściana po lewej od wejścia głównego, zielona szafka z alarmem",
         wewnatrz_budynku=True, kondygnacja=0, typ_dostepu="ograniczony", dostepny_24_7=False,
         godziny_dostepnosci="Mo-Su 07:00-22:00", zabezpieczenie="szafka_z_alarmem",
         instrukcja_dostepu="W godzinach otwarcia – bez ograniczeń; poza nimi ochrona obiektu",
         status_urzadzenia="sprawny", elektrody_pediatryczne=True,
         data_waznosci_elektrod="2027-09-30", data_waznosci_baterii="2029-03-31", data_ostatniego_przegladu="2026-11-02",
         dysponent_nazwa="Centrum Targowe Przykład Sp. z o.o.", telefon_kontaktowy="525550101",
         email_kontaktowy="aed@centrum-przyklad.example", zrodlo_danych="dysponent",
         poziom_weryfikacji="zweryfikowany_przez_dysponenta", data_weryfikacji="2026-11-15",
         data_aktualizacji="2026-11-21T10:15:00", uwagi="PRZYKŁAD – dane fikcyjne"),
    dict(BAZA, id_aed="PL-AED-0000002", id_zrodlowe="UM-RYN-1", nazwa_lokalizacji="Stary Rynek – ratusz, wejście od rynku",
         kod_pocztowy="85-002", cecha_ulicy="rynek", nazwa_ulicy="Stary Rynek", numer_budynku="1",
         szerokosc_geograficzna=53.122640, dlugosc_geograficzna=17.999870,
         opis_lokalizacji="Na zewnątrz, elewacja przy drzwiach głównych, podświetlana szafka",
         wewnatrz_budynku=False, kondygnacja=0, typ_dostepu="publiczny", dostepny_24_7=True,
         godziny_dostepnosci="", zabezpieczenie="szafka_z_alarmem", instrukcja_dostepu="",
         status_urzadzenia="sprawny", elektrody_pediatryczne=True,
         data_waznosci_elektrod="2028-01-31", data_waznosci_baterii="2030-06-30", data_ostatniego_przegladu="2026-11-10",
         dysponent_nazwa="Gmina Przykładowa", dysponent_regon="000000000", telefon_kontaktowy="525550102",
         zrodlo_danych="dysponent", zrodlo_url="https://dane.gov.pl/pl/dataset/PRZYKLAD",
         poziom_weryfikacji="zweryfikowany_w_terenie", data_weryfikacji="2026-11-10",
         data_aktualizacji="2026-11-20T08:00:00", uwagi="PRZYKŁAD – dane fikcyjne; REGON zastępczy"),
    dict(BAZA, id_aed="PL-AED-0000003", id_zrodlowe="SP99-1", nazwa_lokalizacji="Szkoła Podstawowa nr 99 – sala gimnastyczna",
         kod_pocztowy="85-003", cecha_ulicy="ul.", nazwa_ulicy="Szkolna", numer_budynku="5A",
         szerokosc_geograficzna=53.131870, dlugosc_geograficzna=18.034410,
         opis_lokalizacji="Parter, korytarz przy wejściu do sali gimnastycznej",
         wewnatrz_budynku=True, kondygnacja=0, typ_dostepu="ograniczony", dostepny_24_7=False,
         godziny_dostepnosci="Mo-Fr 07:00-17:00", zabezpieczenie="zamkniety_na_klucz",
         instrukcja_dostepu="Klucz w sekretariacie i u woźnego",
         status_urzadzenia="sprawny", elektrody_pediatryczne=True,
         data_waznosci_elektrod="2026-12-31", data_waznosci_baterii="2028-08-31", data_ostatniego_przegladu="2026-09-01",
         dysponent_nazwa="Szkoła Podstawowa nr 99 (przykład)", zrodlo_danych="dysponent",
         poziom_weryfikacji="zweryfikowany_przez_dysponenta", data_weryfikacji="2026-09-01",
         data_aktualizacji="2026-09-01T12:00:00",
         uwagi="PRZYKŁAD – AED zamknięty na klucz: walidator podpowie zmianę na szafkę z alarmem; elektrody wygasają <60 dni"),
    dict(BAZA, id_aed="PL-AED-0000004", id_zrodlowe="OSP-PRZ-1", nazwa_lokalizacji="OSP Przykładowo – remiza",
         miejscowosc="Bydgoszcz", kod_pocztowy="85-004", cecha_ulicy="ul.", nazwa_ulicy="Strażacka", numer_budynku="12",
         szerokosc_geograficzna=53.105530, dlugosc_geograficzna=18.069920,
         opis_lokalizacji="Na zewnątrz, ściana boczna remizy od strony parkingu",
         wewnatrz_budynku=False, kondygnacja=0, typ_dostepu="publiczny", dostepny_24_7=True,
         godziny_dostepnosci="", zabezpieczenie="szafka_na_kod",
         instrukcja_dostepu="Kod do szafki podaje dyspozytor 112",
         status_urzadzenia="w_serwisie", elektrody_pediatryczne=False,
         data_waznosci_elektrod="2027-02-28", data_waznosci_baterii="2027-02-28", data_ostatniego_przegladu="2026-11-18",
         dysponent_nazwa="Ochotnicza Straż Pożarna Przykładowo", zrodlo_danych="dysponent",
         poziom_weryfikacji="zweryfikowany_przez_dysponenta", data_weryfikacji="2026-11-18",
         data_aktualizacji="2026-11-18T19:30:00", uwagi="PRZYKŁAD – czasowo w serwisie do 2026-11-30"),
    dict(BAZA, id_aed="PL-AED-0000005", id_zrodlowe="ZOO-2", nazwa_lokalizacji="Park miejski – pawilon kasowy",
         kod_pocztowy="85-005", cecha_ulicy="al.", nazwa_ulicy="Parkowa", numer_budynku="2",
         szerokosc_geograficzna=53.140210, dlugosc_geograficzna=17.977560,
         opis_lokalizacji="Wewnątrz pawilonu kasowego, za ladą – poprosić kasjera",
         wewnatrz_budynku=True, kondygnacja=0, typ_dostepu="ograniczony", dostepny_24_7=False,
         godziny_dostepnosci="Apr-Oct: Mo-Su 09:00-19:00; Nov-Mar: Mo-Su 09:00-16:00", zabezpieczenie="brak",
         instrukcja_dostepu="Dostępny przez personel kasy",
         status_urzadzenia="niesprawny", elektrody_pediatryczne=False,
         data_waznosci_elektrod="2026-08-31", data_waznosci_baterii="2028-05-31", data_ostatniego_przegladu="2026-04-15",
         dysponent_nazwa="Zarząd Terenów Zieleni (przykład)", zrodlo_danych="rejestr_publiczny",
         poziom_weryfikacji="zweryfikowany_przez_dysponenta", data_weryfikacji="2026-10-20",
         data_aktualizacji="2026-10-20T09:00:00", uwagi="PRZYKŁAD – elektrody przeterminowane: status niesprawny"),
    dict(BAZA, id_aed="PL-AED-0000006", id_zrodlowe="node/0000000001", nazwa_lokalizacji="Pływalnia osiedlowa – recepcja",
         kod_pocztowy="85-006", cecha_ulicy="ul.", nazwa_ulicy="Sportowa", numer_budynku="8",
         szerokosc_geograficzna=53.114470, dlugosc_geograficzna=18.006780,
         opis_lokalizacji="Recepcja, na ścianie za ladą",
         wewnatrz_budynku=True, kondygnacja=0, typ_dostepu="ograniczony", dostepny_24_7=False,
         godziny_dostepnosci="Mo-Fr 06:00-22:00; Sa,Su 08:00-20:00", zabezpieczenie="brak", instrukcja_dostepu="",
         status_urzadzenia="nieznany", elektrody_pediatryczne=False,
         data_waznosci_elektrod="", data_waznosci_baterii="", data_ostatniego_przegladu="",
         dysponent_nazwa="Ośrodek Sportu (przykład)", zrodlo_danych="zgloszenie_obywatelskie",
         poziom_weryfikacji="niezweryfikowany", data_weryfikacji="2026-11-19",
         data_aktualizacji="2026-11-19T21:12:00",
         uwagi="PRZYKŁAD – zgłoszenie obywatelskie; czeka na potwierdzenie dysponenta"),
    dict(BAZA, id_aed="PL-AED-0000007", id_zrodlowe="UNI-B-3", nazwa_lokalizacji="Uczelnia – budynek B, portiernia",
         kod_pocztowy="85-007", cecha_ulicy="ul.", nazwa_ulicy="Akademicka", numer_budynku="3",
         szerokosc_geograficzna=53.127990, dlugosc_geograficzna=18.011230,
         opis_lokalizacji="Parter, portiernia całodobowa, szafka obok okienka",
         wewnatrz_budynku=True, kondygnacja=0, typ_dostepu="publiczny", dostepny_24_7=True,
         godziny_dostepnosci="", zabezpieczenie="szafka_otwarta", instrukcja_dostepu="Budynek otwarty całą dobę – portier na miejscu",
         status_urzadzenia="sprawny", producent="Przykładowy Producent", model="AED-1000",
         elektrody_pediatryczne=True,
         data_waznosci_elektrod="2027-11-30", data_waznosci_baterii="2030-01-31", data_ostatniego_przegladu="2026-11-05",
         dysponent_nazwa="Uczelnia Przykładowa", email_kontaktowy="bhp@uczelnia.example",
         zrodlo_danych="dysponent", poziom_weryfikacji="zweryfikowany_w_terenie", data_weryfikacji="2026-11-05",
         data_aktualizacji="2026-11-05T14:40:00", uwagi="PRZYKŁAD – dane fikcyjne"),
    dict(BAZA, id_aed="PL-AED-0000008", id_zrodlowe="ST-PAL-1", nazwa_lokalizacji="Stacja paliw przy obwodnicy",
         kod_pocztowy="85-008", cecha_ulicy="ul.", nazwa_ulicy="Toruńska", numer_budynku="300",
         szerokosc_geograficzna=53.102340, dlugosc_geograficzna=18.098760,
         opis_lokalizacji="Wewnątrz sklepu stacji, przy kasach",
         wewnatrz_budynku=True, kondygnacja=0, typ_dostepu="publiczny", dostepny_24_7=True,
         godziny_dostepnosci="", zabezpieczenie="szafka_z_alarmem", instrukcja_dostepu="",
         status_urzadzenia="sprawny", elektrody_pediatryczne=False,
         data_waznosci_elektrod="2027-04-30", data_waznosci_baterii="2028-12-31", data_ostatniego_przegladu="2026-10-28",
         dysponent_nazwa="Sieć Stacji Przykład S.A.", zrodlo_danych="baza_zewnetrzna",
         poziom_weryfikacji="zweryfikowany_przez_dysponenta", data_weryfikacji="2026-10-28",
         data_aktualizacji="2026-10-28T07:05:00", uwagi="PRZYKŁAD – dane fikcyjne"),
]


def fmt(v):
    """Formatowanie wartości wg Standardu technicznego (true/false, kropka dziesiętna)."""
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float):
        return f"{v:.6f}"
    return str(v)


def zapisz_csv(nazwa, naglowek, wiersze):
    buf = io.StringIO(newline="")
    w = csv.writer(buf, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL, lineterminator="\r\n")
    w.writerow(naglowek)
    for r in wiersze:
        assert len(r) == len(naglowek), (nazwa, r)
        w.writerow(r)
    (HERE / nazwa).write_bytes(buf.getvalue().encode("utf-8"))  # UTF-8 bez BOM


def zapisz_json(nazwa, obj):
    (HERE / nazwa).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def typ_tableschema(t):
    return {"enum": "string", "datetime": "datetime"}.get(t, t)


def main():
    for r in REKORDY:
        assert set(r) == set(NAZWY), set(NAZWY) ^ set(r)

    # --- CSV ---------------------------------------------------------------
    zapisz_csv("aed_wzorzec_przyklad.csv", NAZWY, [[fmt(r[k]) for k in NAZWY] for r in REKORDY])
    zapisz_csv("aed_wzorzec_szablon.csv", NAZWY, [])
    zapisz_csv(
        "slownik_kolumn.csv",
        ["lp", "kolumna", "typ", "wymagalnosc", "grupa", "opis", "przyklad", "slownik", "regula_jakosci_dane_gov_pl", "typ_kolumny_w_portalu"],
        [[str(i), n, t, w, g, o, p, n if n in SLOWNIKI else "", reg,
          "tekst" if (t in ("string", "enum")) else {"number": "liczba zmiennoprzecinkowa", "integer": "liczba całkowita",
                                                      "boolean": "wartość logiczna", "date": "data", "datetime": "data i czas"}[t]]
         for i, (n, t, w, g, o, p, reg) in enumerate(KOLUMNY, 1)],
    )
    zapisz_csv(
        "mapowanie_zrodel.csv",
        ["kolumna_wzorca", "openaedmap_osm_tag", "danegovpl_krosno_marki", "danegovpl_przemysl", "warszawa_api", "przeksztalcenie"],
        [
            ["nazwa_lokalizacji", "name / description", "Nazwa (w Krośnie zawsze 'Defibrylator') + Lokalizacja", "name", "nazwa obiektu", "gdy nazwa = 'Defibrylator' → użyj pola Lokalizacja"],
            ["szerokosc_geograficzna", "geometry.coordinates[1]", "Szerokość geograficzna (Marki: zamienione z długością!)", "geometry (GeoJSON w komórce)", "wsp. y", "kontrola zakresu 49.0–54.9; zamiana lat/lon, gdy poza zakresem"],
            ["dlugosc_geograficzna", "geometry.coordinates[0]", "Długość geograficzna", "geometry (GeoJSON w komórce)", "wsp. x", "kontrola zakresu 14.1–24.2"],
            ["nazwa_ulicy / numer_budynku / kod_pocztowy / miejscowosc", "addr:street / addr:housenumber / addr:postcode / addr:city", "Adres (jedno pole: 'ul. Jasna, 38-400 Krosno')", "street, home_number, postcode, city", "adres", "parser adresu + dopasowanie do TERYT/PRG"],
            ["opis_lokalizacji", "defibrillator:location", "Lokalizacja", "brak (description = tekst ogólny o AED)", "?", "puste → flaga 'brak_opisu_lokalizacji'"],
            ["wewnatrz_budynku", "indoor=yes/no", "brak", "brak", "?", "yes→true, no→false"],
            ["kondygnacja", "level", "brak", "brak", "?", "liczba całkowita"],
            ["typ_dostepu", "access", "brak", "brak", "?", "yes→publiczny; customers/permit→ograniczony; private→prywatny (odfiltrować)"],
            ["dostepny_24_7 / godziny_dostepnosci", "opening_hours", "brak", "brak", "?", "'24/7' → dostepny_24_7=true; inne → godziny_dostepnosci"],
            ["dysponent_nazwa", "operator", "dostawca zbioru", "dostawca zbioru", "Urząd m.st. Warszawy", "z metadanych zbioru, gdy brak w rekordzie"],
            ["telefon_kontaktowy", "phone / emergency:phone", "brak", "phone", "?", "normalizacja do 9 cyfr; odrzucić numery prywatne"],
            ["data_weryfikacji", "check_date (formaty mieszane)", "brak", "brak", "?", "parsowanie dd.mm.yyyy / yyyy-mm-dd → ISO"],
            ["status_urzadzenia", "brak tagu", "brak", "brak", "brak", "domyślnie 'nieznany'"],
            ["zabezpieczenie / daty ważności", "brak tagu", "brak", "brak", "brak", "puste – do uzupełnienia przez dysponenta"],
            ["zrodlo_danych", "(stała) openstreetmap", "(stała) dysponent", "(stała) dysponent", "(stała) dysponent", "OSM: tylko porównanie (ODbL ≠ CC0)"],
        ],
    )

    # --- JSON: Table Schema (walidator) -----------------------------------
    pola = []
    for n, t, w, g, o, p, reg in KOLUMNY:
        f = {"name": n, "type": typ_tableschema(t), "description": o}
        c = {}
        if w == "W" and n != "id_aed":
            c["required"] = True
        if n in SLOWNIKI:
            c["enum"] = [x["kod"] for x in SLOWNIKI[n]["wartosci"]]
        if n == "szerokosc_geograficzna":
            c.update(minimum=49.0, maximum=54.9)
        if n == "dlugosc_geograficzna":
            c.update(minimum=14.1, maximum=24.2)
        if n == "kod_pocztowy":
            c["pattern"] = r"^\d{2}-\d{3}$"
        if n == "kod_terc":
            c["pattern"] = r"^\d{7}$"
        if n in ("kod_simc",):
            c["pattern"] = r"^\d{7}$"
        if n == "kod_ulic":
            c["pattern"] = r"^\d{5}$"
        if n == "dysponent_regon":
            c["pattern"] = r"^(\d{9}|\d{14})$"
        if n == "telefon_kontaktowy":
            c["pattern"] = r"^(\+48)?\d{9}$"
        if n == "id_aed":
            c.update(pattern=r"^PL-AED-\d{7}$", unique=True)
        if t == "boolean":
            f.update(trueValues=["true"], falseValues=["false"])
        if t == "date":
            f["format"] = "%Y-%m-%d"
        if c:
            f["constraints"] = c
        f["x-wymagalnosc"] = w
        f["x-grupa"] = g
        pola.append(f)
    zapisz_json("schemat_tableschema.json", {
        "$comment": "Frictionless Table Schema dla wzorca AED. Pola x-* to rozszerzenia projektu.",
        "name": "aed-wzorzec",
        "title": "Wzorcowy zakres danych o defibrylatorach AED",
        "version": "0.1.0",
        "fields": pola,
        "primaryKey": "id_aed",
        "missingValues": [""],
        "x-reguly-dodatkowe": [
            "dostepny_24_7=true ⇒ godziny_dostepnosci puste lub '24/7'",
            "dostepny_24_7=false ⇒ godziny_dostepnosci wymagane",
            "typ_dostepu=prywatny ⇒ rekord nie trafia do zbioru publicznego",
            "data_waznosci_elektrod < dzisiaj ⇒ ostrzeżenie + sugestia status_urzadzenia=niesprawny",
            "data_weryfikacji starsza niż 180 dni ⇒ ostrzeżenie 'dane nieświeże'",
            "zabezpieczenie=zamkniety_na_klucz ⇒ podpowiedź: szafka z alarmem lub szafka na kod",
            "punkt musi leżeć w gminie wskazanej przez kod_terc (kontrola PRG)",
            "dwa rekordy < 30 m od siebie ⇒ kandydat na duplikat",
            "pola tekstowe bez znaków nowej linii (Alt+Enter)",
        ],
    })

    zapisz_json("slowniki_wartosci.json", SLOWNIKI)

    # --- JSON: odpowiedź API (JSON:API + JSON-LD) --------------------------
    kontekst = {
        "schema": "https://schema.org/",
        "dcat": "http://www.w3.org/ns/dcat#",
        "dct": "http://purl.org/dc/terms/",
        "aed": "https://otworzaed.example/ns#",
        "nazwa_lokalizacji": "schema:name",
        "opis_lokalizacji": "schema:description",
        "szerokosc_geograficzna": "schema:latitude",
        "dlugosc_geograficzna": "schema:longitude",
        "miejscowosc": "schema:addressLocality",
        "kod_pocztowy": "schema:postalCode",
        "nazwa_ulicy": "schema:streetAddress",
        "kondygnacja": "schema:floorLevel",
        "godziny_dostepnosci": "schema:openingHours",
        "dysponent_nazwa": "schema:provider",
        "telefon_kontaktowy": "schema:telephone",
        "producent": "schema:manufacturer",
        "model": "schema:model",
        "zdjecie_url": {"@id": "schema:image", "@type": "@id"},
        "data_aktualizacji": {"@id": "schema:dateModified", "@type": "schema:DateTime"},
        "data_weryfikacji": {"@id": "aed:dataWeryfikacji", "@type": "schema:Date"},
        "typ_dostepu": "aed:typDostepu",
        "dostepny_24_7": "aed:dostepny247",
        "zabezpieczenie": "aed:zabezpieczenie",
        "status_urzadzenia": "aed:statusUrzadzenia",
        "zrodlo_danych": "aed:zrodloDanych",
        "poziom_weryfikacji": "aed:poziomWeryfikacji",
        "kod_terc": "aed:kodTERC",
    }
    dane = []
    for r in REKORDY:
        attrs = {k: (r[k] if r[k] != "" else None) for k in NAZWY if k != "id_aed"}
        dane.append({
            "type": "defibrylatory",
            "id": r["id_aed"],
            "attributes": attrs,
            "links": {"self": f"{API}/defibrylatory/{r['id_aed']}"},
        })
    zapisz_json("aed_wzorzec_przyklad.json", {
        "jsonapi": {"version": "1.0"},
        "@context": kontekst,
        "meta": {
            "count": len(dane),
            "data_na_dzien": DATA_NA_DZIEN,
            "dateModified": "2026-11-21T10:15:00Z",
            "licencja": "https://creativecommons.org/publicdomain/zero/1.0/",
            "uwaga": "PRZYKŁAD – dane fikcyjne, ilustracja formatu",
        },
        "data": dane,
        "links": {
            "self": f"{API}/defibrylatory?page[number]=1&page[size]=50",
            "first": f"{API}/defibrylatory?page[number]=1&page[size]=50",
            "prev": None,
            "next": None,
            "last": f"{API}/defibrylatory?page[number]=1&page[size]=50",
        },
    })

    # --- GeoJSON ------------------------------------------------------------
    zapisz_json("aed_wzorzec_przyklad.geojson", {
        "type": "FeatureCollection",
        "name": "aed_wzorzec_przyklad",
        "features": [{
            "type": "Feature",
            "id": r["id_aed"],
            "geometry": {"type": "Point", "coordinates": [r["dlugosc_geograficzna"], r["szerokosc_geograficzna"]]},
            "properties": {k: r[k] for k in NAZWY if k not in ("szerokosc_geograficzna", "dlugosc_geograficzna")},
        } for r in REKORDY],
    })

    # --- Rekord scalony: jak wskazujemy referencyjność ---------------------
    zapisz_json("rekord_scalony_przyklad.json", {
        "$comment": "PRZYKŁAD – jeden AED znaleziony w 3 źródłach. Agregator wybiera rekord referencyjny i zachowuje ślad pochodzenia (provenance).",
        "id_aed": "PL-AED-0000002",
        "rekord_referencyjny": {"zrodlo_danych": "dysponent", "id_zrodlowe": "UM-RYN-1",
                                 "zrodlo_url": "https://dane.gov.pl/pl/dataset/PRZYKLAD"},
        "regula_wyboru": "1) priorytet źródła (dysponent > rejestr_publiczny > baza_zewnetrzna > openstreetmap > zgloszenie_obywatelskie); 2) przy remisie nowsza data_weryfikacji; 3) przy remisie wyższa kompletność pól W+Z",
        "wiarygodnosc": {
            "wynik": 92,
            "skala": "0–100",
            "skladowe": {
                "priorytet_zrodla": {"waga": 40, "punkty": 40, "opis": "dysponent"},
                "poziom_weryfikacji": {"waga": 25, "punkty": 25, "opis": "zweryfikowany_w_terenie"},
                "swiezosc": {"waga": 20, "punkty": 19, "opis": "11 dni od weryfikacji (pełne punkty do 30 dni, 0 po 365 dniach)"},
                "kompletnosc": {"waga": 15, "punkty": 8, "opis": "uzupełnione 16 z 30 pól W+Z"},
            },
        },
        "gotowosc": {
            "$comment": "Wyliczane w API w chwili zapytania – odpowiedź na 3 pytania z zadania",
            "gdzie": "Na zewnątrz, elewacja przy drzwiach głównych, podświetlana szafka",
            "czy_dostepny_teraz": True,
            "czy_dziala": "sprawny (zweryfikowano 2026-11-10; elektrody ważne do 2028-01-31)",
            "etykieta": "GOTOWY",
        },
        "zrodla": [
            {"zrodlo_danych": "dysponent", "id_zrodlowe": "UM-RYN-1", "odleglosc_m": 0.0,
             "data_weryfikacji": "2026-11-10", "referencyjny": True, "licencja": "CC0 1.0"},
            {"zrodlo_danych": "openstreetmap", "id_zrodlowe": "node/0000000002", "odleglosc_m": 6.4,
             "data_weryfikacji": "2023-04-03", "referencyjny": False, "licencja": "ODbL 1.0",
             "uwaga": "Tylko do porównania – atrybuty OSM nie są kopiowane do zbioru CC0"},
            {"zrodlo_danych": "zgloszenie_obywatelskie", "id_zrodlowe": "ZGL-2026-000123", "odleglosc_m": 11.9,
             "data_weryfikacji": "2026-11-19", "referencyjny": False, "licencja": "CC0 1.0",
             "uwaga": "Zgłoszenie 'szafka podświetlona, działa' – potwierdza rekord, nie nadpisuje go"},
        ],
        "konflikty": [
            {"pole": "godziny_dostepnosci", "dysponent": "(24/7)", "openstreetmap": "Mo-Fr 08:00-16:00",
             "rozstrzygniecie": "wartość dysponenta; różnica zgłoszona do weryfikacji w OSM"},
        ],
    })

    # --- Metadane zbioru krajowego (DCAT-AP, JSON-LD) ----------------------
    zapisz_json("metadane_zbioru_dcat.json", {
        "@context": {"dcat": "http://www.w3.org/ns/dcat#", "dct": "http://purl.org/dc/terms/",
                     "foaf": "http://xmlns.com/foaf/0.1/", "vcard": "http://www.w3.org/2006/vcard/ns#"},
        "@type": "dcat:Dataset",
        "dct:title": [{"@language": "pl", "@value": "Defibrylatory AED w Polsce – zbiór krajowy"},
                      {"@language": "en", "@value": "AED defibrillators in Poland – national dataset"}],
        "dct:description": [
            {"@language": "pl", "@value": "Ogólnopolski zbiór lokalizacji automatycznych defibrylatorów zewnętrznych (AED) wraz z informacją o dostępności, sprawności, dysponencie i źródle danych. Zbiór powstaje automatycznie ze zbiorów dysponentów opublikowanych wg wzorcowego zakresu danych (akcja „Otwórz AED”). Aktualizowany codziennie."},
            {"@language": "en", "@value": "National dataset of automated external defibrillators (AED) in Poland with availability, readiness, operator and data provenance. Built daily from operators' datasets published using the common AED data model."}],
        "dcat:keyword": ["AED", "defibrylator", "defibrylatory", "pierwsza pomoc", "nagłe zatrzymanie krążenia",
                         "ratownictwo", "OtworzAED", "defibrillator", "first aid"],
        "dcat:theme": "Zdrowie",
        "dct:license": "https://creativecommons.org/publicdomain/zero/1.0/",
        "dct:accrualPeriodicity": "http://publications.europa.eu/resource/authority/frequency/DAILY",
        "dct:spatial": "Polska",
        "dct:issued": "2026-11-21",
        "dct:modified": "2026-11-21T10:15:00",
        "dct:publisher": {"@type": "foaf:Agent", "foaf:name": "DO USTALENIA (MC / MZ)"},
        "dcat:contactPoint": {"@type": "vcard:Organization", "vcard:hasEmail": "mailto:kontakt@otworzaed.example"},
        "dcat:distribution": [
            {"@type": "dcat:Distribution", "dct:title": "Defibrylatory AED – dane na 2026-11-21 (CSV)",
             "dcat:downloadURL": "https://otworzaed.example/eksport/aed.csv", "dcat:mediaType": "text/csv",
             "dct:conformsTo": "https://otworzaed.example/wzorzec/v0.1/schemat_tableschema.json"},
            {"@type": "dcat:Distribution", "dct:title": "API JSON:API",
             "dcat:accessURL": f"{API}/defibrylatory", "dcat:mediaType": "application/vnd.api+json"},
            {"@type": "dcat:Distribution", "dct:title": "GeoJSON",
             "dcat:downloadURL": "https://otworzaed.example/eksport/aed.geojson", "dcat:mediaType": "application/geo+json"},
        ],
        "x-dane-gov-pl": {
            "kategoria": "Zdrowie", "dane_dynamiczne": False, "dane_o_wysokiej_wartosci": False,
            "mapa": {"szerokosc": "szerokosc_geograficzna", "dlugosc": "dlugosc_geograficzna", "etykieta": "nazwa_lokalizacji"},
            "typy_kolumn_tekst": ["kod_pocztowy", "kod_terc", "kod_simc", "kod_ulic", "dysponent_regon", "telefon_kontaktowy", "numer_budynku"],
            "automatyczna_aktualizacja": "codziennie (zasób jako link HTTPS do CSV)",
            "dokumenty_uzupelniajace": ["slownik_kolumn.csv", "slowniki_wartosci.json", "dokumentacja API (OpenAPI 3)"],
        },
    })

    print("Wygenerowano:")
    for p in sorted(HERE.iterdir()):
        if p.suffix in (".csv", ".json", ".geojson"):
            print(f"  {p.name:34s} {p.stat().st_size:7d} B")


if __name__ == "__main__":
    main()
