# Uzasadnienie decyzji: wzorcowy zakres danych i mechanizm Wykazu AED

Dokument zbiera decyzje przyjęte 21.11.2026 razem z powodami. Pliki formatu opisuje [`README.md`](README.md), a reguły w postaci maszynowej są w arkuszu `5_Zasady` pliku `wzorcowy_zakres_danych.xlsx` i w polu `x-reguly-dodatkowe` schematu [`schemat/aed_punkty.tableschema.json`](schemat/aed_punkty.tableschema.json).

Oznaczenia: **[D]** wynika wprost z dokumentu lub kodu portalu, **[W]** jest naszym wnioskiem.

## 1. Jak portal rozpozna zbiory i zasoby AED

**Decyzja:** zbiór deklaruje zgodność ze wzorcem w istniejącym polu „Pola niestandardowe” (`Dataset.customfields`): `standard` = `AED` (dopuszczalna wersja, np. `AED 1.1`; wielkość liter nie ma znaczenia). Dodatkowo portal sprawdza kolumny **każdego** zasobu takiego zbioru. Zbiór zbiorczy jest rozpoznawany tą samą metadaną (`zestawienie` = `AED-krajowe`).

**Powody:**
- Założenie projektu: bez migracji portalu; tagi i checkbox są niezalecane, lepsza jest inna metadana, niepowiązana z innymi.
- `customfields` istnieje w bazie, jest w formularzu zbioru (także dla zbiorów z harvestu) i nie jest używane przez żadną inną logikę, więc nie wymaga migracji [D].
- Tagi realnych zbiorów AED są niespójne: Krosno „Defibrylator”, Przemyśl „AED” i „Defibrylator”, Warszawa „aed”, Legionowo „aed” w zbiorze „Zdrowie”, Marki i Gdańsk bez tagu. Tagi są wolnym tekstem, publicznym, zależnym od języka i nadpisywanym przez harvester [D].
- Checkbox jak w DGA (`Resource.contains_protected_data`) to nowa kolumna modelu, czyli migracja [D].
- Zbiory bywają mieszane (Legionowo: AED obok aptek) i mają wiele dystrybucji (Przemyśl: CSV, GeoJSON, JSON, GML; Marki: CSV i XLSX), więc samo oznaczenie zbioru nie wystarcza i trzeba sprawdzić każdy zasób [D].

**Rozważone warianty:**

| | Wariant | Ocena |
|---|---|---|
| W1 | `customfields`: `standard` = `AED` | **przyjęty**: jawna deklaracja dostawcy, zero zmian w modelu; wada: wpisywane ręcznie |
| W2 | W1 plus kontrolka w formularzu zbioru | odłożony: wygodniejszy, ale UI w formie checkboxa jest niezalecany |
| W3 | tag kontrolowany | odrzucony: niezalecany, niespójny, publiczny, nadpisywany przez harvester |
| W4 | rozpoznanie po kolumnach zasobu | **przyjęty jako kontrola** każdego zasobu; samodzielnie brak deklaracji dostawcy |

Z zasobów zbioru oznaczonego `AED` do wykazu trafiają tylko tabelaryczne z wymaganymi kolumnami. Pozostałe są pomijane z powodem w logu (strona WWW lub API, brak kolumn, licencja ODbL, format nietabelaryczny).

## 2. Dlaczego wzorzec wygląda tak

**Dwie warstwy.** Wzorzec dostawcy (42 kolumny, wersja 2.1.0) to plik, który publikuje dostawca. Zasób zbiorczy (52 kolumny) buduje co noc portal: kolumny wzorca, 3 wyliczane i 6 kolumn pochodzenia. Dostawca nie wypełnia kolumn wyliczanych ani pochodzenia.

**Zakres.** Stałe punkty AED i ich stan. AED w pojazdach i flotach (np. ZTM Gdańsk) nie są punktami: baza ZTM ma 503 pojazdy, z czego 278 z AED, ale bez lokalizacji punktowej. To ograniczenie opisane w prezentacji.

