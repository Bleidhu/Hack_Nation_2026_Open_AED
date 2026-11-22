# Hack_Nation_2026_Open_AED: Otwórz AED

> **Pokaż, gdzie jest. Powiedz, czy działa.**

**Wersja v1.0.0: rozwiązanie podstawowe.**
- Brakuje prezentacji.
- Kampania promocyjna z logotypem, hasłem i księgą znaku jest niezakończona; w `branding/` są materiały robocze.
- Integrator nie wchodzi w zakres tej wersji.

Pliki do zgłoszenia są w [`ZGLOSZENIE/`](ZGLOSZENIE/README.md).

**Zacznij tutaj:**
- [`INSTRUKCJA_DLA_JURY.md`](INSTRUKCJA_DLA_JURY.md): każde wymaganie zadania w ponumerowanych krokach;
- [`demo/index.html`](demo/index.html): klikalny prototyp offline;
- [`ZMIANY_W_PORTALU.md`](ZMIANY_W_PORTALU.md): opis zmian w kodzie portalu.

Rozwiązanie zadania „Misja AED – Dane na ratunek” (HackNation 2026, Ministerstwo Cyfryzacji). Modyfikujemy otwarty kod portalu [dane.gov.pl](https://dane.gov.pl/source-code/) tak, żeby **zbierał zasoby z danymi o defibrylatorach AED od wielu dysponentów i co noc budował z nich jeden krajowy zasób zbiorczy** z tabelą, mapą i API. Robimy to bez migracji bazy portalu, na wzór istniejącego mechanizmu zbiorczego wykazu DGA.

| Część | Gdzie | Rola |
|---|---|---|
| **Modyfikacja portalu** | `portal/backend`, `portal/frontend` | główny rezultat (krok 1) |
| Wzorcowy zakres danych AED | `format_danych/` (m.in. `wzorcowy_zakres_danych.xlsx`) | kontrakt kolumn dla dostawców i agregacji |
| Integrator danych | `integrator/` | dodatek (krok 2) dla dostawców bez wzorcowego formatu |
| Akcja „Otwórz AED” | `branding/` | logo, księga znaku, opis akcji |
| Materiały źródłowe | `references/`, `docs/` | polecenie, regulamin, wytyczne organizatora, standardy, wiedza |

Zmiany w portalu najłatwiej zobaczyć jako diff względem commita `a119b1b` z oryginalnym kodem portalu: `git diff a119b1b -- portal/backend`. Opis zmian jest w [`ZMIANY_W_PORTALU.md`](ZMIANY_W_PORTALU.md).

Instrukcje dla zespołu i agentów są w [`CLAUDE.md`](CLAUDE.md).
