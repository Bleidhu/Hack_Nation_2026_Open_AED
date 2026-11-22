# Instrukcja dla jury: Dane (prze)życie, Wykaz AED w portalu dane.gov.pl

Każde wymaganie zadania „Misja AED – Dane na ratunek” ma osobny krok: który plik otworzyć, co w nim zobaczyć i czego to dowodzi. Wszystkie dowody są plikami w repozytorium. Nie jest potrzebne logowanie, instalacja ani połączenie z serwerami zespołu. Pliki do zgłoszenia zebrano w [`ZGLOSZENIE/`](../ZGLOSZENIE/README.md).

**Najkrótsza ścieżka (5 minut):** krok 1 (prototyp), potem krok 2 (zmiany w portalu). Jeszcze szybciej: film [`demo/wideo/dane_przezycie_wykaz_aed.mp4`](../demo/wideo/dane_przezycie_wykaz_aed.mp4) (1 min 49 s) z nagraniem działającego portalu i prototypu (krok 4).

## Krok 0: otwarcie paczki

1. Proszę rozpakować archiwum ZIP albo sklonować repozytorium.
2. Pliki `.md` można czytać w przeglądarce lub edytorze, pliki `.csv` w arkuszu (UTF-8, separator przecinek), a `.png` i `.pdf` w przeglądarce.
3. Prototyp [`demo/index.html`](../demo/index.html) otwiera się dwuklikiem. Działa z dysku, bez sieci, w Chrome, Edge i Firefox.

## Mapa wymagań

| Wymaganie | Krok | Główny plik |
|---|---|---|
| §4 opis i tytuł projektu | 12 | [`README.md`](../README.md) |
| §4 prezentacja (min. 5 slajdów ze zrzutami, kroki użytkownika, ograniczenia) | 13 | [`prezentacja/dane_przezycie_prezentacja.pdf`](../prezentacja/dane_przezycie_prezentacja.pdf) |
| §4 prototyp rozwiązania | 1, 2, 4 | [`demo/index.html`](../demo/index.html), [`portal/backend/`](../portal/backend/) |
| §4 wzorcowy zakres danych (XLSX) | 6 | [`format_danych/wzorcowy_zakres_danych.xlsx`](../format_danych/wzorcowy_zakres_danych.xlsx) |
| §4 kod źródłowy | 2, 3 | [`ZMIANY_W_PORTALU.md`](../ZMIANY_W_PORTALU.md) |
| §4 logotyp (.jpg .png .pdf, format otwarty) i księga znaku | 10 | [`branding/logo/`](../branding/logo/), [`branding/ksiega_znaku.pdf`](../branding/ksiega_znaku.pdf) |
| §5 format odczytywalny maszynowo | 7 | [`format_danych/schemat/`](../format_danych/schemat/) |
| §5 zgodność z zasadami portalu | 2, 8 | [`format_danych/UZASADNIENIE.md`](../format_danych/UZASADNIENIE.md), [`ZMIANY_W_PORTALU.md`](../ZMIANY_W_PORTALU.md) |
| §5 WCAG, responsywność, UX | 9 | [`demo/index.html`](../demo/index.html) |
| §5 użycie AI | 16 | krok 16 |
| §6 uruchomienie i weryfikacja | 3, 4, 5 | [`demo/wynik/testy.txt`](../demo/wynik/testy.txt), [`demo/zrzuty/`](../demo/zrzuty/README.md), [`demo/wideo/`](../demo/wideo/README.md), [`demo/agreguj.py`](../demo/agreguj.py) |
| §2 integracja danych wielu dysponentów w jednym zbiorze | 2, 4, 5 | [`demo/wynik/raport_agregacji.txt`](../demo/wynik/raport_agregacji.txt) |
| §2 nazwa akcji, logotyp, hasło | 10 | [`branding/AKCJA_DANE_PRZEZYCIE.md`](../branding/AKCJA_DANE_PRZEZYCIE.md) |
| §8 kryteria oceny | 11 | krok 11 |

