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
- Zgodne zasoby zadanie scala w jeden CSV o 51 kolumnach, z pochodzeniem każdego wiersza, i publikuje go jako zasób w zbiorze „Wykaz defibrylatorów AED – wykaz zbiorczy”.
- Portal sam daje temu zasobowi tabelę, mapę, wyszukiwanie i API, a stały adres aktualnego zasobu zwraca nowy endpoint `/1.4/aed-aggregated`.

## Zasady, których się trzymaliśmy

- **Rozszerzamy, niczego nie usuwamy.**
  - Kod AED jest w nowych plikach obok DGA. Funkcje DGA wielokrotnego użytku (`check_all_resource_validations_status`, wyjątki walidacji, `request_remote_dga`) importujemy, a nie kopiujemy ani przenosimy.
  - W istniejących plikach są tylko dopisane punkty zaczepienia. Jedyna zamieniona linia to sygnatura `get_beat_schedule` w `celeryapp.py`, rozszerzona o parametr opcjonalny z wartością domyślną.
- **Zero migracji.** Nie ma nowych modeli, pól ani tabel. Zbiory źródłowe i zbiór zbiorczy rozpoznajemy po istniejącym polu `Dataset.customfields`: `standard = AED` dla zbiorów źródłowych, `zestawienie = AED-krajowe` dla zbioru zbiorczego. `makemigrations --check` zwraca „No changes detected”.
- **DGA działa bez zmian.** Istniejące testy DGA przechodzą bez modyfikacji.
- **Wyłącznik.** Przy `AED_AGGREGATION_ENABLED = False` harmonogram nie ma wpisu AED, zadanie nic nie robi, a `/aed-aggregated` zwraca 404. Portal działa wtedy jak oryginał.

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
5. **Publikacja** (`create_main_aed_resource_with_dataset`, zadanie `create_main_aed_resource_task`):
   - zadanie tworzy nowy zasób z plikiem CSV, a gdy trzeba, także zbiór zbiorczy (licencja CC BY 4.0, kategoria „Zdrowie”, tagi);
   - ustawia schemat z mapowaniem `geo`, który włącza mapę portalu;
   - czeka na wynik walidacji i do tego czasu ponawia zadanie;
   - po sukcesie usuwa poprzedni zasób zbiorczy, a po błędzie sprząta wszystko, co utworzyło;
   - przebieg jest taki sam jak w zadaniu DGA.
6. **Dostęp:**
   - zasób zbiorczy ma standardowe widoki i API portalu (`/1.4/resources/{id}/data`, `/geo`, pobieranie CSV i JSON-LD);
   - nowy endpoint `GET /1.4/aed-aggregated` zwraca identyfikatory i slugi aktualnego zbioru i zasobu, jak `/dga-aggregated`.
7. **Ręczne uruchomienie:**
   - `python manage.py create_main_aed_resource --dry-run` pokazuje statystyki i plik CSV bez zapisu do bazy;
   - `--eager` buduje wykaz synchronicznie;
   - bez opcji polecenie wysyła zadanie do Celery.

## Dane z zewnątrz w XML ze schematem XSD (AED-11 do AED-13)

Dostawca nie musi być na dane.gov.pl. Może wystawić plik XML pod adresem https na własnym serwerze:
- **Schemat:** `aed_punkty.xsd` powstaje z Table Schema wzorca (`format_danych/narzedzia/generuj_xsd.py`). Struktura płaska: `<wykaz><aed>…</aed></wykaz>`, jedno pole wzorca to jeden element, pola wymagane mają `minOccurs="1"`, słowniki to `enumeration`, `id_zrodlowe` jest unikalne.
- **Wejście do portalu:** zasób z linkiem do pliku (w panelu albo `manage.py import_aed_xml <adres> --organizacja <ID>`). Portal klasyfikuje go jako typ `api`, format `xml`, bez kopii pliku, więc wybór źródeł akceptuje taki zasób przy samym poprawnym linku (zadania plikowe go nie dotyczą).
- **Budowa wykazu:** to samo nocne zadanie pobiera XML spod linku, waliduje go XSD (`aed_xml.validate_aed_xml`), zamienia na kolumny wzorca i scala z CSV i XLSX. Niezgodny plik jest pomijany, a powód (linia, pole, komunikat) trafia do statystyk i logu.
- **Bezpieczeństwo:** parser nie wczytuje DTD ani zewnętrznych encji, deklaracje `DOCTYPE` i `ENTITY` są odrzucane, rozmiar pliku ograniczony do 20 MB. Zależności: `lxml`, które portal już miał.
- **Zero migracji, DGA bez zmian:** tylko nowe pliki i dopisek w `aed_utils.py` (wybór źródeł, odczyt).

