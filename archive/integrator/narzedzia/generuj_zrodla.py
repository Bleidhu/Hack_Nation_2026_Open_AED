#!/usr/bin/env python3
"""
Generuje warianty danych przykładowych od różnych typów dostawców – każdy w swoim
„natywnym” formacie (tak, jak dane wyglądają u źródła, zanim trafią do wzorca),
razem z plikiem mapowania na wzorzec i opisem źródła (zrodlo.json).

    python deliverable/narzedzia/generuj_zrodla.py

Pliki trafiają do deliverable/dane_przykladowe/<NN_typ_zrodla>/. Skrypt NIE nadpisuje
plików tworzonych przez generuj.py (format docelowy, bank CSV, sieć sklepów TSV,
OSM GeoJSON, aktualizacje CSV) – dopisuje tylko nowe pliki i opisy zrodlo.json.

Wszystkie dane są FIKCYJNE. Współrzędne wskazują ogólnodostępne miejsca w Krakowie
(dworzec, rynek), ale urządzenia, numery seryjne, firmy i zdarzenia są zmyślone.
Tylko biblioteka standardowa Pythona.
"""
from __future__ import annotations

import json
from pathlib import Path

D = Path(__file__).resolve().parents[1] / "dane_przykladowe"
FIKCJA = "PRZYKŁAD – dane fikcyjne"


def zapisz(folder: str, nazwa: str, obj) -> None:
    p = D / folder / nazwa
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", "utf-8", newline="")


# --------------------------------------------------------------------------- #
# 01 – duży integrator: OpenStreetMap (Overpass API JSON)
# --------------------------------------------------------------------------- #
OVERPASS = {
    "version": 0.6,
    "generator": "Overpass API (PRZYKŁAD – odpowiedź spreparowana do demo)",
    "osm3s": {"timestamp_osm_base": "2026-11-21T06:00:00Z",
              "copyright": "The data included in this document is from www.openstreetmap.org. The data is made available under ODbL."},
    "elements": [
        {"type": "node", "id": 900000001, "lat": 50.06160, "lon": 19.93820,
         "tags": {"emergency": "defibrillator", "access": "customers", "indoor": "yes", "level": "0",
                  "opening_hours": "Mo-Fr 09:00-17:00", "operator": "Bank Przykład",
                  "defibrillator:location:pl": "w holu banku", "check_date": "2023-04-02", "note": FIKCJA}},
        {"type": "node", "id": 900000002, "lat": 50.07040, "lon": 19.93760,
         "tags": {"emergency": "defibrillator", "access": "yes", "indoor": "yes", "name": "Apteka",
                  "opening_hours": "Mo-Fr 08:00-20:00", "note": FIKCJA}},
        {"type": "node", "id": 900000003, "lat": 50.06785, "lon": 19.94770,
         "tags": {"emergency": "defibrillator", "access": "yes", "indoor": "yes", "opening_hours": "24/7",
                  "defibrillator:location:pl": "hala dworca, obok kas", "operator": "PKP", "check_date": "2025-06-10",
                  "note": FIKCJA}},
        {"type": "node", "id": 900000004, "lat": 50.06720, "lon": 19.94500,
         "tags": {"emergency": "defibrillator", "access": "customers", "indoor": "yes", "level": "1",
                  "defibrillator:location:pl": "galeria handlowa, 1 piętro przy toaletach", "note": FIKCJA}},
        {"type": "node", "id": 900000005, "lat": 50.06400, "lon": 19.94000,
         "tags": {"emergency": "defibrillator", "access": "yes", "indoor": "no", "opening_hours": "24/7",
                  "defibrillator:location:pl": "Planty, przy kiosku", "check_date": "2021-09-14", "note": FIKCJA}},
        {"type": "node", "id": 900000006, "lat": 50.01205, "lon": 19.89010,
         "tags": {"emergency": "defibrillator", "access": "yes", "indoor": "no", "opening_hours": "24/7",
                  "operator": "OSP", "defibrillator:location:pl": "elewacja remizy", "note": FIKCJA}},
    ],
}

MAP_OSM = {
    "wersja": "1.0",
    "opis": "OpenStreetMap (Overpass JSON / GeoJSON OpenAEDMap) → wzorzec. Licencja ODbL: rekordy służą tylko do porównania "
            "i wykrywania braków – nie trafiają do zbioru krajowego CC0.",
    "licencja_zrodla": "ODbL-1.0",
    "kolumny": {
        "id_zrodlowe": {"z": ["@id", "@osm_id"]},
        "nazwa_lokalizacji": {"z": ["name", "defibrillator:location:pl", "operator"]},
        "opis_lokalizacji": {"z": ["defibrillator:location:pl", "defibrillator:location", "description"]},
        "szerokosc_geograficzna": {"z": "__lat"}, "dlugosc_geograficzna": {"z": "__lon"},
        "miejscowosc": {"z": "addr:city"}, "kod_pocztowy": {"z": "addr:postcode"},
        "nazwa_ulicy": {"z": "addr:street"}, "numer_budynku": {"z": "addr:housenumber"},
        "wewnatrz_budynku": {"z": "indoor", "mapa": {"yes": "true", "no": "false"}},
        "kondygnacja": {"z": "level"},
        "typ_dostepu": {"z": "access", "mapa": {"yes": "publiczny", "permissive": "publiczny", "customers": "ograniczony",
                                                "permit": "ograniczony", "private": "prywatny", "no": "prywatny"}},
        "godziny_dostepnosci": {"z": "opening_hours"},
        "dostepny_24_7": {"z": "opening_hours", "mapa": {"24/7": "true", "*": "false"}},
        "dysponent_nazwa": {"z": "operator"},
        "data_weryfikacji": {"z": "check_date"},
        "status_urzadzenia": {"stala": "nieznany"},
        "zrodlo_danych": {"stala": "openstreetmap"},
        "poziom_weryfikacji": {"stala": "niezweryfikowany"},
        "uwagi": {"z": "note"},
    },
}

