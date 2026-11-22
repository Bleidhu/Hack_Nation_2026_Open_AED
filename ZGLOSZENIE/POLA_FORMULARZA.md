# Pola formularza zgłoszenia (HackNation 2026, „Your Project”)

Teksty do wklejenia w formularz na stronie HackNation, pole po polu, w kolejności z formularza. Nazwy pól są przepisane z formularza dosłownie. Formularz nie podaje limitów znaków dla pól tekstowych, więc długość przy każdym bloku służy tylko do kontroli. Liczono znaki Unicode, a każdy znak nowej linii to 1 znak. Na wypadek ukrytego limitu każdy blok ma mniej niż 2000 znaków. Jeśli pole mimo to utnie tekst, trzeba go skrócić.

Liczby pochodzą z plików repozytorium (stan na 22.11.2026, wersja v2.1.0):
- testy portalu: `demo/wynik/testy.txt`, ostatnia linia: „270 passed, 2 skipped”;
- weryfikacja maszynowa: `demo/wynik/weryfikacja.txt`: „20/20 PASS”;
- integrator: 97 testów (`DODATKOWE_INFORMACJE.md`, krok 14);
- wzorzec dostawcy: 42 kolumny, Wykaz AED: 52 kolumny;
- zmiany w portalu: 34 nowe pliki (w tym 7 próbek danych testowych), 11 istniejących z dopiskami;
- prezentacja: 28 slajdów, księga znaku: 12 stron, film: 1 min 14 s.

Miejsca oznaczone **[SPRAWDŹ]** mogą się jeszcze zmienić przed wysłaniem (lista na końcu pliku).

---

## 1. Project Name

```
Dane (prze)życie: Wykaz AED w portalu dane.gov.pl
```
Długość: 49 znaków (limit: brak w formularzu).

## 2. Team lead

Lista wyboru. Bez zmian (wybrany lider zespołu).

## 3. Problem

Podpowiedź formularza: krótko, dlaczego projekt jest potrzebny, najlepiej ze statystykami. Statystyki poniżej pochodzą z migawki realnych zbiorów (`references/dane_gov_pl_aed/`) i raportu agregacji (`demo/wynik/raport_agregacji.txt`).

```
Dane o defibrylatorach AED są w dane.gov.pl rozproszone, a każdy dysponent publikuje je inaczej (migawka z 21.11.2026):
- Krosno: plik CSV bez kolumny z miejscowością;
- Przemyśl: link do systemu miasta, te same dane w pięciu dystrybucjach;
- Marki: CSV i XLSX z błędami, cały wiersz w jednym polu;
- Legionowo: zasób z AED w zbiorze mieszanym „Zdrowie”;
- Warszawa: w portalu tylko strona WWW, dane w API miasta wymagającym tokenu;
- Gdańsk: AED w 278 pojazdach ZTM, w pliku JSON floty.

Z 11 zasobów tej migawki (bez Gdańska) do wspólnej tabeli wzorca pasuje tylko jeden: Legionowo, 24 punkty. Większość pozostałych nie ma kolumn wzorca albo ma format nietabelaryczny. Wyszukiwarka portalu nie przeszukuje zawartości tabel, a jednej ogólnopolskiej listy AED w portalu nie ma. Przy nagłym zatrzymaniu krążenia liczy się każda minuta, więc trzeba szybko wiedzieć, gdzie jest najbliższy defibrylator.
```
Długość: 899 znaków (limit: brak w formularzu).

## 4. Solution

Podpowiedź formularza: opis rozwiązania i korzyści dla użytkownika.

