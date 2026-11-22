# Zmiany w portalu dane.gov.pl: Wykaz AED

Ten plik opisuje wszystkie nasze zmiany w kodzie portalu (`portal/backend`) względem nietkniętego oryginału z commita `a1adc22` („Oryginalny kod portalu dane.gov.pl”). Dokładny diff:

```bash
git diff --stat a1adc22 -- portal/backend
git diff a1adc22 -- portal/backend
```

## W skrócie

Dodaliśmy do portalu **Wykaz AED**, czyli nocny zasób zbiorczy zbudowany na wzór istniejącego wykazu DGA:
- Dostawca oznacza swój zbiór w istniejących „Polach niestandardowych” wpisem `standard = AED`.
- Co noc o 4:15 zadanie Celery zbiera zasoby tabelaryczne z takich zbiorów i sprawdza każdy z nich (licencja, format, kolumny wzorca).
- Zgodne zasoby zadanie scala w jeden CSV o 52 kolumnach, z pochodzeniem każdego wiersza, usuwa duplikaty tego samego urządzenia i publikuje wynik jako zasób w zbiorze „Wykaz defibrylatorów AED – wykaz zbiorczy”.
- Portal sam daje temu zasobowi tabelę, mapę, wyszukiwanie i API, a stały adres aktualnego zasobu zwraca nowy endpoint `/1.4/aed-aggregated`.
- Dostawca spoza dane.gov.pl wystawia na swoim serwerze **opis zbioru w XML** (schemat XSD) z linkiem do pliku CSV i sumą md5. Komenda `import_aed_xml` sprawdza opis, plik i sumę, a dopiero potem tworzy zbiór i zasób w portalu. Co noc o 4:05, przed budową wykazu, zadanie `refresh_aed_opis_task` ponownie pobiera każdy taki opis i przy nowej sumie md5 zastępuje zasób.

## Zasady, których się trzymaliśmy

- **Rozszerzamy, niczego nie usuwamy.**
  - Kod AED jest w nowych plikach obok DGA. Funkcje DGA wielokrotnego użytku (`check_all_resource_validations_status`, wyjątki walidacji, `request_remote_dga`) importujemy, a nie kopiujemy ani przenosimy.
  - W istniejących plikach są tylko dopisane punkty zaczepienia. Jedyna zamieniona linia to sygnatura `get_beat_schedule` w `celeryapp.py`, rozszerzona o parametr opcjonalny z wartością domyślną.
- **Zero migracji.** Nie ma nowych modeli, pól ani tabel. Zbiory rozpoznajemy po istniejącym polu `Dataset.customfields`: `standard = AED` dla zbiorów źródłowych, `zestawienie = AED-krajowe` dla zbioru zbiorczego, a `opis_xml` i `md5` dla zbiorów zaczytanych z opisu XML. `makemigrations --check` zwraca „No changes detected”.
- **DGA działa bez zmian.** Istniejące testy DGA przechodzą bez modyfikacji.
- **Wyłącznik.** Przy `AED_AGGREGATION_ENABLED = False` harmonogram nie ma wpisów AED, oba zadania nic nie robią, a `/aed-aggregated` zwraca 404. Portal działa wtedy jak oryginał.

## Jak działa mechanizm

1. **Oznaczenie zbioru** (`aed_utils.is_aed_dataset`): w `customfields` zbioru jest klucz `standard` z wartością `AED`. Wielkość liter nie ma znaczenia, a wersja po spacji jest dopuszczalna, np. `AED 1.1`. Formularz zbioru w panelu podpowiada, co wpisać.
2. **Wybór zasobów** (`get_aed_source_resources`):
   - zasób i zbiór są opublikowane, a plik i link zasobu przeszły walidację portalu;
   - zbiór ma licencję CC0 1.0 albo CC BY 4.0;
   - zasób ma format tabelaryczny;
   - pozostałe zasoby są pomijane z powodem w logu.

   W odróżnieniu od DGA nie wymagamy udanej walidacji *danych*. Portal zgaduje typy kolumn z pierwszych wierszy i odrzuca pliki zgodne ze wzorcem (np. „5A” w `numer_budynku`), a zgodność ze wzorcem i tak sprawdza agregacja.