# --------------------------------------------------------------------------- #
# 02 – bank: eksport z systemu zarządzania placówkami (zagnieżdżony JSON)
# --------------------------------------------------------------------------- #
BANK = {
    "system": "FM-Placówki v4 (PRZYKŁAD)",
    "wygenerowano": "2026-11-20T23:00:00+01:00",
    "organizacja": {"nazwa": "Bank Przykład S.A.", "organizacja_id": "bank-przyklad"},
    "uwagi": FIKCJA,
    "placowki": [
        {"kod": "KR-001", "nazwa": "Oddział Kraków Rynek",
         "adres": {"ulica": "Rynek Główny", "nr": "30", "kod": "31-010", "miasto": "Kraków"},
         "geo": {"lat": 50.06155, "lng": 19.93810},
         "godziny": {"pn": "09:00-17:00", "wt": "09:00-17:00", "sr": "09:00-17:00", "cz": "09:00-17:00", "pt": "09:00-17:00",
                     "sb": None, "nd": None},
         "urzadzenia": [
             {"nr_inwentarzowy": "AED-KR-001-1", "producent": "Philips", "model": "HeartStart FRx", "nr_seryjny": "PRZ-FRX-0001",
              "lokalizacja": "hol kasowy, przy wejściu, szafka z alarmem", "dla_klientow": True, "szafka": "alarm",
              "elektrody_waznosc": "2027-03", "bateria_waznosc": "2029-01", "przeglad": "2026-10-05", "elektrody_dzieciece": False},
         ]},
        {"kod": "KR-002", "nazwa": "Centrum Biznesowe Kraków Pawia",
         "adres": {"ulica": "ul. Pawia", "nr": "5", "kod": "31-154", "miasto": "Kraków"},
         "geo": {"lat": 50.06690, "lng": 19.94390},
         "godziny": {"pn": "08:00-19:00", "wt": "08:00-19:00", "sr": "08:00-19:00", "cz": "08:00-19:00", "pt": "08:00-19:00",
                     "sb": "09:00-14:00", "nd": None},
         "urzadzenia": [
             {"nr_inwentarzowy": "AED-KR-002-1", "producent": "ZOLL", "model": "AED Plus", "nr_seryjny": "PRZ-ZOLL-0002",
              "lokalizacja": "parter, recepcja", "dla_klientow": True, "szafka": "alarm",
              "elektrody_waznosc": "2028-06", "bateria_waznosc": "2030-02", "przeglad": "2026-09-12", "elektrody_dzieciece": True},
             {"nr_inwentarzowy": "AED-KR-002-2", "producent": "ZOLL", "model": "AED Plus", "nr_seryjny": "PRZ-ZOLL-0003",
              "lokalizacja": "3 piętro, strefa biurowa (tylko pracownicy)", "dla_klientow": False, "szafka": "brak",
              "elektrody_waznosc": "2028-06", "bateria_waznosc": "2030-02", "przeglad": "2026-09-12", "elektrody_dzieciece": False},
         ]},
        {"kod": "KR-003", "nazwa": "Oddział Kraków Nowa Huta",
         "adres": {"ulica": "os. Centrum B", "nr": "1", "kod": "31-927", "miasto": "Kraków"},
         "geo": {"lat": 50.07170, "lng": 20.03780},
         "godziny": {"pn": "09:00-16:00", "wt": "09:00-16:00", "sr": "09:00-16:00", "cz": "09:00-16:00", "pt": "09:00-16:00",
                     "sb": None, "nd": None},
         "urzadzenia": [
             {"nr_inwentarzowy": "AED-KR-003-1", "producent": "Philips", "model": "HeartStart HS1", "nr_seryjny": "PRZ-HS1-0004",
              "lokalizacja": "sala obsługi klienta, za stanowiskiem kasy", "dla_klientow": True, "szafka": "brak",
              "elektrody_waznosc": "2026-10", "bateria_waznosc": "2028-04", "przeglad": "2025-10-01", "elektrody_dzieciece": False},
         ]},
    ],
}

MAP_BANK = {
    "wersja": "1.0",
    "opis": "System placówek Banku Przykład (zagnieżdżony JSON: placówka → lista urządzeń) → wzorzec. " + FIKCJA,
    "organizacja_id": "bank-przyklad",
    "wejscie": {"format": "json", "sciezka": "placowki", "rozwin": "urzadzenia",
                "opis": "Każde urządzenie z listy 'urzadzenia' staje się osobnym rekordem; pola placówki są kopiowane."},
    "przeksztalcenia": {
        "__godziny": {"funkcja": "godziny_z_dni", "z": "godziny", "opis": "{pn: '09:00-17:00', …} → 'Mo-Fr 09:00-17:00'"},
        "__elektrody": {"funkcja": "miesiac_na_date", "z": "urzadzenia.elektrody_waznosc", "opis": "'2027-03' → '2027-03-31'"},
        "__bateria": {"funkcja": "miesiac_na_date", "z": "urzadzenia.bateria_waznosc"},
        "__data_eksportu": {"funkcja": "data_z_czasu", "z": "^wygenerowano"},
    },
    "nr_seryjny": {"z": "urzadzenia.nr_seryjny"},
    "kolumny": {
        "id_zrodlowe": {"z": "urzadzenia.nr_inwentarzowy"},
        "nazwa_lokalizacji": {"z": "nazwa"},
        "cecha_ulicy": {"z": "adres.ulica", "regex": "^(ul\\.|al\\.|os\\.|pl\\.|Rynek)", "mapa": {"Rynek": "rynek"}},
        "nazwa_ulicy": {"z": "adres.ulica", "regex": "^(?:ul\\.|al\\.|os\\.|pl\\.)?\\s*(.+)$"},
        "numer_budynku": {"z": "adres.nr"},
        "kod_pocztowy": {"z": "adres.kod"},
        "miejscowosc": {"z": "adres.miasto"},
        "szerokosc_geograficzna": {"z": "geo.lat"},
        "dlugosc_geograficzna": {"z": "geo.lng"},
        "opis_lokalizacji": {"z": "urzadzenia.lokalizacja"},
        "wewnatrz_budynku": {"stala": "true"},
        "typ_dostepu": {"z": "urzadzenia.dla_klientow", "mapa": {"true": "ograniczony", "false": "prywatny"}},
        "dostepny_24_7": {"stala": "false"},
        "godziny_dostepnosci": {"z": "__godziny"},
        "zabezpieczenie": {"z": "urzadzenia.szafka", "mapa": {"alarm": "szafka_z_alarmem", "brak": "brak"}},
        "status_urzadzenia": {"stala": "sprawny"},
        "producent": {"z": "urzadzenia.producent"},
        "model": {"z": "urzadzenia.model"},
        "elektrody_pediatryczne": {"z": "urzadzenia.elektrody_dzieciece"},
        "data_waznosci_elektrod": {"z": "__elektrody"},
        "data_waznosci_baterii": {"z": "__bateria"},
        "data_ostatniego_przegladu": {"z": "urzadzenia.przeglad"},
        "dysponent_nazwa": {"z": "^organizacja.nazwa"},
        "zrodlo_danych": {"stala": "dysponent"},
        "poziom_weryfikacji": {"stala": "zweryfikowany_przez_dysponenta"},
        "data_weryfikacji": {"z": "__data_eksportu"},
        "uwagi": {"z": "^uwagi"},
    },
}

