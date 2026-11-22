# Próbki testowe Zestawienia AED

Pobrane 21.11.2026 przez publiczne API dane.gov.pl (`https://api.dane.gov.pl/1.4/resources/<id>` → `download_url`), poza dwoma przykładami wzorca. Używają ich testy `mcod/resources/tests/test_aed_*.py`.

| Plik | Źródło | Licencja | Oczekiwane zachowanie w agregacji |
|---|---|---|---|
| `aed_punkty_przyklad.csv` | `format_danych/przyklady/` (dane FIKCYJNE, wzorzec v2) | – | 8 wierszy przyjętych |
| `aed_zestawienie_przyklad.csv` | `format_danych/przyklady/` (wynik implementacji referencyjnej) | – | wynik oczekiwany testu golden (bajt w bajt) |
| `legionowo_2625221.csv` | zasób 2625221, zbiór 40593, Urząd Miasta Legionowo | CC0 1.0 | 24 wiersze przyjęte; aliasy `nazwa`, `nr_budynku`, `nr_lokalu`; plik ma BOM |
| `krosno_54632.csv` | zasób 54632, zbiór 3624, Urząd Miasta Krosna | CC0 1.0 | zasób pominięty: brak kolumny `miejscowosc` (cały adres w polu `Adres`) |
| `przemysl_62095.csv` | zasób 62095, zbiór 4581, Urząd Miejski w Przemyślu (link do systemu miasta, wersja z 21.11.2026) | CC0 1.0 | zasób pominięty: brak kolumn współrzędnych (współrzędne w jednej kolumnie `geometry`); separator `;`, BOM |
| `marki_68353.csv` | zasób 68353, zbiór 4955, Urząd Miasta Marki | CC BY 4.0 | zasób pominięty: każdy wiersz jest w całości w cudzysłowie, więc tabela ma jedną kolumnę |

Pliki z dane.gov.pl są zapisane bez zmian. Atrybucja danych CC BY 4.0: Urząd Miasta Marki, dane.gov.pl, zasób 68353.