## Kroki

### 1. Prototyp offline

1. Proszę otworzyć [`demo/index.html`](../demo/index.html) i przejść siedem kroków przyciskiem „Dalej”: problem, oznaczenie zbioru przez dostawcę, publikacja zasobu, budowa wykazu, przegląd przez odbiorcę, pobieranie i API, zmiany w portalu.
2. W kroku 5 proszę wybrać miejscowość „Bydgoszcz” (mapa przybliży się do 8 punktów) i kliknąć punkt lub nazwę w tabeli. Pojawi się pełny rekord z pochodzeniem: wydawcą, licencją, zasobem źródłowym i datą agregacji.
3. W kroku 6 przycisk „Pobierz CSV” daje plik identyczny z [`demo/wynik/zestawienie_aed.csv`](../demo/wynik/zestawienie_aed.csv).

**Dowodzi:** prototyp działa bez sieci i konfiguracji (§4, §6). Zrzuty pochodzą z działającego portalu, a tabela i mapa z rzeczywistego wyniku funkcji agregacji.

### 2. Zmiany w kodzie portalu (główny rezultat)

1. [`ZMIANY_W_PORTALU.md`](../ZMIANY_W_PORTALU.md): opis mechanizmu i lista zmienionych plików z celem każdej zmiany.
2. Dokładny diff względem nietkniętego kodu portalu (commit `a1adc22`, „Oryginalny kod portalu dane.gov.pl”):
   ```bash
   git diff --stat a1adc22 -- portal/backend
   git diff a1adc22 -- portal/backend
   ```
3. Najważniejsze nowe pliki: [`aed_utils.py`](../portal/backend/mcod/resources/aed_utils.py) (wzór: `dga_utils.py`), [`aed_aggregation.py`](../portal/backend/mcod/resources/aed_aggregation.py), [`aed_constants.py`](../portal/backend/mcod/resources/aed_constants.py), [`tasks/aed.py`](../portal/backend/mcod/resources/tasks/aed.py). Wpisy zmian: [`portal/backend/CHANGELOG.md`](../portal/backend/CHANGELOG.md), sekcja „Unreleased”, AED-01 do AED-10.

**Dowodzi:** mechanizm DGA (nocny zasób zbiorczy z zasobów wielu instytucji) przerobiono na Wykaz AED. Portal rozszerzono, a nie przepisano: 22 nowe pliki i 11 istniejących z dopiskami. Jedyna zmieniona linia to sygnatura `get_beat_schedule` w `celeryapp.py`, rozszerzona o parametr opcjonalny.

### 3. Testy, brak migracji, nienaruszony DGA

1. [`demo/wynik/testy.txt`](../demo/wynik/testy.txt) to log uruchomienia w kontenerze testowym portalu z 22.11.2026. Na końcu jest „192 passed”, a wyżej `makemigrations --check`: „No changes detected”.
2. Nowe testy: pliki `test_aed_*.py` i [`test_main_aed_resource.py`](../portal/backend/mcod/resources/tests/test_main_aed_resource.py) w [`portal/backend/mcod/resources/tests/`](../portal/backend/mcod/resources/tests/) oraz [`test_aed_customfields_help.py`](../portal/backend/mcod/datasets/tests/test_aed_customfields_help.py).
3. Istniejące testy DGA (`test_main_dga.py`: 53, testy DGA w `test_api.py`) przechodzą bez zmian.

**Dowodzi:** zero migracji, DGA działa jak dotąd, każda zmiana ma testy.

### 4. Wykaz AED w portalu uruchomionym we własnym środowisku