# --------------------------------------------------------------------------- #
# 04 – pojedyncze sklepy: zgłoszenia z formularza www „Dodaj swoje AED”
# --------------------------------------------------------------------------- #
FORMULARZ = {
    "formularz": "Dodaj swoje AED – wersja 1 (PRZYKŁAD)",
    "eksport": "2026-11-21T07:00:00+01:00",
    "uwagi": FIKCJA,
    "zgloszenia": [
        {"id_zgloszenia": "F-2026-0042", "wyslano": "2026-11-18T19:22:31+01:00",
         "sklep": {"firma": "Apteka Pod Przykładem s.c.", "nazwa": "Apteka Pod Przykładem",
                   "adres_tekst": "ul. Długa 20, 31-146 Kraków",
                   "link_mapy": "https://www.openstreetmap.org/?mlat=50.07030&mlon=19.93750#map=19/50.07030/19.93750"},
         "aed": {"gdzie": "za ladą, na ścianie obok kasy", "godziny_tekst": "pn-pt 8-20, sob 9-14", "zamkniety": True,
                 "kto_ma_klucz": "farmaceuta na zmianie", "dziala": "tak", "model": "nie wiem"},
         "kontakt": {"imie_nazwisko": "Jan Przykładowy", "telefon": "600 000 001", "email": "apteka@przyklad.example"},
         "zgoda_licencja_cc0": True, "zdjecie_dolaczone": True},
        {"id_zgloszenia": "F-2026-0043", "wyslano": "2026-11-19T06:05:12+01:00",
         "sklep": {"firma": "Piekarnia Przykład Sp. z o.o.", "nazwa": "Piekarnia Przykład",
                   "adres_tekst": "Kalwaryjska 40 30-504 Kraków",
                   "link_mapy": "https://www.google.com/maps/place/@50.04501,19.94812,19z"},
         "aed": {"gdzie": "przy wejściu, biała szafka", "godziny_tekst": "pon.-sob. 6:00-18:00", "zamkniety": False,
                 "kto_ma_klucz": "", "dziala": "nie wiem", "model": ""},
         "kontakt": {"imie_nazwisko": "Anna Przykład", "telefon": "+48 600 000 002", "email": ""},
         "zgoda_licencja_cc0": True, "zdjecie_dolaczone": False},
        {"id_zgloszenia": "F-2026-0044", "wyslano": "2026-11-20T23:48:00+01:00",
         "sklep": {"firma": "Stacja Paliw Przykład", "nazwa": "Stacja paliw Przykład – Konopnickiej",
                   "adres_tekst": "ul. Konopnickiej 100, 30-302 Kraków",
                   "link_mapy": "https://www.openstreetmap.org/?mlat=50.03100&mlon=19.93000"},
         "aed": {"gdzie": "wewnątrz, przy kasie", "godziny_tekst": "całą dobę", "zamkniety": False,
                 "kto_ma_klucz": "", "dziala": "tak", "model": "ZOLL AED Plus"},
         "kontakt": {"imie_nazwisko": "Piotr Przykładny", "telefon": "600 000 003", "email": ""},
         "zgoda_licencja_cc0": False, "zdjecie_dolaczone": False},
    ],
}

MAP_FORMULARZ = {
    "wersja": "1.0",
    "opis": "Formularz www dla pojedynczych sklepów i punktów usługowych → wzorzec. Adres w jednym polu, położenie z linku do mapy, "
            "godziny opisane słowami. Dane osobowe z sekcji 'kontakt' NIE są przenoszone (RODO). " + FIKCJA,
    "wejscie": {"format": "json", "sciezka": "zgloszenia"},
    "warunek_publikacji": {"pole": "zgoda_licencja_cc0", "wartosc": "true",
                           "komunikat": "brak zgody na licencję CC0 – rekord wstrzymany do kontaktu z dysponentem"},
    "pomin_dane_osobowe": ["kontakt.imie_nazwisko", "kontakt.telefon", "kontakt.email"],
    "przeksztalcenia": {
        "__lat": {"funkcja": "szerokosc_z_linku", "z": "sklep.link_mapy"},
        "__lon": {"funkcja": "dlugosc_z_linku", "z": "sklep.link_mapy"},
        "__godziny": {"funkcja": "godziny_z_tekstu", "z": "aed.godziny_tekst",
                      "opis": "'pn-pt 8-20, sob 9-14' → 'Mo-Fr 08:00-20:00; Sa 09:00-14:00'"},
        "__data": {"funkcja": "data_z_czasu", "z": "wyslano"},
    },
    "kolumny": {
        "id_zrodlowe": {"z": "id_zgloszenia"},
        "nazwa_lokalizacji": {"z": "sklep.nazwa"},
        "cecha_ulicy": {"z": "sklep.adres_tekst", "regex": "^(ul\\.|al\\.|os\\.|pl\\.)"},
        "nazwa_ulicy": {"z": "sklep.adres_tekst", "regex": "^(?:ul\\.|al\\.|os\\.|pl\\.)?\\s*([^\\d,]+?)\\s+\\d"},
        "numer_budynku": {"z": "sklep.adres_tekst", "regex": "^[^\\d]+?\\s(\\d+[A-Za-z]?)\\b"},
        "kod_pocztowy": {"z": "sklep.adres_tekst", "regex": "(\\d{2}-\\d{3})"},
        "miejscowosc": {"z": "sklep.adres_tekst", "regex": "\\d{2}-\\d{3}\\s+(.+)$"},
        "szerokosc_geograficzna": {"z": "__lat"},
        "dlugosc_geograficzna": {"z": "__lon"},
        "opis_lokalizacji": {"z": "aed.gdzie"},
        "wewnatrz_budynku": {"stala": "true"},
        "typ_dostepu": {"stala": "ograniczony"},
        "godziny_dostepnosci": {"z": "__godziny"},
        "dostepny_24_7": {"z": "__godziny", "mapa": {"24/7": "true", "*": "false"}},
        "zabezpieczenie": {"z": "aed.zamkniety", "mapa": {"true": "zamkniety_na_klucz", "false": "szafka_otwarta"}},
        "instrukcja_dostepu": {"z": "aed.kto_ma_klucz", "regex": "^(.+)$"},
        "status_urzadzenia": {"z": "aed.dziala", "mapa": {"tak": "sprawny", "nie": "niesprawny", "*": "nieznany"}},
        "dysponent_nazwa": {"z": "sklep.firma"},
        "zrodlo_danych": {"stala": "dysponent"},
        "poziom_weryfikacji": {"stala": "zweryfikowany_przez_dysponenta"},
        "data_weryfikacji": {"z": "__data"},
        "uwagi": {"z": "^uwagi"},
    },
}

