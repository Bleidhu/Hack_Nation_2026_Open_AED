> **Kopia z poprzedniego workspace (21.11.2026).** Ścieżki typu `../deliverable/`, `../scratch/`, `../portal_kod/` odnoszą się do starego układu. Mapowanie: `deliverable/` → `format_danych/`, `portal_kod/backend_latest/` → `portal/backend/`, `portal_kod/frontend_latest/` → `portal/frontend/`, `scratch/importer.py` → `integrator/importer.py`.  Nadrzędny jest `CLAUDE.md`.

# Format danych AED: pełny opis

Wersja 1.1.0 z 21.11.2026. Pliki maszynowe i generator znajdują się w `../deliverable/`. Ten opis jest specyfikacją projektu, nie standardem portalu; wymagania portalowe podsumowuje `02_DANE_GOV_PL_I_PRZEPLYW_PUBLIKACJI.md`.

## 1. Model danych: cztery tabele

| Tabela | Co opisuje | Kto dostarcza | Schemat | Szablon |
|--------|-----------|---------------|---------|---------|
| **aed_punkty** | Pojedynczy defibrylator w stałym miejscu (wzorzec 44 kolumn + 3 rozszerzenia) | dysponent, JST, firma, duży dostawca | `../deliverable/schemat/aed_punkty.tableschema.json` | `../deliverable/szablony/aed_punkty_szablon.csv` |
| **aed_obszarowe** | AED bez stałego punktu: flota pojazdów, patrol, wydarzenie, teren, trasa | przewoźnik, organizator, WOPR, służby | `../deliverable/schemat/aed_obszarowe.tableschema.json` | `../deliverable/szablony/aed_obszarowe_szablon.csv` |
| **organizacje** | Dysponent lub firma: logo, strona www, kontakt instytucjonalny | firma, sieć, JST | `../deliverable/schemat/organizacje.tableschema.json` | `../deliverable/szablony/organizacje_szablon.csv` |
| **aktualizacje** | Zdarzenia zmieniające stan AED: użycie, usterka, serwis | obywatel, dysponent, firma serwisująca, ZRM, dyspozytor 112, służby | `../deliverable/schemat/aktualizacje.tableschema.json` | `../deliverable/szablony/aktualizacje_szablon.csv` |

Powiązania między tabelami:
- `aed_punkty.organizacja_id` wskazuje na `organizacje.organizacja_id` (stąd logo i link przy każdej placówce);
- `aed_punkty.id_obszaru` wskazuje na `aed_obszarowe.id_obszaru` (np. AED w konkretnym tramwaju);
- `aktualizacje.id_aed` wskazuje na `aed_punkty.id_aed`.

Pełna lista kolumn ze słownikami jest w **`../deliverable/wzorcowy_zakres_danych.xlsx`**, w arkuszach od 1 do 6. W obecnym workbooku arkusz 1 (`1_Zakres_AED_punkty`) to słownik/definicje, a arkusz 2 (`2_Szablon_AED_punkty`) to tabela przykładowa. Dlatego **nie wgrywaj całego workbooka jako zasobu tabelarycznego do portalu**: portal może potraktować pierwszy arkusz definicji jak tabelę danych. Do publikacji przygotuj osobny, czysty plik CSV albo osobny XLSX z tabelą punktów jako pierwszym arkuszem. Przed publikacją porównaj workbook, CSV, Table Schema i typy pól w panelu; jeśli wartość nie jest dostępna u dostawcy, nie fałszuj jej tylko po to, by przejść walidację.

## 2. Formaty plików

| Format | Do czego | Zasady |
|--------|----------|--------|
| **CSV** (podstawowy) | wszystkie 4 tabele; publikacja na dane.gov.pl | RFC 4180: UTF-8 bez BOM, przecinek jako separator, CRLF, jeden wiersz nagłówka z nazwami kolumn ze schematu (snake_case, ASCII), cudzysłowy przy polach z przecinkiem lub nową linią. Bez scaleń, formuł, pustych wierszy i kolumn. |
| **XLSX** | wygodne wypełnianie przez dysponenta i artefakt konkursowy | Workbook konkursowy zawiera dodatkowe arkusze opisowe. Do publikacji przygotuj prostą tabelę i przetestuj faktyczną konwersję w panelu; nie zakładaj, że wszystkie zakładki staną się osobnymi zasobami. Nagłówki jak w CSV, bez formuł i makr. |
| **GeoJSON** (RFC 7946) | mapy i aplikacje; `aed_obszarowe` z geometrią | WGS84, kolejność współrzędnych `[lon, lat]`, właściwości jak kolumny CSV |
| **JSON:API + JSON-LD** | API | `application/vnd.api+json`; znaczenie pól przez `../deliverable/schemat/kontekst.jsonld` (schema.org), co daje ★★★★ tylko przy poprawnym pełnym kontekście |
| **CSVW** | opis maszynowy CSV (★★★★) | `../deliverable/schemat/aed_punkty.csvw.json`, dokument towarzyszący plikowi CSV |
| **Table Schema** (frictionless) | walidacja | `../deliverable/schemat/*.tableschema.json`: typy, wymagalność, słowniki, wzorce |
| **DCAT-AP** | metadane zbioru | `../deliverable/schemat/metadane_zbioru_dcat.json` |
| Wejście: TSV, CSV ze średnikiem, CP1250, Overpass JSON (OSM) | import od dostawców | Akceptowane **tylko na wejściu**. Importer przekształca je do CSV RFC 4180 UTF-8. |

