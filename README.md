# Hack_Nation_2026_Open_AED: Otwórz AED

> **Pokaż, gdzie jest. Powiedz, czy działa.**

Rozwiązanie zadania „Misja AED – Dane na ratunek” (HackNation 2026, Ministerstwo Cyfryzacji). Modyfikujemy otwarty kod portalu [dane.gov.pl](https://dane.gov.pl/source-code/) tak, żeby **zbierał zasoby z danymi o defibrylatorach AED od wielu dysponentów i co noc budował z nich jeden krajowy zasób zbiorczy** z tabelą, mapą i API. Robimy to bez migracji bazy portalu, na wzór istniejącego mechanizmu zbiorczego wykazu DGA.

| Część | Gdzie | Rola |
|---|---|---|
| **Modyfikacja portalu** | `portal/backend`, `portal/frontend` | główny rezultat (krok 1) |
| Wzorcowy zakres danych AED | `format_danych/` (m.in. `wzorcowy_zakres_danych.xlsx`) | kontrakt kolumn dla dostawców i agregacji |
| Integrator danych | `integrator/` | dodatek (krok 2) dla dostawców bez wzorcowego formatu |
| Akcja „Otwórz AED” | `branding/` | logo, księga znaku, opis akcji |
| Materiały źródłowe | `references/`, `docs/` | polecenie, regulamin, wytyczne organizatora, standardy, wiedza |

Zmiany w portalu najłatwiej zobaczyć jako diff względem pierwszego commitu z oryginalnym kodem portalu (commit „Oryginalny kod portalu dane.gov.pl”).

Instrukcje dla zespołu i agentów są w [`CLAUDE.md`](CLAUDE.md).