# --------------------------------------------------------------------------- #
# 05 – małe instytucje: zestawienie zebrane przez koordynatora gminy
# --------------------------------------------------------------------------- #
GMINA = {
    "zebrano_przez": "Wydział Bezpieczeństwa – koordynator AED (PRZYKŁAD)",
    "data_zebrania": "15.11.2026",
    "gmina": "Kraków (PRZYKŁAD – jednostki fikcyjne)",
    "uwagi": FIKCJA,
    "jednostki": [
        {"Lp": 1, "Jednostka": "Szkoła Podstawowa nr 999 (PRZYKŁAD)", "Typ": "szkoła",
         "Adres": "ul. Przykładowa 1, 30-001 Kraków", "Współrzędne": "50,08500; 19,92000",
         "Gdzie wisi AED": "hol główny przy portierni", "Dostęp": "w godzinach pracy", "Godziny": "pn-pt 7:30-16:00",
         "Szafka": "z alarmem", "Sprawny": "tak", "Data przeglądu": "12.03.2026", "Elektrody ważne do": "03/2027",
         "Elektrody dziecięce": "TAK", "Model": "ZOLL AED Plus", "Nr seryjny": "PRZ-ZOLL-0101",
         "Osoba odpowiedzialna": "Anna Przykładowa, tel. 600 100 200"},
        {"Lp": 2, "Jednostka": "Przedszkole nr 998 (PRZYKŁAD)", "Typ": "przedszkole",
         "Adres": "ul. Wzorcowa 12, 30-002 Kraków", "Współrzędne": "50,05600; 19,90500",
         "Gdzie wisi AED": "pokój nauczycielski, 1 piętro", "Dostęp": "w godzinach pracy", "Godziny": "pn-pt 6:30-17:00",
         "Szafka": "zamknięta na klucz", "Sprawny": "tak", "Data przeglądu": "02.12.2025", "Elektrody ważne do": "11/2026",
         "Elektrody dziecięce": "TAK", "Model": "Philips HeartStart FRx", "Nr seryjny": "PRZ-FRX-0103",
         "Osoba odpowiedzialna": "dyrektor"},
        {"Lp": 3, "Jednostka": "OSP Przykładowo (PRZYKŁAD)", "Typ": "OSP",
         "Adres": "ul. Strażacka 5, 30-899 Kraków", "Współrzędne": "50,01200; 19,89000",
         "Gdzie wisi AED": "elewacja remizy, przy bramie garażowej", "Dostęp": "całodobowo – szafka na zewnątrz", "Godziny": "",
         "Szafka": "z alarmem", "Sprawny": "tak", "Data przeglądu": "20.05.2026", "Elektrody ważne do": "08/2028",
         "Elektrody dziecięce": "NIE", "Model": "Philips HeartStart FRx", "Nr seryjny": "PRZ-FRX-0102",
         "Osoba odpowiedzialna": "naczelnik OSP"},
        {"Lp": 4, "Jednostka": "Biblioteka – filia nr 7 (PRZYKŁAD)", "Typ": "biblioteka",
         "Adres": "ul. Książkowa 7, 31-003 Kraków", "Współrzędne": "50,09500; 19,96000",
         "Gdzie wisi AED": "wypożyczalnia, na ścianie przy ladzie", "Dostęp": "w godzinach pracy", "Godziny": "wt-sob 10-18",
         "Szafka": "brak", "Sprawny": "nie wiem", "Data przeglądu": "", "Elektrody ważne do": "brak danych",
         "Elektrody dziecięce": "", "Model": "", "Nr seryjny": "", "Osoba odpowiedzialna": "kierownik filii"},
        {"Lp": 5, "Jednostka": "Hala sportowa klubu Przykład (PRZYKŁAD)", "Typ": "klub sportowy",
         "Adres": "ul. Sportowa 3, 30-004 Kraków", "Współrzędne": "",
         "Gdzie wisi AED": "korytarz przy szatniach", "Dostęp": "w godzinach pracy", "Godziny": "pn-nd 8-22",
         "Szafka": "z alarmem", "Sprawny": "tak", "Data przeglądu": "01.09.2026", "Elektrody ważne do": "09/2028",
         "Elektrody dziecięce": "NIE", "Model": "", "Nr seryjny": "",
         "Osoba odpowiedzialna": "Tomasz Przykładowy, tel. 600 100 300"},
    ],
}

MAP_GMINA = {
    "wersja": "1.0",
    "opis": "Zestawienie AED w jednostkach gminy (szkoły, przedszkola, OSP, biblioteki, kluby) zebrane przez koordynatora → wzorzec. "
            "Polskie nagłówki, przecinek dziesiętny, daty dd.mm.rrrr, ważność elektrod jako mm/rrrr. "
            "Kolumna 'Osoba odpowiedzialna' NIE jest przenoszona (RODO). " + FIKCJA,
    "wejscie": {"format": "json", "sciezka": "jednostki"},
    "pomin_dane_osobowe": ["Osoba odpowiedzialna"],
    "przeksztalcenia": {
        "__godziny": {"funkcja": "godziny_z_tekstu", "z": "Godziny"},
        "__elektrody": {"funkcja": "miesiac_na_date", "z": "Elektrody ważne do", "opis": "'03/2027' → '2027-03-31'"},
    },
    "nr_seryjny": {"z": "Nr seryjny"},
    "kolumny": {
        "id_zrodlowe": {"z": "Lp"},
        "nazwa_lokalizacji": {"z": "Jednostka"},
        "cecha_ulicy": {"z": "Adres", "regex": "^(ul\\.|al\\.|os\\.|pl\\.)"},
        "nazwa_ulicy": {"z": "Adres", "regex": "^(?:ul\\.|al\\.|os\\.|pl\\.)?\\s*([^\\d,]+?)\\s+\\d"},
        "numer_budynku": {"z": "Adres", "regex": "^[^\\d]+?\\s(\\d+[A-Za-z]?)\\b"},
        "kod_pocztowy": {"z": "Adres", "regex": "(\\d{2}-\\d{3})"},
        "miejscowosc": {"z": "Adres", "regex": "\\d{2}-\\d{3}\\s+(.+)$"},
        "szerokosc_geograficzna": {"z": "Współrzędne", "regex": "^\\s*([\\d.,]+)\\s*;"},
        "dlugosc_geograficzna": {"z": "Współrzędne", "regex": ";\\s*([\\d.,]+)\\s*$"},
        "opis_lokalizacji": {"z": "Gdzie wisi AED"},
        "wewnatrz_budynku": {"z": "Dostęp", "mapa": {"całodobowo – szafka na zewnątrz": "false", "*": "true"}},
        "typ_dostepu": {"z": "Dostęp", "mapa": {"całodobowo – szafka na zewnątrz": "publiczny", "*": "ograniczony"}},
        "dostepny_24_7": {"z": "Dostęp", "mapa": {"całodobowo – szafka na zewnątrz": "true", "*": "false"}},
        "godziny_dostepnosci": {"z": "__godziny"},
        "zabezpieczenie": {"z": "Szafka", "mapa": {"z alarmem": "szafka_z_alarmem", "zamknięta na klucz": "zamkniety_na_klucz",
                                                   "brak": "brak"}},
        "status_urzadzenia": {"z": "Sprawny", "mapa": {"tak": "sprawny", "nie": "niesprawny", "*": "nieznany"}},
        "model": {"z": "Model"},
        "elektrody_pediatryczne": {"z": "Elektrody dziecięce"},
        "data_waznosci_elektrod": {"z": "__elektrody"},
        "data_ostatniego_przegladu": {"z": "Data przeglądu"},
        "dysponent_nazwa": {"z": "Jednostka"},
        "zrodlo_danych": {"stala": "rejestr_publiczny"},
        "poziom_weryfikacji": {"stala": "zweryfikowany_przez_dysponenta"},
        "data_weryfikacji": {"z": "^data_zebrania"},
        "uwagi": {"z": "^uwagi"},
    },
}