```
Projekt zmienia kod otwartego portalu dane.gov.pl, a nie buduje osobnej aplikacji. Portal ma nocny mechanizm DGA, który scala zasoby wielu instytucji w jeden zasób zbiorczy. Przerobiono go na Wykaz AED.

1. Dostawca oznacza zbiór w istniejących „Polach niestandardowych” (standard = AED). Nie trzeba migracji bazy, nowego pola, tagu ani checkboxa.
2. Dostawca publikuje zasób według wzorcowego zakresu danych (42 kolumny). Portal waliduje go swoim zwykłym potokiem.
3. Co noc o 4:15 zadanie Celery wybiera zasoby z oznaczonych zbiorów i sprawdza każdy z osobna: kolumny wzorca, licencję (przyjmuje CC0 1.0 i CC BY 4.0, pomija ODbL z OpenStreetMap) i dane kontaktowe, które usuwa, gdy zbiór deklaruje dane osobowe. Każdy pominięty zasób trafia do logu z powodem.
4. To samo urządzenie zgłoszone przez dwóch dostawców trafia do wykazu raz. Kluczem jest numer seryjny, a między różnymi zasobami także ten sam producent lub model w odległości do 30 m (bez producenta: ta sama nazwa do 10 m).
5. Wynik to jeden zasób CSV (52 kolumny). Każdy wiersz ma pochodzenie: wydawcę, licencję, zasób źródłowy i datę. Portal sam daje mu tabelę, mapę, pobieranie i API (stały adres /1.4/aed-aggregated).

Dostawca spoza portalu wystawia opis zbioru w XML (schemat XSD) z linkiem do pliku CSV i sumą md5. Komenda import_aed_xml sprawdza kod 200, zgodność z XSD, sumę md5 i kolumny, a dopiero potem tworzy zbiór i zasób. Przy niezgodności nic nie zapisuje.

Dodatek wyłącza się ustawieniem AED_AGGREGATION_ENABLED. Po wyłączeniu portal działa jak oryginał.

Korzyści: dysponent AED dostaje jeden szablon i publikuje w portalu bez nowego systemu. Służby ratownicze, mieszkańcy i twórcy map oraz aplikacji dostają jeden otwarty wykaz z mapą i API, z informacją, skąd pochodzi każdy rekord.

Poza portalem: wzorcowy zakres danych (XLSX), akcja promocyjna „Dane (prze)życie” z hasłem „Twoje dane – czyjeś życie.”, logotypem i księgą znaku oraz, jako dodatek, integrator danych.
```
Długość: 1953 znaków (limit: brak w formularzu).

## 5. Challenges

Zablokowane przez organizatora („Challenge change locked”). Bez zmian: „[Departament Zarządzania Danymi - Ministerstwo Cyfryzacji]: Misja AED - Dane Na Ratunek”.

## 6. Cover image

Wymagania z formularza: zalecane 800×600 px (proporcje 4:3), PNG, JPG lub WEBP, maksymalnie 5 MB.

Wgrać: **`branding/okladka/okladka_800x600.png`** (800×600 px, ok. 56 kB). Zapasowo: `branding/okladka/okladka_800x600.jpg` (ok. 58 kB).

Okładka to wersja negatywowa znaku na granacie zgodnie z księgą znaku: znak, nazwa „Dane (prze)życie”, hasło „Twoje dane – czyjeś życie.” i podpis „Wykaz AED w portalu dane.gov.pl”. Bez logotypów instytucji. Źródło: `branding/build_okladka.py` (polecenie w nagłówku skryptu).

## 7. Idea stage

Lista wyboru, obecnie „New Idea”. Formularz pyta, czy to nowy pomysł, czy projekt rozwijany już wcześniej. Pierwszy commit repozytorium pochodzi z 21.11.2026, więc „New Idea” zgadza się z historią repozytorium. **[DECYZJA]** Jeśli zespół pracował nad pomysłem przed wydarzeniem, trzeba wybrać inną opcję.

## 8. What's done so far and goal of your project

Podpowiedź formularza: co zrobiono przed wydarzeniem, a co w jego trakcie.

