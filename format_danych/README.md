# Wzorcowy zakres danych AED, wersja 2

Specyfikacją jest `schemat/aed_punkty.tableschema.json` (reguły dodatkowe w `x-reguly-dodatkowe`), a zasady portalu, ochrony danych i licencji zbiera arkusz `5_Zasady` w `wzorcowy_zakres_danych.xlsx`. Wszystkie pliki poniżej generuje jedno źródło prawdy, a przykłady są **fikcyjne**.

## Dwie warstwy

| Warstwa | Kto wypełnia | Kolumny | Schemat |
|---|---|---|---|
| **Wzorzec dostawcy** (plik publikowany przez gminę, instytucję lub firmę) | dostawca | 41 | `schemat/aed_punkty.tableschema.json` |
| **Zasób zbiorczy** (budowany co noc przez portal) | portal | 51 = `id_aed` + 41 kolumn wzorca + 3 wyliczane + 6 pochodzenia | `schemat/aed_zestawienie.tableschema.json` |

Jeden wiersz to jedno urządzenie. Kilka AED w jednym miejscu to kilka wierszy z różnym `id_zrodlowe`; te same współrzędne są dopuszczalne.

## Kolumny wzorca dostawcy

Pełny opis kolumn (typ, wymagalność, minimum agregacji, przykład, słownik) jest w `wzorcowy_zakres_danych.xlsx`, arkusz `1_Zakres_wzorca`, oraz w `zrodla_wzorca/slownik_kolumn.csv`.

- **Wymagane we wzorcu (W, 9):** `id_zrodlowe`, `nazwa_lokalizacji`, `miejscowosc`, `szerokosc_geograficzna`, `dlugosc_geograficzna`, `opis_lokalizacji`, `typ_dostepu`, `dostepny_24_7`, `data_aktualizacji`.
- **Minimum agregacji (4):** `nazwa_lokalizacji`, `miejscowosc`, `szerokosc_geograficzna`, `dlugosc_geograficzna`. Bez tych kolumn portal pomija zasób, a wiersz z pustą wartością pomija z podaniem powodu.
- **Grupy kolumn:** identyfikacja, lokalizacja (adres wg TERYT, WGS84), dostęp, urządzenie i stan, dysponent i kontakt (tylko instytucjonalny), źródło i aktualność.
- **Usunięte względem v1:** `id_aed` (nadaje portal), `uwagi`, `zdjecie_url`, `organizacja_id`, `id_obszaru`, `id_pojazdu`.

## Kolumny dopisywane przez portal (zasób zbiorczy)

| Kolumna | Znaczenie |
|---|---|
| `id_aed` | `PL-AED-` + 12 znaków hex z SHA-1(id instytucji wydawcy, `id_zrodlowe`) |
| `wymaga_przegladu` | `true`: minął termin elektrod lub baterii albo przegląd był ponad 12 miesięcy temu; pusta, gdy brak dat |
| `dysponent_z_wydawcy` | `true`, gdy dysponenta zastąpiono nazwą wydawcy |
| `przetworzenie` | kody `naglowki`, `osie`, `domyslne`, `dysponent_z_wydawcy`, `kontakt_usuniety` (art. 15 ust. 1 pkt 2 ustawy) |
| `wydawca_zasobu`, `licencja_zasobu`, `id_zasobu_zrodlowego`, `url_zasobu_zrodlowego`, `data_danych_zasobu`, `data_agregacji` | pochodzenie i atrybucja (art. 15 ust. 1 pkt 1) |

Reguły agregacji mają implementację referencyjną (z samokontrolą) w `zrodla_wzorca/generuj_dane.py`, funkcje `zestaw`, `id_aed`, `wymaga_przegladu` i `powod_pominiecia`. Portal ma dawać ten sam wynik.

## Najważniejsze zasady

- Brak statusu oznacza `nieznany`, a brak weryfikacji `niezweryfikowany`. Nigdy nie przyjmujemy domyślnie „sprawny”.
- Kontakty są wyłącznie instytucjonalne lub funkcyjne. Gdy zbiór źródłowy deklaruje dane osobowe, portal usuwa kontakty.
- Bez zdjęć. W polach tekstowych bez kodów do szafek, miejsca przechowywania klucza, imion i nazwisk. AED w lokalach mieszkalnych nie są publikowane.
- Do zasobu zbiorczego trafiają źródła na CC0 1.0 i CC BY 4.0. Wiersze z OpenStreetMap (ODbL) są wykluczone. Zasób zbiorczy ma licencję CC BY 4.0 z atrybucją w każdym wierszu.
- Format według POD 2021–2027 zał. 2:
  - CSV RFC 4180: UTF-8, przecinek, CRLF;
  - daty `yyyy-mm-dd` i `yyyy-mm-ddThh:mm:ss`, `true`/`false`, kropka dziesiętna;
  - REGON 9 lub 14 cyfr, telefon 9 cyfr;
  - adres w osobnych polach według TERYT.

## Pliki

| Ścieżka | Zawartość |
|---|---|
| `wzorcowy_zakres_danych.xlsx` | dokumentacja zakresu (plik wymagany w zadaniu konkursowym) w 5 arkuszach: zakres, szablon z przykładami, słowniki, zasób zbiorczy, zasady. **Nie jest plikiem do publikacji.** |
| `szablony/aed_punkty_szablon.csv`, `.xlsx` | pusty szablon dla dostawcy; XLSX ma jeden arkusz, zgodnie z POD |
| `schemat/aed_punkty.tableschema.json` | Table Schema wzorca dostawcy (walidator) |
| `schemat/aed_zestawienie.tableschema.json` | Table Schema zasobu zbiorczego z mapowaniem `geo` dla mapy portalu |
| `schemat/aed_punkty.csvw.json`, `schemat/kontekst.jsonld` | opis CSVW (★★★★) i kontekst JSON-LD (schema.org) |
| `schemat/slowniki.json` | słowniki wartości (w tym `przetworzenie`, `licencja_zasobu`) |
| `schemat/metadane_zbioru_dcat.json` | metadane zbioru zbiorczego (DCAT-AP), w tym `customfields` `standard = AED` |
| `przyklady/` | przykład pliku dostawcy (CSV, GeoJSON) i wynikowego zasobu zbiorczego (CSV, JSON:API) |
| `zrodla_wzorca/` | źródło prawdy (`generuj_dane.py`), słowniki kolumn i mapowanie nagłówków realnych źródeł (`mapowanie_zrodel.csv`) |

## Regeneracja i walidacja

```bash
python format_danych/zrodla_wzorca/generuj_dane.py   # źródło prawdy + samokontrola reguł agregacji
python format_danych/narzedzia/generuj.py            # schemat/, szablony/, przyklady/, XLSX
# walidacja przykładów (opcjonalnie):
cd format_danych && uv run --with "frictionless==5.18.0" python -c "from frictionless import Resource, Schema; print(Resource(path='przyklady/aed_punkty_przyklad.csv', schema=Schema('schemat/aed_punkty.tableschema.json')).validate().valid)"
```

Generatory używają tylko biblioteki standardowej. Wynik jest deterministyczny; pliki XLSX różnią się między uruchomieniami jedynie znacznikami czasu w archiwum.

Materiał integratora (krok 2, dodatek) jest w `../integrator/`: próbki dostawców z mapowaniami, lokalne UI i testy – wszystko już na wzorcu v2 (41 kolumn, czyli `schemat/aed_punkty.tableschema.json`). Tabele obszarowe, organizacji i aktualizacji oraz opis wzorca v1 są w `../archive/integrator/`.
