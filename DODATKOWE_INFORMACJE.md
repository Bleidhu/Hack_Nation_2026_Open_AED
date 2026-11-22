# Dodatkowe informacje dla jury: Dane (prze)życie, Wykaz AED w portalu dane.gov.pl

**To wersja pełna, do wglądu po krótkiej instrukcji** ([`INSTRUKCJA_DLA_JURY.md`](INSTRUKCJA_DLA_JURY.md), kilka zdań i jedno polecenie). Każde wymaganie zadania „Misja AED – Dane na ratunek” ma tu osobny krok: który plik otworzyć, co w nim zobaczyć i czego to dowodzi. Wszystkie dowody są plikami w repozytorium. Nie jest potrzebne logowanie, instalacja ani połączenie z serwerami zespołu. Pliki do zgłoszenia zebrano w [`ZGLOSZENIE/`](ZGLOSZENIE/README.md).

**Najszybciej:** `python demo/sprawdz.py` (weryfikacja maszynowa, wynik w [`demo/wynik/weryfikacja.txt`](demo/wynik/weryfikacja.txt)) albo film <https://youtu.be/wiHsN31m_6o> (1 min 14 s, krok 4). Dane z zewnątrz: opis zbioru w XML z sumą md5 w kroku 18, rekordy w XML w kroku 17. Deduplikacja: krok 19. Opcjonalna wersja live i wymuszenie harvestu: krok 20.

## Krok 0: otwarcie paczki

1. Proszę rozpakować archiwum ZIP albo sklonować repozytorium.
2. Pliki `.md` można czytać w przeglądarce lub edytorze, pliki `.csv` w arkuszu (UTF-8, separator przecinek), a `.png` i `.pdf` w przeglądarce.
3. Prototyp [`demo/index.html`](demo/index.html) otwiera się dwuklikiem. Działa z dysku, bez sieci, w Chrome, Edge i Firefox.

## Mapa wymagań

| Wymaganie | Krok | Główny plik |
|---|---|---|
| §4 opis i tytuł projektu | 12 | [`README.md`](README.md) |
| §4 prezentacja (min. 5 slajdów ze zrzutami, kroki użytkownika, ograniczenia) | 13 | [`prezentacja/dane_przezycie_prezentacja.pdf`](prezentacja/dane_przezycie_prezentacja.pdf) |
| §4 prototyp rozwiązania | 1, 2, 4 | [`demo/index.html`](demo/index.html), [`portal/backend/`](portal/backend/) |
| §4 wzorcowy zakres danych (XLSX) | 6 | [`format_danych/wzorcowy_zakres_danych.xlsx`](format_danych/wzorcowy_zakres_danych.xlsx) |
| §4 kod źródłowy | 2, 3 | [`ZMIANY_W_PORTALU.md`](ZMIANY_W_PORTALU.md) |
| §4 logotyp (.jpg .png .pdf, format otwarty) i księga znaku | 10 | [`branding/logo/`](branding/logo/), [`branding/ksiega_znaku.pdf`](branding/ksiega_znaku.pdf) |
| §5 format odczytywalny maszynowo | 7 | [`format_danych/schemat/`](format_danych/schemat/) |
| §5 zgodność z zasadami portalu | 2, 8 | [`format_danych/UZASADNIENIE.md`](format_danych/UZASADNIENIE.md), [`ZMIANY_W_PORTALU.md`](ZMIANY_W_PORTALU.md) |
| §5 WCAG, responsywność, UX | 9 | [`demo/index.html`](demo/index.html) |
| §5 użycie AI | 16 | krok 16 |
| §6 uruchomienie i weryfikacja | 3, 4, 5 | [`demo/wynik/testy.txt`](demo/wynik/testy.txt), [`demo/zrzuty/`](demo/zrzuty/README.md), film <https://youtu.be/wiHsN31m_6o>, [`demo/agreguj.py`](demo/agreguj.py) |
| dane z zewnątrz przez API: opis zbioru w XML (XSD), link do CSV, suma md5, wczytanie do portalu i nocne odświeżanie | 18 | [`format_danych/przyklady/opis/`](format_danych/przyklady/opis/), [`demo/wynik/import_opisu.json`](demo/wynik/import_opisu.json) |
| dane z zewnątrz: rekordy w XML ze schematem XSD (wariant dodatkowy) | 17 | [`format_danych/przyklady/xml/`](format_danych/przyklady/xml/), [`demo/wynik/weryfikacja.txt`](demo/wynik/weryfikacja.txt) |
| §2 integracja danych wielu dysponentów w jednym zbiorze | 2, 4, 5, 19 | [`demo/wynik/raport_agregacji.txt`](demo/wynik/raport_agregacji.txt) |
| §2 nazwa akcji, logotyp, hasło | 10 | [`branding/AKCJA_DANE_PRZEZYCIE.md`](branding/AKCJA_DANE_PRZEZYCIE.md) |
| §8 kryteria oceny | 11 | krok 11 |

## Kroki