3. **Odczyt zasobu** (`get_aed_source_df`):
   - zasoby z CKAN są pobierane spod `resource.link`, jak w DGA;
   - pozostałe są czytane z danych tabelarycznych portalu, a gdy ich brak, wprost z pliku zasobu.
4. **Scalenie** (`aed_aggregation.build_aggregate_rows`, czyste funkcje na `DataFrame`, bez ORM):
   - dopasowanie nagłówków przez aliasy;
   - kontrola kolumn minimum: `nazwa_lokalizacji`, `miejscowosc`, `szerokosc_geograficzna`, `dlugosc_geograficzna`;
   - pominięcie wierszy z OpenStreetMap (ODbL), bez współrzędnych albo z punktem poza Polską;
   - naprawa zamienionych osi;
   - nadanie stałego `id_aed`;
   - jawne wartości domyślne, np. status `nieznany`, a nie „sprawny”;
   - `wymaga_przegladu` z dat ważności elektrod, baterii i przeglądu;
   - usunięcie telefonu i e-maila, gdy zbiór źródłowy deklaruje dane osobowe;
   - kolumny pochodzenia: wydawca, licencja, id i URL zasobu źródłowego, data danych, data agregacji;
   - kody `przetworzenie` opisujące, co portal zmienił w wierszu.
5. **Deduplikacja** (`aed_dedup.deduplicate_rows`, wywołana w `create_main_aed_df`): to samo urządzenie zgłoszone przez dwóch dostawców trafia do wykazu raz. Reguły opisuje sekcja „Deduplikacja” niżej.
6. **Publikacja** (`create_main_aed_resource_with_dataset`, zadanie `create_main_aed_resource_task`):
   - zadanie tworzy nowy zasób z plikiem CSV, a gdy trzeba, także zbiór zbiorczy (licencja CC BY 4.0, kategoria „Zdrowie”, tagi);
   - ustawia schemat z mapowaniem `geo`, który włącza mapę portalu;
   - czeka na wynik walidacji i do tego czasu ponawia zadanie;
   - po sukcesie usuwa poprzedni zasób zbiorczy, a po błędzie sprząta wszystko, co utworzyło;
   - przebieg jest taki sam jak w zadaniu DGA.
7. **Dostęp:**
   - zasób zbiorczy ma standardowe widoki i API portalu (`/1.4/resources/{id}/data`, `/geo`, pobieranie CSV i JSON-LD);
   - nowy endpoint `GET /1.4/aed-aggregated` zwraca identyfikatory i slugi aktualnego zbioru i zasobu, jak `/dga-aggregated`.
8. **Ręczne uruchomienie:**
   - `python manage.py create_main_aed_resource --dry-run` pokazuje statystyki i plik CSV bez zapisu do bazy;
   - `--eager` buduje wykaz synchronicznie;
   - bez opcji polecenie wysyła zadanie do Celery.

## Numer seryjny (AED-14)

Wzorzec dostawcy ma od wersji 2.1.0 opcjonalną kolumnę `numer_seryjny`, zaraz po `model`. Wzorzec ma więc 42 kolumny (było 41), a zasób zbiorczy 52 (było 51). Numer seryjny pochodzi z tabliczki znamionowej urządzenia, nie dotyczy osoby i jest kluczem deduplikacji. Nagłówki `nr_seryjny`, `serial`, `serial_number` i `sn` są dopasowywane jako aliasy (`aed_constants.AED_HEADER_ALIASES`). Źródłem prawdy jest `format_danych/zrodla_wzorca/generuj_dane.py`; schematy, szablony, XLSX i próbki testowe portalu zostały z niego wygenerowane na nowo.

## Deduplikacja (AED-14)

Moduł `mcod/resources/aed_dedup.py` nie importuje Django ani ORM: przyjmuje i zwraca `DataFrame` z kolumnami zasobu zbiorczego. Działa na całej scalonej ramce, więc obejmuje wszystkie źródła: zasoby z portalu, z CKAN, z XML i z importu opisu.