1. [`demo/zrzuty/README.md`](../demo/zrzuty/README.md): podpis każdego zrzutu mówi, co widać i czego dowodzi.
2. Zrzuty w kolejności: [01](../demo/zrzuty/01_formularz_zbioru_standard_aed.png) formularz zbioru z `standard = AED`, [02](../demo/zrzuty/02_zasoby_dostawcow.png) zasoby dostawców, [03](../demo/zrzuty/03_komenda_wykaz_statystyki.png) budowa wykazu, [04](../demo/zrzuty/04_wykaz_tabela.png) tabela, [05](../demo/zrzuty/05_wykaz_mapa.png) mapa, [06](../demo/zrzuty/06_api_aed_aggregated.png) `/aed-aggregated`, [07](../demo/zrzuty/07_api_dane_zasobu.png) dane w API z atrybucją, [09](../demo/zrzuty/09_testy.png) testy.
3. Pełny log budowy wykazu: [`demo/wynik/komenda_create_main_aed_resource.txt`](../demo/wynik/komenda_create_main_aed_resource.txt). Statystyki: [`demo/wynik/statystyki_agregacji.json`](../demo/wynik/statystyki_agregacji.json).
4. Film [`demo/wideo/dane_przezycie_wykaz_aed.mp4`](../demo/wideo/dane_przezycie_wykaz_aed.mp4) (1 min 49 s, bez dźwięku, opis: [`demo/wideo/README.md`](../demo/wideo/README.md)) pokazuje te same ekrany w ruchu: panel dostawcy z `standard = AED`, zasób zbiorczy we froncie (tabela, mapa), odpowiedź `/aed-aggregated` i prototyp offline. Skrócone fragmenty są oznaczone na ekranie.

**Dowodzi:** portal z modyfikacjami uruchomiono w Dockerze (backend, API, Celery, frontend) i sprawdzono w praktyce. Zasób zbiorczy ma tabelę, mapę i API portalu bez nowego frontendu.

### 5. Agregacja na realnych danych z dane.gov.pl

1. [`demo/wynik/raport_agregacji.txt`](../demo/wynik/raport_agregacji.txt): realne zasoby AED (migawka z 21.11.2026 w [`references/dane_gov_pl_aed/`](../references/dane_gov_pl_aed/README.md)), z informacją, który zasób przyjęto, który pominięto i dlaczego.
2. [`demo/wynik/zestawienie_aed.csv`](../demo/wynik/zestawienie_aed.csv): 32 wiersze, 51 kolumn.
3. Wynik można odtworzyć jednym poleceniem, bez bazy i Dockera ([`demo/README.md`](../demo/README.md)):
   ```bash
   uv run --python 3.11 --with "pandas==1.5.3" --with "numpy<2" --with openpyxl python demo/agreguj.py
   ```

**Dowodzi:** ta sama funkcja agregacji co w portalu ([`aed_aggregation.py`](../portal/backend/mcod/resources/aed_aggregation.py)) scala zasoby różnych dostawców w jedną listę, a niezgodne pomija z podaniem powodu.

### 6. Wzorcowy zakres danych (XLSX)

1. [`format_danych/wzorcowy_zakres_danych.xlsx`](../format_danych/wzorcowy_zakres_danych.xlsx), arkusze:
   1. `1_Zakres_wzorca`: 41 kolumn z typem, wymagalnością (W/Z/O), minimum agregacji i grupą;
   2. `2_Szablon_z_przykladami`: układ pliku dostawcy z 8 przykładowymi wierszami;
   3. `3_Slowniki`: dozwolone wartości;
   4. `4_Zasob_zbiorczy`: 51 kolumn wykazu z pochodzeniem każdej kolumny;
   5. `5_Zasady`: jednostka rekordu, identyfikatory, licencje, dane osobowe, ze źródłami.
2. Uzasadnienie decyzji: [`format_danych/UZASADNIENIE.md`](../format_danych/UZASADNIENIE.md). Reguły w postaci maszynowej: `x-reguly-dodatkowe` w [`aed_punkty.tableschema.json`](../format_danych/schemat/aed_punkty.tableschema.json). Opis plików: [`format_danych/README.md`](../format_danych/README.md).

