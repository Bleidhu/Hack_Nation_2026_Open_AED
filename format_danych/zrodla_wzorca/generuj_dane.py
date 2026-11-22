#!/usr/bin/env python3
"""
Wzorcowy zakres danych AED, wersja 2: jedno źródło prawdy dla kolumn, słowników i przykładów.
Specyfikacja: format_danych/schemat/, zasady: arkusz 5_Zasady w wzorcowym zakresie danych.

Tylko biblioteka standardowa (Python 3.8+). Uruchomienie:
    python format_danych/zrodla_wzorca/generuj_dane.py

Wyniki (w tym samym folderze):
  Wzorzec dostawcy (42 kolumny)
    schemat_tableschema.json        – Table Schema wzorca dostawcy (walidator)
    slownik_kolumn.csv              – opis kolumn: typ, wymagalność W/Z/O, minimum agregacji, reguły
    slowniki_wartosci.json          – zamknięte słowniki wartości
    aed_wzorzec_szablon.csv         – pusty szablon (sam nagłówek)
    aed_wzorzec_przyklad.csv        – 8 przykładowych rekordów dostawcy (FIKCYJNE)
    aed_wzorzec_przyklad.geojson    – te same rekordy jako GeoJSON
    mapowanie_zrodel.csv            – jak nagłówki realnych źródeł odpowiadają kolumnom wzorca
  Zasób zbiorczy budowany przez portal (52 kolumny)
    schemat_zestawienia_tableschema.json
    slownik_kolumn_zestawienia.csv
    aed_zestawienie_przyklad.csv    – wynik reguł agregacji dla przykładów (referencyjna implementacja niżej)
    aed_zestawienie_przyklad.json   – ten sam wynik jako JSON:API z kontekstem JSON-LD
    metadane_zbioru_dcat.json       – metadane zbioru zbiorczego (DCAT-AP, JSON-LD)

Wszystkie rekordy są FIKCYJNE: współrzędne przybliżone, nazwy zmyślone, numery nie należą do nikogo.
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import io
import json
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
WERSJA = "2.1.0"

# ---------------------------------------------------------------------------
# 1. WZORZEC DOSTAWCY: kolumny (kolejność = kolejność w CSV/XLSX)
#    (nazwa, typ, wymagalność W/Z/O, grupa, opis, przykład, reguła jakości dane.gov.pl)
#    W = wymagane we wzorcu, Z = zalecane, O = opcjonalne. Minimum agregacji: MINIMUM_AGREGACJI.
# ---------------------------------------------------------------------------
KOLUMNY = [
    # Identyfikacja
    ("id_zrodlowe", "string", "W", "Identyfikacja", "Identyfikator urządzenia nadany przez dostawcę; unikalny w pliku i stały między wersjami pliku. Na jego podstawie portal nadaje id_aed", "BYD-AED-045", ""),
    # Lokalizacja
    ("nazwa_lokalizacji", "string", "W", "Lokalizacja", "Nazwa obiektu; etykieta punktu na mapie portalu", "Dworzec – hala główna", ""),
    ("wojewodztwo", "string", "Z", "Lokalizacja", "Nazwa województwa wg TERYT, małymi literami", "kujawsko-pomorskie", ""),
    ("powiat", "string", "Z", "Lokalizacja", "Nazwa powiatu wg TERYT", "Bydgoszcz", ""),
    ("gmina", "string", "Z", "Lokalizacja", "Nazwa gminy wg TERYT", "Bydgoszcz", ""),
    ("kod_terc", "string", "Z", "Lokalizacja", "Kod TERC gminy (7 cyfr, TEKST – zera wiodące)", "0461011", ""),
    ("miejscowosc", "string", "W", "Lokalizacja", "Nazwa miejscowości literalnie wg TERYT (SIMC)", "Bydgoszcz", ""),
    ("kod_simc", "string", "Z", "Lokalizacja", "Identyfikator SIMC miejscowości (7 cyfr, TEKST)", "", ""),
    ("kod_pocztowy", "string", "Z", "Lokalizacja", "Kod pocztowy PNA w formacie 00-000", "85-001", "Kod PNA"),
    ("cecha_ulicy", "enum", "Z", "Lokalizacja", "Cecha ulicy ze słownika cecha_ulicy", "ul.", "Cecha adresu"),
    ("nazwa_ulicy", "string", "Z", "Lokalizacja", "Nazwa ulicy literalnie wg TERYT (ULIC); puste, gdy miejscowość bez ulic", "Gdańska", ""),
    ("kod_ulic", "string", "O", "Lokalizacja", "Identyfikator ULIC (5 cyfr, TEKST)", "", ""),
    ("numer_budynku", "string", "Z", "Lokalizacja", "Numer porządkowy budynku (tekst – bywają litery)", "187", ""),
    ("numer_lokalu", "string", "O", "Lokalizacja", "Numer lokalu", "", ""),
    ("adres_uniwersalny", "string", "O", "Lokalizacja", "Adres uniwersalny wg Standardu technicznego (POD 2021–2027 zał. 2, pkt 3.3): kody rozdzielone |", "", "Adres uniwersalny"),
    ("szerokosc_geograficzna", "number", "W", "Lokalizacja", "Szerokość geograficzna WGS84, kropka dziesiętna, min. 6 miejsc po przecinku, zakres 49.0–54.9", "53.123456", "Pole numeryczne"),
    ("dlugosc_geograficzna", "number", "W", "Lokalizacja", "Długość geograficzna WGS84, kropka dziesiętna, min. 6 miejsc po przecinku, zakres 14.1–24.2", "18.012345", "Pole numeryczne"),
    ("opis_lokalizacji", "string", "W", "Lokalizacja", "Gdzie dokładnie jest urządzenie (piętro, ściana, punkt orientacyjny). Bez kodów do szafek, bez informacji, gdzie leży klucz, bez imion i nazwisk", "Parter, przy wejściu głównym, zielona szafka", ""),
    ("wewnatrz_budynku", "boolean", "Z", "Lokalizacja", "true – wewnątrz budynku; false – na zewnątrz", "true", "Pole wartości logicznych"),
    ("kondygnacja", "integer", "O", "Lokalizacja", "0 = parter, liczby ujemne = poziomy podziemne", "0", "Pole numeryczne"),
    # Dostęp
    ("typ_dostepu", "enum", "W", "Dostęp", "Kto może skorzystać – słownik typ_dostepu. AED w lokalu mieszkalnym osoby fizycznej nie jest publikowany", "publiczny", ""),
    ("dostepny_24_7", "boolean", "W", "Dostęp", "true – dostępny całą dobę, 7 dni w tygodniu", "true", "Pole wartości logicznych"),
    ("godziny_dostepnosci", "string", "Z", "Dostęp", "Godziny w składni opening_hours (OSM); puste, gdy 24/7", "Mo-Fr 07:00-21:00; Sa 08:00-14:00", ""),
    ("zabezpieczenie", "enum", "Z", "Dostęp", "Sposób zabezpieczenia urządzenia – słownik zabezpieczenie", "szafka_z_alarmem", ""),
    ("instrukcja_dostepu", "string", "O", "Dostęp", "Jak dostać się do urządzenia. Bez kodów do szafek (podaje je dyspozytor 112), bez imion i nazwisk", "Klucz w portierni (całodobowo)", ""),
    # Urządzenie i stan
    ("status_urzadzenia", "enum", "Z", "Urządzenie i stan", "Stan urządzenia – słownik status_urzadzenia. Puste w pliku dostawcy = 'nieznany' w zasobie zbiorczym (nigdy domyślnie 'sprawny')", "sprawny", ""),
    ("producent", "string", "O", "Urządzenie i stan", "Producent urządzenia", "", ""),
    ("model", "string", "O", "Urządzenie i stan", "Model urządzenia", "", ""),
    ("numer_seryjny", "string", "O", "Urządzenie i stan", "Numer seryjny urządzenia (z tabliczki znamionowej). Służy do zwrotu AED właścicielowi i do deduplikacji w zasobie zbiorczym (producent + numer seryjny). To numer urządzenia, a nie osoby", "", ""),
    ("elektrody_pediatryczne", "boolean", "Z", "Urządzenie i stan", "Czy dostępne elektrody lub tryb pediatryczny", "true", "Pole wartości logicznych"),
    ("data_waznosci_elektrod", "date", "Z", "Urządzenie i stan", "Data ważności elektrod (yyyy-mm-dd)", "2027-05-31", ""),
    ("data_waznosci_baterii", "date", "Z", "Urządzenie i stan", "Data ważności baterii (yyyy-mm-dd)", "2029-01-31", ""),
    ("data_ostatniego_przegladu", "date", "Z", "Urządzenie i stan", "Data ostatniego przeglądu lub autotestu potwierdzonego przez opiekuna (yyyy-mm-dd)", "2026-10-02", ""),
    ("poziom_weryfikacji", "enum", "Z", "Urządzenie i stan", "Jak potwierdzono dane – słownik poziom_weryfikacji. Puste = 'niezweryfikowany' w zasobie zbiorczym", "zweryfikowany_przez_dysponenta", ""),
    ("data_weryfikacji", "date", "Z", "Urządzenie i stan", "Kiedy ostatnio potwierdzono obecność i sprawność AED (yyyy-mm-dd). Puste, jeśli nikt nie weryfikował – data importu nie jest datą weryfikacji", "2026-11-15", ""),
    # Dysponent i kontakt (tylko instytucjonalny)
    ("dysponent_nazwa", "string", "Z", "Dysponent i kontakt", "Właściciel lub opiekun AED. Osoba fizyczna (np. jednoosobowa działalność): wpisz rodzaj podmiotu (np. 'gabinet lekarski') albo zostaw puste. Puste = nazwa wydawcy zasobu w zasobie zbiorczym", "Gmina Przykładowa", ""),
    ("dysponent_regon", "string", "Z", "Dysponent i kontakt", "REGON dysponenta: 9 lub 14 cyfr, TEKST; tylko dla osób prawnych i instytucji", "", "REGON"),
    ("telefon_kontaktowy", "string", "Z", "Dysponent i kontakt", "Telefon WYŁĄCZNIE instytucjonalny lub funkcyjny (centrala, recepcja), nigdy imienny: 9 cyfr lub + i prefiks", "", "Numer telefonu"),
    ("email_kontaktowy", "string", "O", "Dysponent i kontakt", "E-mail WYŁĄCZNIE instytucjonalny lub funkcyjny (np. aed@, sekretariat@), nigdy imienny", "", ""),
    # Źródło i aktualność
    ("zrodlo_danych", "enum", "Z", "Źródło i aktualność", "Pochodzenie rekordu – słownik zrodlo_danych. Wiersze 'openstreetmap' nie trafiają do zasobu zbiorczego (ODbL)", "dysponent", ""),
    ("zrodlo_url", "string", "Z", "Źródło i aktualność", "Link do źródła rekordu u dostawcy (https)", "", ""),
    ("data_aktualizacji", "datetime", "W", "Źródło i aktualność", "Ostatnia zmiana rekordu (yyyy-mm-ddThh:mm:ss)", "2026-11-21T10:15:00", ""),
]
NAZWY = [k[0] for k in KOLUMNY]
assert len(NAZWY) == 42 and len(set(NAZWY)) == 42, len(NAZWY)
WYMAGANE = [k[0] for k in KOLUMNY if k[2] == "W"]
assert WYMAGANE == ["id_zrodlowe", "nazwa_lokalizacji", "miejscowosc", "szerokosc_geograficzna", "dlugosc_geograficzna",
                    "opis_lokalizacji", "typ_dostepu", "dostepny_24_7", "data_aktualizacji"], WYMAGANE
# Minimum, bez którego portal nie dołącza zasobu (brak kolumny) albo wiersza (pusta wartość) do zestawienia.
MINIMUM_AGREGACJI = ["nazwa_lokalizacji", "miejscowosc", "szerokosc_geograficzna", "dlugosc_geograficzna"]

# ---------------------------------------------------------------------------
# 2. SŁOWNIKI (zamknięte listy wartości)
# ---------------------------------------------------------------------------
SLOWNIKI = {
    "typ_dostepu": {
        "opis": "Kto może skorzystać z urządzenia",
        "wartosci": [
            {"kod": "publiczny", "etykieta": "Publiczny – każdy, bez ograniczeń", "osm": "access=yes"},
            {"kod": "ograniczony", "etykieta": "Ograniczony – w godzinach obiektu / przez personel lub ochronę", "osm": "access=customers|permit"},
            {"kod": "prywatny", "etykieta": "Teren niepubliczny instytucji lub firmy (np. tylko dla pracowników); nie lokal mieszkalny", "osm": "access=private"},
        ],
    },
    "zabezpieczenie": {
        "opis": "Sposób zabezpieczenia urządzenia",
        "wartosci": [
            {"kod": "brak", "etykieta": "Brak – urządzenie na uchwycie"},
            {"kod": "szafka_otwarta", "etykieta": "Szafka bez zamka"},
            {"kod": "szafka_z_alarmem", "etykieta": "Szafka z alarmem (otwiera każdy)"},
            {"kod": "szafka_na_kod", "etykieta": "Szafka na kod (kod podaje dyspozytor 112; kodu nie publikujemy)"},
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
            {"kod": "nieznany", "etykieta": "Nieznany – brak potwierdzenia (wartość domyślna dla pustego pola)"},
        ],
    },
    "zrodlo_danych": {
        "opis": "Pochodzenie rekordu",
        "wartosci": [
            {"kod": "dysponent", "etykieta": "Dane własne dysponenta"},
            {"kod": "rejestr_publiczny", "etykieta": "Rejestr publiczny / dane JST"},
            {"kod": "baza_zewnetrzna", "etykieta": "Baza zewnętrzna o licencji CC0 lub CC BY 4.0"},
            {"kod": "openstreetmap", "etykieta": "OpenStreetMap / OpenAEDMap (ODbL) – wykluczony z zasobu zbiorczego"},
            {"kod": "zgloszenie_obywatelskie", "etykieta": "Zgłoszenie obywatela – wymaga potwierdzenia"},
        ],
    },
    "poziom_weryfikacji": {
        "opis": "Jak potwierdzono dane",
        "wartosci": [
            {"kod": "zweryfikowany_w_terenie", "etykieta": "Sprawdzony na miejscu"},
            {"kod": "zweryfikowany_przez_dysponenta", "etykieta": "Potwierdzony przez dysponenta"},
            {"kod": "niezweryfikowany", "etykieta": "Niezweryfikowany (wartość domyślna dla pustego pola)"},
        ],
    },
    "cecha_ulicy": {
        "opis": "Cecha ulicy wg TERYT (reguła „Cecha adresu” w dane.gov.pl)",
        "wartosci": [{"kod": c} for c in ["ul.", "al.", "pl.", "skwer", "bulw.", "rondo", "park", "rynek", "szosa", "droga", "os.", "ogród", "wyspa", "wyb.", "inne"]],
    },
    "licencja_zasobu": {
        "opis": "Licencje źródeł dopuszczone do zasobu zbiorczego",
        "wartosci": [{"kod": "CC0 1.0"}, {"kod": "CC BY 4.0"}],
    },
    "przetworzenie": {
        "opis": "Kody przetworzenia wiersza przez portal (art. 15 ust. 1 pkt 2 ustawy), oddzielone ';'",
        "wartosci": [
            {"kod": "naglowki", "etykieta": "Nagłówek źródła dopasowany do kolumny wzorca (alias)"},
            {"kod": "osie", "etykieta": "Zamienione szerokość i długość geograficzna"},
            {"kod": "domyslne", "etykieta": "Wpisane wartości jawne dla pustych pól (nieznany, niezweryfikowany)"},
            {"kod": "dysponent_z_wydawcy", "etykieta": "Pusty dysponent zastąpiony nazwą wydawcy zasobu"},
            {"kod": "kontakt_usuniety", "etykieta": "Usunięte telefon i e-mail, bo zbiór źródłowy deklaruje dane osobowe"},
        ],
    },
}

# ---------------------------------------------------------------------------
# 3. ZASÓB ZBIORCZY: kolumny dopisywane przez portal (id na początku, reszta po kolumnach wzorca)
# ---------------------------------------------------------------------------
KOLUMNY_ZESTAWIENIA_ID = [
    ("id_aed", "string", "Identyfikacja", "Identyfikator AED nadany przez portal: 'PL-AED-' + 12 znaków hex SHA-1(id instytucji wydawcy | id_zrodlowe). Bez id_zrodlowe: SHA-1(id instytucji | nazwa_lokalizacji znormalizowana | szerokość | długość z 5 miejscami)", "PL-AED-3f2a9c01b7de"),
]
KOLUMNY_ZESTAWIENIA_DODATKOWE = [
    ("wymaga_przegladu", "boolean", "Wyliczane", "true: minął termin elektrod lub baterii albo ostatni przegląd był ponad 12 miesięcy przed agregacją; false: znane daty są aktualne; puste: brak dat. Nie zmienia status_urzadzenia", "false"),
    ("dysponent_z_wydawcy", "boolean", "Wyliczane", "true, gdy dostawca nie podał dysponenta i wpisano nazwę wydawcy zasobu", "false"),
    ("przetworzenie", "string", "Wyliczane", "Kody przetworzenia wiersza oddzielone ';' (słownik przetworzenie); puste = wiersz bez zmian względem źródła", "domyslne;dysponent_z_wydawcy"),
    ("wydawca_zasobu", "string", "Pochodzenie", "Instytucja publikująca zasób źródłowy w portalu (atrybucja)", "Gmina Przykładowa"),
    ("licencja_zasobu", "enum", "Pochodzenie", "Licencja zbioru źródłowego – słownik licencja_zasobu", "CC0 1.0"),
    ("id_zasobu_zrodlowego", "integer", "Pochodzenie", "Identyfikator zasobu źródłowego w portalu", "900001"),
    ("url_zasobu_zrodlowego", "string", "Pochodzenie", "Link do zasobu źródłowego w portalu", "https://dane.gov.pl/pl/dataset/1/resource/900001"),
    ("data_danych_zasobu", "date", "Pochodzenie", "„Dane na dzień” zasobu źródłowego; dla zasobu dodanego linkiem – data kopii w portalu", "2026-11-20"),
    ("data_agregacji", "datetime", "Pochodzenie", "Data i czas zbudowania zasobu zbiorczego (yyyy-mm-ddThh:mm:ss)", "2026-11-22T04:15:00"),
]
NAZWY_ZESTAWIENIA = [k[0] for k in KOLUMNY_ZESTAWIENIA_ID] + NAZWY + [k[0] for k in KOLUMNY_ZESTAWIENIA_DODATKOWE]
assert len(NAZWY_ZESTAWIENIA) == 52 and len(set(NAZWY_ZESTAWIENIA)) == 52, len(NAZWY_ZESTAWIENIA)

# ---------------------------------------------------------------------------
# 4. PRZYKŁADOWE REKORDY DOSTAWCY (FIKCYJNE). Każdy pokazuje inny przypadek z praktyki.
# ---------------------------------------------------------------------------
BAZA = dict(wojewodztwo="kujawsko-pomorskie", powiat="Bydgoszcz", gmina="Bydgoszcz",
            kod_terc="0461011", miejscowosc="Bydgoszcz", kod_simc="", kod_ulic="",
            numer_lokalu="", adres_uniwersalny="", producent="", model="", numer_seryjny="", dysponent_regon="",
            telefon_kontaktowy="", email_kontaktowy="", zrodlo_url="")

REKORDY = [
    dict(BAZA, id_zrodlowe="CT-01", producent="Philips", model="HeartStart FRx", numer_seryjny="FRX-2026-0001", nazwa_lokalizacji="Centrum targowe – hala A, wejście główne",
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
         data_aktualizacji="2026-11-21T10:15:00"),
    dict(BAZA, id_zrodlowe="UM-RYN-1", producent="Zoll", model="AED Plus", numer_seryjny="ZP-2026-0002", nazwa_lokalizacji="Stary Rynek – ratusz, wejście od rynku",
         kod_pocztowy="85-002", cecha_ulicy="rynek", nazwa_ulicy="Stary Rynek", numer_budynku="1",
         szerokosc_geograficzna=53.122640, dlugosc_geograficzna=17.999870,
         opis_lokalizacji="Na zewnątrz, elewacja przy drzwiach głównych, podświetlana szafka",
         wewnatrz_budynku=False, kondygnacja=0, typ_dostepu="publiczny", dostepny_24_7=True,
         godziny_dostepnosci="", zabezpieczenie="szafka_z_alarmem", instrukcja_dostepu="",
         status_urzadzenia="sprawny", elektrody_pediatryczne=True,
         data_waznosci_elektrod="2028-01-31", data_waznosci_baterii="2030-06-30", data_ostatniego_przegladu="2026-11-10",
         dysponent_nazwa="Gmina Przykładowa", dysponent_regon="000000000", telefon_kontaktowy="525550102",
         zrodlo_danych="dysponent", zrodlo_url="https://gmina-przyklad.example/aed",
         poziom_weryfikacji="zweryfikowany_w_terenie", data_weryfikacji="2026-11-10",
         data_aktualizacji="2026-11-20T08:00:00"),
    dict(BAZA, id_zrodlowe="SP99-1", producent="Defibtech", model="Lifeline AED", numer_seryjny="DL-2026-0003", nazwa_lokalizacji="Szkoła Podstawowa nr 99 – sala gimnastyczna",
         kod_pocztowy="85-003", cecha_ulicy="ul.", nazwa_ulicy="Szkolna", numer_budynku="5A",
         szerokosc_geograficzna=53.131870, dlugosc_geograficzna=18.034410,
         opis_lokalizacji="Parter, korytarz przy wejściu do sali gimnastycznej",
         wewnatrz_budynku=True, kondygnacja=0, typ_dostepu="ograniczony", dostepny_24_7=False,
         godziny_dostepnosci="Mo-Fr 07:00-17:00", zabezpieczenie="zamkniety_na_klucz",
         instrukcja_dostepu="Klucz w sekretariacie szkoły",
         status_urzadzenia="sprawny", elektrody_pediatryczne=True,
         data_waznosci_elektrod="2026-12-31", data_waznosci_baterii="2028-08-31", data_ostatniego_przegladu="2026-09-01",
         dysponent_nazwa="Szkoła Podstawowa nr 99 (przykład)", zrodlo_danych="dysponent",
         poziom_weryfikacji="zweryfikowany_przez_dysponenta", data_weryfikacji="2026-09-01",
         data_aktualizacji="2026-09-01T12:00:00"),
    # Dwa AED w jednym budynku = dwa wiersze z różnym id_zrodlowe (ten sam punkt, inna kondygnacja).
    dict(BAZA, id_zrodlowe="SP99-2", producent="Defibtech", model="Lifeline AED", numer_seryjny="DL-2026-0004", nazwa_lokalizacji="Szkoła Podstawowa nr 99 – pokój nauczycielski",
         kod_pocztowy="85-003", cecha_ulicy="ul.", nazwa_ulicy="Szkolna", numer_budynku="5A",
         szerokosc_geograficzna=53.131870, dlugosc_geograficzna=18.034410,
         opis_lokalizacji="I piętro, pokój nauczycielski, szafka przy drzwiach",
         wewnatrz_budynku=True, kondygnacja=1, typ_dostepu="ograniczony", dostepny_24_7=False,
         godziny_dostepnosci="Mo-Fr 07:00-17:00", zabezpieczenie="szafka_otwarta", instrukcja_dostepu="",
         status_urzadzenia="sprawny", elektrody_pediatryczne=True,
         data_waznosci_elektrod="2027-06-30", data_waznosci_baterii="2029-06-30", data_ostatniego_przegladu="2026-09-01",
         dysponent_nazwa="Szkoła Podstawowa nr 99 (przykład)", zrodlo_danych="dysponent",
         poziom_weryfikacji="zweryfikowany_przez_dysponenta", data_weryfikacji="2026-09-01",
         data_aktualizacji="2026-09-01T12:00:00"),
    dict(BAZA, id_zrodlowe="OSP-PRZ-1", producent="Physio-Control", model="LIFEPAK CR2", numer_seryjny="LP-2026-0005", nazwa_lokalizacji="OSP Przykładowo – remiza",
         kod_pocztowy="85-004", cecha_ulicy="ul.", nazwa_ulicy="Strażacka", numer_budynku="12",
         szerokosc_geograficzna=53.105530, dlugosc_geograficzna=18.069920,
         opis_lokalizacji="Na zewnątrz, ściana boczna remizy od strony parkingu",
         wewnatrz_budynku=False, kondygnacja=0, typ_dostepu="publiczny", dostepny_24_7=True,
         godziny_dostepnosci="", zabezpieczenie="szafka_na_kod",
         instrukcja_dostepu="Kod do szafki podaje dyspozytor 112",
         status_urzadzenia="w_serwisie", elektrody_pediatryczne=False,
         data_waznosci_elektrod="2027-02-28", data_waznosci_baterii="2027-02-28", data_ostatniego_przegladu="2026-11-18",
         dysponent_nazwa="Ochotnicza Straż Pożarna Przykładowo", zrodlo_danych="dysponent",
         poziom_weryfikacji="zweryfikowany_przez_dysponenta", data_weryfikacji="2026-11-18",
         data_aktualizacji="2026-11-18T19:30:00"),
    dict(BAZA, id_zrodlowe="ZOO-2", nazwa_lokalizacji="Park miejski – pawilon kasowy",
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
         data_aktualizacji="2026-10-20T09:00:00"),
    # Zgłoszenie obywatelskie: brak dysponenta, statusu, weryfikacji i dat serwisowych.
    dict(BAZA, id_zrodlowe="ZGL-2026-0017", nazwa_lokalizacji="Pływalnia osiedlowa – recepcja",
         kod_pocztowy="85-006", cecha_ulicy="ul.", nazwa_ulicy="Sportowa", numer_budynku="8",
         szerokosc_geograficzna=53.114470, dlugosc_geograficzna=18.006780,
         opis_lokalizacji="Recepcja, na ścianie za ladą",
         wewnatrz_budynku=True, kondygnacja=0, typ_dostepu="ograniczony", dostepny_24_7=False,
         godziny_dostepnosci="Mo-Fr 06:00-22:00; Sa,Su 08:00-20:00", zabezpieczenie="brak", instrukcja_dostepu="",
         status_urzadzenia="", elektrody_pediatryczne="",
         data_waznosci_elektrod="", data_waznosci_baterii="", data_ostatniego_przegladu="",
         dysponent_nazwa="", zrodlo_danych="zgloszenie_obywatelskie",
         poziom_weryfikacji="", data_weryfikacji="",
         data_aktualizacji="2026-11-19T21:12:00"),
    dict(BAZA, id_zrodlowe="UNI-B-3", nazwa_lokalizacji="Uczelnia – budynek B, portiernia",
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
         data_aktualizacji="2026-11-05T14:40:00"),
]

# Fikcyjne zasoby źródłowe w portalu (do przykładu zasobu zbiorczego).
ZRODLA = {
    "gmina": dict(id_instytucji=1001, wydawca="Gmina Przykładowa (PRZYKŁAD)", licencja="CC0 1.0", id_zasobu=900001,
                  url="https://dane.gov.pl/pl/dataset/1/resource/900001", data_danych="2026-11-20", dane_osobowe=False),
    # Zbiór deklaruje warunki dla danych osobowych (art. 15 ust. 1 pkt 4) → portal czyści kontakty.
    "powiat": dict(id_instytucji=1002, wydawca="Starostwo Powiatowe Przykład (PRZYKŁAD)", licencja="CC BY 4.0", id_zasobu=900002,
                   url="https://dane.gov.pl/pl/dataset/2/resource/900002", data_danych="2026-11-19", dane_osobowe=True),
}
PRZYPISANIE = {"UNI-B-3": "powiat"}  # pozostałe rekordy pochodzą z zasobu gminy
DATA_AGREGACJI = "2026-11-22T04:15:00"


# ---------------------------------------------------------------------------
# 5. REGUŁY AGREGACJI – implementacja referencyjna. Portal ma dawać ten sam wynik.
# ---------------------------------------------------------------------------
def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s).replace("ł", "l").replace("Ł", "L"))
    return " ".join("".join(c for c in s if not unicodedata.combining(c)).lower().split())


def id_aed(id_instytucji: int, r: dict) -> str:
    if r.get("id_zrodlowe"):
        klucz = f"{id_instytucji}|{r['id_zrodlowe']}"
    else:
        klucz = f"{id_instytucji}|{_norm(r['nazwa_lokalizacji'])}|{float(r['szerokosc_geograficzna']):.5f}|{float(r['dlugosc_geograficzna']):.5f}"
    return "PL-AED-" + hashlib.sha1(klucz.encode("utf-8")).hexdigest()[:12]


def wymaga_przegladu(r: dict, dzis: dt.date):
    el, bat, prz = (r.get(k) or "" for k in ("data_waznosci_elektrod", "data_waznosci_baterii", "data_ostatniego_przegladu"))
    if not (el or bat or prz):
        return ""
    d = dt.date.fromisoformat
    return bool((el and d(el) < dzis) or (bat and d(bat) < dzis) or (prz and d(prz) < dzis - dt.timedelta(days=365)))


def powod_pominiecia(r: dict):
    if r.get("zrodlo_danych") == "openstreetmap":
        return "licencja ODbL (OpenStreetMap)"
    brak = [k for k in MINIMUM_AGREGACJI if r.get(k) in ("", None)]
    return f"brak wartości: {', '.join(brak)}" if brak else None


def zestaw(r: dict, zrodlo: dict, data_agregacji: str) -> dict:
    """Jeden wiersz dostawcy → wiersz zasobu zbiorczego (bez nagłówków-aliasów i zamiany osi, które dotyczą surowych plików)."""
    w, kody = dict(r), []
    for k, domyslna in (("status_urzadzenia", "nieznany"), ("poziom_weryfikacji", "niezweryfikowany")):
        if not w.get(k):
            w[k] = domyslna
            kody.append("domyslne")
    z_wydawcy = not w.get("dysponent_nazwa")
    if z_wydawcy:
        w["dysponent_nazwa"] = zrodlo["wydawca"]
        kody.append("dysponent_z_wydawcy")
    if zrodlo["dane_osobowe"] and (w.get("telefon_kontaktowy") or w.get("email_kontaktowy")):
        w["telefon_kontaktowy"] = w["email_kontaktowy"] = ""
        kody.append("kontakt_usuniety")
    w.update(
        id_aed=id_aed(zrodlo["id_instytucji"], r),
        wymaga_przegladu=wymaga_przegladu(w, dt.date.fromisoformat(data_agregacji[:10])),
        dysponent_z_wydawcy=z_wydawcy,
        przetworzenie=";".join(dict.fromkeys(kody)),
        wydawca_zasobu=zrodlo["wydawca"], licencja_zasobu=zrodlo["licencja"], id_zasobu_zrodlowego=zrodlo["id_zasobu"],
        url_zasobu_zrodlowego=zrodlo["url"], data_danych_zasobu=zrodlo["data_danych"], data_agregacji=data_agregacji,
    )
    return w


def _samokontrola():
    g = ZRODLA["gmina"]
    assert id_aed(1, {"id_zrodlowe": "A"}) == id_aed(1, {"id_zrodlowe": "A"}) != id_aed(2, {"id_zrodlowe": "A"})
    bez_id = {"id_zrodlowe": "", "nazwa_lokalizacji": "Ratusz  Łódź", "szerokosc_geograficzna": 51.7, "dlugosc_geograficzna": 19.4}
    assert id_aed(1, bez_id) == id_aed(1, dict(bez_id, nazwa_lokalizacji="ratusz lodz"))
    dzis = dt.date(2026, 11, 22)
    assert wymaga_przegladu({}, dzis) == ""
    assert wymaga_przegladu({"data_waznosci_elektrod": "2026-11-21"}, dzis) is True
    assert wymaga_przegladu({"data_ostatniego_przegladu": "2025-11-21"}, dzis) is True
    assert wymaga_przegladu({"data_ostatniego_przegladu": "2025-11-23", "data_waznosci_baterii": "2027-01-01"}, dzis) is False
    assert powod_pominiecia({"zrodlo_danych": "openstreetmap"}).startswith("licencja ODbL")
    assert powod_pominiecia({"nazwa_lokalizacji": "X", "miejscowosc": "", "szerokosc_geograficzna": 52.0, "dlugosc_geograficzna": 21.0}) == "brak wartości: miejscowosc"
    w = zestaw({"status_urzadzenia": "", "dysponent_nazwa": "", "telefon_kontaktowy": "123456789", "id_zrodlowe": "A"},
               dict(g, dane_osobowe=True), DATA_AGREGACJI)
    assert (w["status_urzadzenia"], w["poziom_weryfikacji"], w["dysponent_nazwa"], w["telefon_kontaktowy"]) == ("nieznany", "niezweryfikowany", g["wydawca"], "")
    assert w["przetworzenie"] == "domyslne;dysponent_z_wydawcy;kontakt_usuniety" and w["dysponent_z_wydawcy"] is True
    assert zestaw({"status_urzadzenia": "sprawny", "poziom_weryfikacji": "niezweryfikowany", "dysponent_nazwa": "X", "id_zrodlowe": "A"}, g, DATA_AGREGACJI)["przetworzenie"] == ""


# ---------------------------------------------------------------------------
# 6. ZAPIS
# ---------------------------------------------------------------------------
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


TYP_W_PORTALU = {"string": "tekst", "enum": "tekst", "number": "liczba zmiennoprzecinkowa", "integer": "liczba całkowita",
                 "boolean": "wartość logiczna", "date": "data", "datetime": "data i czas"}


def pole_schematu(n, t, opis, wymagane=False):
    f = {"name": n, "type": {"enum": "string"}.get(t, t), "description": opis}
    c = {}
    if wymagane:
        c["required"] = True
    if n == "przetworzenie":  # lista kodów rozdzielonych ';', więc wzorzec zamiast enum
        kody = "|".join(x["kod"] for x in SLOWNIKI[n]["wartosci"])
        c["pattern"] = rf"^({kody})(;({kody}))*$"
    elif n in SLOWNIKI:
        c["enum"] = [x["kod"] for x in SLOWNIKI[n]["wartosci"]]
    c.update({
        "szerokosc_geograficzna": dict(minimum=49.0, maximum=54.9), "dlugosc_geograficzna": dict(minimum=14.1, maximum=24.2),
        "kod_pocztowy": dict(pattern=r"^\d{2}-\d{3}$"), "kod_terc": dict(pattern=r"^\d{7}$"), "kod_simc": dict(pattern=r"^\d{7}$"),
        "kod_ulic": dict(pattern=r"^\d{5}$"), "dysponent_regon": dict(pattern=r"^(\d{9}|\d{14})$"),
        "telefon_kontaktowy": dict(pattern=r"^(\+\d{2})?\d{9}$"), "id_aed": dict(pattern=r"^PL-AED-[0-9a-f]{12}$", unique=True),
    }.get(n, {}))
    if t == "boolean":
        f.update(trueValues=["true"], falseValues=["false"])
    if t == "date":
        f["format"] = "%Y-%m-%d"
    if t == "datetime":
        f["format"] = "%Y-%m-%dT%H:%M:%S"
    if c:
        f["constraints"] = c
    return f


def main():
    _samokontrola()
    for r in REKORDY:
        assert set(r) == set(NAZWY), set(NAZWY) ^ set(r)
    assert len({r["id_zrodlowe"] for r in REKORDY}) == len(REKORDY)

    # --- wzorzec dostawcy ---------------------------------------------------
    zapisz_csv("aed_wzorzec_przyklad.csv", NAZWY, [[fmt(r[k]) for k in NAZWY] for r in REKORDY])
    zapisz_csv("aed_wzorzec_szablon.csv", NAZWY, [])
    zapisz_csv(
        "slownik_kolumn.csv",
        ["lp", "kolumna", "typ", "wymagalnosc", "minimum_agregacji", "grupa", "opis", "przyklad", "slownik", "regula_jakosci_dane_gov_pl", "typ_kolumny_w_portalu"],
        [[str(i), n, t, w, "tak" if n in MINIMUM_AGREGACJI else "", g, o, p, n if n in SLOWNIKI else "", reg, TYP_W_PORTALU[t]]
         for i, (n, t, w, g, o, p, reg) in enumerate(KOLUMNY, 1)],
    )
    pola = []
    for n, t, w, g, o, p, reg in KOLUMNY:
        f = pole_schematu(n, t, o, wymagane=(w == "W"))
        f.update({"x-wymagalnosc": w, "x-grupa": g, "x-minimum-agregacji": n in MINIMUM_AGREGACJI})
        if n == "id_zrodlowe":
            f["constraints"]["unique"] = True
        pola.append(f)
    zapisz_json("schemat_tableschema.json", {
        "$comment": "Frictionless Table Schema wzorca dostawcy AED v2 (decyzje projektu). Pola x-* to rozszerzenia projektu.",
        "name": "aed-wzorzec-dostawcy", "title": "Wzorcowy zakres danych o defibrylatorach AED – plik dostawcy",
        "version": WERSJA, "fields": pola, "primaryKey": "id_zrodlowe", "missingValues": [""],
        "x-minimum-agregacji": MINIMUM_AGREGACJI,
        "x-reguly-dodatkowe": [
            "jeden wiersz = jedno urządzenie; kilka AED w jednym miejscu = kilka wierszy z różnym id_zrodlowe (te same współrzędne są dopuszczalne)",
            "dostepny_24_7=true ⇒ godziny_dostepnosci puste; dostepny_24_7=false ⇒ godziny_dostepnosci zalecane",
            "AED w lokalu mieszkalnym osoby fizycznej nie jest publikowany",
            "telefon_kontaktowy i email_kontaktowy tylko instytucjonalne lub funkcyjne (RODO; dane firm z definicji bez danych osobowych)",
            "opis_lokalizacji i instrukcja_dostepu bez kodów do szafek, bez miejsca przechowywania klucza, bez imion i nazwisk",
            "status_urzadzenia nigdy domyślnie 'sprawny'; data importu nie jest datą weryfikacji",
            "zrodlo_danych=openstreetmap ⇒ wiersz nie trafia do zasobu zbiorczego (ODbL)",
            "data_waznosci_elektrod lub data_waznosci_baterii < dzisiaj ⇒ ostrzeżenie (wymaga_przegladu w zasobie zbiorczym)",
            "pola tekstowe bez znaków nowej linii",
        ],
    })
    zapisz_json("slowniki_wartosci.json", SLOWNIKI)
    zapisz_json("aed_wzorzec_przyklad.geojson", {
        "type": "FeatureCollection", "name": "aed_wzorzec_przyklad",
        "features": [{
            "type": "Feature", "id": r["id_zrodlowe"],
            "geometry": {"type": "Point", "coordinates": [r["dlugosc_geograficzna"], r["szerokosc_geograficzna"]]},
            "properties": {k: r[k] for k in NAZWY if k not in ("szerokosc_geograficzna", "dlugosc_geograficzna")},
        } for r in REKORDY],
    })
    zapisz_csv(
        "mapowanie_zrodel.csv",
        ["kolumna_wzorca", "openaedmap_osm_tag", "danegovpl_krosno_marki", "danegovpl_legionowo", "danegovpl_przemysl", "warszawa_api", "przeksztalcenie"],
        [
            ["id_zrodlowe", "@id (node/…)", "Numer Id", "brak", "id", "defibrillator_id", "brak → id_aed liczone z nazwy i współrzędnych"],
            ["nazwa_lokalizacji", "name / description", "Nazwa (często 'Defibrylator') + Lokalizacja", "nazwa", "name", "nazwa obiektu", "gdy nazwa = 'Defibrylator' → użyj pola Lokalizacja"],
            ["szerokosc_geograficzna", "geometry.coordinates[1]", "Szerokość geograficzna (Marki: zamienione z długością!)", "szerokosc_geograficzna", "geometry (WKT w komórce)", "geometry.coordinates[1]", "kontrola zakresu 49.0–54.9; zamiana osi → przetworzenie=osie"],
            ["dlugosc_geograficzna", "geometry.coordinates[0]", "Długość geograficzna", "dlugosc_geograficzna", "geometry (WKT w komórce)", "geometry.coordinates[0]", "kontrola zakresu 14.1–24.2"],
            ["miejscowosc / nazwa_ulicy / numer_budynku / kod_pocztowy", "addr:city / addr:street / addr:housenumber / addr:postcode", "Adres (jedno pole: 'ul. Jasna, 38-400 Krosno')", "miejscowosc / nazwa_ulicy / nr_budynku / kod_pocztowy", "city / street / home_number / postcode", "adres", "nr_budynku → numer_budynku (alias); jedno pole adresu → parser (krok 2)"],
            ["opis_lokalizacji", "defibrillator:location", "Lokalizacja", "brak", "brak (description = tekst ogólny)", "device_access_description", "puste → wiersz niezgodny ze wzorcem (nie blokuje agregacji)"],
            ["typ_dostepu", "access", "brak", "brak", "brak", "?", "yes→publiczny; customers/permit→ograniczony; private→prywatny (teren niepubliczny)"],
            ["dostepny_24_7 / godziny_dostepnosci", "opening_hours", "brak", "brak", "brak", "?", "'24/7' → dostepny_24_7=true; inne → godziny_dostepnosci"],
            ["dysponent_nazwa", "operator", "brak", "brak", "brak", "?", "puste → nazwa wydawcy zasobu, dysponent_z_wydawcy=true"],
            ["telefon_kontaktowy / email_kontaktowy", "phone / email", "brak", "brak", "phone / email", "?", "tylko instytucjonalne; zbiór z warunkiem dla danych osobowych → usunięte (kontakt_usuniety)"],
            ["status_urzadzenia", "brak tagu", "brak", "brak", "brak", "?", "puste → 'nieznany' (domyslne)"],
            ["poziom_weryfikacji / data_weryfikacji", "check_date", "brak", "brak", "brak", "?", "puste → 'niezweryfikowany'; data_weryfikacji zostaje pusta"],
            ["zrodlo_danych", "(stała) openstreetmap", "(stała) dysponent", "(stała) dysponent", "(stała) dysponent", "(stała) dysponent", "openstreetmap → wiersz wykluczony (ODbL)"],
        ],
    )

    # --- zasób zbiorczy -----------------------------------------------------
    wiersze = []
    for r in REKORDY:
        assert powod_pominiecia(r) is None, r["id_zrodlowe"]
        wiersze.append(zestaw(r, ZRODLA[PRZYPISANIE.get(r["id_zrodlowe"], "gmina")], DATA_AGREGACJI))
    assert len({w["id_aed"] for w in wiersze}) == len(wiersze)
    zapisz_csv("aed_zestawienie_przyklad.csv", NAZWY_ZESTAWIENIA, [[fmt(w[k]) for k in NAZWY_ZESTAWIENIA] for w in wiersze])

    opisy = {n: (t, g, o, p) for n, t, w, g, o, p, reg in KOLUMNY}
    opisy.update({n: (t, g, o, p) for n, t, g, o, p in KOLUMNY_ZESTAWIENIA_ID + KOLUMNY_ZESTAWIENIA_DODATKOWE})
    zapisz_csv(
        "slownik_kolumn_zestawienia.csv",
        ["lp", "kolumna", "typ", "pochodzenie", "grupa", "opis", "przyklad", "typ_kolumny_w_portalu"],
        [[str(i), n, opisy[n][0], "wzorzec dostawcy" if n in NAZWY else "portal", opisy[n][1], opisy[n][2], opisy[n][3], TYP_W_PORTALU[opisy[n][0]]]
         for i, n in enumerate(NAZWY_ZESTAWIENIA, 1)],
    )
    zapisz_json("schemat_zestawienia_tableschema.json", {
        "$comment": "Table Schema zasobu zbiorczego AED budowanego przez portal (decyzje projektu). Pola wzorca bez wymagalności dostawcy.",
        "name": "aed-zestawienie", "title": "Wykaz defibrylatorów AED – wykaz zbiorczy", "version": WERSJA,
        "fields": [dict(pole_schematu(n, opisy[n][0], opisy[n][2], wymagane=(n in MINIMUM_AGREGACJI or n in
                   ("id_aed", "status_urzadzenia", "poziom_weryfikacji", "dysponent_nazwa", "dysponent_z_wydawcy", "wydawca_zasobu",
                    "licencja_zasobu", "id_zasobu_zrodlowego", "url_zasobu_zrodlowego", "data_agregacji"))),
                        **{"x-grupa": opisy[n][1]}) for n in NAZWY_ZESTAWIENIA],
        "primaryKey": "id_aed", "missingValues": [""],
        "x-mapa-portalu": {"b": "szerokosc_geograficzna", "l": "dlugosc_geograficzna", "label": "nazwa_lokalizacji"},
        "x-licencja": "CC BY 4.0",
    })

    kontekst = {
        "schema": "https://schema.org/", "xsd": "http://www.w3.org/2001/XMLSchema#", "aed": "https://dane.gov.pl/aed/def#",
        "id_aed": "@id", "nazwa_lokalizacji": "schema:name", "opis_lokalizacji": "schema:description",
        "szerokosc_geograficzna": {"@id": "schema:latitude", "@type": "xsd:decimal"},
        "dlugosc_geograficzna": {"@id": "schema:longitude", "@type": "xsd:decimal"},
        "miejscowosc": "schema:addressLocality", "kod_pocztowy": "schema:postalCode", "nazwa_ulicy": "schema:streetAddress",
        "kondygnacja": "schema:floorLevel", "godziny_dostepnosci": "schema:openingHours", "dysponent_nazwa": "schema:provider",
        "telefon_kontaktowy": "schema:telephone", "email_kontaktowy": "schema:email", "producent": "schema:manufacturer", "model": "schema:model",
        "data_aktualizacji": {"@id": "schema:dateModified", "@type": "xsd:dateTime"},
        "data_weryfikacji": {"@id": "aed:dataWeryfikacji", "@type": "xsd:date"},
        "typ_dostepu": "aed:typDostepu", "dostepny_24_7": {"@id": "aed:dostepny247", "@type": "xsd:boolean"},
        "zabezpieczenie": "aed:zabezpieczenie", "status_urzadzenia": "aed:statusUrzadzenia", "poziom_weryfikacji": "aed:poziomWeryfikacji",
        "zrodlo_danych": "aed:zrodloDanych", "kod_terc": "aed:kodTERC", "wymaga_przegladu": {"@id": "aed:wymagaPrzegladu", "@type": "xsd:boolean"},
        "wydawca_zasobu": "schema:publisher", "licencja_zasobu": "schema:license", "url_zasobu_zrodlowego": {"@id": "schema:isBasedOn", "@type": "@id"},
        "data_agregacji": {"@id": "schema:dateCreated", "@type": "xsd:dateTime"},
    }
    zapisz_json("aed_zestawienie_przyklad.json", {
        "jsonapi": {"version": "1.0"}, "@context": kontekst,
        "meta": {"count": len(wiersze), "data_agregacji": DATA_AGREGACJI, "licencja": "https://creativecommons.org/licenses/by/4.0/",
                 "uwaga": "PRZYKŁAD – dane fikcyjne; postać wierszy zasobu zbiorczego w API portalu"},
        "data": [{"type": "defibrylatory", "id": w["id_aed"], "attributes": {k: (w[k] if w[k] != "" else None) for k in NAZWY_ZESTAWIENIA if k != "id_aed"}}
                 for w in wiersze],
    })
    zapisz_json("metadane_zbioru_dcat.json", {
        "@context": {"dcat": "http://www.w3.org/ns/dcat#", "dct": "http://purl.org/dc/terms/", "foaf": "http://xmlns.com/foaf/0.1/"},
        "@type": "dcat:Dataset",
        "dct:title": [{"@language": "pl", "@value": "Wykaz defibrylatorów AED – wykaz zbiorczy"},
                      {"@language": "en", "@value": "AED defibrillators in Poland – national aggregate"}],
        "dct:description": [
            {"@language": "pl", "@value": "Zasób zbiorczy budowany codziennie przez portal z zasobów dostawców, których zbiory deklarują zgodność ze wzorcem AED (Pola niestandardowe: standard = AED). Każdy wiersz ma atrybucję źródła (wydawca, licencja, link). Pominięte: wiersze z OpenStreetMap (ODbL), wiersze bez minimum danych, kontakty ze zbiorów deklarujących dane osobowe. Brak statusu oznacza 'nieznany', a nie 'sprawny'."},
            {"@language": "en", "@value": "Daily aggregate of AED resources from providers whose datasets declare conformance with the AED template. Each row carries source attribution."}],
        "dcat:keyword": ["AED", "defibrylator", "defibrylatory", "pierwsza pomoc", "nagłe zatrzymanie krążenia", "defibrillator"],
        "dcat:theme": "Zdrowie",
        "dct:license": "https://creativecommons.org/licenses/by/4.0/",
        "dct:accrualPeriodicity": "http://publications.europa.eu/resource/authority/frequency/DAILY",
        "dct:spatial": "Polska",
        "dct:publisher": {"@type": "foaf:Agent", "foaf:name": "Ministerstwo Cyfryzacji (właściciel zbioru zbiorczego – ustawienie portalu)"},
        "dcat:distribution": [{"@type": "dcat:Distribution", "dct:title": "Wykaz defibrylatorów AED – wykaz zbiorczy (CSV)", "dcat:mediaType": "text/csv",
                               "dct:conformsTo": "format_danych/schemat/aed_zestawienie.tableschema.json",
                               "dcat:accessURL": "DO UZUPEŁNIENIA – zasób tworzy portal"}],
        "x-dane-gov-pl": {
            "kategoria": "Zdrowie", "dane_dynamiczne": False, "dane_o_wysokiej_wartosci": False,
            "pola_niestandardowe": {"standard": "AED", "zestawienie": "AED-krajowe"},
            "mapa": {"b": "szerokosc_geograficzna", "l": "dlugosc_geograficzna", "label": "nazwa_lokalizacji"},
            "typy_kolumn_tekst": ["id_zrodlowe", "kod_pocztowy", "kod_terc", "kod_simc", "kod_ulic", "dysponent_regon", "telefon_kontaktowy", "numer_budynku"],
            "warunki_art_15": {"zrodlo_i_czas": "kolumny wydawca_zasobu, url_zasobu_zrodlowego, data_danych_zasobu, data_agregacji",
                               "przetworzenie": "kolumna przetworzenie", "dane_osobowe": "zasób nie zawiera danych osobowych (kontakty czyszczone)"},
        },
    })

    print("Wygenerowano:")
    for p in sorted(HERE.iterdir()):
        if p.suffix in (".csv", ".json", ".geojson"):
            print(f"  {p.name:40s} {p.stat().st_size:7d} B")


if __name__ == "__main__":
    main()