1. **Klucz mocny: numer seryjny.** Ten sam znormalizowany numer seryjny (małe litery, bez polskich znaków, spacji i znaków interpunkcyjnych) oznacza to samo urządzenie, także w obrębie jednego pliku. Wyjątek: oba wiersze podają producenta i producenci się różnią. Wartości w rodzaju „brak”, „nieznany”, „nd”, numery krótsze niż 4 znaki i ciągi jednego znaku nie są traktowane jako numer.
2. **Klucz słaby, tylko między różnymi zasobami** (`id_zasobu_zrodlowego`): punkty w odległości do 30 m, gdy nic ich nie wyklucza i coś je łączy.
   - Wykluczają: różne numery seryjne, różni producenci, różne modele, różne kondygnacje.
   - Łączy: ten sam producent albo ten sam model (powód `marka_model_i_lokalizacja`), a gdy producenta brakuje, ta sama znormalizowana nazwa lokalizacji w odległości do 10 m (powód `nazwa_i_lokalizacja`).
   - W obrębie jednego zasobu dwa AED w jednym miejscu bez numerów seryjnych to dwa urządzenia, więc nie są łączone.
3. **Który wiersz zostaje:** wyższy `poziom_weryfikacji` (`zweryfikowany_w_terenie`, potem `zweryfikowany_przez_dysponenta`), potem nowsza `data_aktualizacji`, potem wiersz wcześniejszy w kolejności. Puste `producent`, `model` i `numer_seryjny` zachowanego wiersza są uzupełniane z duplikatów. Kolejność pozostałych wierszy się nie zmienia.
4. **Wydajność:** kandydatów szuka siatka komórek ok. 100 m i grupa wspólnego numeru seryjnego, a nie porównanie każdego wiersza z każdym. Grupy łączy union-find, więc trzy zgłoszenia jednego urządzenia dają jeden wiersz.
5. **Raport:** `create_main_aed_df` zapisuje w statystykach `wiersze_zdeduplikowane` (liczba) i `duplikaty` (lista par `zachowany`, `pominiety`, `powod` po `id_aed`), a każdy duplikat trafia do logu.

## Dane z zewnątrz przez API: opis zbioru w XML, link do CSV i suma md5 (AED-15, AED-16)

Główna droga dla dostawcy, który nie publikuje na dane.gov.pl. Dostawca wystawia w swoim API (na własnym serwerze https) dwa pliki: opis zbioru w XML i plik CSV zgodny ze wzorcem. Pierwszy import uruchamia komenda, a dalej zbiór odświeża nocne zadanie:

```bash
python manage.py import_aed_xml <adres https opisu> --organizacja <ID> [--uzytkownik <e-mail>] [--dry-run]
python manage.py import_aed_xml --odswiez
```

1. **Opis zbioru** (`aed_opis_zbioru.xsd`, kopia `format_danych/schemat/aed_opis_zbioru.xsd`; zgodność kopii pilnuje test): tytuł, opis, dysponent (nazwa, opcjonalnie REGON i e-mail), licencja (`CC0 1.0` albo `CC BY 4.0`), częstotliwość aktualizacji, data aktualizacji oraz element `zasob` z tytułem, linkiem https do CSV, formatem `csv`, sumą md5 (32 znaki szesnastkowe) i opcjonalną liczbą rekordów. Same rekordy AED są w CSV, nie w opisie.
2. **Kolejność kontroli** (`aed_import.prepare_import`): pobranie opisu (tylko https, wymagany kod 200, brak odpowiedzi to błąd z powodem) → walidacja XSD (`aed_opis.parse_opis`; deklaracje `DOCTYPE` i `ENTITY` odrzucane jak w `aed_xml`) → pobranie CSV spod `link_csv` (https, kod 200) → porównanie md5 pliku z sumą z opisu (wielkość liter bez znaczenia) → kontrola CSV (`aed_opis.inspect_csv`: kolumny minimum, liczba wierszy przyjętych i pominiętych, duplikaty w pliku). Każda niezgodność przerywa import z komunikatem „Import odrzucony, nic nie zapisano: …”.
3. **Zapis** (`aed_import.import_dataset`, w jednej transakcji):
   - nowy opis: zbiór z tytułem, opisem, licencją i częstotliwością z opisu, kategorią „Zdrowie” i `customfields` = `standard: AED`, `opis_xml: <adres opisu>`, `md5: <suma>`, oraz zasób z linkiem do CSV; dalej działa zwykły potok portalu (pobranie pliku, walidacja), a nocne zadanie włącza zasób do Wykazu AED;
   - ten sam opis i ta sama suma md5: nic się nie zmienia (wynik `bez_zmian`);
   - ten sam opis i nowa suma md5: stary zasób jest usuwany, metadane zbioru aktualizowane, a nowy zasób powstaje tą samą drogą (wynik `zaktualizowano`).