### 1. Prototyp offline

1. Proszę otworzyć [`demo/index.html`](demo/index.html) i przejść dziewięć kroków przyciskiem „Dalej”: problem, oznaczenie zbioru, publikacja zasobu, dane z zewnątrz w XML (z walidacją XSD), budowa wykazu, przegląd przez odbiorcę, pobieranie i API, zmiany w portalu, dodatek (integrator).
2. W kroku 6 proszę wybrać miejscowość „Bydgoszcz” (mapa przybliży się do 8 punktów) i kliknąć punkt lub nazwę w tabeli. Pojawi się pełny rekord z pochodzeniem: wydawcą, licencją, zasobem źródłowym i datą agregacji.
3. W kroku 7 przycisk „Pobierz CSV” daje plik identyczny z [`demo/wynik/zestawienie_aed.csv`](demo/wynik/zestawienie_aed.csv).

**Dowodzi:** prototyp działa bez sieci i konfiguracji (§4, §6). Zrzuty pochodzą z działającego portalu, a tabela i mapa z rzeczywistego wyniku funkcji agregacji.

### 2. Zmiany w kodzie portalu (główny rezultat)

1. [`ZMIANY_W_PORTALU.md`](ZMIANY_W_PORTALU.md): opis mechanizmu i lista zmienionych plików z celem każdej zmiany.
2. Dokładny diff względem nietkniętego kodu portalu (commit `a1adc22`, „Oryginalny kod portalu dane.gov.pl”):
   ```bash
   git diff --stat a1adc22 -- portal/backend
   git diff a1adc22 -- portal/backend
   ```
3. Najważniejsze nowe pliki: [`aed_utils.py`](portal/backend/mcod/resources/aed_utils.py) (wzór: `dga_utils.py`), [`aed_aggregation.py`](portal/backend/mcod/resources/aed_aggregation.py), [`aed_dedup.py`](portal/backend/mcod/resources/aed_dedup.py), [`aed_opis.py`](portal/backend/mcod/resources/aed_opis.py), [`aed_import.py`](portal/backend/mcod/resources/aed_import.py), [`aed_constants.py`](portal/backend/mcod/resources/aed_constants.py), [`tasks/aed.py`](portal/backend/mcod/resources/tasks/aed.py). Wpisy zmian: [`portal/backend/CHANGELOG.md`](portal/backend/CHANGELOG.md), sekcja „Unreleased”, AED-01 do AED-15.

**Dowodzi:** mechanizm DGA (nocny zasób zbiorczy z zasobów wielu instytucji) przerobiono na Wykaz AED. Portal rozszerzono, a nie przepisano: 34 nowe pliki (w tym 7 próbek danych testowych) i 11 istniejących z dopiskami. Jedyna zmieniona linia to sygnatura `get_beat_schedule` w `celeryapp.py`, rozszerzona o parametr opcjonalny.

### 3. Testy, brak migracji, nienaruszony DGA

1. [`demo/wynik/testy.txt`](demo/wynik/testy.txt) to log uruchomienia w kontenerze testowym portalu z 22.11.2026. Na końcu jest „270 passed, 2 skipped”, a wyżej `makemigrations --check`: „No changes detected”. Dwa pominięte testy porównują kopie schematów XSD w portalu z katalogiem `format_danych/`, którego kontener nie widzi; sprawdza je `demo/sprawdz.py`.
2. Nowe testy: pliki `test_aed_*.py` (m.in. `test_aed_dedup.py`, `test_aed_opis.py`, `test_aed_import_xml_command.py`) i [`test_main_aed_resource.py`](portal/backend/mcod/resources/tests/test_main_aed_resource.py) w [`portal/backend/mcod/resources/tests/`](portal/backend/mcod/resources/tests/) oraz [`test_aed_customfields_help.py`](portal/backend/mcod/datasets/tests/test_aed_customfields_help.py).
3. Istniejące testy DGA (`test_main_dga.py`: 53, testy DGA w `test_api.py`) przechodzą bez zmian.

**Dowodzi:** zero migracji, DGA działa jak dotąd, każda zmiana ma testy.

### 4. Wykaz AED w portalu uruchomionym we własnym środowisku

1. [`demo/zrzuty/README.md`](demo/zrzuty/README.md): podpis każdego zrzutu mówi, co widać i czego dowodzi.
2. Zrzuty w kolejności: [01](demo/zrzuty/01_formularz_zbioru_standard_aed.png) formularz zbioru z `standard = AED`, [02](demo/zrzuty/02_zasoby_dostawcow.png) zasoby dostawców, [03](demo/zrzuty/03_komenda_wykaz_statystyki.png) budowa wykazu, [04](demo/zrzuty/04_wykaz_tabela.png) tabela, [05](demo/zrzuty/05_wykaz_mapa.png) mapa, [06](demo/zrzuty/06_api_aed_aggregated.png) `/aed-aggregated`, [07](demo/zrzuty/07_api_dane_zasobu.png) dane w API z atrybucją, [09](demo/zrzuty/09_testy.png) testy.
3. Pełny log budowy wykazu: [`demo/wynik/komenda_create_main_aed_resource.txt`](demo/wynik/komenda_create_main_aed_resource.txt). Statystyki: [`demo/wynik/statystyki_agregacji.json`](demo/wynik/statystyki_agregacji.json).
4. Film <https://youtu.be/wiHsN31m_6o> (1 min 14 s, bez dźwięku) pokazuje te same ekrany w ruchu: panel dostawcy z `standard = AED`, zasób zbiorczy we froncie (tabela, mapa), odpowiedź `/aed-aggregated`. Skrócone fragmenty są oznaczone na ekranie.

