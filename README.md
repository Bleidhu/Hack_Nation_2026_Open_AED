# Dane (prze)życie: Wykaz AED w portalu dane.gov.pl

> **Twoje dane – czyjeś życie.**

Rozwiązanie zadania „Misja AED – Dane na ratunek” (HackNation 2026, Ministerstwo Cyfryzacji). Zmieniamy otwarty kod portalu [dane.gov.pl](https://dane.gov.pl/source-code/) tak, żeby zbierał zasoby z danymi o defibrylatorach AED od wielu dysponentów i co noc scalał je w jeden ogólnopolski Wykaz AED z tabelą, mapą i API. Do tego dajemy wzorcowy zakres danych dla dysponentów i akcję promocyjną „Dane (prze)życie”, która ma ich zachęcić do publikacji.

**Od czego zacząć:**
- [`INSTRUKCJA_DLA_JURY.md`](INSTRUKCJA_DLA_JURY.md): krótka instrukcja, pełna lista wymagań w [`DODATKOWE_INFORMACJE.md`](DODATKOWE_INFORMACJE.md);
- [`demo/index.html`](demo/index.html): klikalny prototyp całego procesu, działa offline;
- [`demo/wideo/dane_przezycie_wykaz_aed.mp4`](demo/wideo/dane_przezycie_wykaz_aed.mp4): film (1 min 14 s) z nagraniem działającego portalu;
- [`prezentacja/dane_przezycie_prezentacja.pdf`](prezentacja/dane_przezycie_prezentacja.pdf): prezentacja (28 slajdów);
- [`ZMIANY_W_PORTALU.md`](ZMIANY_W_PORTALU.md): opis zmian w kodzie portalu;
- [`ZGLOSZENIE/`](ZGLOSZENIE/README.md): pliki do zgłoszenia zebrane w jednym miejscu;
- [`WERSJA_LIVE.md`](WERSJA_LIVE.md): opcjonalny adres wersji live. Do oceny nie jest potrzebny, bo wszystko powyżej działa offline.

## Problem

Przy nagłym zatrzymaniu krążenia liczy się każda minuta, a defibrylatora AED może użyć każdy. Trzeba tylko wiedzieć, gdzie jest najbliższy. W dane.gov.pl są dziś pojedyncze zbiory o AED, ale każdy wygląda inaczej (migawka z 21.11.2026, [`references/dane_gov_pl_aed/`](references/dane_gov_pl_aed/README.md)):

- **Krosno:** plik CSV bez kolumny z miejscowością;
- **Przemyśl:** link do systemu miasta, te same dane w pięciu dystrybucjach;
- **Marki:** CSV i XLSX z błędami, cały wiersz w jednym polu;
- **Legionowo:** zasób AED w zbiorze mieszanym „Zdrowie”;
- **Warszawa:** w portalu tylko strona WWW, dane w API miasta wymagającym tokenu;
- **Gdańsk:** AED w 278 pojazdach ZTM, w pliku JSON floty.

Wyszukiwarka portalu nie przeszukuje zawartości tabel, a jednej listy AED w portalu nie ma.

## Rozwiązanie

### 1. Wykaz AED w kodzie portalu (główny rezultat)

Portal ma już mechanizm, który co noc scala zasoby wielu instytucji w jeden zasób zbiorczy: wykaz DGA. Przerobiliśmy go na defibrylatory.

1. **Dostawca oznacza zbiór** w istniejących „Polach niestandardowych”: `standard` = `AED`. To zwykła metadana zbioru, więc nie trzeba nowego pola, tagu, checkboxa ani migracji bazy.
2. **Dostawca publikuje zasób** według wzorcowego zakresu danych. Portal waliduje go swoim zwykłym potokiem.
3. **Co noc o 4:15** zadanie Celery wybiera zasoby z oznaczonych zbiorów i sprawdza każdy z osobna:
   - przyjmuje tylko zasoby z kolumnami wzorca;
   - przyjmuje tylko licencje CC0 1.0 i CC BY 4.0, a dane z OpenStreetMap (ODbL) pomija;
   - usuwa dane kontaktowe, gdy zbiór deklaruje dane osobowe;
   - każdy pominięty zasób zapisuje w logu z powodem.
4. **Deduplikacja:** to samo urządzenie zgłoszone przez dwóch dostawców trafia do wykazu raz. Kluczem jest numer seryjny (o ile producenci się nie wykluczają). Między różnymi zasobami portal łączy też wiersze tego samego producenta lub modelu oddalone najwyżej o 30 m albo, gdy brakuje producenta, wiersze o tej samej nazwie oddalone najwyżej o 10 m. Każdy duplikat trafia do statystyk i logu.
5. **Wykaz AED** to jeden zasób zbiorczy CSV (52 kolumny). Każdy wiersz ma pochodzenie: wydawcę, licencję, zasób źródłowy i datę. Portal sam daje mu tabelę, mapę (schemat z polem `geo`), pobieranie CSV i JSON-LD oraz API (`/1.4/resources/{id}/data`, stały adres `/1.4/aed-aggregated`).

**Dostawca spoza dane.gov.pl** wystawia w swoim API (na własnym serwerze https) opis zbioru w XML (schemat [`aed_opis_zbioru.xsd`](format_danych/schemat/aed_opis_zbioru.xsd)) z linkiem do pliku CSV i sumą md5. Komenda `python manage.py import_aed_xml <adres https opisu> --organizacja <ID>` sprawdza po kolei: kod 200, zgodność opisu z XSD, plik CSV, zgodność sumy md5 i kolumny wzorca. Dopiero potem tworzy zbiór (`standard`, `opis_xml` i `md5` w „Polach niestandardowych”) i zasób CSV, który nocne zadanie włącza do wykazu. Przy niezgodności nic nie zapisuje. Co noc o 4:05, przed budową wykazu, zadanie Celery `refresh_aed_opis_task` ponownie pobiera każdy taki opis: ta sama suma md5 niczego nie zmienia, a nowa zastępuje zasób. Przykłady: [`format_danych/przyklady/opis/`](format_danych/przyklady/opis/).

Portal jest rozszerzony, nie przepisany: 34 nowe pliki obok DGA (w tym 7 próbek danych testowych) i 11 istniejących z dopiskami (punkty zaczepienia). Dodatek wyłącza się ustawieniem `AED_AGGREGATION_ENABLED`, a po wyłączeniu portal działa jak oryginał. Testy: 270 passed (2 pominięte w kontenerze, sprawdzane przez `demo/sprawdz.py`), w tym regresja DGA; `makemigrations --check`: „No changes detected” ([`demo/wynik/testy.txt`](demo/wynik/testy.txt)). Diff względem nietkniętego kodu portalu: `git diff a1adc22 -- portal/backend`.

### 2. Wzorcowy zakres danych

[`format_danych/wzorcowy_zakres_danych.xlsx`](format_danych/wzorcowy_zakres_danych.xlsx) (wersja 2.1.0):
- 42 kolumny dla dostawcy, każda z typem i wymagalnością, w tym opcjonalny `numer_seryjny` (klucz deduplikacji);
- szablon z przykładami;
- słowniki wartości;
- 52 kolumny wykazu;
- zasady (identyfikatory, licencje, dane osobowe, „nieznany” zamiast domyślnego „sprawny”).

Do tego wersje maszynowe: Table Schema, CSVW, kontekst JSON-LD, metadane DCAT-AP i schematy XSD opisu zbioru oraz rekordów ([`format_danych/`](format_danych/README.md)).

### 3. Akcja „Dane (prze)życie”

Nazwa czyta się na dwa sposoby: „dane przeżycie” i „dane życie”, a „dane” to także dane.gov.pl. W znaku czerwona linia migotania komór i zielony rytm serca spotykają się w środku folderu z danymi: chaos zamienia się w porządek w sercu po defibrylacji i w danych po publikacji według wzorca.

- Księga znaku: [`branding/ksiega_znaku.pdf`](branding/ksiega_znaku.pdf).
- Logotyp w JPG, PNG, PDF i SVG: [`branding/logo/`](branding/logo/).
- Opis akcji (odbiorcy, mechanika, zachęty, teksty): [`branding/AKCJA_DANE_PRZEZYCIE.md`](branding/AKCJA_DANE_PRZEZYCIE.md).

## Dla kogo

- **Dostawcy danych:** samorządy, szkoły, firmy i instytucje, które mają AED. Dostają jeden wzorzec, prostą instrukcję i naklejkę oraz odznakę w ramach akcji.
- **Odbiorcy:** służby ratownicze, mieszkańcy i twórcy map oraz aplikacji. Dostają jeden otwarty wykaz z mapą i API, z informacją, skąd pochodzi każdy rekord.

## Struktura repozytorium

| Część | Gdzie | Rola |
|---|---|---|
| **Modyfikacja portalu** | [`portal/backend/`](portal/backend/), [`portal/frontend/`](portal/frontend/) | główny rezultat: Wykaz AED |
| Wzorcowy zakres danych | [`format_danych/`](format_danych/README.md) | kontrakt kolumn dla dostawców i agregacji, schematy XSD |
| Prototyp i dowody | [`demo/`](demo/README.md) | klikalny prototyp offline, zrzuty z portalu, film, testy, wynik agregacji, serwer dostawcy |
| Źródła filmu | [`video/`](video/README.md) | skrypty nagrań (Playwright) i kompozycja (Remotion) filmu z `demo/wideo/` |
| Prezentacja | [`prezentacja/`](prezentacja/README.md) | 28 slajdów, PPTX i PDF |
| Akcja „Dane (prze)życie” | [`branding/`](branding/README.md) | logotyp, księga znaku, materiały, opis akcji |
| Integrator danych | [`integrator/`](integrator/README.md) | dodatek dla dostawców bez wzorcowego formatu; generuje też opis zbioru w XML z sumą md5 |
| Materiały źródłowe | [`references/`](references/) | polecenie, regulamin, realne dane AED, standardy portalu |
| Zgłoszenie | [`ZGLOSZENIE/`](ZGLOSZENIE/README.md) | kopie plików do przekazania organizatorowi |

## Uruchomienie portalu lokalnie

Jury nie musi uruchamiać portalu: dowody z naszego środowiska są w [`demo/zrzuty/`](demo/zrzuty/README.md). Instrukcja samodzielnego uruchomienia (Docker): [`portal/backend/README.md`](portal/backend/README.md). Znane problemy oryginalnego środowiska:
- na Windows port 1025 bywa zablokowany, więc kontener `mcod-smtp` nie startuje (SMTP nie jest potrzebny do Wykazu AED);
- w `mcod/settings/local.py.sample` ustawienie `"timeout": 1` w ustawieniach indeksów Elasticsearch blokuje tworzenie indeksów w ES 6.8;
- mapa we froncie uruchomionym przez `ng serve` wymaga `"prebundle": false` w `angular.json`.

W portalu opisy zbiorów są odświeżane co noc o 4:05, a wykaz powstaje o 4:15. W demo nie trzeba czekać: skrypt `demo/wymus_harvest.py` od razu wykonuje import z `--odswiez`, czeka na walidację zasobu przez Celery i buduje wykaz (`create_main_aed_resource --eager`). Przebieg: [`demo/wynik/wymus_harvest.txt`](demo/wynik/wymus_harvest.txt).

Logikę agregacji można sprawdzić bez Dockera i bazy jednym poleceniem (opis w [`demo/README.md`](demo/README.md)):

```bash
uv run --python 3.11 --with "pandas==1.5.3" --with "numpy<2" --with openpyxl python demo/agreguj.py
```

## Licencje i źródła

- **Kod portalu dane.gov.pl:** pobrany z https://dane.gov.pl/source-code/. Archiwa kodu nie zawierają pliku licencji, więc warunki licencji trzeba potwierdzić u organizatora.
- **Dane AED z dane.gov.pl** ([`references/dane_gov_pl_aed/`](references/dane_gov_pl_aed/README.md)): licencje CC0 1.0 i CC BY 4.0 według metadanych zbiorów, z atrybucją wydawców.
- **Kontur Polski** w prototypie: Natural Earth, domena publiczna.
- **Krój Atkinson Hyperlegible:** SIL Open Font License 1.1 ([`branding/fonty/OFL.txt`](branding/fonty/OFL.txt)).
- **Zrzuty ekranu** pokazują interfejs oryginalnego portalu (w tym elementy identyfikacji gov.pl) uruchomionego lokalnie.
- Nie kopiujemy baz zamkniętych (np. Staying Alive, Pierwszy Ratownik). Dane OpenStreetMap (ODbL) nie trafiają do wykazu.

## Użycie AI

Zakres użycia AI opisuje krok 16 w [`DODATKOWE_INFORMACJE.md`](DODATKOWE_INFORMACJE.md) i ostatni slajd prezentacji.

## Wersje

Co zawiera każda wersja: [`WYDANIA.md`](WYDANIA.md).