# --------------------------------------------------------------------------- #
# 06 – serwis: protokoły przeglądów + telemetria producenta
# --------------------------------------------------------------------------- #
SERWIS = {
    "firma": "AED-Tech Serwis Sp. z o.o. (PRZYKŁAD)",
    "organizacja_id": "aedtech-serwis",
    "eksport": "2026-11-21T08:00:00+01:00",
    "uwagi": FIKCJA + ". Urządzenia identyfikowane numerem seryjnym; id_aed tylko gdy technik zeskanował naklejkę.",
    "protokoly": [
        {"nr": "SRV/2026/2001", "data": "2026-11-19", "technik": "T-07",
         "urzadzenie": {"nr_seryjny": "PRZ-ZOLL-0101", "model": "ZOLL AED Plus", "id_aed_z_naklejki": None},
         "lokalizacja_tekst": "SP nr 999, hol", "wynik": "sprawny",
         "czynnosci": ["wymiana elektrod", "test samokontroli – OK"],
         "elektrody_do": "2029-05-31", "bateria_do": "2030-01-31", "nastepny_przeglad": "2027-11-19"},
        {"nr": "SRV/2026/2002", "data": "2026-11-20", "technik": "T-03",
         "urzadzenie": {"nr_seryjny": "PRZ-HS1-0004", "model": "Philips HeartStart HS1", "id_aed_z_naklejki": None},
         "lokalizacja_tekst": "Bank, Nowa Huta", "wynik": "wymaga_serwisu",
         "czynnosci": ["kontrola – elektrody przeterminowane (10/2026)"],
         "uwagi": "Elektrody zamówione, wymiana do 2026-11-27", "elektrody_do": None, "bateria_do": None},
        {"nr": "SRV/2026/2003", "data": "2026-11-20", "technik": "T-03",
         "urzadzenie": {"nr_seryjny": "PRZ-XYZ-9999", "model": "nieznany", "id_aed_z_naklejki": None},
         "lokalizacja_tekst": "Klient indywidualny – lokal usługowy", "wynik": "sprawny",
         "czynnosci": ["przegląd okresowy"], "elektrody_do": "2028-01-31", "bateria_do": "2029-01-31"},
    ],
}

TELEMETRIA = {
    "platforma": "Zdalny monitoring AED producenta (PRZYKŁAD)",
    "format": "raport dobowy z autotestu, wysyłany przez modem LTE urządzenia",
    "uwagi": FIKCJA,
    "raporty": [
        {"nr_seryjny": "PRZ-FRX-0102", "czas": "2026-11-21T03:00:00Z", "autotest": "BLAD", "kod_bledu": "E-BAT-LOW",
         "bateria_proc": 12, "elektrody_waznosc": "2028-08-31", "temperatura_c": -9, "polaczenie": "LTE"},
        {"nr_seryjny": "PRZ-FRX-0001", "czas": "2026-11-21T03:00:00Z", "autotest": "OK", "kod_bledu": None,
         "bateria_proc": 87, "elektrody_waznosc": "2027-03-31", "temperatura_c": 21, "polaczenie": "LTE"},
        {"nr_seryjny": "PRZ-ZOLL-0002", "czas": "2026-11-21T03:00:00Z", "autotest": "OK", "kod_bledu": None,
         "bateria_proc": 95, "elektrody_waznosc": "2028-06-30", "temperatura_c": 22, "polaczenie": "WiFi"},
    ],
}

# --------------------------------------------------------------------------- #
# 07 – ZRM / dyspozytor medyczny: zdarzenia z systemu dyspozytorskiego
# --------------------------------------------------------------------------- #
SWD = {
    "specversion": "1.0",
    "source": "swd-prm/przyklad",
    "opis": "Strumień zdarzeń w stylu CloudEvents. Bez danych pacjenta: tylko numer zdarzenia, czas i położenie AED. " + FIKCJA,
    "zdarzenia": [
        {"id": "ev-0001", "type": "pl.prm.aed.uzyty", "time": "2026-11-21T09:15:00+01:00",
         "data": {"numer_zdarzenia": "PRZYKLAD-2026-000501", "zespol": "ZRM typu P (PRZYKŁAD)",
                  "aed": {"lat": 50.06157, "lon": 19.93812, "opis": "bank, Rynek Główny"},
                  "elektrody_zuzyte": True, "aed_pozostawiony_na_miejscu": True}},
        {"id": "ev-0002", "type": "pl.prm.aed.niedostepny", "time": "2026-11-20T22:40:00+01:00",
         "data": {"numer_zdarzenia": "PRZYKLAD-2026-000502", "zrodlo_informacji": "dyspozytor medyczny – relacja świadka",
                  "aed": {"lat": 50.07031, "lon": 19.93751, "opis": "apteka, ul. Długa"},
                  "powod": "obiekt zamknięty, AED za ladą – świadek nie uzyskał dostępu"}},
        {"id": "ev-0003", "type": "pl.prm.aed.zabrany_przez_zrm", "time": "2026-11-21T11:30:00+01:00",
         "data": {"numer_zdarzenia": "PRZYKLAD-2026-000507", "zespol": "ZRM typu S (PRZYKŁAD)",
                  "aed": {"lat": 50.06772, "lon": 19.94762, "opis": "dworzec Kraków Główny, hala"},
                  "opis": "AED podłączony do pacjenta, przekazany wraz z pacjentem do SOR", "przewidywany_zwrot": "2026-11-22"}},
    ],
}

# --------------------------------------------------------------------------- #
# 08 – przewoźnik miejski (wzorowane na komunikacji w Krakowie)
# --------------------------------------------------------------------------- #
PRZEWOZNIK = {
    "przewoznik": {"nazwa": "Miejski Przewoźnik Przykład – Kraków (PRZYKŁAD)", "organizacja_id": "przewoznik-krakow-przyklad"},
    "wygenerowano": "2026-11-21T06:00:00+01:00",
    "uwagi": FIKCJA + ". Rozkład GTFS i pozycje pojazdów to prawdziwe, otwarte dane ZTP Kraków; przypisanie AED do pojazdów jest zmyślone.",
    "aed_stacjonarne": [
        {"id": "MPP-S-01", "miejsce": "Zajezdnia tramwajowa (PRZYKŁAD) – portiernia",
         "adres": "ul. Zajezdniowa 1, 30-701 Kraków", "lat": 50.03000, "lon": 19.98500,
         "godziny": "24/7", "dostep": "publiczny", "zabezpieczenie": "brak", "instrukcja": "AED wydaje portier – całą dobę"},
        {"id": "MPP-S-02", "miejsce": "Punkt Obsługi Pasażera (PRZYKŁAD)",
         "adres": "ul. Biletowa 2, 30-702 Kraków", "lat": 50.03500, "lon": 19.97000,
         "godziny": "Mo-Fr 07:00-19:00", "dostep": "ograniczony", "zabezpieczenie": "szafka_z_alarmem", "instrukcja": ""},
    ],
    "aed_w_pojazdach": {
        "opis": "AED w kabinie motorniczego w części tramwajów",
        "typ_pojazdow": "tramwaj", "liczba_aed": 40, "liczba_pojazdow": 200,
        "linie": ["1", "4", "8", "13", "52"],
        "godziny": "Mo-Su 05:00-23:30",
        "jak_uzyskac": "Zatrzymaj tramwaj lub podejdź do kabiny motorniczego – motorniczy poda AED i wezwie 112",
        "gtfs": "https://gtfs.ztp.krakow.pl/GTFS_KRK_T.zip",
        "gtfs_rt": "https://gtfs.ztp.krakow.pl/VehiclePositions_T.pb",
        "pojazdy": [
            {"nr_taborowy": "PRZ-301", "aed_model": "ZOLL AED Plus", "elektrody_do": "2028-02"},
            {"nr_taborowy": "PRZ-302", "aed_model": "ZOLL AED Plus", "elektrody_do": "2028-02"},
            {"nr_taborowy": "PRZ-415", "aed_model": "Philips HeartStart FRx", "elektrody_do": "2027-07"},
        ],
    },
    "obszar_obslugi": {"type": "Polygon", "coordinates": [[[19.85, 49.99], [20.10, 49.99], [20.10, 50.11], [19.85, 50.11], [19.85, 49.99]]]},
}