**Dowodzi:** portal z modyfikacjami uruchomiono w Dockerze (backend, API, Celery, frontend) i sprawdzono w praktyce. Zasób zbiorczy ma tabelę, mapę i API portalu bez nowego frontendu.

### 5. Agregacja na realnych danych z dane.gov.pl

1. [`demo/wynik/raport_agregacji.txt`](demo/wynik/raport_agregacji.txt): realne zasoby AED (migawka z 21.11.2026 w [`references/dane_gov_pl_aed/`](references/dane_gov_pl_aed/README.md)), z informacją, który zasób przyjęto, który pominięto i dlaczego. Do realnych zasobów dochodzą przykład wzorca (8 wierszy) i fikcyjny dostawca zewnętrzny z opisem XML (7 wierszy). Deduplikacja usuwa 1 wiersz: to samo urządzenie (ten sam numer seryjny) zgłoszone przez dwóch dostawców.
2. [`demo/wynik/zestawienie_aed.csv`](demo/wynik/zestawienie_aed.csv): 38 wierszy, 52 kolumny.
3. Wynik można odtworzyć jednym poleceniem, bez bazy i Dockera ([`demo/README.md`](demo/README.md)):
   ```bash
   uv run --python 3.11 --with "pandas==1.5.3" --with "numpy<2" --with openpyxl python demo/agreguj.py
   ```

**Dowodzi:** te same funkcje agregacji i deduplikacji co w portalu ([`aed_aggregation.py`](portal/backend/mcod/resources/aed_aggregation.py), [`aed_dedup.py`](portal/backend/mcod/resources/aed_dedup.py)) scalają zasoby różnych dostawców w jedną listę, a niezgodne pomijają z podaniem powodu.

### 6. Wzorcowy zakres danych (XLSX)

1. [`format_danych/wzorcowy_zakres_danych.xlsx`](format_danych/wzorcowy_zakres_danych.xlsx) (wersja 2.1.0), arkusze:
   1. `1_Zakres_wzorca`: 42 kolumny z typem, wymagalnością (W/Z/O), minimum agregacji i grupą, w tym opcjonalny `numer_seryjny`;
   2. `2_Szablon_z_przykladami`: układ pliku dostawcy z 8 przykładowymi wierszami;
   3. `3_Slowniki`: dozwolone wartości;
   4. `4_Zasob_zbiorczy`: 52 kolumny wykazu z pochodzeniem każdej kolumny;
   5. `5_Zasady`: jednostka rekordu, identyfikatory, licencje, dane osobowe, ze źródłami.
2. Uzasadnienie decyzji: [`format_danych/UZASADNIENIE.md`](format_danych/UZASADNIENIE.md). Reguły w postaci maszynowej: `x-reguly-dodatkowe` w [`aed_punkty.tableschema.json`](format_danych/schemat/aed_punkty.tableschema.json). Opis plików: [`format_danych/README.md`](format_danych/README.md).

**Dowodzi:** wymagania §2 i §4 oraz kryterium „Wzorcowy zakres danych” (10%).

### 7. Formaty odczytywalne maszynowo

1. Dane wykazu: CSV (RFC 4180, UTF-8), [`demo/wynik/zestawienie_aed.csv`](demo/wynik/zestawienie_aed.csv).
2. [`format_danych/schemat/`](format_danych/schemat/): Table Schema wzorca i zasobu zbiorczego (z mapowaniem `geo`), CSVW, kontekst JSON-LD, słowniki JSON, metadane DCAT-AP, schematy XSD opisu zbioru (`aed_opis_zbioru.xsd`) i rekordów (`aed_punkty.xsd`).
3. W portalu wykaz jest dostępny jako CSV, JSON-LD i przez API (`/1.4/resources/{id}/data`, `/geo`, `/1.4/aed-aggregated`); zrzuty 04, 06 i 07.

**Dowodzi:** §5, format odczytywalny maszynowo (PDF tylko dla logotypu i księgi znaku).

### 8. Zgodność z zasadami portalu, ochrona danych, licencje

