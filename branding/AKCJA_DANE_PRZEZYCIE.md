# Akcja „Dane (prze)życie”

Akcja zachęca dysponentów defibrylatorów AED (gminy, szkoły, firmy, instytucje) do publikowania danych o swoich urządzeniach w portalu dane.gov.pl według wzorcowego zakresu danych. Opublikowane zasoby trafiają co noc do **Wykazu AED**, czyli jednej, standardowej listy defibrylatorów w portalu (opis mechanizmu: [`../ZMIANY_W_PORTALU.md`](../ZMIANY_W_PORTALU.md)).

- Księga znaku: [`ksiega_znaku.pdf`](ksiega_znaku.pdf).
- Logotyp w JPG, PNG, PDF i SVG: [`logo/`](logo/).
- Materiały akcji (naklejka, odznaka, post): [`materialy/`](materialy/).

## 1. Nazwa, hasło, znak

| Element | Treść | Rola |
|---|---|---|
| **Nazwa akcji** | **Dane (prze)życie** | marka akcji |
| **Hasło** | **Twoje dane – czyjeś życie.** | emocja: związek między publikacją danych a ratowaniem życia |
| **Wezwanie** | Weź dane do serca. Opublikuj swoje AED na dane.gov.pl. | listy i posty do dysponentów |
| **Hashtag** | `#DanePrzeżycie` (bez znaków diakrytycznych: `#DanePrzezycie`) | media społecznościowe |
| **Napis na naklejce** | Ten AED jest w Wykazie AED na dane.gov.pl | informacja przy urządzeniu |

**Nazwa.** Nawias pozwala przeczytać ją na dwa sposoby: „dane przeżycie” i „dane życie”. Słowo „dane” to także dane.gov.pl. W mowie używamy pełnej frazy „Dane przeżycie”, bo nawiasu nie słychać, a hasło dopowiada resztę. Porównanie 24 nazw z oceną według kryteriów jury: [`NAZWY_KAMPANII.md`](NAZWY_KAMPANII.md).

**Znak.** Czerwona linia migotania komór (rytmu, który przerywa defibrylator) i zielony, miarowy rytm serca spotykają się na środku znaku. Na miejsce spotkania nałożony jest folder z danymi, więc przejście z chaosu w rytm dzieje się w jego środku. To podwójna metafora: chaos w sercu zamienia się w rytm po defibrylacji, a rozproszone dane zamieniają się w jeden wykaz po publikacji według wzorca. Szkice wariantów, z których wyrósł znak finalny: [`koncepcje_dane_przezycie/`](koncepcje_dane_przezycie/README.md).

**Dlaczego migotanie, a nie linia płaska.** Linia płaska (asystolia) to rytm niedefibrylacyjny, czyli AED go nie leczy. Defibrylator przerywa migotanie komór, dlatego znak zaczyna się od migotania.

## 2. Do kogo mówimy

| Grupa | Dlaczego oni | Co ich przekona | Kanał |
|---|---|---|---|
| **Samorządy (JST)** | kupują najwięcej nowych urządzeń i już publikują dane na dane.gov.pl | gotowy szablon XLSX/CSV; zgodność z ustawą o otwartych danych; mapa AED gminy bez dodatkowej pracy | pismo MC, związki samorządów, webinar |
| **Duzi operatorzy sieciowi** (przewoźnicy, sieci handlowe, uczelnie, ZUS) | jeden plik obejmuje dziesiątki lub setki urządzeń | raport CSR/ESG; odznaka dysponenta; jedno źródło zamiast wielu aplikacji | bezpośredni kontakt, izby gospodarcze |
| **Szkoły, kluby sportowe, OSP** | dużo urządzeń, mało czasu i wiedzy IT | naklejka i odznaka dla rodziców i mieszkańców; publikacja przez organ prowadzący | kuratoria, organy prowadzące |
| **Mieszkańcy i kursanci pierwszej pomocy** | widzą AED na co dzień | naklejka z kodem QR do zgłoszenia „nie działa / zamknięty” | kursy pierwszej pomocy, media lokalne |
| **Twórcy aplikacji i map** | mają użytkowników, brakuje im wiarygodnego źródła | jeden otwarty wykaz z API, licencje CC0 i CC BY 4.0 | dane.gov.pl, spotkania społeczności open data |

## 3. Mechanika: trzy kroki dla dysponenta