**Jednostka rekordu.** Jeden wiersz to jedno fizyczne urządzenie. Wiele AED w jednym miejscu to osobne wiersze z własnym `id_zrodlowe`, rozróżnione `opis_lokalizacji` lub `kondygnacja`; te same współrzędne są dopuszczalne i agregacja ich nie scala. Deduplikacja w portalu łączy wiersze jednego pliku tylko przy tym samym numerze seryjnym; zgodność producenta lub modelu i odległość do 30 m bierze pod uwagę wyłącznie między różnymi zasobami. Gdy źródło nie rozróżnia urządzeń, liczymy jedno (możliwe niedoszacowanie).

**Identyfikatory.** Dostawca podaje `id_zrodlowe`. `id_aed` nadaje portal deterministycznie: `PL-AED-` plus 12 znaków szesnastkowych SHA-1 z (id instytucji wydawcy + `id_zrodlowe`), a gdy `id_zrodlowe` jest puste, z (instytucja + znormalizowana nazwa + współrzędne zaokrąglone do 5 miejsc). Powód: 7 cyfr przy ok. 20 tys. urządzeń daje praktycznie pewną kolizję (paradoks urodzin, n²/2N ≈ 20) [W]. Zmiana `id_zrodlowe` (lub, przy jego braku, nazwy albo współrzędnych) daje nowy `id_aed`.

**Stan urządzenia.** To kolumny tabeli punktów, aktualizowane przez dostawcę nową wersją pliku. Brak wiedzy nie oznacza „sprawny”: puste `status_urzadzenia` to `nieznany`, puste `poziom_weryfikacji` to `niezweryfikowany`, a `data_weryfikacji` zostaje pusta (data importu nie jest datą weryfikacji). Kolumna wyliczana `wymaga_przegladu` ma wartość `true`, gdy minął termin elektrod lub baterii albo od przeglądu minęło ponad 12 miesięcy, i nie nadpisuje statusu podanego przez dostawcę.

**Dysponent i wydawca.** Dysponent to właściciel lub opiekun urządzenia, wydawca to instytucja publikująca zasób. Gdy `dysponent_nazwa` jest pusta, agregacja wpisuje wydawcę i ustawia `dysponent_z_wydawcy` = `true`. Dla osoby fizycznej dostawca podaje rodzaj podmiotu (np. „gabinet lekarski”) albo zostawia pole puste, a `dysponent_regon` dotyczy tylko osób prawnych [W, na podstawie Standardu bezpieczeństwa s. 8, 12, 14].

**Dwa poziomy wymagalności.** Wymagane we wzorcu (norma dla nowych publikacji): `id_zrodlowe`, `nazwa_lokalizacji`, `miejscowosc`, `szerokosc_geograficzna`, `dlugosc_geograficzna`, `opis_lokalizacji`, `typ_dostepu`, `dostepny_24_7`, `data_aktualizacji`. Minimum do agregacji (tolerancja dla istniejących źródeł): nazwa, miejscowość i współrzędne. Brak kolumny minimum pomija zasób z powodem w logu, a pusta wartość pomija wiersz. Powód: realne źródła z dane.gov.pl nie mają wszystkich kolumn, a wykaz ma je mimo to zebrać.

## 3. Ochrona danych, prawa autorskie i licencje