1. [`format_danych/UZASADNIENIE.md`](format_danych/UZASADNIENIE.md) (sekcje 3 i 4) oraz arkusz `5_Zasady`: zasady dane.gov.pl, RODO i licencje z odwołaniami do regulaminu i standardów ([`references/dane_gov_pl_baza_wiedzy/`](references/dane_gov_pl_baza_wiedzy/), [`references/standardy/`](references/standardy/)).
2. Realizacja w kodzie ([`ZMIANY_W_PORTALU.md`](ZMIANY_W_PORTALU.md)):
   - **Oznaczenie bez migracji:** istniejące „Pola niestandardowe” zbioru (`standard = AED`) zamiast nowego pola, tagu czy checkboxa (porównanie wariantów: [`UZASADNIENIE.md`](format_danych/UZASADNIENIE.md), sekcja 1). W tym samym polu import zapisuje adres opisu XML (`opis_xml`) i sumę md5 (`md5`);
   - **Licencje:** do wykazu trafiają tylko zbiory na CC0 1.0 i CC BY 4.0, a rekordy z OpenStreetMap (ODbL) są pomijane. Opis zbioru w XML dopuszcza tylko te dwie licencje;
   - **Atrybucja:** każdy wiersz ma wydawcę, licencję, identyfikator i adres zasobu źródłowego oraz datę danych;
   - **Dane osobowe:** gdy zbiór źródłowy je deklaruje, telefon i e-mail są usuwane, a `przetworzenie` ma kod `kontakt_usuniety`. `numer_seryjny` to numer z tabliczki urządzenia, nie dane osoby;
   - **Rzetelność:** puste pole statusu dostaje wartość `nieznany`, a nie „sprawny”.
3. Mechanizm używa standardowej drogi portalu: zbiór, zasób, walidacja, zasób tabelaryczny z mapą i API.

**Dowodzi:** kryterium „Zgodność z zasadami działania portalu” (30%) i §5.

### 9. Dostępność (WCAG), responsywność, UX

1. W [`demo/index.html`](demo/index.html) cały proces można przejść samą klawiaturą (Tab, Enter, Spacja). Punkty mapy są przyciskami, fokus jest widoczny.
2. Szerokość telefonu: proszę zwęzić okno lub obejrzeć [`podglad_demo_390.png`](demo/wynik/podglad_demo_390.png) (390 px) i [`podglad_demo_1440.png`](demo/wynik/podglad_demo_1440.png). Strona nie przewija się w poziomie, a szerokie tabele przewijają się we własnym obszarze.
3. Strona ma strukturę nagłówków, tabele z `scope`, `aria-current` w krokach, teksty alternatywne zrzutów i kontrast kolorów zgodny z WCAG 2.1 AA. Krój: Atkinson Hyperlegible.
4. W portalu wykaz korzysta z istniejących, dostępnych widoków tabeli i mapy, a podpowiedź w formularzu zbioru (zrzut 01) wskazuje dostawcy, co wpisać.

**Dowodzi:** §5, WCAG, responsywność i UX.

### 10. Akcja promocyjna: nazwa, hasło, logotyp, księga znaku

1. Nazwa: **Dane (prze)życie**. Hasło: **„Twoje dane – czyjeś życie.”** Opis akcji: [`branding/AKCJA_DANE_PRZEZYCIE.md`](branding/AKCJA_DANE_PRZEZYCIE.md). Porównanie 24 nazw według kryteriów jury: [`branding/NAZWY_KAMPANII.md`](branding/NAZWY_KAMPANII.md).
2. Logotyp w [`branding/logo/`](branding/logo/): [JPG](branding/logo/dane-przezycie_logo_poziome.jpg), [PNG](branding/logo/dane-przezycie_logo_poziome.png) (przezroczyste tło), [PDF](branding/logo/dane-przezycie_logo_poziome.pdf) (wektorowy), [SVG](branding/logo/dane-przezycie_logo_poziome.svg) (format otwarty). Te same cztery formaty mają wersje: z hasłem, pionowa, sam znak i sygnet; negatywy w SVG i PNG, wersje jednobarwne w SVG.
3. Księga znaku: [`branding/ksiega_znaku.pdf`](branding/ksiega_znaku.pdf), 12 stron: koncepcja (5 zdań) i zasady komunikacji, budowa i wersje znaku, kolorystyka (HEX, RGB, CMYK, kontrast WCAG), pole ochronne, minimalna wielkość (test ekranowy), niedozwolone użycia, typografia, zastosowania (naklejka na szafkę AED, odznaka dysponenta, post), pliki i prawa.
4. Materiały akcji: [`branding/materialy/`](branding/materialy/).

**Dowodzi:** §2 i §4 oraz kryterium „Logotyp i hasło” (25%).

### 11. Kryteria oceny (§8)

