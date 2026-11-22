# Demo Wykazu AED

## Weryfikacja maszynowa: `sprawdz.py`

```bash
python demo/sprawdz.py
```

Jedno polecenie, bez Dockera i bazy (brakujące biblioteki dociąga `uv`). Wywołuje funkcje portalu z `portal/backend/mcod/resources/` (`aed_xml.py`, `aed_aggregation.py`, `aed_opis.py`, `aed_dedup.py`) poza Django i wykonuje 20 kontroli wymagań:

- schemat XSD wzorca (42 kolumny, z `numer_seryjny`), walidacja XML poprawnego i błędnego, ochrona przed XXE;
- **opis zbioru w XML**: `opis_poprawny.xml` przechodzi `aed_opis_zbioru.xsd`, a `opis_bledny_xsd.xml` jest odrzucany z linią i polem;
- **suma md5**: zgodna dla `opis_poprawny.xml` i `aed_dostawcy.csv`, niezgodna dla `opis_bledny_md5.xml` (import odrzucony);
- **kontrola CSV** przed zapisem (`inspect_csv`): kolumny minimum, wiersze przyjęte i pominięte;
- **deduplikacja**: urządzenie CT-01 z przykładu wzorca i jego kopia BYD-HALA-A z pliku dostawcy (ten sam producent i numer seryjny) dają w wykazie jeden wiersz (15 → 14);
- **serwer dostawcy**: `serwer_zewnetrzny.py` uruchomiony w wątku na wolnym porcie 127.0.0.1 odpowiada 200 w czasie poniżej 1 s, a md5 z pobranego opisu jest równe md5 pobranego CSV;
- scalenie XML i CSV, 52 kolumny wykazu, licencje, brak migracji i usunięć w diffie, testy, XLSX, prototyp offline, `proces.json`, pliki do zgłoszenia.

Zapisuje `wynik/weryfikacja.txt` i `weryfikacja.json` (PASS/FAIL z plikiem dowodowym) oraz `wynik/import_opisu.json` (wyniki importu opisu, deduplikacji i serwera, z których korzysta krok 4 prototypu). Kod wyjścia 0 oznacza komplet PASS.

Dane z zewnątrz: `serwer_zewnetrzny.py` (serwer dostawcy: opisy zbioru w XML, CSV i schematy XSD, `--https` dla portalu), `NGROK.md` (wystawienie przez ngrok, ostrożnie), `scenariusz/przygotuj_dane_xml.py` i `zrzuty_xml.py` (scenariusz w portalu i zrzuty 10–15). `proces.json` opisuje kroki prototypu w postaci do odczytu maszynowego.

## Klikalny prototyp offline: `index.html`

Otwórz `demo/index.html` w przeglądarce, bez instalacji i bez sieci. Dziewięć kroków prowadzi przez cały proces:

1. problem;
2. dostawca oznacza zbiór wpisem `standard = AED`;
3. dostawca publikuje zasób (CSV lub XLSX, 42 kolumny wzorca);
4. dane z zewnątrz: opis zbioru w XML → walidacja XSD → pobranie CSV → kontrola md5 → kontrola CSV → zbiór i zasób w portalu → deduplikacja przy budowie wykazu. Do wyboru są trzy opisy (poprawny, z błędną sumą md5, niezgodny z XSD), a wyniki każdego kroku pochodzą z `wynik/import_opisu.json` (uruchomienie funkcji portalu przez `sprawdz.py`). Wariant dodatkowy z rekordami wprost w XML (`aed_punkty.xsd`) ma zrzuty 10–14;
5. portal buduje wykaz;
6. odbiorca przegląda wykaz w tabeli z filtrami, na mapie SVG i w szczegółach rekordu z pochodzeniem danych;
7. pobieranie CSV i API;
8. lista zmian w portalu;
9. dodatek: integrator.

Zrzuty importu opisu z portalu `build_demo.py` dołącza do kroku 4 samoczynnie, gdy pliki istnieją (pole `zrzuty_oczekiwane` w `proces.json`): `zrzuty/16_opis_xml_dostawcy.png`, `17_import_opisu_komenda.png`, `18_zbior_z_opisu_w_panelu.png`, `19_wykaz_deduplikacja.png`. Bez nich krok 4 ma notkę, że wyniki pochodzą z `sprawdz.py`.

Zrzuty pochodzą z działającego portalu (`zrzuty/`, podpisy w `zrzuty/README.md`). Tabela i mapa korzystają dokładnie z `wynik/zestawienie_aed.csv`, a przycisk pobierania zwraca ten plik bajt w bajt.