4. **Opcje komendy:** `--dry-run` wykonuje wszystkie kontrole i pokazuje raport (md5, wiersze, duplikaty w pliku) bez zapisu. `--odswiez` ponawia import wszystkich zbiorów, które mają w `customfields` klucz `opis_xml`; gdy któryś opis lub plik jest niezgodny, zbiór zostaje bez zmian, a powód trafia na stderr.
5. **Nocne odświeżenie (AED-16):** zadanie Celery `refresh_aed_opis_task` (`tasks/aed.py`, wpis harmonogramu `aed_opis_refresh` o 4:05, kolejka `resources`) wywołuje `aed_import.refresh_imported_datasets()`, tę samą funkcję co `--odswiez`. Dla każdego zbioru z `opis_xml` pobiera opis, sprawdza XSD, pobiera CSV i porównuje md5. Ta sama suma nic nie zmienia, nowa zastępuje zasób, a odrzucony import zostawia zbiór bez zmian z ostrzeżeniem w logu. Nowy zasób przechodzi zwykły potok portalu, a o 4:15 trafia do wykazu. Przy `AED_AGGREGATION_ENABLED = False` harmonogram nie ma tego wpisu, a zadanie nic nie robi.
6. **Przykłady i serwer dostawcy** (dane fikcyjne): `format_danych/przyklady/opis/` (`opis_poprawny.xml`, `opis_bledny_md5.xml`, `opis_bledny_xsd.xml`, `aed_dostawcy.csv` z 7 rekordami, w tym urządzenie zgłaszane też przez innego dostawcę, żeby pokazać deduplikację), generator `format_danych/narzedzia/generuj_opis.py`. Serwer `demo/serwer_zewnetrzny.py` wydaje opisy i CSV (kod 200, GET i HEAD, `/stan`) i podstawia w opisie własny adres, więc ten sam opis działa lokalnie, z kontenera i przez ngrok.
7. **Wynik w portalu uruchomionym lokalnie** (22.11.2026, zrzuty 16–23 w [`demo/zrzuty/`](demo/zrzuty/README.md)): import poprawnego opisu utworzył zbiór 4251 i zasób CSV 40253; opis z błędną sumą md5 i opis niezgodny z XSD zostały odrzucone (kod wyjścia 1, nic nie zapisano), a powtórka z tą samą sumą nic nie zmieniła. Budowa wykazu (zasób 40258): 45 wierszy przed deduplikacją, 38 po, 7 duplikatów. Logi: [`komenda_import_aed_xml.txt`](demo/wynik/komenda_import_aed_xml.txt), [`komenda_create_main_aed_resource_opis.txt`](demo/wynik/komenda_create_main_aed_resource_opis.txt), [`statystyki_opis_dedup.json`](demo/wynik/statystyki_opis_dedup.json), [`wymus_harvest.txt`](demo/wynik/wymus_harvest.txt).
8. **Integrator (dodatek poza portalem)** potrafi wygenerować taki opis z md5 dla przygotowanego pliku CSV: `python integrator/importer.py opis …` (opis w [`integrator/README.md`](integrator/README.md)).

## Dane z zewnątrz, wariant dodatkowy: rekordy AED wprost w XML (AED-11 do AED-13)

