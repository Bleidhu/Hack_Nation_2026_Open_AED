# Wydania

## v2.1.0 (22.11.2026): opis zbioru w XML z sumą md5, deduplikacja, numer seryjny

Tym razem **kod portalu się zmienia**. Dane z zewnątrz przychodzą jako opis zbioru w XML z linkiem do CSV i sumą md5, a wykaz nie powtarza tego samego urządzenia zgłoszonego przez kilku dostawców. Opis zmian w kodzie: [`ZMIANY_W_PORTALU.md`](ZMIANY_W_PORTALU.md), wpisy AED-14 do AED-16 w [`portal/backend/CHANGELOG.md`](portal/backend/CHANGELOG.md). Nadal zero migracji: nowe metadane zbioru są w istniejącym polu `Dataset.customfields`.

### Co dochodzi względem v2.0.0

- **Wcześniej zacommitowane, bez osobnego wydania (commit `0a4242e`):** rekordy AED wprost w XML ze schematem `aed_punkty.xsd` (źródło w nocnym zadaniu), `demo/sprawdz.py`, prototyp w 9 krokach, zrzuty 10–15, `DODATKOWE_INFORMACJE.md` i skrócona instrukcja dla jury.
- **Kolumna `numer_seryjny`** (opcjonalna, po `model`): wzorzec dostawcy ma 42 kolumny (było 41), Wykaz AED 52 (było 51). Wersja wzorca 2.1.0. Schematy, szablony, XLSX, przykłady, próbki testowe portalu i integrator zaktualizowane.
- **Deduplikacja w budowie wykazu** (`mcod/resources/aed_dedup.py`, wywołana w `create_main_aed_df`): klucz mocny to numer seryjny (chyba że producenci się różnią); klucz słaby działa tylko między różnymi zasobami: ten sam producent lub model w odległości do 30 m albo, gdy brakuje producenta, ta sama nazwa do 10 m. Różne numery seryjne, producenci, modele lub kondygnacje wykluczają połączenie. Statystyki `wiersze_zdeduplikowane` i `duplikaty`, każdy duplikat w logu.
- **Opis zbioru w XML z linkiem do CSV i sumą md5** (`format_danych/schemat/aed_opis_zbioru.xsd`, `aed_opis.py`, `aed_import.py`): komenda `python manage.py import_aed_xml <adres https opisu> --organizacja ID [--dry-run] [--odswiez]` sprawdza kolejno kod 200, XSD, plik CSV, md5 i kolumny, a dopiero potem tworzy zbiór (`standard`, `opis_xml`, `md5` w `customfields`) i zasób CSV. Ta sama suma md5 nic nie zmienia, nowa zastępuje zasób, a przy niezgodności nic nie jest zapisywane.
- **Nocne odświeżenie opisów:** zadanie Celery `refresh_aed_opis_task` o 4:05, przed budową wykazu o 4:15 (wpis `aed_opis_refresh`, za wyłącznikiem `AED_AGGREGATION_ENABLED`). Ponawia import każdego zbioru z `opis_xml` tą samą funkcją co `--odswiez` (`refresh_imported_datasets`).
- **Sprawdzone w portalu uruchomionym lokalnie** (zrzuty 16–23): zbiór 4251 i zasób CSV 40253 z opisu, opisy z błędną sumą md5 i niezgodny z XSD odrzucone bez zapisu, wykaz 40258 z 45 wierszy przed deduplikacją i 38 po (7 duplikatów).
- **Przykłady dostawcy** w `format_danych/przyklady/opis/` (opis poprawny, z błędną sumą md5 i niezgodny z XSD, CSV z 7 rekordami) i przepisany serwer dostawcy `demo/serwer_zewnetrzny.py`.
- **Integrator (dodatek)** generuje opis zbioru w XML z sumą md5: podkomenda `opis` w `integrator/importer.py`.
- **Wymuszenie harvestu w demo:** `demo/wymus_harvest.py` (import opisu z `--odswiez`, czekanie na walidację zasobu przez Celery, potem `create_main_aed_resource --eager`). Opcjonalna wersja live: [`WERSJA_LIVE.md`](WERSJA_LIVE.md).
- **Testy:** nowe `test_aed_dedup.py` i `test_aed_opis.py`, przepisany `test_aed_import_xml_command.py`. W kontenerze testowym portalu: 270 passed, 2 skipped, `makemigrations --check`: „No changes detected” ([`demo/wynik/testy.txt`](demo/wynik/testy.txt)). Integrator: 97 testów bez Dockera.

### Czego nie zawiera

- Scalania rekordów między wykazem a OpenStreetMap: dane ODbL nadal nie trafiają do wykazu.

## v2.0.0 (22.11.2026): integrator danych (dodatek), ukończona faza 2

Zakończona faza 2 planu: integrator danych dla dostawców bez wzorcowego formatu, cały w `integrator/`. **Kod portalu bez zmian względem v1.5.0** – integrator celowo nie dotyka `portal/`, bo oceniany jest główny rezultat, a nie dodatki.

### Co dochodzi względem v1.5.0