| Kryterium | Waga | Dowody |
|---|---|---|
| Zgodność z zasadami działania portalu | 30% | kroki 2, 3, 8: mechanizm na wzór DGA, zero migracji, licencje i dane osobowe |
| Logotyp i hasło | 25% | krok 10 |
| Kreatywność i innowacyjność | 15% | kroki 1, 8, 18 i 19: oznaczenie przez „Pola niestandardowe” bez migracji, kontrola zasobów po kolumnach, kolumny pochodzenia i przetworzenia, opis zbioru w XML z sumą md5, deduplikacja po numerze seryjnym, prototyp offline |
| Zgodność z tematem wyzwania | 15% | kroki 4, 5 i 19: jeden ogólnopolski wykaz z wielu źródeł, bez powtórzeń tego samego urządzenia, ze statusem urządzenia, dostępnością i mapą |
| Wzorcowy zakres danych | 10% | krok 6 |
| Prezentacja | 5% | krok 13 |

### 12. Opis projektu

[`README.md`](README.md): tytuł, opis rozwiązania i części repozytorium.

### 13. Prezentacja

1. [`prezentacja/dane_przezycie_prezentacja.pdf`](prezentacja/dane_przezycie_prezentacja.pdf), 28 slajdów. Wersja edytowalna: [`.pptx`](prezentacja/dane_przezycie_prezentacja.pptx).
2. Slajdy 8–9, 11–14 i 16–21 to dowody (zrzuty integratora: 23–24): zrzuty z portalu uruchomionego lokalnie, z podpisami zgodnymi z [`demo/zrzuty/README.md`](demo/zrzuty/README.md).
3. Problem i źródła: slajdy 2–3, z potrzeb do pól wzorca: 4–6, mechanizm: 7. Kroki dostawcy: 8–9. Integracja przez API (opis XML, XSD, CSV, md5): 10–13. Scalanie: 14. Deduplikacja: 15–17. Kroki odbiorcy: 18–20. Integrator (dodatek): 22–24. Ograniczenia: 25. Akcja: 26–27. Użycie AI: 28.

**Dowodzi:** §4 (min. 5 slajdów ze zrzutami, opis funkcji i kroków użytkownika, lista ograniczeń).

### 14. Dodatek: integrator danych

Integrator nie jest głównym rezultatem. Wykaz AED działa bez niego. Dodatek pokazuje, jak dostawcy bez wzorcowego formatu (m.in. Warszawa i Gdańsk) mogą przygotować dane.

Proszę otworzyć [`integrator/README.md`](integrator/README.md) i [`demo/integrator/`](demo/integrator/README.md) (wyniki wygenerowane poleceniem `python integrator/generuj_demo.py` na realnych plikach, bez internetu):

- [`warszawa_wzorcowy_v2.csv`](demo/integrator/warszawa_wzorcowy_v2.csv): odpowiedź API Warszawy przepisana na 42 kolumny wzorca, z jawną licencją CC BY 4.0 i dysponentem. Portal sam nie tworzy z tych danych tabeli;
- [`raport_warszawa.json`](demo/integrator/raport_warszawa.json): 1 wiersz poprawny, licencja przeszła kontrolę dla celu „portal”;
- [`raport_duplikatow.json`](demo/integrator/raport_duplikatow.json): kandydaci na duplikaty tylko flagowani, bez scalania (scala dopiero portal przy budowie wykazu, krok 19);
- [`raport_porownania_osm.json`](demo/integrator/raport_porownania_osm.json): porównanie wykazu z OSM, z oznaczeniem licencji ODbL (nie do publikacji);
- [`statystyka_gdansk.json`](demo/integrator/statystyka_gdansk.json): 503 pojazdy, 278 z AED, zero wierszy punktowych (dane flotowe).

Opis zbioru dla portalu: podkomenda `python integrator/importer.py opis aed.csv --link-csv https://… --tytul … --opis … --dysponent … --licencja "CC BY 4.0" --czestotliwosc daily` zapisuje `opis.xml` zgodny z `aed_opis_zbioru.xsd`, z sumą md5 pliku CSV (sekcja „Opis zbioru XML + CSV + md5” w [`integrator/README.md`](integrator/README.md)). Oba pliki dostawca wystawia pod https, a portal zaczytuje je jak w kroku 18.

Lokalny interfejs: `python integrator/ui/serwer.py`, adres `http://127.0.0.1:8765/`. Działa offline, nasłuchuje tylko na 127.0.0.1 i nic nie zapisuje na dysku. Testy bez Dockera: `python -m unittest discover -s integrator/testy -t .` (97 testów).

### 15. Ograniczenia