Dostawca może też wystawić same rekordy AED w XML pod adresem https:
- **Schemat:** `aed_punkty.xsd` powstaje z Table Schema wzorca (`format_danych/narzedzia/generuj_xsd.py`). Struktura płaska: `<wykaz><aed>…</aed></wykaz>`, jedno pole wzorca to jeden element, pola wymagane mają `minOccurs="1"`, słowniki to `enumeration`, `id_zrodlowe` jest unikalne.
- **Wejście do portalu:** zasób z linkiem do pliku dodany w panelu. Portal klasyfikuje go jako typ `api`, format `xml`, bez kopii pliku, więc wybór źródeł akceptuje taki zasób przy samym poprawnym linku (zadania plikowe go nie dotyczą). Komenda `import_aed_xml` służy od AED-15 do importu opisu zbioru (sekcja wyżej).
- **Budowa wykazu:** to samo nocne zadanie pobiera XML spod linku, waliduje go XSD (`aed_xml.validate_aed_xml`), zamienia na kolumny wzorca i scala z CSV i XLSX. Niezgodny plik jest pomijany, a powód (linia, pole, komunikat) trafia do statystyk i logu.
- **Bezpieczeństwo:** parser nie wczytuje DTD ani zewnętrznych encji, deklaracje `DOCTYPE` i `ENTITY` są odrzucane, rozmiar pliku ograniczony do 20 MB. Zależności: `lxml`, które portal już miał.
- **Zero migracji, DGA bez zmian:** tylko nowe pliki i dopisek w `aed_utils.py` (wybór źródeł, odczyt).

## Wymuszenie harvestu w demo

W portalu odświeżanie opisów działa co noc (4:05), a wykaz powstaje o 4:15. Żeby w demo nie czekać na noc, skrypt `demo/wymus_harvest.py` wykonuje po kolei w kontenerze portalu `import_aed_xml --odswiez`, czeka, aż Celery zwaliduje zasób (statusy zadań linku i pliku), i buduje wykaz poleceniem `create_main_aed_resource --eager`. Kod portalu nie jest przy tym zmieniany. Opcjonalna wersja live demo (adres przez ngrok) jest opisana w [`WERSJA_LIVE.md`](WERSJA_LIVE.md).

## Pliki

### Nowe pliki: kod

| Plik | Co robi |
|---|---|
| `mcod/resources/aed_constants.py` | kontrakt kolumn: 42 kolumny wzorca dostawcy, 52 kolumny zasobu zbiorczego, minimum agregacji, aliasy nagłówków, dopuszczone licencje, klucze `customfields`, kody `przetworzenie` |
| `mcod/resources/aed_aggregation.py` | logika ramek danych bez ORM: odczyt CSV/XLSX, aliasy, kontrola kolumn, normalizacja, `id_aed`, pochodzenie, CSV wynikowy (RFC 4180). Tę samą logikę uruchamia `demo/agreguj.py` poza Django |
| `mcod/resources/aed_dedup.py` | deduplikacja wierszy wykazu bez ORM: klucz mocny (numer seryjny), klucz słaby (producent lub model, nazwa, odległość), wybór zachowanego wiersza, raport duplikatów |
| `mcod/resources/aed_utils.py` | warstwa portalu (wzór: `dga_utils.py`): rozpoznanie zbiorów, wybór i odczyt zasobów, scalenie z deduplikacją, plik CSV, schemat z `geo`, utworzenie zbioru i zasobu zbiorczego, zastąpienie poprzedniego zasobu, sprzątanie |
| `mcod/resources/aed_opis.py`, `mcod/resources/aed_opis_zbioru.xsd` | opis zbioru w XML bez Django: walidacja XSD, odczyt, suma md5, kontrola CSV (kolumny, wiersze, duplikaty); kopia schematu z `format_danych/schemat/` |
| `mcod/resources/aed_import.py` | import z opisu XML (ORM): pobranie opisu i CSV (https, kod 200), md5, zbiór z `customfields` `standard`, `opis_xml`, `md5` i zasób CSV; zastąpienie zasobu przy nowej sumie md5; `refresh_imported_datasets` dla `--odswiez` i zadania nocnego |
| `mcod/resources/aed_xml.py`, `mcod/resources/aed_punkty.xsd` | źródło XML z rekordami: walidacja XSD i zamiana na ramkę (bez Django); kopia schematu z `format_danych/schemat/` |
| `mcod/resources/management/commands/import_aed_xml.py` | komenda importu opisu zbioru (`--organizacja`, `--uzytkownik`, `--dry-run`, `--odswiez`) |
| `mcod/resources/tasks/aed.py` | zadania Celery `create_main_aed_resource_task` (wzór: zadanie DGA) i `refresh_aed_opis_task` (nocne odświeżenie zbiorów z opisu XML) |
| `mcod/resources/management/commands/create_main_aed_resource.py` | komenda ręcznego uruchomienia (`--dry-run`, `--eager`) |
| `mcod/templates/docs/resources/aggregated_aed_info_view.yml` | dokumentacja endpointu `/aed-aggregated` w specyfikacji API |