**Podstawy [D]:**
- Dostawca jest administratorem danych, które publikuje, i odpowiada za ich treść (Regulamin §2 pkt 5, §4; Przewodnik dla dostawców 1.23, s. 92–94). Upublicznienie nie zwalnia z realizacji praw osób, których dane dotyczą. Przed publikacją danych osobowych zaleca się ocenę skutków (art. 35 RODO), a danych wrażliwych portal nie rekomenduje.
- Dane kontaktowe osób reprezentujących instytucje to nadal dane osobowe: imię i nazwisko trzeba usunąć lub zanonimizować (Standard bezpieczeństwa s. 11–15).
- Dane podmiotu niezobowiązanego (np. firmy) są „danymi prywatnymi” z wyjątkiem danych osobowych (Regulamin §2 pkt 4).
- Edytor nie może zamieszczać danych naruszających prawa osób trzecich, w tym prawa autorskie i wizerunek (Regulamin §7); zdjęcie może być utworem (Standard prawny s. 9).
- Podmiot zobowiązany może określić warunki ponownego wykorzystywania: źródło i czas, przetworzenie, odpowiedzialność, dane osobowe (art. 15 ust. 1 ustawy z 11.08.2021). W portalu są to pola zbioru (`license_condition_*`).
- Portal zaleca CC0 1.0 i dopuszcza CC BY 4.0 (Przewodnik s. 17–19).
- Dokumenty nie regulują łączenia CC0 z CC BY ani publikacji kodów do szafek. Poniższe decyzje w tych sprawach są naszymi wnioskami [W].

**Decyzje:**
- Kontakty (`telefon_kontaktowy`, `email_kontaktowy`) tylko instytucjonalne lub funkcyjne. Gdy zbiór źródłowy deklaruje dane osobowe (`license_condition_personal_data`), agregacja czyści kontakty w jego wierszach i dopisuje kod `kontakt_usuniety` do `przetworzenie`. Zasób zbiorczy z założenia nie zawiera danych osobowych.
- W polach `opis_lokalizacji` i `instrukcja_dostepu` nie wolno podawać kodów do szafek, miejsca przechowywania klucza ani imion i nazwisk (zakaz to nasza decyzja ze względu na bezpieczeństwo urządzeń).
- Kolumny `uwagi` i `zdjecie_url` nie wchodzą do wzorca (prawa autorskie, wizerunek, dane osobowe w tekście).
- AED w lokalach mieszkalnych osób fizycznych nie są publikowane. `typ_dostepu` = `prywatny` oznacza teren niepubliczny instytucji lub firmy.
- Do wykazu wchodzą tylko źródła na CC0 1.0 i CC BY 4.0. Wiersze z `zrodlo_danych` = `openstreetmap` są wykluczone (ODbL), nawet gdy zbiór deklaruje CC0.
- Zasób zbiorczy ma licencję CC BY 4.0, a każdy wiersz atrybucję: `wydawca_zasobu`, `licencja_zasobu`, `id_zasobu_zrodlowego`, `url_zasobu_zrodlowego`, `data_danych_zasobu`, `data_agregacji`. Kolumna `przetworzenie` informuje o zmianach: `naglowki` (dopasowanie aliasu nagłówka), `osie` (zamiana współrzędnych), `domyslne` (wpisane wartości jawne), `dysponent_z_wydawcy`, `kontakt_usuniety` (art. 15 ust. 1 pkt 1–2).
- Opis zbioru zbiorczego podaje przyczyny pomijania wierszy i pól: dane osobowe, licencja, brak kolumn, OSM (Standard prawny s. 25).

**Źródła w repozytorium:** [`references/dane_gov_pl_baza_wiedzy/regulamin_portalu.txt`](../references/dane_gov_pl_baza_wiedzy/regulamin_portalu.txt), [`dane_osobowe_w_portalu.txt`](../references/dane_gov_pl_baza_wiedzy/dane_osobowe_w_portalu.txt) oraz PDF-y w [`references/standardy/`](../references/standardy/) (Program otwierania danych 2021–2027, Przewodnik dla dostawców, Standard prawny, Standard bezpieczeństwa).

## 4. Wymagania techniczne, które spełnia wzorzec

Program otwierania danych 2021–2027, załącznik nr 2 (Standard techniczny) [D]:
- wartości logiczne `true`/`false`, kropka dziesiętna bez separatora tysięcy, data `yyyy-mm-dd`, data z czasem `yyyy-mm-ddThh:mm:ss` (s. 123);
- jeden wiersz nagłówka, bez scalonych komórek, bez formuł, jeden arkusz zamiast skoroszytu (s. 123–124);
- REGON 9 lub 14 cyfr, telefon 9 cyfr z dopuszczalnym prefiksem `+`, bez spacji i łączników (s. 124);
- adres w osobnych polach, wartości zgodne z TERYT (s. 124–125);
- CSV zgodny z RFC 4180: UTF-8, przecinek, CRLF, jeden nagłówek, bez pustych i powtórzonych kolumn (s. 126).