Film z nagraniem działającego portalu (1 min 14 s, bez przejścia przez ten prototyp): `wideo/dane_przezycie_wykaz_aed.mp4` (opis w `wideo/README.md`, źródła w `../video/`).

Strona jest generowana i nie edytuje się jej ręcznie. Po zmianie szablonu albo wyników zbuduj ją ponownie (biblioteka standardowa i git):

```bash
python demo/build_demo.py
```

Skrypt składa `szablon.html` z wynikami z `wynik/`, konturem Polski z `dane/kontur_polski.json` (Natural Earth, domena publiczna), logo i fontem z `branding/` oraz listą plików portalu zmienionych względem oryginału (`git diff a1adc22`). Strona nie ładuje nic z innych domen. Podgląd na szerokości 1440 i 390 px: `wynik/podglad_demo_1440.png`, `wynik/podglad_demo_390.png`.

Kopie plików do zgłoszenia (instrukcja, opis zmian, prototyp ze zrzutami, XLSX, CSV wykazu i łatkę z kodem portalu) składa w `ZGLOSZENIE/` polecenie `python demo/zloz_zgloszenie.py`. Uruchom je po `build_demo.py`.

PDF z warstwą tekstową z instrukcji dla jury i dodatkowych informacji (`INSTRUKCJA_DLA_JURY.pdf`, `DODATKOWE_INFORMACJE.pdf` w katalogu głównym, odnośniki do repo na GitHubie) tworzy `uv run --with markdown-it-py python demo/build_pdf_dokumentow.py` (Edge lub Chrome headless); uruchom je przed `zloz_zgloszenie.py`, które kopiuje oba pliki do `ZGLOSZENIE/`.

## Weryfikacja agregacji bez bazy: `agreguj.py`

Jedno polecenie uruchamia **tę samą logikę agregacji co portal** (`portal/backend/mcod/resources/aed_aggregation.py`) bez Dockera, bazy i Django:

```bash
uv run --python 3.11 --with "pandas==1.5.3" --with "numpy<2" --with openpyxl --with lxml python demo/agreguj.py
```

Wejście:
- migawka realnych zasobów AED z dane.gov.pl (`references/dane_gov_pl_aed/`, metadane z API w `metadane_api/`);
- przykład wzorca `format_danych/przyklady/aed_punkty_przyklad.csv`;
- plik dostawcy zewnętrznego `format_danych/przyklady/opis/aed_dostawcy.csv` (wydawca, licencja i link z `opis_poprawny.xml`, suma md5 sprawdzona).

Skrypt przechodzi po zasobach każdego zbioru tak jak portal: pomija formaty nietabelaryczne i licencje spoza CC0 1.0 / CC BY 4.0, czyta CSV i XLSX funkcją portalu `read_tabular_bytes`, buduje wiersze funkcją `build_aggregate_rows` i odrzuca zasoby bez kolumn minimum wzorca. Na końcu, tak jak `create_main_aed_df` w portalu, usuwa duplikaty funkcją `aed_dedup.deduplicate_rows`. Wszystkie zbiory z migawki traktuje tak, jakby miały w „Polach niestandardowych” `standard = AED`.

Wynik (gotowy do przeczytania bez uruchamiania):
- `wynik/raport_agregacji.txt`: przyjęte i pominięte zasoby z powodami, liczby wierszy, zgodność przykładu z referencją;
- `wynik/zestawienie_aed.csv`: zasób zbiorczy (52 kolumny, RFC 4180), który portal opublikowałby jako Wykaz AED;
- `wynik/statystyki_agreguj.json`: statystyki w układzie `create_main_aed_df` (zasoby przyjęte i pominięte, wiersze, `wiersze_zdeduplikowane`, `duplikaty`).

Co pokazuje wynik:
- **Legionowo** (zasób AED w zbiorze mieszanym „Zdrowie”) jest przyjęte: 24 punkty, nagłówki dopasowane aliasami.
- **Przykład wzorca** daje wiersze identyczne z `format_danych/przyklady/aed_zestawienie_przyklad.csv` (ten sam test wykonuje portal: `test_golden_matches_reference`).
- **Plik dostawcy z opisem XML** daje 7 wierszy, z których jeden (BYD-HALA-A) to urządzenie CT-01 z przykładu wzorca: deduplikacja zostawia 38 z 39 wierszy (powód `numer_seryjny`).
- **Krosno, Przemyśl, Marki** są pominięte, bo nie mają kolumn minimum wzorca (Marki: cały wiersz w jednym polu). **Warszawa** i dodatkowe dystrybucje Przemyśla (XML, GeoJSON, JSON) są pominięte jako formaty nietabelaryczne. Takie zasoby wymagają dostosowania do wzorca u dostawcy albo integratora (krok 2).
- Gdańsk (pole `aed` w bazie pojazdów ZTM) to dane flotowe, a nie punkty, więc nie wchodzi do tej weryfikacji.

