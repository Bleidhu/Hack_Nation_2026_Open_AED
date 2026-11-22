# Rzeczy do zgłoszenia (submit): Otwórz AED, Wykaz AED w portalu dane.gov.pl

**Wersja v1.0.0: rozwiązanie podstawowe.** Tu są pliki do przekazania organizatorowi. To kopie: oryginały zostają w repozytorium. Kopie składa polecenie `python demo/zloz_zgloszenie.py`, uruchamiane po `python demo/build_demo.py`.

**Zacznij od [`INSTRUKCJA_DLA_JURY.md`](INSTRUKCJA_DLA_JURY.md)**, a potem otwórz [`prototyp/index.html`](prototyp/index.html) (działa offline).

## Stan wersji

- **Zawiera:** modyfikację portalu dane.gov.pl, czyli Wykaz AED na wzór wykazu DGA, z testami i bez migracji. Do tego prototyp offline, wzorcowy zakres danych XLSX, wynik agregacji oraz dowody z portalu uruchomionego we własnym środowisku.
- **Niezakończone:** kampania promocyjna (nazwa, hasło, logotyp) i księga znaku. W repozytorium są tylko materiały robocze (`../branding/`), które nie są częścią tego zgłoszenia.
- **Brakuje:** prezentacji (min. 5 slajdów ze zrzutami). Materiał do niej to zrzuty z portalu w `prototyp/zrzuty/`, kroki użytkownika w prototypie i ograniczenia w kroku 15 instrukcji.
- **Poza zakresem:** integrator danych dla dostawców bez wzorcowego formatu (`../integrator/`, zalążek).

## Zawartość i wymagania

| Wymaganie | Gdzie | Stan |
|---|---|---|
| Instrukcja dla jury w ponumerowanych krokach | [`INSTRUKCJA_DLA_JURY.md`](INSTRUKCJA_DLA_JURY.md) | jest |
| §4 tytuł i szczegółowy opis projektu | [`ZMIANY_W_PORTALU.md`](ZMIANY_W_PORTALU.md), [`../README.md`](../README.md) | jest |
| §4 prototyp rozwiązania, klikalny | [`prototyp/index.html`](prototyp/index.html) | jest |
| §4 kod źródłowy | całe repozytorium; zmiany portalu jako łatka względem oryginału (`a119b1b`): [`kod/zmiany_portalu_wzgledem_oryginalu.patch`](kod/zmiany_portalu_wzgledem_oryginalu.patch) | jest |
| §4 wzorcowy zakres danych (XLSX) | [`wzorcowy_zakres_danych.xlsx`](wzorcowy_zakres_danych.xlsx) | jest |
| §5 format odczytywalny maszynowo | [`dane/wykaz_aed_wynik_agregacji.csv`](dane/wykaz_aed_wynik_agregacji.csv) (CSV, 51 kolumn); schematy: [`../format_danych/schemat/`](../format_danych/schemat/) | jest |
| Portal uruchomiony we własnym środowisku | [`prototyp/zrzuty/`](prototyp/zrzuty/README.md), [`prototyp/wynik/testy.txt`](prototyp/wynik/testy.txt) | jest |
| §5 WCAG, responsywność, UX | prototyp; podglądy 1440 i 390 px: [`../demo/wynik/`](../demo/wynik/) | jest |
| Zakres użycia AI (`regulamin_zadania.pdf` §2 ust. 8) | instrukcja, krok 16 | jest |
| §4 prezentacja (min. 5 slajdów ze zrzutami, kroki użytkownika, ograniczenia) | — | **brak** |
| §4 logotyp (.jpg, .png, .pdf i format otwarty) | — (robocze: `../branding/logo/`) | **niezakończone** |
| §4 księga znaku (.pdf) | — (robocza: `../branding/ksiega_znaku.pdf`) | **niezakończone** |
| Integrator danych (dodatek, krok 2) | — (zalążek: `../integrator/`) | **poza zakresem** |

## Weryfikacja z `references/`

Sprawdziliśmy:
- listę wymagań formalnych (§4), technicznych (§5) i kryteriów (§8) z `references/zadanie_konkursowe.pdf`;
- obowiązek wskazania zakresu użycia AI z `references/regulamin_zadania.pdf` (§2 ust. 8);
- instrukcja dla jury, klikalny prototyp i portal uruchomiony we własnym środowisku.

Wszystko, czego brakuje albo co jest niezakończone, opisuje sekcja „Stan wersji”.
