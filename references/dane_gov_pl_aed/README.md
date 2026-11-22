# Źródła danych AED na dane.gov.pl (migawka z 21.11.2026)

Materiał testowy dla mechanizmu agregacji w portalu. Pokazuje, **w jakich postaciach dostawcy faktycznie publikują dane AED**: plik w portalu, link do pliku u dostawcy, link do strony WWW, harvest z lokalnego katalogu CKAN, JSON spoza tabeli. Licencje są zachowane, a dane na CC BY 4.0 wymagają atrybucji dostawcy.

## Jak szukaliśmy

Publiczne API `https://api.dane.gov.pl/1.4/`:
- `datasets?q=` i `resources?q=` dla fraz: AED, defibrylator, defibrylatory, defibrylatorów, defibrylatora, defibrylatorem, defibrylatorach, „automatyczny defibrylator zewnętrzny”, DAE, defibrillator;
- globalne `search?q=`, które przeszukuje tytuły **i opisy** zbiorów oraz zasobów. Dopiero ono znalazło Gdańsk, bo „AED” występuje tam tylko w opisie pól.

Wynik dla „AED”: 17 trafień, z czego 7 to fałszywe trafienia (projekt „AED – Automatyczny Eksplorator Danych”, cennik). Wildcardy (`defibryl*`) nie działają. **Wyszukiwarka portalu nie przeszukuje zawartości tabel**, więc zasoby z kolumną „defibrylator” ukryte w innych zbiorach (np. wykazy obiektów) są niewidoczne. To osobny argument za jawnym oznaczaniem zbiorów AED.

## Zestawienie źródeł

| Zbiór | Dostawca | Licencja | Jak trafia do portalu | Zasoby i lokalne kopie | Co to znaczy dla agregacji |
|---|---|---|---|---|---|
| [3624](https://dane.gov.pl/pl/dataset/3624) Defibrylatory w Mieście Krosno | Urząd Miasta Krosna | CC0 1.0 | plik w portalu | 54632 CSV → `zasob_54632_zbior_3624.csv` | czyta się wprost (`tabular_data`) |
| [4581](https://dane.gov.pl/pl/dataset/4581) Lokalizacje AED w Przemyślu | Urząd Miejski w Przemyślu | CC0 1.0 | **link** do systemu SkyCMS (5 dystrybucji: CSV, GeoJSON, JSON, 2×GML) | 62095 CSV → `zasob_62095_zbior_4581.csv`; 62093 GeoJSON → `zasob_62093_zbior_4581.geojson` | link pobierany przez portal; tylko CSV daje tabelę. Brać jeden zasób na zbiór, inaczej będą duplikaty z różnych formatów |
| [4955](https://dane.gov.pl/pl/dataset/4955) Defibrylatory w Mieście Marki | Urząd Miasta Marki | CC BY 4.0 | plik w portalu (CSV + XLSX) | 68353 CSV → `zasob_68353_zbior_4955.csv`; 68355 XLSX → `zasob_68355_zbior_4955.xlsx` | **oba wadliwe**. W CSV każdy wiersz jest w całości w cudzysłowie, czyli jest jednym polem. XLSX ma całe wiersze CSV wklejone do jednej kolumny. Nagłówki współrzędnych są zamienione (pierwsza wartość to szerokość, choć kolumna nazywa się „Długość”), a punkt 7 leży poza Markami. Kontrola struktury musi takie zasoby odrzucić z czytelnym powodem |
| [40593](https://dane.gov.pl/pl/dataset/40593) Zdrowie | Urząd Miasta Legionowo | CC0 1.0 | plik w portalu, **w zbiorze mieszanym** | 2625221 CSV → `zasob_2625221_zbior_40593.csv` | oznaczenie na poziomie zbioru obejmie też zasoby nie-AED. Potrzebna kontrola kolumn per zasób |
| [39512](https://dane.gov.pl/pl/dataset/39512) Lokalizacja defibrylatorów (AED) | Urząd m.st. Warszawy | CC BY 4.0 | **harvester CKAN** („Otwarte dane Warszawy”, codziennie); zasób 2512040 to **link do strony WWW** katalogu | w portalu brak danych tabelarycznych. Dane są w API `POST https://dane.um.warszawa.pl/api/action/get_scb_lokalizacja_defibrylatorow` z **obowiązkowym tokenem użytkownika**; opis pól i przykład odpowiedzi w `warszawa_api/` | portal nie ma pliku, tabeli ani mapy. Zasób z CKAN trzeba czytać przez `resource.link` (jak DGA), ale link prowadzi do HTML. Bez integratora lub zmiany u dostawcy Warszawa wypada |
| [1803](https://dane.gov.pl/pl/dataset/1803) Otwarte dane ZTM w Gdańsku | ZTM w Gdańsku | CC BY 4.0 | **harvester CKAN** („Otwarte dane w Gdańsku”); zasób 31843 „Baza pojazdów ZTM” to link do JSON | `gdansk_ztm/zasob_31843_baza_pojazdow.json`: 503 pojazdy z polem `aed` (true/false). **AED ma 278 pojazdów: 122 tramwaje i 156 autobusów** | AED w pojazdach to dane **obszarowe/flotowe**, a nie punkty. JSON nie jest tabelą w portalu, więc potrzebny jest integrator (krok 2) lub osobna tabela `aed_obszarowe` |

Metadane z API (JSON:API) są w `metadane_api/`: `dataset_*`, `inst_*`, `resources_*` i `resource_*`.

## Wnioski dla modyfikacji portalu

1. Realne zasoby AED trafiają do portalu **wszystkimi drogami**: plik, link do pliku, link do strony i harvester CKAN. Mechanizm agregacji musi obsłużyć ścieżkę lokalną (`resource.tabular_data`) i ścieżkę CKAN (`resource.link`), tak jak DGA. Zasoby bez tabeli ma pomijać z czytelnym powodem w logu.
2. **Zbiory mieszane** (Legionowo) i **wiele dystrybucji tych samych danych** (Przemyśl, Marki) wymagają wyboru zasobu: kontrola kolumn per zasób i preferencja jednego formatu tabelarycznego.
3. Dwa największe źródła (Warszawa i Gdańsk) **nie dają dziś tabeli w portalu**. To mocny argument dla jury, że krok 2 (integrator wystawiający CSV pod linkiem) ma sens, ale dopiero po kroku 1.
4. Jakość danych (np. uszkodzony CSV z Marek, punkty skopiowane między miastami) widać w plikach z tego katalogu.