## 3. Tabela `aed_punkty`

Wzorzec 44 kolumn opisano w `../plan_rozwiazania/dane/slownik_kolumn.csv` oraz w arkuszu 1 pliku XLSX. Oznaczenia: **W** wymagane, **Z** zalecane, **O** opcjonalne. To wymagalność w projekcie; nie jest uniwersalnym wymogiem portalu. Przed wdrożeniem sprawdź, czy pola W są realnie dostępne w źródłach. Gdy brakuje statusu lub daty weryfikacji, jawnie zapisz brak/nieznany i dostosuj wymaganie zamiast odrzucać albo zmyślać dane.

**Minimum, czyli kolumny W:**
`id_aed`, `nazwa_lokalizacji`, `miejscowosc`, `kod_pocztowy`, `numer_budynku`, `szerokosc_geograficzna`, `dlugosc_geograficzna`, `opis_lokalizacji`, `typ_dostepu`, `dostepny_24_7`, `status_urzadzenia`, `dysponent_nazwa`, `zrodlo_danych`, `poziom_weryfikacji`, `data_weryfikacji`, `data_aktualizacji`.

**Rozszerzenia z wersji 1.1** (wszystkie opcjonalne):

| Kolumna | Typ | Opis |
|---------|-----|------|
| `organizacja_id` | string `^[a-z0-9][a-z0-9-]{1,62}$` | Powiązanie z tabelą organizacji (logo, strona www). Np. wszystkie placówki banku mają `bank-przyklad`. |
| `id_obszaru` | string `^PL-AEDO-\d{5}$` | AED należący do obszaru lub floty |
| `id_pojazdu` | string | Numer taborowy pojazdu z AED |

**Zasady wartości:**
- daty w formacie `yyyy-mm-dd`, data z czasem `yyyy-mm-ddThh:mm:ss`;
- liczby z kropką dziesiętną;
- wartości logiczne jako `true`/`false`;
- telefon jako 9 cyfr albo `+48…`;
- REGON jako 9 lub 14 cyfr;
- kod pocztowy w formacie `NN-NNN`;
- kody TERYT jako tekst;
- godziny w składni OSM `opening_hours`, np. `Mo-Fr 08:00-16:00`.

**Identyfikator `id_aed`** ma postać `PL-AED-NNNNNNN`. Gdy dostawca go nie poda, importer nadaje trwały identyfikator wyliczany ze skrótu (hash) z organizacji, `id_zrodlowe` i współrzędnych. Ponowny import tego samego pliku daje więc te same identyfikatory.

## 4. Tabela `aed_obszarowe`: informacje obszarowe o AED

Służy do opisu AED, które nie wiszą na stałej ścianie: w tramwajach i autobusach, u patroli (WOPR, straż miejska), na wydarzeniach masowych, na dużych terenach (kampus, stok, plaża) i na trasach (szlak, pociąg).

