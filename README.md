# Dane (prze)życie: Wykaz AED w portalu dane.gov.pl

> **Twoje dane – czyjeś życie.**

Rozwiązanie zadania „Misja AED – Dane na ratunek” (HackNation 2026, Ministerstwo Cyfryzacji). Zmieniamy otwarty kod portalu [dane.gov.pl](https://dane.gov.pl/source-code/) tak, żeby zbierał zasoby z danymi o defibrylatorach AED od wielu dysponentów i co noc scalał je w jeden ogólnopolski Wykaz AED z tabelą, mapą i API. Do tego dajemy wzorcowy zakres danych dla dysponentów i akcję promocyjną „Dane (prze)życie”, która ma ich zachęcić do publikacji.

**Zacznij tutaj:**
- [`INSTRUKCJA_DLA_JURY.md`](INSTRUKCJA_DLA_JURY.md): każde wymaganie zadania w ponumerowanych krokach;
- [`demo/index.html`](demo/index.html): klikalny prototyp całego procesu, działa offline;
- [`prezentacja/dane_przezycie_prezentacja.pdf`](prezentacja/dane_przezycie_prezentacja.pdf): prezentacja (14 slajdów);
- [`ZMIANY_W_PORTALU.md`](ZMIANY_W_PORTALU.md): opis zmian w kodzie portalu;
- [`ZGLOSZENIE/`](ZGLOSZENIE/README.md): pliki do zgłoszenia zebrane w jednym miejscu.

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
4. **Wykaz AED** to jeden zasób zbiorczy CSV (51 kolumn). Każdy wiersz ma pochodzenie: wydawcę, licencję, zasób źródłowy i datę. Portal sam daje mu tabelę, mapę (schemat z polem `geo`), pobieranie CSV i JSON-LD oraz API (`/1.4/resources/{id}/data`, stały adres `/1.4/aed-aggregated`).

Portal jest rozszerzony, nie przepisany: 22 nowe pliki obok DGA i 11 istniejących z dopiskami (punkty zaczepienia). Dodatek wyłącza się ustawieniem `AED_AGGREGATION_ENABLED`, a po wyłączeniu portal działa jak oryginał. Testy: 192 passed, w tym regresja DGA; `makemigrations --check`: „No changes detected” ([`demo/wynik/testy.txt`](demo/wynik/testy.txt)). Diff względem nietkniętego kodu portalu: `git diff a119b1b -- portal/backend`.

### 2. Wzorcowy zakres danych

[`format_danych/wzorcowy_zakres_danych.xlsx`](format_danych/wzorcowy_zakres_danych.xlsx):
- 41 kolumn dla dostawcy, każda z typem i wymagalnością;
- szablon z przykładami;
- słowniki wartości;
- 51 kolumn wykazu;
- zasady (identyfikatory, licencje, dane osobowe, „nieznany” zamiast domyślnego „sprawny”).

Do tego wersje maszynowe: Table Schema, CSVW, kontekst JSON-LD i metadane DCAT-AP ([`format_danych/`](format_danych/README.md)).

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
| Wzorcowy zakres danych | [`format_danych/`](format_danych/README.md) | kontrakt kolumn dla dostawców i agregacji |
| Prototyp i dowody | [`demo/`](demo/README.md) | klikalny prototyp offline, zrzuty z portalu, testy, wynik agregacji |
| Prezentacja | [`prezentacja/`](prezentacja/README.md) | 14 slajdów, PPTX i PDF |
| Akcja „Dane (prze)życie” | [`branding/`](branding/README.md) | logotyp, księga znaku, materiały, opis akcji |
| Integrator danych | [`integrator/`](integrator/README.md) | dodatek (zalążek) dla dostawców bez wzorcowego formatu |
| Materiały źródłowe | [`references/`](references/) | polecenie, regulamin, realne dane AED, standardy portalu |
| Zgłoszenie | [`ZGLOSZENIE/`](ZGLOSZENIE/README.md) | kopie plików do przekazania organizatorowi |

## Uruchomienie portalu lokalnie

Jury nie musi uruchamiać portalu: dowody z naszego środowiska są w [`demo/zrzuty/`](demo/zrzuty/README.md). Jeśli chcesz go postawić, postępuj według [`portal/backend/README.md`](portal/backend/README.md) (Docker). Znane problemy oryginalnego środowiska:
- na Windows port 1025 bywa zablokowany, więc kontener `mcod-smtp` nie startuje (SMTP nie jest potrzebny do Wykazu AED);
- w `mcod/settings/local.py.sample` ustawienie `"timeout": 1` w ustawieniach indeksów Elasticsearch blokuje tworzenie indeksów w ES 6.8;
- mapa we froncie uruchomionym przez `ng serve` wymaga `"prebundle": false` w `angular.json`.

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

Zakres użycia AI opisuje krok 16 instrukcji dla jury i ostatni slajd prezentacji.

## Wersje

Co zawiera każda wersja: [`WYDANIA.md`](WYDANIA.md).