### Istniejące pliki: dopisane punkty zaczepienia

| Plik | Dopisek |
|---|---|
| `mcod/celeryapp.py` | parametr `enable_aed_aggregation` i dwa wpisy harmonogramu: odświeżenie opisów XML o 4:05 i budowa wykazu o 4:15 (po harvesterze o 3:00 i DGA o 3:30), tylko gdy dodatek jest włączony |
| `mcod/settings/base.py` | `AED_AGGREGATION_ENABLED`, ustawienia `MAIN_AED_*` (właściciel zbioru, katalog pliku, tytuły i opisy, kategoria, tagi) i kolejka `resources` dla obu zadań AED |
| `mcod/settings/test.py` | ustawienia AED dla testów |
| `mcod/resources/tasks/__init__.py` | eksport obu zadań AED |
| `mcod/resources/views.py` | widok `AggregatedAEDInfoView` |
| `mcod/resources/serializers.py` | serializer `AggregatedAEDInfoApiResponse` |
| `mcod/routes.py` | trasa `/aed-aggregated` |
| `mcod/core/api/utils/views.py` | rejestracja schematu i ścieżki w specyfikacji OpenAPI |
| `mcod/datasets/forms.py` | `help_text` pola „Pola niestandardowe” z instrukcją dla dostawcy |
| `mcod/core/tests/fixtures/__init__.py` | rejestracja fikstur AED |
| `CHANGELOG.md` | wpisy AED-01 do AED-16 w sekcji „Unreleased” |

### Nowe pliki: testy i dane testowe

| Plik | Co sprawdza |
|---|---|
| `mcod/resources/tests/test_aed_constants.py` | kontrakt kolumn: liczba (42 i 52) i kolejność kolumn, minimum, aliasy nagłówków, licencje bez „share-alike” |
| `mcod/resources/tests/test_aed_aggregation.py` | logikę ramek bez bazy, w tym realne przypadki: Legionowo (zbiór mieszany), wadliwe pliki z Marek, Krosno bez miejscowości, Przemyśl, a także zgodność z referencyjnym wynikiem wzorca |
| `mcod/resources/tests/test_aed_dedup.py` | deduplikację bez bazy: numer seryjny między dostawcami i w jednym pliku, różni producenci, numery-zaślepki, marka i miejsce między zasobami i w jednym zasobie, różne numery, kondygnacje i modele, odległość, nazwa do 10 m, wybór zachowanego wiersza i uzupełnianie luk, trzy zgłoszenia jednego urządzenia |
| `mcod/resources/tests/test_aed_opis.py` | opis zbioru: poprawny, błędny z polem, zepsuty, `DOCTYPE`, md5 bez względu na wielkość liter, kontrola CSV (wiersze, duplikaty, brak kolumn minimum), zgodność kopii XSD |
| `mcod/resources/tests/test_aed_sources.py` | wybór źródeł (oznaczenie, licencje, formaty, statusy), odczyt plików lokalnych i z CKAN, pominięcia z powodem |
| `mcod/resources/tests/test_main_aed_resource.py` | tworzenie zbioru i zasobu zbiorczego, schemat z `geo`, zastąpienie poprzedniego zasobu, sprzątanie po błędzie |
| `mcod/resources/tests/test_aed_task.py` | zadania Celery (budowa wykazu i odświeżenie opisów: eksport, routing, wyłącznik), harmonogram (4:05 przed 4:15) i komendę `create_main_aed_resource` |
| `mcod/resources/tests/test_aed_xml.py`, `test_aed_xml_source.py` | walidacja XSD rekordów (poprawny, błędny, zepsuty, XXE, zgodność z Table Schema), wybór i odczyt zasobu XML z linku, scalenie XML z CSV |
| `mcod/resources/tests/test_aed_import_xml_command.py` | import opisu: utworzenie zbioru i zasobu po kontroli md5, ponowny import z tą samą i nową sumą, odrzucenie bez zapisu (zła suma md5, opis niezgodny z XSD, kod 503 lub 404, serwer nie odpowiada, brak kolumn minimum), `--dry-run` z raportem duplikatów, błędy argumentów, `--odswiez` i `refresh_imported_datasets` (zastąpienie zmienionego, pozostawienie odrzuconego, brak zbiorów) |
| `mcod/resources/tests/test_aed_api.py` | endpoint `/aed-aggregated`: najnowszy zasób, 404 bez zbioru lub zasobu, wersja robocza i usunięta, wyłączony dodatek, specyfikacja |
| `mcod/resources/tests/test_aed_settings.py` | ustawienia domyślne, wyłącznik i routing zadania do kolejki |
| `mcod/datasets/tests/test_aed_customfields_help.py` | podpowiedź w formularzu zbioru |
| `mcod/core/tests/fixtures/aed.py` | fikstury zbiorów i zasobów AED |
| `data/test_samples/aed/` | próbki: realne pliki z dane.gov.pl (Krosno, Legionowo, Marki, Przemyśl) i przykład wzorca z oczekiwanym wynikiem |

