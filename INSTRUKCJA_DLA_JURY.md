# Instrukcja dla jury (2 minuty)

**Dane (prze)życie: Wykaz AED w portalu dane.gov.pl.** Portal zmodyfikowano tak, że co noc składa ogólnopolski wykaz defibrylatorów z zasobów wielu dostawców, także z danych z zewnątrz w XML sprawdzanych schematem XSD. Nic nie trzeba instalować ani logować.

1. **Otwórz [`demo/index.html`](demo/index.html)** (dwuklik, działa offline) i kliknij „Dalej” przez 9 kroków. Krok 4 pokazuje dane z zewnątrz w XML: przełącz plik poprawny i błędny i zobacz wynik walidacji. Ten sam proces na zrzutach z działającego portalu jest w krokach 2–8.
2. **Sprawdź maszynowo: `python demo/sprawdz.py`** (potrzebny Python; brakujące biblioteki skrypt dociągnie przez `uv`). Wynik, bez uruchamiania, jest w [`demo/wynik/weryfikacja.txt`](demo/wynik/weryfikacja.txt): każde wymaganie z PASS/FAIL i plikiem dowodowym ([JSON](demo/wynik/weryfikacja.json)).
3. **Zobacz minimalny przykład danych i walidacji:** [`aed_poprawny.xml`](format_danych/przyklady/xml/aed_poprawny.xml), [`aed_bledny.xml`](format_danych/przyklady/xml/aed_bledny.xml), schemat [`aed_punkty.xsd`](format_danych/schemat/aed_punkty.xsd) i raport [`walidacja_xml.json`](demo/wynik/walidacja_xml.json).
4. **Zmiany w kodzie portalu:** [`ZMIANY_W_PORTALU.md`](ZMIANY_W_PORTALU.md); dokładny diff: `git diff a1adc22 --stat -- portal/backend` (rozszerzenie, nic nie usunięto, zero migracji).
5. **Pozostałe pliki do oceny:** wzorcowy zakres danych [`format_danych/wzorcowy_zakres_danych.xlsx`](format_danych/wzorcowy_zakres_danych.xlsx), prezentacja [`prezentacja/dane_przezycie_prezentacja.pdf`](prezentacja/dane_przezycie_prezentacja.pdf), logotyp i hasło [`branding/logo/`](branding/logo/) z księgą znaku [`branding/ksiega_znaku.pdf`](branding/ksiega_znaku.pdf).

Film z działającego portalu (1 min 49 s): [`demo/wideo/dane_przezycie_wykaz_aed.mp4`](demo/wideo/dane_przezycie_wykaz_aed.mp4).

**Dodatkowe informacje** (pełna instrukcja: gdzie jest realizacja każdego wymagania, testy, licencje, ograniczenia, użycie AI): [`DODATKOWE_INFORMACJE.md`](DODATKOWE_INFORMACJE.md). Zgłoszenie w jednym katalogu: [`ZGLOSZENIE/`](ZGLOSZENIE/README.md).