| Kolumna | W/Z/O | Opis |
|---------|:-----:|------|
| `id_obszaru` | W | `PL-AEDO-NNNNN` |
| `nazwa_obszaru` | W | np. „Tramwaje MZK – cała sieć” |
| `typ_obszaru` | W | `flota_pojazdow`, `patrol_mobilny`, `wydarzenie`, `teren_obiektu`, `trasa`, `inne` |
| `geometria_wkt` | W | Zasięg w **WKT, WGS84, kolejność lon lat**: `POLYGON`, `MULTIPOLYGON`, `LINESTRING`, `MULTILINESTRING`. W GeoJSON zamiast tego jest `geometry`. |
| `bufor_m` | O | Bufor wokół linii trasy, w metrach |
| `liczba_aed` / `liczba_pojazdow` | W / O | np. 69 AED w 120 tramwajach. Wiadomo wtedy, że AED jest tylko w części floty. |
| `gtfs_url`, `gtfs_rt_url` | O | Rozkład oraz pozycje pojazdów na żywo. Aplikacja rysuje torowiska, przystanki i pojazdy. |
| `typy_pojazdow`, `linie` | O | Listy oddzielone znakiem `\|` |
| `jak_uzyskac_dostep` | W | **Instrukcja dla świadka zdarzenia**, np. „zatrzymaj tramwaj, AED przy kabinie motorniczego, motorniczy wezwie 112” |
| `status_programu` | W | `aktywny`, `w_realizacji`, `planowany`, `zakonczony` |
| `aktywny_od`, `aktywny_do` | O | Dla wydarzeń i sezonów (np. kąpieliska) |
| `godziny_dostepnosci`, `telefon_kontaktowy`, `strona_www`, `organizacja_id`, `dysponent_nazwa`, `dysponent_regon`, `zrodlo_danych`, `data_aktualizacji`, `uwagi` | | jak w tabeli `aed_punkty` |

**Pojedynczy AED w pojeździe** (gdy przewoźnik wie, który pojazd go ma) jest rekordem w `aed_punkty`, z polami `id_obszaru` i `id_pojazdu`. Współrzędne podaje się wtedy dla zajezdni, a bieżące położenie pochodzi z GTFS-RT.

Przykład: `../deliverable/dane_przykladowe/00_format_docelowy/aed_obszarowe_przyklad.csv` i `.geojson` (flota tramwajów, patrol WOPR, bieg uliczny).

## 5. Tabela `organizacje`: firmy i ich logo

Dla firm takich jak banki, sieci handlowe czy stacje paliw, które mają wiele placówek z AED. Każda placówka w `aed_punkty` dostaje `organizacja_id`, a aplikacja i API pokazują przy niej logo oraz link do strony firmy.

| Kolumna | W/Z/O | Opis |
|---------|:-----:|------|
| `organizacja_id` | W | np. `bank-przyklad` |
| `nazwa`, `typ_organizacji` | W | `jst`, `administracja`, `firma`, `przewoznik`, `uczelnia`, `szkola`, `ngo`, `sluzby`, `inne` |
| `regon`, `nip` | Z / O | |
| `strona_www` | Z | tylko `https://` |
| `logo_url` | O | `https://`, PNG lub SVG, co najmniej 128 px, przezroczyste tło |
| `logo_alt` | O, ale **wymagany, gdy jest logo** (WCAG) | np. „Logo Banku Przykład” |
| `email_kontaktowy`, `telefon_kontaktowy` | Z / O | tylko kontakt instytucjonalny, bez danych osobowych |
| `liczba_aed` | O | deklarowana liczba AED, porównywana z importem (kontrola kompletności) |
| `licencja_danych` | W | `CC0-1.0` (zalecana) lub `CC-BY-4.0` |

**Zastrzeżenie prawne:** logo i nazwa firmy są znakami towarowymi. Licencja CC0 obejmuje dane o AED, ale nie logo. Logo jest tylko linkowane z serwera firmy (`logo_url`) i nie jest kopiowane do zbioru.

## 6. Mapowanie kolumn: import pliku w dowolnym formacie

Duży dostawca lub firma nie muszą przerabiać swojego eksportu. Wystarczy plik mapowania JSON (schemat: `../deliverable/schemat/mapowanie.schema.json`):

```json
{
  "wersja": "1.0",
  "organizacja_id": "bank-przyklad",
  "kolumny": {
    "nazwa_lokalizacji":      { "z": "Nazwa placówki" },
    "szerokosc_geograficzna": { "z": "Lat" },
    "nazwa_ulicy":            { "z": "Adres", "regex": "^(?:ul\\.)?\\s*(.+?)\\s+\\d" },
    "typ_dostepu":            { "z": "Dostęp dla klientów", "mapa": { "TAK": "ograniczony", "NIE": "prywatny" } },
    "dostepny_24_7":          { "z": "GODZINY", "mapa": { "24/7": "true", "*": "false" } },
    "zrodlo_danych":          { "stala": "dysponent" }
  }
}
```

| Klucz | Działanie |
|-------|-----------|
| `z` | kolumna źródła; może to być lista, wtedy brana jest pierwsza niepusta |
| `stala` | wartość stała dla wszystkich wierszy |
| `mapa` | przekodowanie wartości; klucz `*` oznacza wartość domyślną |
| `regex` | wyrażenie regularne; pierwsza grupa staje się wartością |