Szablon publikacyjny XLSX ma jeden arkusz. Wieloarkuszowy `wzorcowy_zakres_danych.xlsx` jest dokumentacją zakresu, a nie plikiem do publikacji w portalu.

## 5. Dlaczego Wykaz AED na wzór DGA

Założenie: zbiorcza tabela (wykaz) budowana z zasobów wielu dostawców, na wzór wykazów już działających w portalu, oraz przebudowania logiki portalu tak, by takie wykazy dało się pobierać i scalać w jedną listę. W kodzie portalu są trzy takie mechanizmy:

| Mechanizm | Skąd dane | Jak scala | Wynik |
|---|---|---|---|
| **Wykaz chronionych danych (DGA)** | zasoby dostawców o stałych kolumnach, oznaczone flagą zasobu | nocne zadanie Celery czyta zasoby (lokalnie lub z CKAN), waliduje kolumny, dokleja dysponenta i skleja | zasób zbiorczy, API `/dga-aggregated`, strona z tabelą i filtrami |
| Harmonogramy udostępniania danych | pozycje wpisywane przez dostawców | scalenie w jeden harmonogram | eksport CSV/XLSX przez generyczny `TabularView` |
| Katalog metadanych | metadane zbiorów i zasobów | cotygodniowe zadanie | pliki CSV i ZIP |

**Decyzja:** wzorcem jest DGA, bo odpowiada procesowi „zasoby wielu dostawców → jeden zasób zbiorczy”. Wykaz AED powstaje jako dodatek obok DGA, w nowych plikach (`aed_*.py`, `tasks/aed.py`), z punktami zaczepienia w istniejącym kodzie ograniczonymi do harmonogramu, ustawień, trasy API i eksportu zadania, oraz z wyłącznikiem `AED_AGGREGATION_ENABLED`. Po wyłączeniu portal działa jak oryginał. Istniejący kod DGA nie jest zmieniany ani przenoszony; jego funkcje wielokrotnego użytku są importowane.

**Odrzucony wariant:** generyczny pakiet „wykazów” z rejestrem definicji (AED byłby pierwszą z nich). Zrezygnowaliśmy z niego, bo zmiana rdzenia DGA zwiększałaby ryzyko regresji, a zasada nadrzędna to rozszerzanie portalu bez usuwania. Ten sam wzorzec da się powtórzyć dla innych wykazów.

Pobieranie wykazu nie wymaga osobnej pracy: zasób zbiorczy jest dostępny mechanizmami portalu (tabela, CSV, API `/resources/{id}/data`, mapa `/geo`).

## 6. Co jest ograniczeniem lub nie zostało potwierdzone

- Tekstu ustawy z 11.08.2021 nie mamy lokalnie: standardy z 2020 r. cytują wyłączenia z ustawy z 2016 r., więc numer artykułu o wyłączeniach (prywatność, tajemnica przedsiębiorcy) trzeba sprawdzić w ustawie.
- Żaden dokument nie zabrania wprost publikacji kodów do szafek AED. Zakaz we wzorcu jest naszą decyzją.
- Brak wytycznych portalu o łączeniu licencji CC0 i CC BY. Decyzja „CC BY 4.0 plus atrybucja w wierszu” jest naszym wnioskiem.
- Trwałość `customfields` po ponownym harvestowaniu zbioru oraz to, czy redaktor instytucji (nie tylko superuser) może je edytować w zbiorze zaimportowanym, należy potwierdzić w działającym portalu.
- Możliwe niedoszacowanie liczby AED, gdy źródło nie rozróżnia urządzeń w jednym miejscu (sekcja 2).