## Weryfikacja

- **Testy:** w kontenerze testowym portalu przechodzą 270 testów (2 pominięte w kontenerze: porównują kopie schematów XSD z katalogiem `format_danych/`, którego kontener nie widzi; sprawdza je `demo/sprawdz.py`), w tym wszystkie testy AED oraz regresja DGA (`test_main_dga.py`, testy DGA w `test_api.py`). Log: [`demo/wynik/testy.txt`](demo/wynik/testy.txt).
- **Migracje:** `makemigrations --check` zwraca „No changes detected” (ten sam log).
- **Portal uruchomiony lokalnie:** zrzuty i log komendy są w [`demo/zrzuty/`](demo/zrzuty/README.md) i [`demo/wynik/`](demo/wynik/).
- **Bez bazy:** [`demo/agreguj.py`](demo/agreguj.py) uruchamia logikę agregacji na realnych plikach z dane.gov.pl ([`demo/wynik/raport_agregacji.txt`](demo/wynik/raport_agregacji.txt)).
- **Styl:** black i flake8 z długością linii 130 oraz isort zgodnie z konfiguracją portalu.

## Poza portalem (dla kontekstu)

- **Prototyp i dowody:**
  - [`demo/index.html`](demo/index.html): klikalny prototyp offline;
  - [`demo/zrzuty/`](demo/zrzuty/README.md): zrzuty z portalu;
  - [`demo/wynik/`](demo/wynik/): wyniki i logi;
  - [`WERSJA_LIVE.md`](WERSJA_LIVE.md): opcjonalny adres wersji live (ocena nie wymaga sieci).
- **Wzorcowy zakres danych:** [`format_danych/`](format_danych/README.md).
- **Akcja „Dane (prze)życie”:** [`branding/`](branding/README.md): logotyp, księga znaku, opis akcji.
- **Prezentacja:** [`prezentacja/`](prezentacja/README.md).
- **Integrator** dla dostawców bez wzorcowego formatu (dodatek): [`integrator/`](integrator/README.md).
  - Integrator jest **osobną aplikacją poza `portal/`**: mapa kolumn na wzorzec v2, normalizacja, walidacja, kandydaci na duplikaty, porównanie z OSM, adaptery Warszawy i Gdańska, lokalne UI, generowanie opisu zbioru w XML z sumą md5. Wynik wchodzi do portalu zwykłym zasobem typu „link” albo przez opis zbioru i komendę `import_aed_xml`, więc w `portal/` nie przybyło przez niego ani jednej linii kodu ani żadnej migracji.
  - Przykładowe wyniki na realnych plikach z dane.gov.pl: [`demo/integrator/`](demo/integrator/README.md) (generuje je jedno polecenie, `python integrator/generuj_demo.py`).
- **Instrukcja dla jury:** [`INSTRUKCJA_DLA_JURY.md`](INSTRUKCJA_DLA_JURY.md).
