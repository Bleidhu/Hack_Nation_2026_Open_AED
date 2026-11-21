# Dane przykładowe: warianty od różnych dostawców

Każdy folder to jeden typ dostawcy danych o AED. Pliki pokazują dane **tak, jak wyglądają u źródła** (natywny format), a obok leży **plik mapowania na wzorzec** i opis źródła `zrodlo.json` (kto, jakim kanałem, jak często, licencja, czy trafia do zbioru krajowego CC0).

**Wszystkie dane są fikcyjne** (oznaczone „PRZYKŁAD – dane fikcyjne”). Współrzędne wskazują ogólnodostępne miejsca w Krakowie i Bydgoszczy, ale urządzenia, firmy, numery seryjne i zdarzenia są zmyślone.

| Folder | Dostawca | Format natywny | Trafia do tabeli | Co pokazuje |
|---|---|---|---|---|
| `00_format_docelowy` | dysponent / JST publikujący już we wzorcu | CSV RFC 4180, GeoJSON | punkty, obszarowe, organizacje | cel: zero mapowania |
| `01_integrator_osm` | OpenStreetMap / OpenAEDMap | Overpass JSON, GeoJSON | punkty (**tylko porównanie**, ODbL) | brak adresu i stanu; punkty spoza innych źródeł → kandydaci do weryfikacji |
| `02_bank` | bank, sieć placówek | zagnieżdżony JSON z systemu + CSV ze średnikiem | punkty | placówka z 2 AED to 2 rekordy, nie duplikat; godziny per dzień; elektrody `rrrr-mm`; AED tylko dla pracowników |
| `03_siec_sklepow` | duża sieć handlowa | TSV w CP1250 | punkty | kodowanie, zapisane mapowanie, odrzucenie wiersza z brakami |
| `04_pojedyncze_sklepy` | apteka, piekarnia, stacja paliw | JSON z formularza www | punkty | adres w jednym polu, położenie z linku do mapy, godziny słowami, pomijanie danych osobowych, brak zgody na CC0 |
| `05_male_instytucje` | szkoła, przedszkole, OSP, biblioteka, klub (zestawienie gminy) | JSON z polskimi nagłówkami | punkty | przecinek dziesiętny, daty `dd.mm.rrrr`, AED zamknięty na klucz, jednostka bez współrzędnych |
| `06_serwis` | firma serwisująca, telemetria producenta | JSON protokołów, JSON autotestów, CSV aktualizacji | aktualizacje | dopasowanie po numerze seryjnym, błąd baterii z autotestu, protokół dla nieznanego urządzenia |
| `07_zrm_dyspozytor` | ZRM, dyspozytor medyczny, CPR 112 | strumień zdarzeń (styl CloudEvents), CSV aktualizacji | aktualizacje | AED użyty (zużyte elektrody), brak dostępu w nocy, AED zabrany z pacjentem |
| `08_przewoznik_miejski` | komunikacja miejska (wzorowane na Krakowie) | JSON przewoźnika + GTFS / GTFS-RT | punkty + obszarowe | AED w zajezdni i w tramwajach (flota, obszar obsługi) |
| `09_kolej` | zarządca dworców i linii, przewoźnik kolejowy | JSON zarządcy | punkty + obszarowe | dworzec z AED w hali i na peronie, odcinek linii z buforem, pociąg z AED |
| `10_zgloszenia_obywateli` | obywatele (QR na naklejce, aplikacja) | JSON zgłoszeń | aktualizacje | zgłoszenie nie nadpisuje danych dysponenta; „nowy AED” → kandydat |

## Celowe powiązania między źródłami (do demo integracji)

Te same urządzenia występują w kilku źródłach, żeby było widać scalanie i referencyjność:

- **Bank, Rynek Główny**: rekord w systemie banku, punkt w OSM ~9 m dalej, raport telemetrii (autotest OK) i zdarzenie ZRM „AED użyty”. Rekordem referencyjnym jest bank, a po zdarzeniu AED jest niegotowy do wymiany elektrod.
- **Apteka, ul. Długa**: zgłoszenie z formularza, OSM ~13 m dalej i zdarzenie dyspozytora „brak dostępu w nocy”.
- **Dworzec Kraków Główny, hala**: dane zarządcy, OSM ~18 m dalej i zdarzenie „AED zabrany przez ZRM”. AED na peronie 1 (~80 m) to **osobne** urządzenie.
- **OSP Przykładowo**: zestawienie gminy, OSM ~9 m dalej i telemetria z błędem baterii.
- **Przedszkole nr 998**: zamknięte na klucz, zgłoszenie obywatela o braku dostępu.
- **Planty**: punkt tylko w OSM z 2021 r., zgłoszenie obywatela „brak urządzenia”.

## Rekomendacje do wzorca (wynikają z tych danych)

- Dodać opcjonalną kolumnę **`numer_seryjny`**. Serwisy i telemetria identyfikują urządzenie po numerze seryjnym, nie po adresie.
- Rozszerzyć słownik `typ_zdarzenia` o **`brak_dostepu`** i **`czasowo_niedostepny`**. Dziś zdarzenia „świadek nie dostał się do AED” i „ZRM zabrał AED z pacjentem” trzeba zapisywać jako `wymaga_serwisu` lub `w_serwisie`.

## Generowanie

```bash
python deliverable/narzedzia/generuj.py          # format docelowy, bank CSV, sieć sklepów, OSM GeoJSON, aktualizacje CSV, xlsx
python deliverable/narzedzia/generuj_zrodla.py   # natywne JSON-y pozostałych dostawców, mapowania, zrodlo.json
```