## Opis zbioru XML w działającym portalu i wymuszenie harvestu: `wymus_harvest.py`

Scenariusz w portalu uruchomionym w Dockerze (`portal/backend/README.md`), na danych fikcyjnych:

1. Serwer dostawcy: `python demo/serwer_zewnetrzny.py --https` (port 8099; inny: `--port 8098`). Wystawia `/opis.xml`, `/aed.csv`, opisy błędne `/opis_bledny_md5.xml` i `/opis_bledny_xsd.xml` oraz `/stan`. Każdy adres odpowiada kodem 200 (HEAD też), lokalnie w ok. 10 ms. Link do CSV w opisie serwer bierze z nagłówka Host, więc z kontenera działa adres `https://host.docker.internal:8099/opis.xml`.
2. Dane scenariusza: `demo/scenariusz/przygotuj_dane_xml.py` (instrukcja w nagłówku pliku). Tworzy instytucję dostawcy i zbiory wariantu „rekordy w XML”, a do zasobu „Punkty AED – wzorzec v2” wgrywa nową wersję pliku z kolumną `numer_seryjny`. Urządzenie CT-01 z tego pliku i BYD-HALA-A z CSV dostawcy to ten sam AED, co pokazuje deduplikację.
3. Import opisu: `docker exec mcod-admin python manage.py import_aed_xml https://host.docker.internal:8099/opis.xml --organizacja <ID>` (najpierw `--dry-run`). Opisy z błędną sumą md5 i niezgodny z XSD są odrzucane, a w bazie nic się nie zapisuje.
4. Wykaz: `docker exec mcod-admin python manage.py create_main_aed_resource --eager`.

Wyniki uruchomienia z 22.11.2026 (serwer na porcie 8098): `wynik/komenda_import_aed_xml.txt` (zbiór 4251, zasób 40253), `wynik/komenda_create_main_aed_resource_opis.txt` i `wynik/statystyki_opis_dedup.json` (45 wierszy przed deduplikacją, 38 po, 7 duplikatów), wykaz `wynik/wykaz_opis_xml_dedup.csv` (52 kolumny), zrzuty 16–23 (`zrzuty/README.md`, skrypt `scenariusz/zrzuty_xml.py`).

**Wymuszenie harvestu.** Portal odświeża zbiory z opisu XML co noc: zadanie `refresh_aed_opis_task` o 4:05, a Wykaz AED powstaje o 4:15. Żeby w demo nie czekać do nocy, ten sam przebieg można uruchomić od razu z hosta (Python 3.8+, tylko biblioteka standardowa):

```
python demo/wymus_harvest.py https://host.docker.internal:8099/opis.xml --organizacja <ID>
python demo/wymus_harvest.py <adres opisu> [--kontener mcod-admin] [--limit 300] [--zapisz demo/wynik/wymus_harvest.txt]
```

Skrypt przez `docker exec`:
1. Importuje opis. Gdy zbiór z tym opisem już jest w portalu, używa `import_aed_xml --odswiez`, a przy pierwszym imporcie podaje adres i `--organizacja`. Ta sama suma md5 nic nie zmienia, nowa zastępuje zasób.
2. Czeka z limitem czasu, aż Celery przetworzy zasób: `link_tasks_last_status` i `file_tasks_last_status` muszą mieć SUCCESS, a `data_tasks_last_status` ma być zakończony. FAILURE walidacji danych jest tylko raportowany, bo Wykaz AED czyta plik mimo błędów typów zgadywanych przez portal.
3. Buduje wykaz (`create_main_aed_resource --eager`).
4. Wypisuje raport: zbiór i zasób dostawcy, statusy, zasób wykazu, liczbę wierszy i duplikaty.

Kody wyjścia: 0 sukces, 1 import odrzucony, 2 limit czasu albo błąd potoku. Każde wywołanie `manage.py` w kontenerze trwa kilka sekund, więc cały przebieg zajmuje ok. 1–2 min. Przykładowy przebieg jest w `wynik/wymus_harvest.txt`. Przez ngrok podaje się adres https opisu z ngroka (`NGROK.md`).
