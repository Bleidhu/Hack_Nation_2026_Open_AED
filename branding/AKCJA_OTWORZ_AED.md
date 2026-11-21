> **Kopia z poprzedniego workspace (21.11.2026).** Ścieżki typu `../deliverable/`, `../scratch/`, `../portal_kod/` odnoszą się do starego układu. Mapowanie: `deliverable/` → `format_danych/`, `portal_kod/backend_latest/` → `portal/backend/`, `portal_kod/frontend_latest/` → `portal/frontend/`, `scratch/importer.py` → `integrator/importer.py`.  Nadrzędny jest `CLAUDE.md`.

# Szkic akcji promocyjnej „Otwórz AED”

> Wersja robocza z 2026-11-21. Rozwija wcześniejszy szkic `../old/opracowania_historyczne/zacheta_przekazania_danych.md` i odpowiada na pytanie, co skłoni dysponentów do przekazania danych.
> Logo i księga znaku: `../plan_rozwiazania/branding/`.

## 1. Nazwa, hasło, idea

| | Propozycja główna | Warianty do decyzji zespołu |
|--|-------------------|-----------------------------|
| **Nazwa** | **Otwórz AED** | „AED na mapie”, „Pokaż AED”, „Mapa, która ratuje” |
| **Hasło** | **Pokaż, gdzie jest. Powiedz, czy działa.** | „Otwarte dane. Otwarte szafki. Uratowane życie.”, „Każda minuta się liczy. Każdy AED też.” |
| **Podpis pod znakiem** | dane na ratunek | (nawiązanie do nazwy zadania MC) |
| **Tag na dane.gov.pl** | `OtworzAED` | |

**Dlaczego „Otwórz”:** jedno słowo z podwójnym znaczeniem. Po pierwsze **otwórz dane**, czyli opublikuj je na dane.gov.pl. Po drugie **otwórz szafkę**: nie zamykaj AED na klucz. Nazwa nawiązuje wprost do historii z zadania (AED zamknięte na klucz) i do misji portalu (otwarte dane). Jest też trybem rozkazującym, czyli wezwaniem do działania, które da się zmieścić na naklejce.

## 2. Do kogo mówimy

| Grupa | Dlaczego oni | Co ich przekona | Kanał |
|-------|-------------|-----------------|-------|
| **Samorządy (JST)**, zwłaszcza kupujące AED z Programu Ochrony Ludności 2025–2026 | najwięcej nowych urządzeń, często w magazynach; dane i tak już publikują | gotowy szablon i 15 minut pracy; ranking gmin; argument „to jest w POD”; zgodność z ustawą o otwartych danych | pismo MC/MZ, Związek Miast Polskich, Związek Gmin Wiejskich, wojewodowie, webinar |
| **Duzi operatorzy sieciowi** (ZUS, przewoźnicy, sieci handlowe, energetyka, uczelnie). W OSM mają po kilkadziesiąt–180 AED i **już wysyłają dane e-mailem wolontariuszom** | jeden plik obejmuje setki urządzeń | CSR i raport ESG; „Twoje AED widzi dyspozytor 112”; jedno źródło zamiast pięciu aplikacji | bezpośredni kontakt, izby gospodarcze |
| **Szkoły, przedszkola, kluby sportowe, OSP** | dużo AED, mało czasu i wiedzy IT | formularz bez zakładania konta; naklejka i odznaka dla rodziców i mieszkańców | kuratoria, ZOSP RP, organy prowadzące |
| **Obywatele i kursanci pierwszej pomocy** | widzą AED na co dzień | „zgłoś brakujący lub zamknięty AED” (QR) | **instruktorzy KPP i kursy pierwszej pomocy** (Twoja sieć!), social media, lokalne media |
| **Twórcy aplikacji i map** (OSM Polska, Pierwszy Ratownik, ratujzsercem, aedmapa) | już mają użytkowników | jedno otwarte, referencyjne źródło na CC0 i API | bezpośrednio + PoCoTo na dane.gov.pl |

## 3. Mechanika: 3 kroki dla dysponenta

```
 1. POBIERZ            2. SPRAWDŹ                  3. OPUBLIKUJ
 szablon xlsx/csv  →   walidator „Otwórz AED”   →  na dane.gov.pl z tagiem OtworzAED
 (lub formularz)       (raport po polsku,          (lub przez formularz: publikujemy
                        co poprawić)                za Ciebie w zbiorze krajowym)
                                ↓
           Twoje AED w zbiorze krajowym → mapy, aplikacje, OSM → dyspozytor 112
```

Komunikat: **„15 minut, jeden plik, każde AED widoczne dla ratowników.”**

## 4. Zachęty, czyli co dysponent dostaje w zamian

