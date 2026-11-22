# Instrukcja dla jury (2 minuty)

**Dane (prze)życie: Wykaz AED w portalu dane.gov.pl.** Zmodyfikowany portal co noc składa ogólnopolski wykaz defibrylatorów z zasobów wielu dostawców i usuwa duplikaty. Dane spoza portalu pobiera z API dostawcy: opis zbioru w XML (schemat XSD) z linkiem do CSV i sumą md5. Do oceny nie potrzeba instalacji ani logowania.

1. **Prototyp.** Proszę otworzyć [`demo/index.html`](../demo/index.html) (dwuklik, działa offline) i przejść przyciskiem „Dalej” przez 9 kroków. Krok 4 pokazuje pobranie danych przez API: walidację XSD, kontrolę md5 i deduplikację.
2. **Sprawdzenie maszynowe.** Wynik jest w [`demo/wynik/weryfikacja.txt`](../demo/wynik/weryfikacja.txt): każde wymaganie ma PASS lub FAIL i plik dowodowy. Można go powtórzyć poleceniem `python demo/sprawdz.py`.
3. **Przykład danych z API dostawcy:** [`opis_poprawny.xml`](../format_danych/przyklady/opis/opis_poprawny.xml), [`opis_bledny_md5.xml`](../format_danych/przyklady/opis/opis_bledny_md5.xml) (import odrzucony), schemat [`aed_opis_zbioru.xsd`](../format_danych/schemat/aed_opis_zbioru.xsd).
4. **Zmiany w kodzie portalu:** [`ZMIANY_W_PORTALU.md`](../ZMIANY_W_PORTALU.md) (rozszerzenie, nic nie usunięto, zero migracji).
5. **Pozostałe pliki do oceny:** wzorcowy zakres danych [`format_danych/wzorcowy_zakres_danych.xlsx`](../format_danych/wzorcowy_zakres_danych.xlsx), prezentacja [`prezentacja/dane_przezycie_prezentacja.pdf`](../prezentacja/dane_przezycie_prezentacja.pdf), logotyp [`branding/logo/`](../branding/logo/) i księga znaku [`branding/ksiega_znaku.pdf`](../branding/ksiega_znaku.pdf).

**Wersja live do przeklikania:** <https://thumb-abrasive-bovine.ngrok-free.dev/live/>. Pod tym adresem są działający portal z Wykazem AED (tabela, mapa, API, panel), prototyp i serwer dostawcy. Przy pierwszym wejściu ngrok pokazuje stronę ostrzegawczą, wystarczy kliknąć „Visit Site”. Link działa, gdy tunel jest włączony; lista adresów: [`WERSJA_LIVE.md`](../WERSJA_LIVE.md).

Film z działającego portalu (1 min 14 s): [`demo/wideo/dane_przezycie_wykaz_aed.mp4`](../demo/wideo/dane_przezycie_wykaz_aed.mp4).

**Dodatkowe informacje** (realizacja każdego wymagania, testy, licencje, ograniczenia, użycie AI, integrator): [`DODATKOWE_INFORMACJE.md`](../DODATKOWE_INFORMACJE.md). Zgłoszenie w jednym katalogu: [`ZGLOSZENIE/`](../ZGLOSZENIE/README.md).