- **Rdzeń integratora na wzorcu v2** (`integrator/rdzen/`): mapowanie kolumn (presety `wzorzec`, `osm`, `warszawa`, `gdansk`), normalizacja, walidacja z raportem; licencje jawnie i blokada ODbL dla celu „portal”.
- **Adaptery** (`integrator/adaptery/`): OSM (Overpass, GeoJSON, XML), odpowiedź API Warszawy zapisana w pliku (bez tokenów i sieci), baza pojazdów ZTM Gdańska (statystyka i powód zamiast wierszy – dane flotowe).
- **Kandydaci na duplikaty** (tylko flagowanie, bez scalania) i **porównanie wykazu z OSM** (raport lokalny z oznaczeniem ODbL).
- **Util `dodaj`**: dopisywanie pojedynczych rekordów z walidacją, propozycją identyfikatora i kontrolą duplikatów (zapis po `--tak`).
- **Lokalne UI** (`integrator/ui/`): serwer tylko na 127.0.0.1, strona offline (czcionka osadzona, zero CDN), WCAG 2.1 AA, nic nie zapisuje na dysku.
- **Testy: 87, bez Dockera** (`python -m unittest discover -s integrator/testy -t .`).
- **Wyniki demo**: `demo/integrator/` generuje jedno polecenie (`python integrator/generuj_demo.py`).
- **Materiały zgłoszeniowe zaktualizowane**: instrukcja (krok 14), prototyp (krok 8), prezentacja (slajd 14; teraz 15 slajdów), `ZGLOSZENIE/prototyp/integrator/`.

### Czego nie zawiera

- **Zmian w `portal/`** względem v1.5.0. Jedyna rozważana zmiana (schemat źródła wg Table Schema) została świadomie odłożona; deduplikacja w portalu pozostała pomysłem na przyszłość (opisane w `integrator/README.md`).

## v1.5.0 (22.11.2026): wstępne materiały do zgłoszenia, z księgą znaku

Wersja wstępna. Zawiera komplet materiałów, które zamierzamy przesłać, razem z księgą znaku akcji „Dane (prze)życie”. To jeszcze nie wersja ostateczna: lista autorów, licencja kodu portalu i kolizje nazwy akcji (UPRP, EUIPO, domeny) czekają na decyzję zespołu. Kod portalu jest taki sam jak w v1.0.0.

### Co dochodzi względem v1.0.0

- **Akcja „Dane (prze)życie”** zamiast roboczej „Otwórz AED” (archiwum: `branding/archiwum/otworz_aed/`). Hasło: „Twoje dane – czyjeś życie.”
- **Znak finalny:** migotanie komór i rytm zatokowy spotykają się na środku znaku, w środku nałożonego folderu z danymi.
- **Logotyp** w JPG, PNG, PDF i SVG oraz **księga znaku** (12 stron): `branding/`.
- **Prezentacja** (14 slajdów, PPTX i PDF): `prezentacja/`. Slajdy mają zróżnicowane układy i krój Atkinson Hyperlegible.
- **README** z tytułem i szczegółowym opisem; instrukcja dla jury, prototyp i `ZGLOSZENIE/` zaktualizowane.
- **Redakcja** tekstów, księgi znaku, prezentacji i prototypu, żeby mniej przypominały tekst generowany automatycznie.

## v1.0.0 (22.11.2026): działająca integracja danych AED w portalu

Tag `v1.0.0` (commit `8a9e85b`). To podstawowa wersja rozwiązania. Zawiera działający mechanizm integracji danych AED w kodzie portalu dane.gov.pl, czyli **Wykaz AED**. Nie zawiera materiałów do finalnego zgłoszenia.

### Co zawiera

- **Wykaz AED w portalu** (`portal/backend/`): dodatek zbudowany na wzór wykazu DGA. Nocne zadanie scala zasoby AED od wielu dostawców w jeden zasób zbiorczy z tabelą, mapą i API. Opis: [`ZMIANY_W_PORTALU.md`](ZMIANY_W_PORTALU.md).
  - Zbiory oznacza się w „Polach niestandardowych” (`standard = AED`), bez migracji. Każdy zasób jest sprawdzany po kolumnach wzorca.
  - Testy: [`demo/wynik/testy.txt`](demo/wynik/testy.txt). Dowody z portalu uruchomionego lokalnie: [`demo/zrzuty/`](demo/zrzuty/README.md).
- **Wzorcowy zakres danych**: [`format_danych/wzorcowy_zakres_danych.xlsx`](format_danych/wzorcowy_zakres_danych.xlsx) wraz ze schematami.
- **Klikalny prototyp offline**: [`demo/index.html`](demo/index.html).
- **Instrukcja dla jury**: [`INSTRUKCJA_DLA_JURY.md`](INSTRUKCJA_DLA_JURY.md).

### Czego nie zawiera

- **Księgi znaku ani logotypów.** Pliki w `branding/` to szkice robocze, a nie finalny znak akcji.
- **Materiałów do finalnego zgłoszenia.** Nie ma prezentacji ani finalnej kampanii promocyjnej. Folder [`ZGLOSZENIE/`](ZGLOSZENIE/README.md) to robocze zestawienie plików, a nie gotowa paczka do wysłania.
- **Integratora danych** (`integrator/`, krok 2 projektu). Dostawca bez wzorcowego formatu musi na razie sam przygotować plik zgodny ze wzorcem.