```
Projekt powstał w czasie HackNation 2026 (21–22.11.2026). Gotowe i sprawdzone:
- modyfikacja portalu: 34 nowe pliki obok DGA (w tym 7 próbek danych testowych) i dopiski w 11 istniejących, bez migracji;
- testy w kontenerze portalu: 270 passed, 2 skipped, w tym regresja DGA; makemigrations --check zwraca „No changes detected”;
- weryfikacja maszynowa wymagań (python demo/sprawdz.py): 20/20 PASS;
- portal uruchomiony we własnym środowisku: zrzuty ekranu i film (1 min 14 s);
- import danych spoza portalu: opis zbioru w XML ze schematem XSD, link do CSV i suma md5;
- deduplikacja urządzeń przy budowie wykazu.

Gotowe są też: klikalny prototyp offline (demo/index.html), wzorcowy zakres danych w wersji 2.1.0 (XLSX, Table Schema, CSVW, JSON-LD, XSD), logotyp w JPG, PNG, PDF i SVG, księga znaku (12 stron), prezentacja (28 slajdów) i instrukcja dla jury. Dodatek: integrator danych dla dostawców bez wzorca (adaptery Warszawy i Gdańska, blokada ODbL, opis zbioru w XML, 97 testów).

Użycie AI: zespół korzystał z asystentów AI (Claude, Cursor) do wsparcia analizy kodu portalu, pisania kodu i implementacji testów oraz do wsparcia tworzenia księgi znaku i plików znaku. Asystenci pomagali też w redakcji dokumentów, automatyzacji zrzutów ekranu i składaniu prezentacji. Kierunek rozwiązania wybrał i zweryfikował zespół, a każdą zmianę sprawdził testami i w uruchomionym portalu (DODATKOWE_INFORMACJE.md, krok 16).

Cel: ogólnopolski, otwarty i aktualny Wykaz AED w dane.gov.pl, budowany co noc z zasobów wielu dysponentów.
```
Długość: 1526 znaków (limit: brak w formularzu). **[SPRAWDŹ]** liczby testów, plików, slajdów i PASS.

## 9. Team status

Lista wyboru. Bez zmian: „Full team”.

## 10. Current team size

Bez zmian: `2`. **[DECYZJA]** Poprawić, jeśli skład się zmienił.

## 11. Needed skills

Pole dotyczy zespołów, które szukają członków. Przy „Full team” zaznaczenia nie mają znaczenia. **[DECYZJA]** Odznaczyć wszystkie albo zostawić bez zmian.

## 12. Skills comment

Pole dotyczy szukania członków zespołu. Można zostawić puste albo wpisać:

```
Zespół jest kompletny.
```
Długość: 22 znaków (limit: brak w formularzu).

## 13. Your video presentation (Public or Listed YouTube link)

Formularz przyjmuje tylko link do YouTube. Plik filmu: `demo/wideo/dane_przezycie_wykaz_aed.mp4` (1 min 14 s, 1920×1080, bez dźwięku, napisy po polsku, ok. 18 MB). Link do wklejenia: https://youtu.be/wiHsN31m_6o.

Tytuł filmu na YouTube:
```
Dane (prze)życie: Wykaz AED w portalu dane.gov.pl (HackNation 2026)
```
Długość: 67 znaków (YouTube: maks. 100).

Opis filmu na YouTube:
```
Wykaz AED w zmodyfikowanym portalu dane.gov.pl: dostawca oznacza zbiór w „Polach niestandardowych” (standard = AED), portal co noc scala zasoby wielu dysponentów w jeden wykaz z tabelą, mapą i API. Nagrania portalu uruchomionego lokalnie w Dockerze, bez makiet.

Zadanie „Misja AED – Dane na ratunek”, HackNation 2026. Akcja „Dane (prze)życie”: Twoje dane – czyjeś życie.
Kod i dokumentacja: https://github.com/Bleidhu/Hack_Nation_2026_Open_AED
```
Długość: 503 znaków (YouTube: maks. 5000).

Link do wklejenia w formularz:
```
https://youtu.be/wiHsN31m_6o
```
Film jest już na YouTube.

## 14. Website (https://...)

Pole opcjonalne. Wersja live działa tylko przy włączonym tunelu ngrok, a darmowy ngrok może zmienić adres, więc w formularzu bezpieczniej jest wpisać stały adres: instrukcję dla jury w repozytorium.

