# Zbiory AED na dane.gov.pl (migawka z 21.11.2026)

Pobrane przez publiczne API `https://api.dane.gov.pl/1.4/` (wyszukiwanie zbiorów i zasobów po: AED, defibrylator, defibrylatory, defibrylatorów). Służą jako **realne zasoby testowe** dla mechanizmu agregacji w portalu: pokazują, jak różnią się schematy u dostawców. Licencje są zachowane: dane CC BY 4.0 wymagają atrybucji dostawcy.

| Zbiór | Tytuł | Dostawca | Licencja | Modyfikacja | Pliki zasobów |
|---|---|---|---|---|---|
| [3624](https://dane.gov.pl/pl/dataset/3624) | Defibrylatory zlokalizowane w Mieście Krosno | Urząd Miasta Krosna | CC0 1.0 | 2024-03-19 | `zasob_54632_zbior_3624.csv` (Defibrylatory zlokalizowane w Mieście Krosno) |
| [39512](https://dane.gov.pl/pl/dataset/39512) | Lokalizacja defibrylatorów (AED) | Urząd m.st. Warszawy | CC BY 4.0 | 2026-06-01 | brak lokalnej kopii |
| [40593](https://dane.gov.pl/pl/dataset/40593) | Zdrowie | Urząd Miasta Legionowo | CC0 1.0 | 2026-09-21 | `zasob_2625221_zbior_40593.csv` (Wykaz defibrylatorów AED wraz z ich lokalizacją w Legionowie.) |
| [4581](https://dane.gov.pl/pl/dataset/4581) | Lokalizacje AED – Automatycznych Defibrylatorów Zewnętrznych w Przemyślu | Urząd Miejski w Przemyślu | CC0 1.0 | 2024-11-06 | `zasob_62095_zbior_4581.csv` (Lokalizacje AED – Automatycznych Defibrylatorów Zewnętrznych w Przemyślu) |
| [4955](https://dane.gov.pl/pl/dataset/4955) | Defibrylatory zlokalizowane na terenie Miasta Marki | Urząd Miasta Marki | CC BY 4.0 | 2025-07-10 | `zasob_68353_zbior_4955.csv` (Defibrylatory zlokalizowane na terenie Miasta Marki) |

Metadane z API (JSON:API) są w `metadane_api/` (`dataset_*`, `inst_*`, `resources_*`).

Uwagi z analizy: zbiór Urzędu m.st. Warszawy (API z tokenem) nie ma lokalnej kopii; zbiór 40593 (Legionowo) to zbiór mieszany „Zdrowie”, w którym AED jest tylko jednym z zasobów. Szczegóły jakości (duplikaty, błędne współrzędne) w `../../docs/03_ZRODLA_I_LICENCJE.md`.