**Dowodzi:** wymagania §2 i §4 oraz kryterium „Wzorcowy zakres danych” (10%).

### 7. Formaty odczytywalne maszynowo

1. Dane wykazu: CSV (RFC 4180, UTF-8), [`demo/wynik/zestawienie_aed.csv`](../demo/wynik/zestawienie_aed.csv).
2. [`format_danych/schemat/`](../format_danych/schemat/): Table Schema wzorca i zasobu zbiorczego (z mapowaniem `geo`), CSVW, kontekst JSON-LD, słowniki JSON, metadane DCAT-AP.
3. W portalu wykaz jest dostępny jako CSV, JSON-LD i przez API (`/1.4/resources/{id}/data`, `/geo`, `/1.4/aed-aggregated`); zrzuty 04, 06 i 07.

**Dowodzi:** §5, format odczytywalny maszynowo (PDF tylko dla logotypu i księgi znaku).

### 8. Zgodność z zasadami portalu, ochrona danych, licencje

1. [`format_danych/UZASADNIENIE.md`](../format_danych/UZASADNIENIE.md) (sekcje 3 i 4) oraz arkusz `5_Zasady`: zasady dane.gov.pl, RODO i licencje z odwołaniami do regulaminu i standardów ([`references/dane_gov_pl_baza_wiedzy/`](../references/dane_gov_pl_baza_wiedzy/), [`references/standardy/`](../references/standardy/)).
2. Realizacja w kodzie ([`ZMIANY_W_PORTALU.md`](../ZMIANY_W_PORTALU.md)):
   - **Oznaczenie bez migracji:** istniejące „Pola niestandardowe” zbioru (`standard = AED`) zamiast nowego pola, tagu czy checkboxa (porównanie wariantów: [`UZASADNIENIE.md`](../format_danych/UZASADNIENIE.md), sekcja 1);
   - **Licencje:** do wykazu trafiają tylko zbiory na CC0 1.0 i CC BY 4.0, a rekordy z OpenStreetMap (ODbL) są pomijane;
   - **Atrybucja:** każdy wiersz ma wydawcę, licencję, identyfikator i adres zasobu źródłowego oraz datę danych;
   - **Dane osobowe:** gdy zbiór źródłowy je deklaruje, telefon i e-mail są usuwane, a `przetworzenie` ma kod `kontakt_usuniety`;
   - **Rzetelność:** puste pole statusu dostaje wartość `nieznany`, a nie „sprawny”.
3. Mechanizm używa standardowej drogi portalu: zbiór, zasób, walidacja, zasób tabelaryczny z mapą i API.

**Dowodzi:** kryterium „Zgodność z zasadami działania portalu” (30%) i §5.

### 9. Dostępność (WCAG), responsywność, UX

1. W [`demo/index.html`](../demo/index.html) cały proces można przejść samą klawiaturą (Tab, Enter, Spacja). Punkty mapy są przyciskami, fokus jest widoczny.
2. Szerokość telefonu: proszę zwęzić okno lub obejrzeć [`podglad_demo_390.png`](../demo/wynik/podglad_demo_390.png) (390 px) i [`podglad_demo_1440.png`](../demo/wynik/podglad_demo_1440.png). Strona nie przewija się w poziomie, a szerokie tabele przewijają się we własnym obszarze.
3. Strona ma strukturę nagłówków, tabele z `scope`, `aria-current` w krokach, teksty alternatywne zrzutów i kontrast kolorów zgodny z WCAG 2.1 AA. Krój: Atkinson Hyperlegible.
4. W portalu wykaz korzysta z istniejących, dostępnych widoków tabeli i mapy, a podpowiedź w formularzu zbioru (zrzut 01) wskazuje dostawcy, co wpisać.

**Dowodzi:** §5, WCAG, responsywność i UX.

### 10. Akcja promocyjna: nazwa, hasło, logotyp, księga znaku