Wariant A (zalecany, adres stały):
```
https://github.com/Bleidhu/Hack_Nation_2026_Open_AED/blob/main/INSTRUKCJA_DLA_JURY.md
```
Długość: 85 znaków (limit: brak w formularzu).

Wariant B (wersja live, tylko jeśli tunel będzie włączony w czasie oceny):
```
https://thumb-abrasive-bovine.ngrok-free.dev/live/
```
Adres działa, gdy tunel jest włączony (`powershell -ExecutionPolicy Bypass -File demo/uruchom_live.ps1`); lista adresów w `WERSJA_LIVE.md`.

## 15. [Obowiązkowe] Link do repozytorium z kodem

```
https://github.com/Bleidhu/Hack_Nation_2026_Open_AED
```
Długość: 52 znaków (limit: brak w formularzu). Bez zmian. **[SPRAWDŹ]** Repozytorium musi być publiczne albo udostępnione jury, a GitHub musi mieć ostatnią wersję (wypchnięty `main` i tag).

## 16. [Opcjonalne] Instrukcje jak otworzyć projekt

```
Wszystkie dowody są plikami w repozytorium. Nie trzeba się logować, instalować Dockera ani łączyć z serwerami zespołu.

1. INSTRUKCJA_DLA_JURY.md w katalogu głównym: krótka instrukcja na 2 minuty. Pełna lista wymagań z plikami dowodowymi: DODATKOWE_INFORMACJE.md.
2. demo/index.html: klikalny prototyp całego procesu w 9 krokach. Otwiera się dwuklikiem i działa offline.
3. demo/wynik/weryfikacja.txt: sprawdzenie maszynowe, każde wymaganie z wynikiem PASS lub FAIL i plikiem dowodowym. Ponowne uruchomienie: python demo/sprawdz.py
4. ZMIANY_W_PORTALU.md: opis zmian w kodzie portalu. Diff względem nietkniętego kodu: git diff a1adc22 -- portal/backend
5. Dowody z działającego portalu: demo/zrzuty/ (zrzuty ekranu), demo/wynik/testy.txt (270 passed, w tym regresja DGA) i film https://youtu.be/wiHsN31m_6o.
6. Wzorcowy zakres danych: format_danych/wzorcowy_zakres_danych.xlsx. Logotyp: branding/logo/. Księga znaku: branding/ksiega_znaku.pdf. Prezentacja: prezentacja/dane_przezycie_prezentacja.pdf.
7. Pliki do zgłoszenia zebrane w jednym katalogu: ZGLOSZENIE/.
8. Integrator danych to dodatek, a nie główny rezultat: integrator/README.md.

Opcjonalna wersja live (tymczasowa, przez tunel): WERSJA_LIVE.md. Ocena jej nie wymaga.
```
Długość: 1241 znaków (limit: brak w formularzu). **[SPRAWDŹ]** liczba testów w punkcie 5.

## 17. [Obowiązkowe] Nazwa zespołu

```
AGH_BIT_GAMMA
```
Bez zmian.

## 18. [Obowiązkowe] Numer stolika

```
8D
```
Bez zmian.

## 19. [Opcjonalne] Prezentacja

Wymagania z formularza: PDF, maksymalnie 10 MB.

Wgrać: **`prezentacja/dane_przezycie_prezentacja.pdf`** (28 slajdów, ok. 1,4 MB, czyli dużo poniżej limitu). Kopia: `ZGLOSZENIE/prezentacja/`. **[SPRAWDŹ]** Po ostatniej przebudowie prezentacji jeszcze raz sprawdzić rozmiar i liczbę slajdów oraz to, czy kopia w `ZGLOSZENIE/` jest aktualna (`python demo/zloz_zgloszenie.py`).

## 20. [Opcjonalne] Dodatkowe pole na materiały i prezentacje

Pole przyjmuje link. Najprościej wpisać katalog zgłoszenia w repozytorium:

