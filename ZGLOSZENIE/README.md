# Rzeczy do zgłoszenia (submit): Dane (prze)życie, Wykaz AED w portalu dane.gov.pl

Tu są pliki do przekazania organizatorowi. To kopie: oryginały zostają w repozytorium. Kopie składa polecenie `python demo/zloz_zgloszenie.py`, uruchamiane po `python demo/build_demo.py`.

**Zacznij od [`INSTRUKCJA_DLA_JURY.md`](INSTRUKCJA_DLA_JURY.md)**, a potem otwórz [`prototyp/index.html`](prototyp/index.html) (działa offline).

## Stan wersji

- **Zawiera:**
  - modyfikację portalu dane.gov.pl, czyli Wykaz AED na wzór wykazu DGA, z testami i bez migracji;
  - prototyp offline, wzorcowy zakres danych XLSX i wynik agregacji;
  - dowody z portalu uruchomionego we własnym środowisku;
  - prezentację;
  - akcję "Dane (prze)życie": nazwę, hasło, logotyp i księgę znaku.
- **Dodatek (nie główny rezultat):** integrator danych dla dostawców bez wzorcowego formatu (`../integrator/`): mapowanie na wzorzec v2, walidacja, duplikaty, porównanie z OSM, adaptery Warszawy i Gdańska, lokalne UI, 87 testów. Przykładowe wyniki w [`prototyp/integrator/`](prototyp/integrator/README.md); portal nie wymaga integratora do działania.

## Zawartość i wymagania

| Wymaganie | Gdzie | Stan |
|---|---|---|
| Instrukcja dla jury w ponumerowanych krokach | [`INSTRUKCJA_DLA_JURY.md`](INSTRUKCJA_DLA_JURY.md) | jest |
| §4 tytuł i szczegółowy opis projektu | [`../README.md`](../README.md), [`ZMIANY_W_PORTALU.md`](ZMIANY_W_PORTALU.md) | jest |
| §4 prezentacja (min. 5 slajdów ze zrzutami, kroki użytkownika, ograniczenia) | [`prezentacja/dane_przezycie_prezentacja.pdf`](prezentacja/dane_przezycie_prezentacja.pdf), [`.pptx`](prezentacja/dane_przezycie_prezentacja.pptx) | jest (15 slajdów, zrzuty na slajdach 4-10) |
| §4 prototyp rozwiązania, klikalny | [`prototyp/index.html`](prototyp/index.html) | jest |
| §4 wzorcowy zakres danych (XLSX) | [`wzorcowy_zakres_danych.xlsx`](wzorcowy_zakres_danych.xlsx) | jest |
| §4 kod źródłowy | całe repozytorium; zmiany portalu jako łatka względem oryginału (`a119b1b`): [`kod/zmiany_portalu_wzgledem_oryginalu.patch`](kod/zmiany_portalu_wzgledem_oryginalu.patch) | jest |
| §4 logotyp (.jpg, .png, .pdf i format otwarty) | [`logotyp/`](logotyp/): wersja pozioma, z hasłem, pionowa, znak i sygnet, każda w JPG, PNG, PDF i SVG | jest |
| §4 księga znaku (.pdf) | [`ksiega_znaku.pdf`](ksiega_znaku.pdf) | jest |
| §2 nazwa akcji i hasło | „Dane (prze)życie”, „Twoje dane – czyjeś życie.”; opis: [`../branding/AKCJA_DANE_PRZEZYCIE.md`](../branding/AKCJA_DANE_PRZEZYCIE.md) | jest |
| §5 format odczytywalny maszynowo | [`dane/wykaz_aed_wynik_agregacji.csv`](dane/wykaz_aed_wynik_agregacji.csv) (CSV, 51 kolumn); schematy: [`../format_danych/schemat/`](../format_danych/schemat/) | jest |
| Portal uruchomiony we własnym środowisku | [`prototyp/zrzuty/`](prototyp/zrzuty/README.md), [`prototyp/wynik/testy.txt`](prototyp/wynik/testy.txt) | jest |
| §5 WCAG, responsywność, UX | prototyp; podglądy 1440 i 390 px: [`../demo/wynik/`](../demo/wynik/) | jest |
| Zakres użycia AI (`regulamin_zadania.pdf` §2 ust. 8) | instrukcja, krok 16; prezentacja, slajd 15 | jest |
| Integrator danych (dodatek, krok 2) | instrukcja, krok 14; wyniki: [`prototyp/integrator/`](prototyp/integrator/README.md); kod: `../integrator/` | jest (dodatek) |

## Weryfikacja z `references/`

Sprawdziliśmy:
- listę wymagań formalnych (§4), technicznych (§5) i kryteriów (§8) z `references/zadanie_konkursowe.pdf`;
- obowiązek wskazania zakresu użycia AI z `references/regulamin_zadania.pdf` (§2 ust. 8);
- instrukcja dla jury, klikalny prototyp i portal uruchomiony we własnym środowisku.

Otwarte kwestie do decyzji zespołu (nie blokują oceny): lista autorów do README i prezentacji, potwierdzenie licencji kodu portalu u organizatora, sprawdzenie kolizji nazwy akcji (UPRP, EUIPO, domeny).