1. Nazwa: **Dane (prze)życie**. Hasło: **„Twoje dane – czyjeś życie.”** Opis akcji: [`branding/AKCJA_DANE_PRZEZYCIE.md`](../branding/AKCJA_DANE_PRZEZYCIE.md). Porównanie 24 nazw według kryteriów jury: [`branding/NAZWY_KAMPANII.md`](../branding/NAZWY_KAMPANII.md).
2. Logotyp w [`branding/logo/`](../branding/logo/): [JPG](../branding/logo/dane-przezycie_logo_poziome.jpg), [PNG](../branding/logo/dane-przezycie_logo_poziome.png) (przezroczyste tło), [PDF](../branding/logo/dane-przezycie_logo_poziome.pdf) (wektorowy), [SVG](../branding/logo/dane-przezycie_logo_poziome.svg) (format otwarty). Te same cztery formaty mają wersje: z hasłem, pionowa, sam znak i sygnet; negatywy w SVG i PNG, wersje jednobarwne w SVG.
3. Księga znaku: [`branding/ksiega_znaku.pdf`](../branding/ksiega_znaku.pdf), 12 stron: koncepcja (5 zdań) i zasady komunikacji, budowa i wersje znaku, kolorystyka (HEX, RGB, CMYK, kontrast WCAG), pole ochronne, minimalna wielkość (test ekranowy), niedozwolone użycia, typografia, zastosowania (naklejka na szafkę AED, odznaka dysponenta, post), pliki i prawa.
4. Materiały akcji: [`branding/materialy/`](../branding/materialy/).

**Dowodzi:** §2 i §4 oraz kryterium „Logotyp i hasło” (25%).

### 11. Kryteria oceny (§8)

| Kryterium | Waga | Dowody |
|---|---|---|
| Zgodność z zasadami działania portalu | 30% | kroki 2, 3, 8: mechanizm na wzór DGA, zero migracji, licencje i dane osobowe |
| Logotyp i hasło | 25% | krok 10 |
| Kreatywność i innowacyjność | 15% | kroki 1 i 8: oznaczenie przez „Pola niestandardowe” bez migracji, kontrola zasobów po kolumnach, kolumny pochodzenia i przetworzenia, prototyp offline |
| Zgodność z tematem wyzwania | 15% | kroki 4 i 5: jeden ogólnopolski wykaz z wielu źródeł, ze statusem urządzenia, dostępnością i mapą |
| Wzorcowy zakres danych | 10% | krok 6 |
| Prezentacja | 5% | krok 13 |

### 12. Opis projektu

[`README.md`](../README.md): tytuł, opis rozwiązania i części repozytorium.

### 13. Prezentacja

1. [`prezentacja/dane_przezycie_prezentacja.pdf`](../prezentacja/dane_przezycie_prezentacja.pdf), 15 slajdów. Wersja edytowalna: [`.pptx`](../prezentacja/dane_przezycie_prezentacja.pptx).
2. Slajdy 4–10 to dowody: zrzuty z portalu uruchomionego lokalnie, z podpisami zgodnymi z [`demo/zrzuty/README.md`](../demo/zrzuty/README.md).
3. Kroki dostawcy: slajdy 4–5, odbiorcy: 7–9. Ograniczenia: 13. Integrator: 14. Użycie AI: 15.

**Dowodzi:** §4 (min. 5 slajdów ze zrzutami, opis funkcji i kroków użytkownika, lista ograniczeń).

### 14. Dodatek: integrator danych

Integrator nie jest głównym rezultatem. Wykaz AED działa bez niego. Dodatek pokazuje, jak dostawcy bez wzorcowego formatu (m.in. Warszawa i Gdańsk) mogą przygotować dane.

Proszę otworzyć [`integrator/README.md`](../integrator/README.md) i [`demo/integrator/`](../demo/integrator/README.md) (wyniki wygenerowane poleceniem `python integrator/generuj_demo.py` na realnych plikach, bez internetu):

