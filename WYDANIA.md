# Wydania

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