- **Zakres:** integrator jest dodatkiem i nie zmienia `portal/` (schemat źródła wg Table Schema odłożono). Kolizje nazwy akcji (UPRP, EUIPO, domeny) nie zostały sprawdzone.
- **Realne źródła w większości nie wchodzą do wykazu**, bo nie mają kolumn wzorca. Portal podaje powód ([`raport_agregacji.txt`](demo/wynik/raport_agregacji.txt)): Krosno nie ma kolumny miejscowości; Przemyśl ma CSV bez współrzędnych, a pozostałe dystrybucje są nietabelaryczne; Marki mają wadliwe pliki; Warszawa udostępnia stronę WWW, a dane są w API z tokenem. Przyjęto Legionowo (24 punkty).
- **Pierwszy import opisu zbioru uruchamia administrator** komendą `import_aed_xml` z identyfikatorem instytucji dostawcy. Dopiero potem zbiór jest odświeżany co noc (4:05). Formularza zgłoszenia opisu w panelu nie ma.
- **Deduplikacja jest ostrożna:** bez numeru seryjnego łączy wiersze tylko między różnymi zasobami, na podstawie producenta lub modelu i odległości do 30 m albo nazwy i odległości do 10 m. Dwa AED w jednym miejscu z jednego pliku bez numerów seryjnych zostają dwoma wierszami. Duplikat bez producenta, modelu, numeru i z inną nazwą nie zostanie wykryty.
- **Gdańsk** (AED w 278 pojazdach) to dane flotowe, poza zakresem wykazu.
- **Typy zgadywane przez portal:** jego walidacja może odrzucić plik zgodny ze wzorcem (np. „5A” w numerze budynku). Wykaz czyta wtedy plik wprost, ale zasób dostawcy ma w panelu czerwony znak (zrzut 02).
- **Środowisko lokalne:** mapa w `ng serve` wymaga `"prebundle": false`. Do zrzutów użyto kopii `angular.json`, bez zmiany pliku w repozytorium ([`demo/zrzuty/README.md`](demo/zrzuty/README.md)).
- Opcjonalnej strony „Wykaz AED” we frontendzie nie wykonano; wykaz korzysta ze standardowej strony zasobu.

### 16. Użycie sztucznej inteligencji

Zespół korzystał z asystentów AI (Claude, Cursor) do wsparcia analizy kodu portalu, pisania kodu i implementacji testów oraz do wsparcia tworzenia księgi znaku i plików znaku (skrypt `branding/build_branding.py`). Asystenci pomagali też w redakcji dokumentów, automatyzacji zrzutów ekranu i składaniu prezentacji (`prezentacja/build_prezentacja.js`).

Kierunek rozwiązania wybrał i zweryfikował zespół: przeróbka DGA zamiast osobnej aplikacji, oznaczenie przez „Pola niestandardowe”, struktura danych, zasady licencji i ochrony danych oraz nazwa akcji, hasło i koncepcja znaku. Każdą zmianę zespół przejrzał i sprawdził testami oraz w uruchomionym portalu. Uzasadnienie decyzji: [`format_danych/UZASADNIENIE.md`](format_danych/UZASADNIENIE.md).

### 17. Dane z zewnątrz, wariant dodatkowy: rekordy AED w XML ze schematem XSD

Dostawca może wystawić same rekordy AED w XML pod adresem https, a w panelu portalu dodać zasób z linkiem do tego pliku. Nocne zadanie pobiera plik, waliduje go schematem XSD, zamienia na kolumny wzorca i scala z pozostałymi źródłami (CSV, XLSX). Plik niezgodny z XSD jest pomijany z powodem w logu. Główną drogą dla dostawców spoza portalu jest opis zbioru z krokiem 18.

1. Schemat: [`format_danych/schemat/aed_punkty.xsd`](format_danych/schemat/aed_punkty.xsd), generowany z Table Schema wzorca (`python format_danych/narzedzia/generuj_xsd.py`). Struktura płaska: `<wykaz><aed>…</aed></wykaz>`, jedno pole wzorca to jeden element.
2. Przykłady (dane fikcyjne): [`aed_poprawny.xml`](format_danych/przyklady/xml/aed_poprawny.xml) (6 rekordów) i [`aed_bledny.xml`](format_danych/przyklady/xml/aed_bledny.xml) (3 błędy). Raport walidacji, z numerem linii i polem: [`demo/wynik/walidacja_xml.json`](demo/wynik/walidacja_xml.json).
3. Kod w portalu: [`aed_xml.py`](portal/backend/mcod/resources/aed_xml.py) (walidacja i konwersja, bez Django, XXE zablokowane) i punkt zaczepienia w [`aed_utils.py`](portal/backend/mcod/resources/aed_utils.py). Testy: `test_aed_xml.py`, `test_aed_xml_source.py`.
4. Wynik scalenia XML i CSV dwóch dostawców: [`demo/wynik/wykaz_xml_i_csv.csv`](demo/wynik/wykaz_xml_i_csv.csv) (14 wierszy, 52 kolumny, pochodzenie każdego wiersza).
5. Dowody z działającego portalu (zrzuty 10–15, [`demo/zrzuty/README.md`](demo/zrzuty/README.md)): zewnętrzny serwer dostawcy, walidacja XSD, zasób z linkiem w panelu (typ API, format XML), log nocnego zadania (zasób niezgodny z XSD pominięty, poprawny przyjęty: 38 wierszy), tabela i mapa Wykazu z rekordami z XML. Log: [`demo/wynik/komenda_create_main_aed_resource_xml.txt`](demo/wynik/komenda_create_main_aed_resource_xml.txt).
6. Serwer dostawcy do własnego uruchomienia: [`demo/serwer_zewnetrzny.py`](demo/serwer_zewnetrzny.py) (adres `/aed.xml`), opcjonalnie przez ngrok: [`demo/NGROK.md`](demo/NGROK.md).

