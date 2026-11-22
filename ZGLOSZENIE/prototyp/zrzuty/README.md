# Zrzuty z działającego portalu (Wykaz AED)

## Skąd pochodzą zrzuty

- **Data i stan kodu:** zrzuty zrobiono 22.11.2026 w pełnym portalu dane.gov.pl uruchomionym lokalnie w Dockerze (panel, API, Celery, nginx, frontend Angular), na kodzie z commita `a082628` (AED-10). Pliki utworzył skrypt `demo/scenariusz/zrzuty.py` (Playwright z przeglądarką Edge).
- **Dane:** dane scenariusza utworzył skrypt `demo/scenariusz/przygotuj_dane.py`.
  - Legionowo (plik z dane.gov.pl): `standard = AED`, licencja CC0.
  - Wzorzec v2 (dane fikcyjne): `standard = AED 1.1`, licencja CC BY 4.0.
  - Marki i Krosno: pliki z dane.gov.pl.
  - Jeden zbiór bez oznaczenia.
- **Wykaz:** zbudowała go komenda `create_main_aed_resource --eager`. Powstał zbiór 4216 z zasobem 40247.
- **Makiet nie ma:** zrzuty 01, 02, 04 i 05 to widoki portalu. Zrzuty 03, 06, 07 i 09 pokazują prawdziwe wyjście komendy, API i testów, wyświetlone jako tekst. Tytuł każdego z nich mówi, czy wyjście jest sformatowane i czy pokazuje tylko wybrane pola.

## Zrzuty

| Plik | Co widać | Czego dowodzi |
|---|---|---|
| `01_formularz_zbioru_standard_aed.png` | Panel, formularz zbioru „Defibrylatory AED w Legionowie”: w „Polach niestandardowych” wpis `standard` = `AED`, pod polem podpowiedź Wykazu AED. | Oznaczenie zbioru bez migracji i bez tagów: istniejąca metadana `Dataset.customfields` (zadania 04 i 09). |
| `02_zasoby_dostawcow.png` | Panel, lista zasobów (szukaj „AED”): pięć zasobów dostawców i zasób zbiorczy „Wykaz defibrylatorów AED”, wszystkie opublikowane. Oba pliki zbudowane na wzorcu („Punkty AED – wzorzec v2” i „Punkty AED bez deklaracji standardu”) mają czerwony znak w kolumnie widoku tabelarycznego. | Zasoby przechodzą zwykły potok walidacji portalu. Plik zgodny ze wzorcem może mieć błąd walidacji typów zgadywanych przez portal (np. „5A” w `numer_budynku`), a mimo to trafia do wykazu (poprawka z zadania 10). Zbiór bez `standard = AED` nie trafia, choć ma te same kolumny. |
| `03_komenda_wykaz_statystyki.png` | Terminal: `create_main_aed_resource --dry-run` i `--eager`. Przyjęte zasoby: 2 (Legionowo i wzorzec), pominięte: 2 (Krosno: brak kolumny `miejscowosc`; Marki: brak kolumn minimum), 32 wiersze. Poprzedni zasób zbiorczy jest wycofany. Pominięto linie diagnostyczne sygnałów (pełny log: `demo/wynik/komenda_create_main_aed_resource.txt`). | Agregacja wielu dostawców wzorowana na DGA, z powodami pominięć w logu (zadania 06 i 07). |
| `04_wykaz_tabela.png` | Frontend: zasób „Wykaz defibrylatorów AED”, zakładka Tabela, kolumny wzorca (`id_aed`, `id_zrodlowe`, `nazwa_lokalizacji`, …), 32 wiersze na dwóch stronach, pobieranie CSV i JSON-LD. | Zasób zbiorczy działa w portalu jak każdy inny zasób tabelaryczny: bez nowego frontendu. |
| `05_wykaz_mapa.png` | Frontend: zakładka Mapa: punkty wzorca w Bydgoszczy i klaster 24 punktów z Legionowa. | Schemat zasobu zbiorczego z `geo` (b, l, label) włącza mapę portalu. |
| `06_api_aed_aggregated.png` | `GET /1.4/aed-aggregated`: identyfikatory i slugi zbioru i zasobu zbiorczego. | Stały punkt API, odpowiednik `/dga-aggregated` (zadanie 08). |
| `07_api_dane_zasobu.png` | `GET /1.4/resources/40247/data`: `meta.count = 32`, mapowanie geo i pierwszy wiersz z kolumnami pochodzenia (`wydawca_zasobu`, `licencja_zasobu`, `id_zasobu_zrodlowego`, `url_zasobu_zrodlowego`, `data_agregacji`). | Dane wykazu w API portalu, z atrybucją dostawcy wymaganą przez CC BY 4.0. |
| `09_testy.png` | Wynik pytest w kontenerze: testy AED i regresja DGA, 192 passed, `makemigrations --check`: No changes detected (pełna lista: `demo/wynik/testy.txt`). | Zmiany mają testy, mechanizm DGA działa bez zmian, migracji brak. |

Zrzutu `08_strona_wykazu.png` nie ma, bo zadanie 12 (strona Wykazu we froncie) jest opcjonalne i go nie zrobiliśmy.

## Uwagi o środowisku

- Mapa we froncie uruchomionym przez `ng serve` wymaga ustawienia `"prebundle": false` w konfiguracji `serve`. Bez niego `require('leaflet')` w `LeafletService` oryginalnego frontendu kończy się błędem „Dynamic require of "leaflet" is not supported”. Do zrzutów zamontowaliśmy zmienioną kopię `angular.json`, a pliku w repo nie zmienialiśmy.
- Okno „Polityka prywatności i RODO” (treść z CMS, w lokalnym środowisku pusta) jest zamykane przed zrzutem.
- Na zrzutach widać konto administratora środowiska lokalnego (`admin@mcod.local`).