MAP_PRZEWOZNIK = {
    "wersja": "1.0",
    "opis": "Przewoźnik miejski → AED stacjonarne (zajezdnie, punkty obsługi) do tabeli punktów; AED w pojazdach → tabela aed_obszarowe "
            "(flota_pojazdow, obszar obsługi + GTFS). " + FIKCJA,
    "organizacja_id": "przewoznik-krakow-przyklad",
    "wejscie": {"format": "json", "sciezka": "aed_stacjonarne"},
    "przeksztalcenia": {"__data": {"funkcja": "data_z_czasu", "z": "^wygenerowano"}},
    "kolumny": {
        "id_zrodlowe": {"z": "id"},
        "nazwa_lokalizacji": {"z": "miejsce"},
        "cecha_ulicy": {"z": "adres", "regex": "^(ul\\.|al\\.|os\\.|pl\\.)"},
        "nazwa_ulicy": {"z": "adres", "regex": "^(?:ul\\.|al\\.|os\\.|pl\\.)?\\s*([^\\d,]+?)\\s+\\d"},
        "numer_budynku": {"z": "adres", "regex": "^[^\\d]+?\\s(\\d+[A-Za-z]?)\\b"},
        "kod_pocztowy": {"z": "adres", "regex": "(\\d{2}-\\d{3})"},
        "miejscowosc": {"z": "adres", "regex": "\\d{2}-\\d{3}\\s+(.+)$"},
        "szerokosc_geograficzna": {"z": "lat"}, "dlugosc_geograficzna": {"z": "lon"},
        "opis_lokalizacji": {"z": "miejsce"},
        "wewnatrz_budynku": {"stala": "true"},
        "typ_dostepu": {"z": "dostep"},
        "godziny_dostepnosci": {"z": "godziny"},
        "dostepny_24_7": {"z": "godziny", "mapa": {"24/7": "true", "*": "false"}},
        "zabezpieczenie": {"z": "zabezpieczenie"},
        "instrukcja_dostepu": {"z": "instrukcja"},
        "status_urzadzenia": {"stala": "sprawny"},
        "dysponent_nazwa": {"z": "^przewoznik.nazwa"},
        "zrodlo_danych": {"stala": "dysponent"},
        "poziom_weryfikacji": {"stala": "zweryfikowany_przez_dysponenta"},
        "data_weryfikacji": {"z": "__data"},
        "uwagi": {"z": "^uwagi"},
    },
}

# --------------------------------------------------------------------------- #
# 09 – kolej: dworce, odcinki linii i pociągi z AED
# --------------------------------------------------------------------------- #
KOLEJ = {
    "zarzadca": {"nazwa": "Zarządca Dworców i Linii PRZYKŁAD", "organizacja_id": "kolej-przyklad"},
    "wygenerowano": "2026-11-21T05:00:00+01:00",
    "uwagi": FIKCJA + ". Położenie dworców jest prawdziwe, urządzenia i kilometraż są przykładowe.",
    "dworce": [
        {"stacja": "Kraków Główny", "linia": "91", "km": "0,000",
         "adres": {"ulica": "pl. Jana Nowaka-Jeziorańskiego", "nr": "3", "kod": "31-154", "miasto": "Kraków"},
         "aed": [
             {"id": "KOL-KRG-1", "miejsce": "hala dworca, przy kasach biletowych", "lat": 50.06770, "lon": 19.94760,
              "godziny": "24/7", "dostep": "publiczny", "zabezpieczenie": "szafka_z_alarmem", "elektrody_do": "2028-04-30"},
             {"id": "KOL-KRG-2", "miejsce": "peron 1, przy wyjściu z przejścia podziemnego", "lat": 50.06700, "lon": 19.94690,
              "godziny": "24/7", "dostep": "publiczny", "zabezpieczenie": "szafka_z_alarmem", "elektrody_do": "2028-04-30"},
         ]},
        {"stacja": "Kraków Płaszów", "linia": "91", "km": "3,700",
         "adres": {"ulica": "ul. Dworcowa", "nr": "1", "kod": "30-001", "miasto": "Kraków"},
         "aed": [
             {"id": "KOL-KPL-1", "miejsce": "budynek dworca, poczekalnia", "lat": 50.03460, "lon": 19.99890,
              "godziny": "Mo-Su 04:30-23:30", "dostep": "publiczny", "zabezpieczenie": "szafka_z_alarmem", "elektrody_do": "2027-12-31"},
         ]},
    ],
    "odcinki_linii": [
        {"id": "PL-AEDO-00091", "linia": "91", "od": "Kraków Główny", "do": "Kraków Płaszów", "bufor_m": 500,
         "geometria": {"type": "LineString", "coordinates": [[19.9476, 50.0677], [19.9600, 50.0560], [19.9800, 50.0430], [19.9989, 50.0346]]},
         "opis": "Najbliższe AED: na stacjach na początku i końcu odcinka; w razie zdarzenia przy torach dzwoń 112 i podaj numer linii i km"},
    ],
    "pociagi_z_aed": [
        {"id": "PL-AEDO-00092", "kategoria": "IC", "oznaczenie": "pociąg PRZYKŁAD 1", "relacja": "Kraków Główny – Warszawa Centralna",
         "liczba_skladow": 6, "liczba_aed": 6, "gdzie": "wagon barowy, przy przedziale kierownika pociągu",
         "jak_uzyskac": "Powiadom kierownika pociągu lub konduktora; dzwoń 112 i podaj numer pociągu i wagonu",
         "geometria": {"type": "LineString", "coordinates": [[19.9476, 50.0677], [20.0, 50.5], [20.5, 51.4], [21.0031, 52.2287]]}},
    ],
}

MAP_KOLEJ = {
    "wersja": "1.0",
    "opis": "Kolej → AED na dworcach i peronach do tabeli punktów (rozwinięcie listy 'aed' każdego dworca); odcinki linii i pociągi "
            "z AED → tabela aed_obszarowe (trasa / flota_pojazdow). " + FIKCJA,
    "organizacja_id": "kolej-przyklad",
    "wejscie": {"format": "json", "sciezka": "dworce", "rozwin": "aed"},
    "przeksztalcenia": {"__data": {"funkcja": "data_z_czasu", "z": "^wygenerowano"}},
    "kolumny": {
        "id_zrodlowe": {"z": "aed.id"},
        "nazwa_lokalizacji": {"z": "stacja"},
        "cecha_ulicy": {"z": "adres.ulica", "regex": "^(ul\\.|al\\.|os\\.|pl\\.)"},
        "nazwa_ulicy": {"z": "adres.ulica", "regex": "^(?:ul\\.|al\\.|os\\.|pl\\.)?\\s*(.+)$"},
        "numer_budynku": {"z": "adres.nr"},
        "kod_pocztowy": {"z": "adres.kod"},
        "miejscowosc": {"z": "adres.miasto"},
        "szerokosc_geograficzna": {"z": "aed.lat"}, "dlugosc_geograficzna": {"z": "aed.lon"},
        "opis_lokalizacji": {"z": "aed.miejsce"},
        "wewnatrz_budynku": {"stala": "true"},
        "typ_dostepu": {"z": "aed.dostep"},
        "godziny_dostepnosci": {"z": "aed.godziny"},
        "dostepny_24_7": {"z": "aed.godziny", "mapa": {"24/7": "true", "*": "false"}},
        "zabezpieczenie": {"z": "aed.zabezpieczenie"},
        "status_urzadzenia": {"stala": "sprawny"},
        "data_waznosci_elektrod": {"z": "aed.elektrody_do"},
        "dysponent_nazwa": {"z": "^zarzadca.nazwa"},
        "zrodlo_danych": {"stala": "dysponent"},
        "poziom_weryfikacji": {"stala": "zweryfikowany_przez_dysponenta"},
        "data_weryfikacji": {"z": "__data"},
        "uwagi": {"z": "^uwagi"},
    },
}