- [`warszawa_wzorcowy_v2.csv`](../demo/integrator/warszawa_wzorcowy_v2.csv): odpowiedź API Warszawy przepisana na 41 kolumn wzorca, z jawną licencją CC BY 4.0 i dysponentem. Portal sam nie tworzy z tych danych tabeli;
- [`raport_warszawa.json`](../demo/integrator/raport_warszawa.json): 1 wiersz poprawny, licencja przeszła kontrolę dla celu „portal”;
- [`raport_duplikatow.json`](../demo/integrator/raport_duplikatow.json): kandydaci na duplikaty tylko flagowani, bez scalania;
- [`raport_porownania_osm.json`](../demo/integrator/raport_porownania_osm.json): porównanie wykazu z OSM, z oznaczeniem licencji ODbL (nie do publikacji);
- [`statystyka_gdansk.json`](../demo/integrator/statystyka_gdansk.json): 503 pojazdy, 278 z AED, zero wierszy punktowych (dane flotowe).

Lokalny interfejs: `python integrator/ui/serwer.py`, adres `http://127.0.0.1:8765/`. Działa offline, nasłuchuje tylko na 127.0.0.1 i nic nie zapisuje na dysku. Testy bez Dockera: `python -m unittest discover -s integrator/testy -t .` (87 testów).

### 15. Ograniczenia

- **Zakres:** integrator jest dodatkiem i nie zmienia `portal/` (schemat źródła wg Table Schema odłożono). Kolizje nazwy akcji (UPRP, EUIPO, domeny) nie zostały sprawdzone.
- **Realne źródła w większości nie wchodzą do wykazu**, bo nie mają kolumn wzorca. Portal podaje powód ([`raport_agregacji.txt`](../demo/wynik/raport_agregacji.txt)): Krosno nie ma kolumny miejscowości; Przemyśl ma CSV bez współrzędnych, a pozostałe dystrybucje są nietabelaryczne; Marki mają wadliwe pliki; Warszawa udostępnia stronę WWW, a dane są w API z tokenem. Przyjęto Legionowo (24 punkty).
- **Brak deduplikacji między dostawcami:** ten sam AED zgłoszony dwa razy da dwa wiersze.
- **Gdańsk** (AED w 278 pojazdach) to dane flotowe, poza zakresem wykazu.
- **Typy zgadywane przez portal:** jego walidacja może odrzucić plik zgodny ze wzorcem (np. „5A” w numerze budynku). Wykaz czyta wtedy plik wprost, ale zasób dostawcy ma w panelu czerwony znak (zrzut 02).
- **Środowisko lokalne:** mapa w `ng serve` wymaga `"prebundle": false`. Do zrzutów użyto kopii `angular.json`, bez zmiany pliku w repozytorium ([`demo/zrzuty/README.md`](../demo/zrzuty/README.md)).
- Opcjonalnej strony „Wykaz AED” we frontendzie nie wykonano; wykaz korzysta ze standardowej strony zasobu.

### 16. Użycie sztucznej inteligencji

Zespół korzystał z asystentów AI (Claude, Cursor) do wsparcia analizy kodu portalu, pisania kodu i implementacji testów oraz do wsparcia tworzenia księgi znaku i plików znaku (skrypt `branding/build_branding.py`). Asystenci pomagali też w redakcji dokumentów, automatyzacji zrzutów ekranu i składaniu prezentacji (`prezentacja/build_prezentacja.js`).

Kierunek rozwiązania wybrał i zweryfikował zespół: przeróbka DGA zamiast osobnej aplikacji, oznaczenie przez „Pola niestandardowe”, struktura danych, zasady licencji i ochrony danych oraz nazwa akcji, hasło i koncepcja znaku. Każdą zmianę zespół przejrzał i sprawdził testami oraz w uruchomionym portalu. Uzasadnienie decyzji: [`format_danych/UZASADNIENIE.md`](../format_danych/UZASADNIENIE.md).