| Zachęta | Koszt dla państwa | Siła |
|---------|-------------------|------|
| **Naklejka na szafkę** z ID, datą sprawdzenia i QR „nie działa / zamknięty” (wzór w księdze znaku) | druk | ⭐⭐⭐ widoczna dla każdego, buduje zaufanie |
| **Odznaka „Nasz AED jest na mapie”** na www, w stopce maila i przy wejściu | 0 zł | ⭐⭐ |
| **Przypomnienia o elektrodach i baterii** (e-mail 60 i 14 dni przed terminem, wyliczane z pól wzorca) | automat | ⭐⭐⭐ realna korzyść: dysponent nie musi pilnować terminów sam |
| **Ranking gmin i powiatów** według kompletności i świeżości danych | automat | ⭐⭐⭐ działa ambicja i lokalne media |
| **Mapa i raport dla gminy** do wykorzystania w BIP, na sesji rady czy w raporcie o stanie gminy | automat | ⭐⭐ |
| **Wyróżnienie MC/MZ** „Gmina z otwartym AED” wręczane 16 października (Europejski Dzień Przywracania Czynności Serca) | niski | ⭐⭐ |
| **Certyfikat dla firm** do raportu CSR/ESG | 0 zł | ⭐⭐ |
| **Rekomendacja regulacyjna** dla MZ: obowiązek publikacji danych AED kupionych ze środków publicznych (precedens: ceny mieszkań deweloperów, które w 2025 r. zasiliły portal setkami tysięcy rekordów) | proces legislacyjny | ⭐⭐⭐ długoterminowo najskuteczniejsze |

## 5. Harmonogram akcji (propozycja dla MC)

| Faza | Kiedy | Co |
|------|-------|----|
| **0. Pilot** | 3 miesiące | 1 województwo (np. kujawsko-pomorskie, ukłon w stronę Bydgoszczy) + 3 duzi operatorzy; testujemy szablon i walidator |
| **1. Start ogólnopolski** | Światowy Dzień Pierwszej Pomocy (2. sobota września) | pismo do JST, kampania w social media, webinar dla dysponentów, naklejki |
| **2. Kulminacja** | 16 października (Europejski Dzień Przywracania Czynności Serca) | ogłoszenie rankingu gmin, wyróżnienia |
| **3. Utrzymanie** | stale | przypomnienia o elektrodach, kwartalne „potwierdź swoje AED” (model brytyjskiego The Circuit), raport roczny w sprawozdaniu POD |

## 6. Mierniki (KPI)

- liczba dysponentów z tagiem `OtworzAED` na dane.gov.pl (dziś: **0**; zbiory AED na portalu: **4**);
- liczba AED w zbiorze krajowym (punkt odniesienia: ok. 18,3 tys. w OSM);
- % rekordów z kompletem pól W (dziś w OSM godziny ma tylko 37% punktów, statusu nie ma żaden);
- % rekordów zweryfikowanych w ostatnich 180 dniach;
- % gmin z co najmniej jednym opublikowanym AED;
- liczba zgłoszeń obywatelskich i mediana czasu ich obsługi;
- liczba AED przeniesionych z „zamknięty na klucz” do szafki z alarmem.

## 7. Materiały (do wykonania)

| Materiał | Status |
|----------|--------|
| Logo (4 wersje + warianty kolorystyczne), SVG/PNG/JPG/PDF | ✅ v0.1 |
| Księga znaku PDF | ✅ v0.1 |
| Naklejka A6 na szafkę z QR | ✅ makieta w księdze (`../plan_rozwiazania/branding/logo/otworz-aed_naklejka_A6.svg`) |
| Odznaka dysponenta | ✅ makieta |
| Plakat A3 / roll-up | ⬜ |
| Post i karuzela social media (3 plansze: problem, 3 kroki, efekt) | ⬜ |
| Wzór pisma do JST | ⬜ szkic poniżej |
| Landing akcji (część prototypu: „Dla dysponentów”) | ⬜ |
| 60-sekundowe wideo „AED zamknięty na klucz” (opcja) | ⬜ |

## 8. Teksty robocze

**Post (social media):**
> W Polsce wisi kilkanaście tysięcy defibrylatorów AED. Część z nich jest zamknięta na klucz, a o części nikt nie wie, czy działa.
> Jeśli w Twojej szkole, firmie lub gminie jest AED, **Otwórz AED**: pokaż, gdzie jest, i powiedz, czy działa. Jeden plik, 15 minut, a dyspozytor 112 zobaczy go na mapie.
> #OtworzAED #DaneNaRatunek

**Szkic pisma do JST (fragment):**
> Szanowni Państwo,
> zwracamy się z prośbą o opublikowanie w portalu dane.gov.pl informacji o defibrylatorach AED, którymi dysponuje gmina i jej jednostki, z użyciem wzorcowego zakresu danych „Otwórz AED”. Publikacja zajmuje ok. 15 minut: wystarczy uzupełnić gotowy szablon, sprawdzić go w bezpłatnym walidatorze i opublikować z tagiem OtworzAED. Dane trafią do ogólnopolskiego zbioru, z którego korzystają mapy, aplikacje ratownicze i centra powiadamiania ratunkowego. Szczególnie prosimy o informację o godzinach dostępności oraz o tym, czy urządzenie jest zamknięte, bo w nagłym zatrzymaniu krążenia liczy się każda minuta.

**Naklejka:** „Ten AED jest na mapie · Sprawdzony: [data] · Nie działa? Zamknięty? Zeskanuj kod i zgłoś.”

## 9. Uwaga prawna do akcji

- Znak akcji **nie może udawać** oznakowania urządzenia AED (ILCOR / ISO 7010), dlatego ma inny kształt i nie ma krzyża.
- Logotypy MC, MZ czy dane.gov.pl w materiałach wolno umieścić dopiero za zgodą tych instytucji. W makietach jest tylko tekstowa nazwa portalu.
- Partnerów (OSM Polska, Pierwszy Ratownik, ratujzsercem) wymieniamy jako **potencjalnych**, dopóki nie zgodzą się na współpracę.