## Pliki

### Nowe pliki: kod

| Plik | Co robi |
|---|---|
| `mcod/resources/aed_constants.py` | kontrakt kolumn: 41 kolumn wzorca dostawcy, 51 kolumn zasobu zbiorczego, minimum agregacji, aliasy nagłówków, dopuszczone licencje, klucze `customfields`, kody `przetworzenie` |
| `mcod/resources/aed_aggregation.py` | logika ramek danych bez ORM: odczyt CSV/XLSX, aliasy, kontrola kolumn, normalizacja, `id_aed`, pochodzenie, CSV wynikowy (RFC 4180). Tę samą logikę uruchamia `demo/agreguj.py` poza Django |
| `mcod/resources/aed_utils.py` | warstwa portalu (wzór: `dga_utils.py`): rozpoznanie zbiorów, wybór i odczyt zasobów, plik CSV, schemat z `geo`, utworzenie zbioru i zasobu zbiorczego, zastąpienie poprzedniego zasobu, sprzątanie |
| `mcod/resources/aed_xml.py`, `mcod/resources/aed_punkty.xsd` | źródło XML: walidacja XSD i zamiana na ramkę (bez Django); kopia schematu z `format_danych/schemat/` |
| `mcod/resources/management/commands/import_aed_xml.py` | zaczytanie zewnętrznych danych XML: walidacja, zbiór `standard = AED` i zasób z linkiem |
| `mcod/resources/tasks/aed.py` | zadanie Celery `create_main_aed_resource_task` (wzór: zadanie DGA) |
| `mcod/resources/management/commands/create_main_aed_resource.py` | komenda ręcznego uruchomienia (`--dry-run`, `--eager`) |
| `mcod/templates/docs/resources/aggregated_aed_info_view.yml` | dokumentacja endpointu `/aed-aggregated` w specyfikacji API |

### Istniejące pliki: dopisane punkty zaczepienia

| Plik | Dopisek |
|---|---|
| `mcod/celeryapp.py` | parametr `enable_aed_aggregation` i wpis harmonogramu o 4:15 (po harvesterze o 3:00 i DGA o 3:30), tylko gdy dodatek jest włączony |
| `mcod/settings/base.py` | `AED_AGGREGATION_ENABLED` oraz ustawienia `MAIN_AED_*`: właściciel zbioru, katalog pliku, tytuły i opisy, kategoria, tagi |
| `mcod/settings/test.py` | ustawienia AED dla testów |
| `mcod/resources/tasks/__init__.py` | eksport zadania AED |
| `mcod/resources/views.py` | widok `AggregatedAEDInfoView` |
| `mcod/resources/serializers.py` | serializer `AggregatedAEDInfoApiResponse` |
| `mcod/routes.py` | trasa `/aed-aggregated` |
| `mcod/core/api/utils/views.py` | rejestracja schematu i ścieżki w specyfikacji OpenAPI |
| `mcod/datasets/forms.py` | `help_text` pola „Pola niestandardowe” z instrukcją dla dostawcy |
| `mcod/core/tests/fixtures/__init__.py` | rejestracja fikstur AED |
| `CHANGELOG.md` | wpisy AED-01 do AED-13 w sekcji „Unreleased” |

### Nowe pliki: testy i dane testowe