```
https://github.com/Bleidhu/Hack_Nation_2026_Open_AED/tree/main/ZGLOSZENIE
```
Długość: 73 znaków (limit: brak w formularzu).

Jeśli pole przyjmuje dłuższy tekst, można wkleić:
```
Komplet plików do zgłoszenia (prototyp offline, wzorcowy zakres XLSX, logotyp, księga znaku, prezentacja, film): https://github.com/Bleidhu/Hack_Nation_2026_Open_AED/tree/main/ZGLOSZENIE . Start: INSTRUKCJA_DLA_JURY.md
```
Długość: 218 znaków (limit: brak w formularzu).

---

## Co gdzie wgrać (skrót)

| Pole | Plik lub link | Limit z formularza | Stan |
|---|---|---|---|
| Cover image | `branding/okladka/okladka_800x600.png` (800×600, ok. 56 kB) | 800×600 zalecane, PNG/JPG/WEBP, 5 MB | gotowe |
| Your video presentation | https://youtu.be/wiHsN31m_6o | tylko link YouTube | gotowe |
| Website | instrukcja w repozytorium albo adres live z `WERSJA_LIVE.md` | brak | wariant A gotowy, B po ngrok |
| Link do repozytorium | https://github.com/Bleidhu/Hack_Nation_2026_Open_AED | brak | gotowe |
| Prezentacja | `prezentacja/dane_przezycie_prezentacja.pdf` (ok. 1,4 MB) | PDF, 10 MB | gotowe |
| Dodatkowe pole | link do `ZGLOSZENIE/` w repozytorium | brak | gotowe |

## [SPRAWDŹ]: liczby i stany, które mogą się jeszcze zmienić

Przed wklejeniem porównać z plikami:

1. **Testy portalu: 270 passed, 2 skipped** (pola 8 i 16). Źródło: ostatnia linia `demo/wynik/testy.txt`. Zmieni się, jeśli ktoś doda testy w `portal/` i ponownie uruchomi kontener testowy.
2. **Weryfikacja maszynowa: 20/20 PASS** (pole 8). Źródło: pierwsza linia `demo/wynik/weryfikacja.txt`.
3. **34 nowe pliki i 11 istniejących z dopiskami** (pole 8). Źródło: `git diff --name-status a1adc22 -- portal/backend` (28 plików dodanych w śledzonych, 11 zmienionych) plus 6 nowych, jeszcze nieśledzonych plików w `portal/`. Zmieni się, jeśli dojdą pliki w `portal/`.
4. **Prezentacja: 28 slajdów, ok. 1,4 MB** (pola 8 i 19). Prezentację przebudowuje się równolegle (`prezentacja/`).
5. **Integrator: 97 testów** (pole 8). Źródło: `python -m unittest discover -s integrator/testy -t .`.
6. **Kolumny 42/52, księga znaku 12 stron, film 1 min 14 s**: stałe dla v2.1.0, zmienią się tylko przy nowej wersji wzorca, księgi lub filmu.
7. **„Projekt powstał w czasie HackNation 2026”** (pole 8): zgodne z historią repozytorium (pierwszy commit 21.11.2026), ale wymaga potwierdzenia zespołu.
8. **Push na GitHub**: w chwili pisania lokalne zmiany v2.1.0 nie są zacommitowane. Jury zobaczy tylko to, co jest na GitHubie, a linki w polach 14, 15 i 20 prowadzą do gałęzi `main`.

## Decyzje dla zespołu

- Idea stage: „New Idea” czy inna opcja (pole 7).
- Team size i Needed skills (pola 10 i 11).
- Website: stały link do instrukcji czy adres live (pole 14).
- Wgranie filmu na YouTube i konto, z którego wgrać (pole 13).
- Otwarte kwestie z `ZGLOSZENIE/README.md`: lista autorów do README i prezentacji, potwierdzenie licencji kodu portalu u organizatora, sprawdzenie kolizji nazwy akcji (UPRP, EUIPO, domeny).