```
 1. POBIERZ                    2. OPUBLIKUJ                         3. GOTOWE
 wzorcowy zakres danych   →    zasób w swoim zbiorze na dane.gov.pl →   portal co noc dołącza zasób
 (XLSX lub CSV)                i w „Polach niestandardowych” zbioru     do Wykazu AED: tabela, mapa, API
                               wpis: standard = AED
```

Opis kroków z prawdziwymi zrzutami z portalu: [`../INSTRUKCJA_DLA_JURY.md`](../INSTRUKCJA_DLA_JURY.md) i [`../demo/index.html`](../demo/index.html).

## 4. Zachęty

| Zachęta | Koszt | Uwagi |
|---|---|---|
| **Naklejka A6 na szafkę** z ID z wykazu, datą sprawdzenia i kodem QR do zgłoszenia problemu | druk | wzór: [`materialy/dane-przezycie_naklejka_A6.svg`](materialy/dane-przezycie_naklejka_A6.svg) |
| **Odznaka „Nasze AED są w Wykazie AED”** na www, w stopce e-maila i przy wejściu | 0 zł | wzór: [`materialy/dane-przezycie_odznaka_dysponenta.svg`](materialy/dane-przezycie_odznaka_dysponenta.svg) |
| **Przypomnienia o terminach elektrod i baterii** wyliczane z pól wzorca | automat | propozycja rozwoju, poza zakresem prototypu |
| **Ranking gmin i powiatów** według kompletności i aktualności danych | automat | propozycja rozwoju, poza zakresem prototypu |
| **Wyróżnienie „Gmina z otwartym AED”** wręczane 16 października (Europejski Dzień Przywracania Czynności Serca) | niski | decyzja organizatora akcji |

## 5. Harmonogram (propozycja)

| Faza | Kiedy | Co |
|---|---|---|
| Pilot | 3 miesiące | jedno województwo i kilku dużych operatorów; test szablonu i Wykazu AED |
| Start ogólnopolski | Światowy Dzień Pierwszej Pomocy (druga sobota września) | pismo do JST, posty z hasłem, webinar, naklejki |
| Kulminacja | 16 października | podsumowanie i wyróżnienia |
| Utrzymanie | stale | kwartalne „potwierdź swoje AED”, aktualizacja danych |

## 6. Mierniki

- liczba zbiorów z `standard = AED` i zasobów przyjętych do Wykazu AED;
- liczba AED w Wykazie i liczba dysponentów;
- odsetek rekordów z wypełnionymi godzinami dostępności i statusem;
- odsetek rekordów zweryfikowanych w ostatnich 180 dniach;
- odsetek gmin z co najmniej jednym opublikowanym AED.

## 7. Teksty

**Post:**
> Gdy ktoś obok traci przytomność, liczy się każda minuta, a defibrylatora AED może użyć każdy. Trzeba tylko wiedzieć, gdzie jest najbliższy.
> Jeśli w Twojej szkole, firmie albo gminie jest AED, opublikuj o nim dane na dane.gov.pl. Twoje dane – czyjeś życie.
> #DanePrzeżycie

**Fragment pisma do JST:**
> Szanowni Państwo,
> w ramach akcji „Dane (prze)życie” prosimy o opublikowanie w portalu dane.gov.pl informacji o defibrylatorach AED, którymi dysponuje gmina i jej jednostki, według wzorcowego zakresu danych. Wystarczy uzupełnić gotowy szablon, dodać go jako zasób zbioru i w „Polach niestandardowych” zbioru wpisać `standard` = `AED`. Portal każdej nocy dołącza takie zasoby do ogólnopolskiego Wykazu AED, z którego mogą korzystać mapy, aplikacje i służby ratownicze. Szczególnie prosimy o godziny dostępności i informację, czy urządzenie jest zamknięte, bo w nagłym zatrzymaniu krążenia liczy się każda minuta.

## 8. Uwagi prawne

- Znak akcji nie naśladuje oznakowania urządzenia AED (ILCOR, ISO 7010): nie ma serca z błyskawicą ani krzyża.
- Logotypy MC i dane.gov.pl wolno umieścić w materiałach dopiero za zgodą tych instytucji. W makietach jest tylko tekstowa nazwa portalu.
- Kod QR na makiecie naklejki jest nieprawdziwy i służy tylko do pokazania układu.
- Kolizje nazwy (UPRP, EUIPO, domeny) nie zostały sprawdzone; lista kontrolna jest w [`NAZWY_KAMPANII.md`](NAZWY_KAMPANII.md) §7.