| Plik | Co sprawdza |
|---|---|
| `mcod/resources/tests/test_aed_constants.py` | kontrakt kolumn: liczba i kolejność kolumn, minimum, aliasy nagłówków, licencje bez „share-alike” |
| `mcod/resources/tests/test_aed_aggregation.py` | logikę ramek bez bazy, w tym realne przypadki: Legionowo (zbiór mieszany), wadliwe pliki z Marek, Krosno bez miejscowości, Przemyśl, a także zgodność z referencyjnym wynikiem wzorca |
| `mcod/resources/tests/test_aed_sources.py` | wybór źródeł (oznaczenie, licencje, formaty, statusy), odczyt plików lokalnych i z CKAN, pominięcia z powodem |
| `mcod/resources/tests/test_main_aed_resource.py` | tworzenie zbioru i zasobu zbiorczego, schemat z `geo`, zastąpienie poprzedniego zasobu, sprzątanie po błędzie |
| `mcod/resources/tests/test_aed_task.py` | zadanie Celery, harmonogram i komendę `create_main_aed_resource` |
| `mcod/resources/tests/test_aed_xml.py`, `test_aed_xml_source.py`, `test_aed_import_xml_command.py` | walidacja XSD (poprawny, błędny, zepsuty, XXE, zgodność z Table Schema), wybór i odczyt zasobu XML z linku, scalenie XML z CSV, komenda importu |
| `mcod/resources/tests/test_aed_api.py` | endpoint `/aed-aggregated`: najnowszy zasób, 404 bez zbioru lub zasobu, wersja robocza i usunięta, wyłączony dodatek, specyfikacja |
| `mcod/resources/tests/test_aed_settings.py` | ustawienia domyślne, wyłącznik i routing zadania do kolejki |
| `mcod/datasets/tests/test_aed_customfields_help.py` | podpowiedź w formularzu zbioru |
| `mcod/core/tests/fixtures/aed.py` | fikstury zbiorów i zasobów AED |
| `data/test_samples/aed/` | próbki: realne pliki z dane.gov.pl (Krosno, Legionowo, Marki, Przemyśl) i przykład wzorca z oczekiwanym wynikiem |

## Weryfikacja

- **Testy:** w kontenerze testowym portalu przechodzą 219 testów (1 pominięty w kontenerze, sprawdza go `demo/sprawdz.py`), w tym wszystkie testy AED oraz regresja DGA (`test_main_dga.py`, testy DGA w `test_api.py`). Log: [`demo/wynik/testy.txt`](../demo/wynik/testy.txt).
- **Migracje:** `makemigrations --check` zwraca „No changes detected” (ten sam log).
- **Portal uruchomiony lokalnie:** zrzuty i log komendy są w [`demo/zrzuty/`](../demo/zrzuty/README.md) i [`demo/wynik/`](../demo/wynik/).
- **Bez bazy:** [`demo/agreguj.py`](../demo/agreguj.py) uruchamia logikę agregacji na realnych plikach z dane.gov.pl ([`demo/wynik/raport_agregacji.txt`](../demo/wynik/raport_agregacji.txt)).
- **Styl:** black i flake8 z długością linii 130 oraz isort zgodnie z konfiguracją portalu.

## Poza portalem (dla kontekstu)

- **Prototyp i dowody:**
  - [`demo/index.html`](../demo/index.html): klikalny prototyp offline;
  - [`demo/zrzuty/`](../demo/zrzuty/README.md): zrzuty z portalu;
  - [`demo/wynik/`](../demo/wynik/): wyniki i logi.
- **Wzorcowy zakres danych:** [`format_danych/`](../format_danych/README.md).
- **Akcja „Dane (prze)życie”:** [`branding/`](../branding/README.md): logotyp, księga znaku, opis akcji.
- **Prezentacja:** [`prezentacja/`](../prezentacja/README.md).
- **Integrator** dla dostawców bez wzorcowego formatu (dodatek): [`integrator/`](../integrator/README.md).
  - Integrator jest **osobną aplikacją poza `portal/`**: mapa kolumn na wzorzec v2, normalizacja, walidacja, kandydaci na duplikaty, porównanie z OSM, adaptery Warszawy i Gdańska, lokalne UI. Wynik wchodzi do portalu zwykłym zasobem typu „link”, więc w `portal/` nie przybyło przez niego ani jednej linii kodu ani żadnej migracji (faza 2 integratora nie zmienia `portal/`; jedyna rozważana zmiana, schemat źródła wg Table Schema, została świadomie odłożona).
  - Przykładowe wyniki na realnych plikach z dane.gov.pl: [`demo/integrator/`](../demo/integrator/README.md) (generuje je jedno polecenie, `python integrator/generuj_demo.py`).
- **Instrukcja dla jury:** [`INSTRUKCJA_DLA_JURY.md`](../INSTRUKCJA_DLA_JURY.md).