**Automatyczne normalizacje:**
- przecinek dziesiętny zamieniany na kropkę;
- `TAK`/`NIE`, `1`/`0`, `24h` zamieniane na `true`/`false`;
- daty `dd.mm.rrrr` zamieniane na ISO;
- kod `05120` zamieniany na `05-120`;
- telefon czyszczony do 9 cyfr lub `+48…`;
- **zamienione szerokość i długość geograficzna są wykrywane i naprawiane, z ostrzeżeniem**;
- dla AED z ważnością elektrod lub baterii po terminie pojawia się ostrzeżenie „AED wymaga serwisu”.

Bez pliku mapowania importer i aplikacja **same podpowiadają mapowanie** na podstawie synonimów nazw kolumn. Dostawca je tylko poprawia i zapisuje.

**Gotowe presety:**
- `wzorzec`: plik jest już w naszym formacie;
- `osm`: GeoJSON z OpenAEDMap albo Overpass JSON z tagami `emergency=defibrillator`. Tag `access` zamieniany jest na `typ_dostepu`, `opening_hours` na godziny i `24/7`, `defibrillator:location` na opis.

**Licencja OSM:** dane z OSM są na **ODbL**. Import OSM służy do podglądu, porównań i wykrywania braków. **Nie trafia do zbioru krajowego CC0.** Wyjątkiem jest dostawca, który jest autorem własnych danych i publikuje je osobno na CC0. W praktyce rekordy OSM i tak nie przechodzą walidacji wzorca, bo brakuje im adresu, typu dostępu i weryfikacji.

## 7. Tabela `aktualizacje`: zmiany stanu AED

| Kolumna | Opis |
|---------|------|
| `id_aed` lub `aed_ref` | Którego AED dotyczy |
| `typ_zdarzenia` | `uzycie`, `wymaga_serwisu`, `w_serwisie`, `po_serwisie`, `sprawny` |
| `data_zdarzenia` | Czas zdarzenia, dla użycia |
| `rola` | `obywatel`, `dysponent`, `serwis`, `zrm`, `dyspozytor`, `sluzby` |
| `problemy` | Lista oddzielona `\|`, np. `niski_poziom_baterii\|kontrolka_bledu` |
| `data_przegladu`, `data_waznosci_elektrod`, `data_waznosci_baterii`, `numer_protokolu` | Dla firmy serwisującej |
| `numer_zdarzenia` | Numer zdarzenia z CPR lub SWD PRM, dla ZRM i dyspozytorów. **Bez danych pacjenta.** |
| `przewidywany_powrot` | Dla `w_serwisie` |

**Zasady stanu:**
1. O stanie decyduje ostatnie zdarzenie.
2. `uzycie` oznacza AED jako „Użyty – czeka na serwis” (niedostępny).
3. Zdejmują to wyłącznie `po_serwisie` lub `sprawny`, a te może zgłosić tylko **dysponent albo firma serwisująca**.
4. **Rola potwierdzona** wymaga klucza organizacji (nagłówek `X-API-Key`). Bez klucza rola jest „deklarowana” i tak oznaczana w danych.
5. Klucz organizacji wyznacza rolę: wpis w kolumnie `rola` nie może jej podnieść.

W zbiorze krajowym stan przekłada się na `status_urzadzenia`:
- `uzyty` i `wymaga_serwisu` dają `niesprawny`;
- `w_serwisie` daje `w_serwisie`;
- `sprawny` i `po_serwisie` dają `sprawny`, a `data_aktualizacji` przyjmuje czas zdarzenia.

## 8. Walidacja

Walidacja działa tak samo w CLI, w API i w aplikacji:
```bash
python scratch/importer.py plik.csv --mapowanie mapowanie.json --organizacja bank-przyklad --wyjscie wynik.csv --raport raport.json
```

**Wynik:**
- każdy wiersz dostaje status `ok`, `ostrzezenie` albo `odrzucony`;
- błędy podawane są z numerem wiersza pliku i nazwą pola;
- raport zawiera kompletność każdej kolumny w procentach;
- do pliku wynikowego trafiają tylko rekordy, które nie zostały odrzucone.

**Reguły walidacji:**
- typy, wymagalność, słowniki i wzorce według Table Schema;
- współrzędne w granicach Polski;
- unikalność `id_aed`;
- terminy ważności elektrod i baterii;
- `https://` w adresach;
- tekst alternatywny przy logo;
- poprawność WKT.