# --------------------------------------------------------------------------- #
# 10 – zgłoszenia obywateli (QR na naklejce, aplikacja)
# --------------------------------------------------------------------------- #
ZGLOSZENIA = {
    "kanal": "naklejka QR „Otwórz AED” / formularz w aplikacji (PRZYKŁAD)",
    "uwagi": FIKCJA + ". Zgłoszenie nie nadpisuje danych dysponenta – trafia do kolejki weryfikacji.",
    "zgloszenia": [
        {"id": "Z-0001", "czas": "2026-11-19T17:02:00+01:00", "kanal": "naklejka_qr", "id_aed_z_naklejki": None,
         "gps": {"lat": 50.06401, "lon": 19.94002, "dokladnosc_m": 15}, "typ": "brak_urzadzenia",
         "opis": "Pusta szafka na Plantach, brak defibrylatora", "zdjecie": True},
        {"id": "Z-0002", "czas": "2026-11-20T08:10:00+01:00", "kanal": "aplikacja", "id_aed_z_naklejki": None,
         "gps": {"lat": 50.05602, "lon": 19.90498, "dokladnosc_m": 8}, "typ": "brak_dostepu_zamkniete",
         "opis": "AED w przedszkolu zamknięty na klucz, obsługa nie wiedziała, gdzie jest klucz", "zdjecie": False},
        {"id": "Z-0003", "czas": "2026-11-20T19:45:00+01:00", "kanal": "aplikacja", "id_aed_z_naklejki": None,
         "gps": {"lat": 50.05600, "lon": 19.93700, "dokladnosc_m": 20}, "typ": "nowy_aed",
         "opis": "AED w holu kina, przy kasach – nie ma go na mapie", "zdjecie": True},
    ],
}


# --------------------------------------------------------------------------- #
# Opisy źródeł (zrodlo.json) – czytane przez demo integracji
# --------------------------------------------------------------------------- #
def opis(id_, nazwa, typ, kto, kanal, czestotliwosc, licencja, do_cc0, pliki, pokazuje):
    return {"id": id_, "nazwa": nazwa, "typ_dostawcy": typ, "przyklady_dostawcow": kto, "kanal": kanal,
            "czestotliwosc": czestotliwosc, "licencja": licencja, "do_zbioru_krajowego": do_cc0, "pliki": pliki,
            "co_pokazuje": pokazuje}