**Dowodzi:** dane z zewnątrz w XML ze schematem XSD są wczytywane do portalu jako zasoby i scalane tym samym mechanizmem co pozostałe źródła (§2, §5).

### 18. Dane z zewnątrz przez API: opis zbioru w XML, link do CSV i suma md5

Dostawca spoza dane.gov.pl wystawia w swoim API (pod https) dwa pliki: CSV zgodny ze wzorcem i opis zbioru w XML. Opis ma metadane zbioru, link do CSV i sumę md5 tego pliku. Przepływ: opis XML (kod 200) → walidacja XSD → pobranie CSV → zgodność md5 → kontrola kolumn → zbiór i zasób w portalu → nocne odświeżenie opisu (4:05) → budowa wykazu z deduplikacją (4:15, krok 19).

1. Schemat opisu: [`format_danych/schemat/aed_opis_zbioru.xsd`](format_danych/schemat/aed_opis_zbioru.xsd): tytuł, opis, dysponent, licencja (`CC0 1.0` albo `CC BY 4.0`), częstotliwość i data aktualizacji oraz `zasob` z linkiem https do CSV, formatem `csv` i sumą md5.
2. Przykłady (dane fikcyjne) w [`format_danych/przyklady/opis/`](format_danych/przyklady/opis/): [`opis_poprawny.xml`](format_danych/przyklady/opis/opis_poprawny.xml) (md5 zgodne z CSV), [`opis_bledny_md5.xml`](format_danych/przyklady/opis/opis_bledny_md5.xml) (zgodny z XSD, md5 niezgodne), [`opis_bledny_xsd.xml`](format_danych/przyklady/opis/opis_bledny_xsd.xml) (brak tytułu, link http, licencja spoza listy), [`aed_dostawcy.csv`](format_danych/przyklady/opis/aed_dostawcy.csv) (42 kolumny, 7 rekordów).
3. Wynik kontroli wykonanych funkcjami portalu, do odczytu: [`demo/wynik/import_opisu.json`](demo/wynik/import_opisu.json) (XSD, md5, kontrola CSV, odpowiedzi serwera dostawcy) i odpowiednie pozycje w [`demo/wynik/weryfikacja.txt`](demo/wynik/weryfikacja.txt).
4. Kod w portalu: [`aed_opis.py`](portal/backend/mcod/resources/aed_opis.py) (walidacja XSD, md5, kontrola CSV, bez Django), [`aed_import.py`](portal/backend/mcod/resources/aed_import.py) (pobranie tylko z https i przy kodzie 200, zapis zbioru i zasobu w jednej transakcji), komenda [`import_aed_xml.py`](portal/backend/mcod/resources/management/commands/import_aed_xml.py):
   ```bash
   python manage.py import_aed_xml <adres https opisu> --organizacja <ID> [--dry-run]
   python manage.py import_aed_xml --odswiez
   ```
   Przy każdej niezgodności komenda kończy się komunikatem „Import odrzucony, nic nie zapisano: …”. Zbiór dostaje w „Polach niestandardowych” `standard = AED`, `opis_xml` (adres opisu) i `md5`. Ponowny import z tą samą sumą md5 nic nie zmienia, a z nową usuwa stary zasób i tworzy nowy. Testy: `test_aed_opis.py`, `test_aed_import_xml_command.py`.
5. Nocne odświeżenie: zadanie Celery `refresh_aed_opis_task` ([`tasks/aed.py`](portal/backend/mcod/resources/tasks/aed.py), wpis harmonogramu `aed_opis_refresh` o 4:05 w `celeryapp.py`) wywołuje `refresh_imported_datasets()`, tę samą funkcję co `--odswiez`. Odrzucony opis zostawia zbiór bez zmian, z ostrzeżeniem w logu. Zadanie działa tylko przy włączonym `AED_AGGREGATION_ENABLED`. Testy: `test_aed_task.py`.
6. Serwer dostawcy: [`demo/serwer_zewnetrzny.py`](demo/serwer_zewnetrzny.py) wydaje `/opis.xml`, `/aed.csv`, oba błędne opisy i `/stan`; każdy z tych adresów odpowiada kodem 200. Link do CSV w opisie podstawia z adresu, pod którym serwer jest widoczny.
7. Dowody z portalu uruchomionego lokalnie (22.11.2026, [`demo/zrzuty/README.md`](demo/zrzuty/README.md)): [16](demo/zrzuty/16_opis_xml_dostawcy.png) opis XML i CSV na serwerze dostawcy, md5 zgodne; [17](demo/zrzuty/17_import_opisu_komenda.png) komenda importu: poprawny opis przyjęty (zbiór 4251, zasób 40253), opis z błędną sumą md5 i opis niezgodny z XSD odrzucone z kodem 1 bez zapisu, powtórka bez zmian; [18](demo/zrzuty/18_zbior_z_opisu_w_panelu.png) zbiór w panelu z `standard`, `opis_xml` i `md5`; [20](demo/zrzuty/20_zasob_csv_z_opisu_w_panelu.png) zasób CSV z opisu w panelu. Log: [`demo/wynik/komenda_import_aed_xml.txt`](demo/wynik/komenda_import_aed_xml.txt).