ZRODLA = {
    "00_format_docelowy": opis(
        "00_format_docelowy", "Format docelowy (dysponent publikuje już we wzorcu)", "dysponent / JST",
        "gmina, szpital, uczelnia – każdy, kto wypełni szablon", "plik CSV na dane.gov.pl lub upload w kreatorze", "co najmniej raz na kwartał",
        "CC0-1.0", True,
        [{"plik": "aed_punkty_przyklad.csv", "tabela": "punkty", "preset": "wzorzec"},
         {"plik": "aed_obszarowe_przyklad.csv", "tabela": "obszarowe"},
         {"plik": "organizacje_przyklad.csv", "tabela": "organizacje"}],
        ["plik od razu zgodny ze wzorcem – zero mapowania", "przypadki brzegowe: zamknięty na klucz, przeterminowane elektrody, AED w serwisie"]),
    "01_integrator_osm": opis(
        "01_integrator_osm", "Duży integrator: OpenStreetMap / OpenAEDMap", "integrator (baza społecznościowa)",
        "OpenStreetMap, OpenAEDMap (z nich korzysta CPR 112)", "Overpass API / GeoJSON OpenAEDMap", "codziennie",
        "ODbL-1.0", False,
        [{"plik": "osm_overpass_krakow.json", "tabela": "punkty", "mapowanie": "mapowanie_osm.json"},
         {"plik": "osm_przyklad.geojson", "tabela": "punkty", "mapowanie": "mapowanie_osm.json"}],
        ["licencja ODbL – rekordy tylko do porównania, nie do zbioru CC0", "brak adresu, stanu i daty weryfikacji",
         "punkty, których nie ma nigdzie indziej → kandydaci do weryfikacji"]),
    "02_bank": opis(
        "02_bank", "Bank – sieć placówek", "firma z wieloma lokalizacjami",
        "banki, ubezpieczyciele, operatorzy telekomunikacyjni", "eksport z systemu zarządzania nieruchomościami (JSON) albo CSV",
        "co miesiąc (automatycznie)", "CC0-1.0", True,
        [{"plik": "bank_system_placowek.json", "tabela": "punkty", "mapowanie": "mapowanie_bank_system.json"},
         {"plik": "firma_bank_placowki_wlasny_format.csv", "tabela": "punkty", "mapowanie": "mapowanie_bank_przyklad.json"}],
        ["zagnieżdżony JSON: placówka → kilka urządzeń (dwa AED w jednym budynku to dwa rekordy, nie duplikat)",
         "godziny per dzień tygodnia → opening_hours", "ważność elektrod jako rrrr-mm", "AED tylko dla pracowników → typ prywatny, poza widokiem publicznym"]),
    "03_siec_sklepow": opis(
        "03_siec_sklepow", "Duża sieć sklepów", "duży dostawca (eksport z systemu)",
        "sieci handlowe, stacje paliw, sieci fitness", "plik TSV z systemu (CP1250) + zapisane mapowanie", "co miesiąc",
        "CC0-1.0", True,
        [{"plik": "duzy_dostawca_siec_sklepow_eksport.tsv", "tabela": "punkty", "mapowanie": "mapowanie_siec_sklepow.json"}],
        ["kodowanie CP1250, tabulator", "wiersz z brakami → odrzucony z numerem wiersza i pola"]),
    "04_pojedyncze_sklepy": opis(
        "04_pojedyncze_sklepy", "Pojedyncze sklepy i punkty usługowe", "mały dysponent bez działu IT",
        "apteka, piekarnia, stacja paliw, salon fryzjerski", "formularz www „Dodaj swoje AED” (bez konta)", "jednorazowo + przypomnienie co rok",
        "CC0-1.0 (zgoda w formularzu)", True,
        [{"plik": "formularz_zgloszenia_sklepy.json", "tabela": "punkty", "mapowanie": "mapowanie_formularz.json"}],
        ["adres w jednym polu, położenie z linku do mapy (OSM / Google)", "godziny słowami: 'pn-pt 8-20, sob 9-14'",
         "dane osobowe z formularza są odrzucane (RODO)", "brak zgody na CC0 → rekord wstrzymany"]),
    "05_male_instytucje": opis(
        "05_male_instytucje", "Małe instytucje publiczne (zestawienie gminy)", "JST zbierająca dane od swoich jednostek",
        "szkoły, przedszkola, OSP, biblioteki, kluby sportowe", "arkusz koordynatora gminy (tu jako JSON)", "co pół roku",
        "CC0-1.0", True,
        [{"plik": "jednostki_gminy_zbiorczo.json", "tabela": "punkty", "mapowanie": "mapowanie_gmina.json"}],
        ["przecinek dziesiętny, daty dd.mm.rrrr, elektrody mm/rrrr", "AED w przedszkolu zamknięty na klucz",
         "jednostka bez współrzędnych → odrzucona z podpowiedzią", "kolumna z nazwiskiem osoby odpowiedzialnej pomijana (RODO)"]),
    "06_serwis": opis(
        "06_serwis", "Firma serwisująca i telemetria producenta", "serwis / producent",
        "autoryzowane serwisy AED, platformy zdalnego monitoringu producentów", "API (klucz serwisu) lub CSV aktualizacji",
        "po każdym przeglądzie; telemetria codziennie", "CC0-1.0", True,
        [{"plik": "protokoly_przegladow.json", "tabela": "aktualizacje", "adapter": "protokoly_serwisu"},
         {"plik": "telemetria_producenta.json", "tabela": "aktualizacje", "adapter": "telemetria"},
         {"plik": "aktualizacje_serwis_przyklad.csv", "tabela": "aktualizacje"}],
        ["urządzenie rozpoznawane po numerze seryjnym (nie po adresie)", "autotest z błędem baterii → AED niesprawny bez czekania na przegląd",
         "protokół dla nieznanego urządzenia → kolejka do wyjaśnienia"]),
    "07_zrm_dyspozytor": opis(
        "07_zrm_dyspozytor", "Zespoły ratownictwa medycznego i dyspozytorzy", "służby (SWD PRM / CPR 112)",
        "ZRM, dyspozytorzy medyczni, operatorzy numeru 112", "strumień zdarzeń z systemu dyspozytorskiego (API)", "w czasie rzeczywistym",
        "CC0-1.0 (bez danych pacjenta)", True,
        [{"plik": "zdarzenia_swd_prm.json", "tabela": "aktualizacje", "adapter": "swd_prm"},
         {"plik": "aktualizacje_zrm_112_przyklad.csv", "tabela": "aktualizacje"}],
        ["AED użyty → elektrody zużyte → niegotowy do wymiany", "świadek nie dostał się do AED w nocy → sygnał dla dysponenta",
         "ZRM zabrał AED z pacjentem → czasowo niedostępny", "zdarzenie wiązane z AED po położeniu (do 50 m)"]),
    "08_przewoznik_miejski": opis(
        "08_przewoznik_miejski", "Przewoźnik miejski (AED w pojazdach i zajezdniach)", "przewoźnik",
        "MPK, ZTM, MZK – np. komunikacja miejska w Krakowie, Szczecinie, Wrocławiu", "JSON z systemu przewoźnika + GTFS / GTFS-RT",
        "przy zmianie floty; pozycje pojazdów na żywo", "CC0-1.0", True,
        [{"plik": "komunikacja_miejska_przyklad.json", "tabela": "punkty", "mapowanie": "mapowanie_przewoznik.json"},
         {"plik": "komunikacja_miejska_przyklad.json", "tabela": "obszarowe", "adapter": "obszary_przewoznik"}],
        ["AED mobilne: nie punkt, tylko flota i obszar obsługi", "powiązanie z rozkładem GTFS i pozycjami na żywo"]),
    "09_kolej": opis(
        "09_kolej", "Kolej: dworce, linie i pociągi", "zarządca infrastruktury / przewoźnik kolejowy",
        "zarządcy dworców i linii kolejowych, przewoźnicy pasażerscy", "JSON z systemu zarządcy", "co kwartał",
        "CC0-1.0", True,
        [{"plik": "kolej_dworce_linie_pociagi.json", "tabela": "punkty", "mapowanie": "mapowanie_kolej.json"},
         {"plik": "kolej_dworce_linie_pociagi.json", "tabela": "obszarowe", "adapter": "obszary_kolej"}],
        ["dworzec z kilkoma AED (hala, peron) – rozwinięcie listy", "linia kolejowa z buforem: „jesteś przy torach – najbliższe AED są na stacjach”",
         "pociągi z AED jako flota na trasie"]),
    "10_zgloszenia_obywateli": opis(
        "10_zgloszenia_obywateli", "Zgłoszenia obywateli", "obywatel",
        "przechodnie, kursanci pierwszej pomocy, użytkownicy aplikacji", "QR na naklejce „Otwórz AED”, formularz w aplikacji", "na bieżąco",
        "CC0-1.0", True,
        [{"plik": "zgloszenia_qr.json", "tabela": "aktualizacje", "adapter": "zgloszenia_qr"}],
        ["zgłoszenie nie nadpisuje danych dysponenta – obniża pewność i trafia do kolejki",
         "„nowy AED” → kandydat do weryfikacji, nie rekord zbioru"]),
}


def main():
    zapisz("01_integrator_osm", "osm_overpass_krakow.json", OVERPASS)
    zapisz("01_integrator_osm", "mapowanie_osm.json", MAP_OSM)
    zapisz("02_bank", "bank_system_placowek.json", BANK)
    zapisz("02_bank", "mapowanie_bank_system.json", MAP_BANK)
    zapisz("04_pojedyncze_sklepy", "formularz_zgloszenia_sklepy.json", FORMULARZ)
    zapisz("04_pojedyncze_sklepy", "mapowanie_formularz.json", MAP_FORMULARZ)
    zapisz("05_male_instytucje", "jednostki_gminy_zbiorczo.json", GMINA)
    zapisz("05_male_instytucje", "mapowanie_gmina.json", MAP_GMINA)
    zapisz("06_serwis", "protokoly_przegladow.json", SERWIS)
    zapisz("06_serwis", "telemetria_producenta.json", TELEMETRIA)
    zapisz("07_zrm_dyspozytor", "zdarzenia_swd_prm.json", SWD)
    zapisz("08_przewoznik_miejski", "komunikacja_miejska_przyklad.json", PRZEWOZNIK)
    zapisz("08_przewoznik_miejski", "mapowanie_przewoznik.json", MAP_PRZEWOZNIK)
    zapisz("09_kolej", "kolej_dworce_linie_pociagi.json", KOLEJ)
    zapisz("09_kolej", "mapowanie_kolej.json", MAP_KOLEJ)
    zapisz("10_zgloszenia_obywateli", "zgloszenia_qr.json", ZGLOSZENIA)
    for folder, o in ZRODLA.items():
        zapisz(folder, "zrodlo.json", o)
    print("Zapisano warianty źródeł w", D)


if __name__ == "__main__":
    main()