**Dowodzi:** portal waliduje dane z zewnątrz w serwisie (XSD, md5) i dopiero wtedy je zaciąga; niezgodny opis lub plik nie zmienia niczego w bazie (§2, §5).

### 19. Deduplikacja w Wykazie AED

To samo urządzenie zgłoszone przez dwóch dostawców trafia do wykazu raz. Deduplikacja działa przy każdej budowie wykazu, dla wszystkich źródeł.

1. Reguły ([`aed_dedup.py`](portal/backend/mcod/resources/aed_dedup.py), opis w [`ZMIANY_W_PORTALU.md`](ZMIANY_W_PORTALU.md), sekcja „Deduplikacja”):
   - ten sam numer seryjny to to samo urządzenie, także w jednym pliku, chyba że oba wiersze podają różnych producentów; wartości w rodzaju „brak” i numery krótsze niż 4 znaki nie są numerem;
   - tylko między różnymi zasobami: ten sam producent lub model w odległości do 30 m albo, gdy brakuje producenta, ta sama nazwa lokalizacji w odległości do 10 m;
   - różne numery seryjne, producenci, modele lub kondygnacje wykluczają połączenie;
   - zostaje wiersz lepiej zweryfikowany, potem nowszy; puste `producent`, `model` i `numer_seryjny` uzupełnia się z duplikatu.
2. Kolumna `numer_seryjny` jest we wzorcu od wersji 2.1.0 (opcjonalna, po `model`).
3. Wynik w portalu uruchomionym lokalnie (zasób wykazu 40258): 45 wierszy przed deduplikacją, 38 po, 7 duplikatów. Jeden to urządzenie `BYD-HALA-A` z CSV dostawcy, to samo co `CT-01` z przykładu wzorca (powód `numer_seryjny`). Sześć to te same rekordy dostawcy podane raz w zasobie XML (40250), a raz w CSV z opisu (40253), z powodem `nazwa_i_lokalizacja`. Dowody: zrzuty [19](demo/zrzuty/19_wykaz_deduplikacja.png) (log budowy wykazu), [21](demo/zrzuty/21_api_wykaz_numer_seryjny.png) (API: 38 wierszy, 52 kolumny, numer seryjny uzupełniony z duplikatu), [22](demo/zrzuty/22_wykaz_tabela_opis.png) i [23](demo/zrzuty/23_wykaz_mapa_opis.png) (tabela i mapa); log [`komenda_create_main_aed_resource_opis.txt`](demo/wynik/komenda_create_main_aed_resource_opis.txt), statystyki [`statystyki_opis_dedup.json`](demo/wynik/statystyki_opis_dedup.json), wykaz [`wykaz_opis_xml_dedup.csv`](demo/wynik/wykaz_opis_xml_dedup.csv).
4. Przykład do odczytu bez portalu: w [`demo/wynik/raport_agregacji.txt`](demo/wynik/raport_agregacji.txt) (ostatnie linie) deduplikacja pomija 1 z 39 wierszy z powodem `numer_seryjny`; ten sam przypadek opisuje pozycja o deduplikacji w [`demo/wynik/weryfikacja.txt`](demo/wynik/weryfikacja.txt).
5. W portalu statystyki budowy wykazu mają `wiersze_zdeduplikowane` i listę `duplikaty` (zachowany, pominięty, powód), a każdy duplikat trafia do logu. Testy: `test_aed_dedup.py`.

**Dowodzi:** wykaz scala dane wielu dysponentów bez powtórzeń tego samego urządzenia (§2).

### 20. Opcjonalnie: wymuszenie harvestu i wersja live

1. **Wymuszenie harvestu w demo:** w portalu opisy są odświeżane o 4:05, a wykaz powstaje o 4:15. Skrypt [`demo/wymus_harvest.py`](demo/wymus_harvest.py) robi to od razu: wykonuje w kontenerze portalu `import_aed_xml --odswiez`, czeka, aż Celery zwaliduje zasób, i buduje wykaz poleceniem `create_main_aed_resource --eager`. Skrypt wymaga portalu w Dockerze. Zapis przebiegu: [`demo/wynik/wymus_harvest.txt`](demo/wynik/wymus_harvest.txt).
2. **Wersja live:** <https://thumb-abrasive-bovine.ngrok-free.dev/live/> (strona startowa). [`WERSJA_LIVE.md`](WERSJA_LIVE.md) podaje tymczasowe adresy portalu (Wykaz AED, API, panel), prototypu i serwera dostawcy przez tunel ngrok (instrukcja: [`demo/NGROK.md`](demo/NGROK.md)). To tylko dodatek: ocena według kroków 1–19 działa offline.
