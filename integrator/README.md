# Integrator danych AED: KROK 2 (dodatek)

> **To nie jest główny rezultat.** Główny rezultat to modyfikacja portalu w `../portal/` (krok 1). Integrator pomaga tylko tym dostawcom, którzy nie mają danych we wzorcowym formacie z `../format_danych/`.

## Rola w całości

```
dostawca z własnym eksportem (CSV/TSV/XLSX, inne nazwy kolumn, CP1250, OSM)
        │  plik mapowania JSON (raz, potem reużywany)
        ▼
integrator: mapowanie → normalizacja → walidacja (raport z numerami wierszy)
        │  CSV zgodny ze wzorcem (42 kolumny) + opis.xml z sumą md5 (podkomenda `opis`), oba pod https
        ▼
portal dane.gov.pl: import opisu (XSD → CSV → md5) albo zasób typu „link” z automatycznym odświeżaniem
        │  zbiór oznaczony jako zgodny ze wzorcem AED
        ▼
nocne zadanie portalu (krok 1) → scalenie i deduplikacja → Wykaz AED (52 kolumny)
```

## Zawartość

- `importer.py`: silnik oparty wyłącznie na bibliotece standardowej. Obsługuje:
  - formaty wejściowe: CSV/TSV (wykrywa separator i kodowanie UTF-8/CP1250), XLSX (pierwszy arkusz), GeoJSON oraz Overpass JSON;
  - presety `wzorzec`, `osm`, `warszawa` (odpowiedź API `get_scb_lokalizacja_defibrylatorow` zapisana w pliku – bez tokenów i bez połączeń) i `gdansk` (baza pojazdów ZTM: dane flotowe, nie punkty – adapter zwraca statystykę i powód, zero wierszy);
  - automatyczną podpowiedź mapowania;
  - normalizacje: przecinek dziesiętny, `TAK`/`NIE` → `true`/`false`, daty `dd.mm.rrrr` → ISO, kody pocztowe, telefony, zamienione współrzędne;
  - raport kandydatów na duplikaty: `--duplikaty raport.json` (pary w promieniu `--promien` m, domyślnie 25, o podobnej nazwie lub opisie; raport tylko flaguje, niczego nie scala i nie usuwa);
  - porównanie wykazu z OSM: `--porownaj-z-osm plik.json` (w obu / tylko w wykazie / tylko w OSM; raport ma oznaczenie licencyjne ODbL i służy tylko lokalnie).

  Uruchomienie:
  ```bash
  python integrator/importer.py plik.csv --mapowanie mapowanie.json --wyjscie wynik.csv --raport raport.json
  python integrator/importer.py plik.csv --podpowiedz     # propozycja mapowania kolumn
  python integrator/importer.py wykaz.csv --porownaj-z-osm osm.json --raport porownanie.json
  python integrator/importer.py dodaj aed.csv --nazwa_lokalizacji "Apteka" --miejscowosc "Legionowo" \
      --opis_lokalizacji "Przy kasie" --typ_dostepu publiczny --dostepny_24_7 true \
      --szerokosc_geograficzna 52.4011 --dlugosc_geograficzna 20.9284 --prefiks-id LEG
  ```
  Podkomenda `dodaj` (dla małych dostawców bez własnego systemu): flagi odpowiadają kolumnom
  wzorca v2; brakujący `id_zrodlowe` dostaje kolejny wolny numer z prefiksem dostawcy; przed
  zapisem walidacja i kontrola duplikatów (zapis mimo kandydatów dopiero z `--tak`).
- Podkomenda `opis`: opis zbioru w XML z sumą md5 pliku CSV (opis niżej, w sekcji „Opis zbioru XML + CSV + md5”).
- `ui/`: mały lokalny interfejs (zadanie 09). Start jednym poleceniem:
  ```bash
  python integrator/ui/serwer.py          # http://127.0.0.1:8765/
  ```
  Zakładki: Import i mapowanie, Walidacja (pobranie CSV tylko przy celu „portal” i dozwolonej
  licencji), Duplikaty (bez przycisku „scal”), Porównanie z OSM (widoczne oznaczenie ODbL)
  i Dodaj rekord. Strona działa offline (czcionka osadzona w pliku, zero CDN), spełnia
  WCAG 2.1 AA (etykiety pól, `aria-live`, obsługa klawiaturą, kontrast) i jest responsywna.
  Serwer nasłuchuje tylko na 127.0.0.1, używa wyłącznie `rdzen/` i **nie zapisuje nic na dysku** –
  wyniki (CSV po dopisaniu, CSV wynikowy importu) przeglądarka pobiera jako plik.
- **Demo offline:** `python integrator/generuj_demo.py` zapisuje do [`../demo/integrator/`](../demo/integrator/README.md) przykładowe wyniki na realnych plikach z `references/dane_gov_pl_aed/`: CSV v2 z odpowiedzi API Warszawy, raporty walidacji, duplikatów i porównania z OSM oraz statystykę Gdańska.

Przykładowe pliki dostawców wraz z mapowaniami są w `dane_przykladowe/` (bank, sieć sklepów, OSM, gmina, przewoźnik, kolej, serwis, ZRM). Adaptery Warszawy i Gdańska czytają realne pliki z `../references/dane_gov_pl_aed/` (odpowiedź API Warszawy, baza pojazdów ZTM Gdańska) – oba źródła nie dają dziś tabeli w portalu.

> **Archiwum v1.** Pliki z wersji przed wzorcem v2 (`wzorzec_v1/`, próbki v1 z `dane_przykladowe/00_format_v1/`, `schemat/`, `szablony/`, `narzedzia/`, `FORMAT_V1.md`, `ARCHIWUM_V1.md` i szkic `openapi.yaml` z poprzedniego demonstratora) **przeniesiono do [`../archive/integrator/`](../archive/integrator/ARCHIWUM_V1.md)** (nic nie usuwamy; kod i testy nie odwołują się do archiwum, opis w [`../archive/README.md`](../archive/README.md)). Importer działa na wzorcu v2 (`../format_danych/`).

> **Faza 2 (zakończona):** 12 zadań (zadania 01–09, 11 i 12 wykonane; 10, czyli schemat źródła wg wzorca w portalu, świadomie odłożone). Importer jest cienką powłoką CLI nad `rdzen/` (czyste funkcje), `adaptery/` (OSM, Warszawa, Gdańsk), `ui/` i `testy/` (97 testów, bez Dockera; test zgodności opisu z XSD wymaga `lxml` i bez niej jest pomijany).

## Opis zbioru XML + CSV + md5 (wejście do portalu)

Główna droga zaczytania danych zewnętrznych do portalu: dostawca wystawia pod https **dwa pliki**: CSV zgodny ze wzorcem (42 kolumny, `../format_danych/`) i **opis zbioru w XML** zgodny ze schematem [`../format_danych/schemat/aed_opis_zbioru.xsd`](../format_danych/schemat/aed_opis_zbioru.xsd). Opis zawiera metadane zbioru (tytuł, opis, dysponent, licencja, częstotliwość aktualizacji, data), link do CSV i **sumę md5 pliku CSV**. Integrator buduje ten opis z gotowego pliku CSV.

1. Doprowadzić dane do wzorca (jeśli trzeba): `python integrator/importer.py eksport.xlsx --mapowanie mapowanie.json --licencja "CC BY 4.0" --wyjscie aed.csv`.
2. Zbudować opis zbioru:
   ```bash
   python integrator/importer.py opis aed.csv --link-csv https://dostawca.example.pl/aed.csv \
       --tytul "Defibrylatory AED – Gmina Przykład" --opis "Lokalizacje AED w budynkach gminy." \
       --dysponent "Gmina Przykład" --licencja "CC BY 4.0" --czestotliwosc daily \
       [--regon 123456785] [--email aed@example.pl] [--tytul-zasobu "Lokalizacje AED (CSV)"] [--wyjscie katalog/]
   ```
   Wynik: `opis.xml` w katalogu pliku CSV (albo w `--wyjscie`) i komunikat z sumą md5. Przed zapisem podkomenda sprawdza: minimum kolumn wzorca w CSV, kodowanie UTF-8, licencję (tylko `CC0 1.0` i `CC BY 4.0`; ODbL i CC BY-SA są odrzucane), częstotliwość ze słownika schematu, link `https://`, REGON (9 lub 14 cyfr). Liczba rekordów trafia do `<liczba_rekordow>`.
3. Opublikować **oba pliki bez zmian** pod https: `aed.csv` dokładnie pod adresem z `--link-csv` i `opis.xml` obok. Suma md5 jest liczona z bajtów pliku, więc każda zmiana CSV (także końców linii albo kodowania przez serwer) wymaga ponownego uruchomienia `opis`. Inaczej portal odrzuci import.
4. Zgłosić portalowi adres opisu. W portalu (krok 1) robi to komenda `python manage.py import_aed_xml https://dostawca.example.pl/opis.xml --organizacja <ID>` (`--dry-run` tylko sprawdza, `--odswiez` ponawia import wszystkich zbiorów zaczytanych z opisu). Kolejność kontroli w portalu: kod 200 → XSD → pobranie CSV → md5 → kolumny i duplikaty → zbiór (`standard` = `AED`) i zasób CSV. Zmiana md5 przy kolejnym imporcie zastępuje zasób nowym.

Przykład na danych z repozytorium (CSV z 7 rekordami, w tym celowa kopia jednego urządzenia do pokazania deduplikacji):

```bash
python integrator/importer.py opis format_danych/przyklady/opis/aed_dostawcy.csv \
    --link-csv https://dostawca.example.pl/aed.csv --tytul "Defibrylatory AED – Gmina Przykład" \
    --opis "Lokalizacje AED gminy." --dysponent "Gmina Przykład" --licencja "CC BY 4.0" --czestotliwosc daily \
    --wyjscie /tmp/opis
```

Wynik przechodzi walidację schematem `aed_opis_zbioru.xsd` (sprawdzone `lxml`, tak jak w portalu: `mcod/resources/aed_opis.py`), a `<md5>` jest równe `md5sum` pliku CSV. Gotowe przykłady opisów (poprawny, z błędnym md5, niezgodny z XSD) są w `../format_danych/przyklady/opis/`, a serwer dostawcy, który je wystawia, w `../demo/serwer_zewnetrzny.py` (instrukcja tunelu: `../demo/NGROK.md`).

Integrator jest tu **dodatkiem**: dostawca, który ma już CSV zgodny ze wzorcem, może przygotować opis ręcznie według schematu. Integrator oszczędza liczenie md5 i pilnuje słowników.

## Zasady

- Dane OSM (ODbL) służą wyłącznie do porównań i nie trafiają do zbioru CC0.
- Licencji źródła nie zakładamy domyślnie: musi ją jawnie wskazać dostawca.
- Do zasobu zbiorczego trafiają **punkty**, a nie flota: baza pojazdów ZTM w Gdańsku (AED w autobusach i tramwajach) nie ma kolumny we wzorcu v2, więc adapter `gdansk` zwraca tylko statystykę (503 pojazdy, 278 z AED) i jednoznaczny powód, zamiast wierszy punktowych.

## Co dalej, świadomie poza zakresem

- **Deduplikacja: integrator flaguje, portal scala.** Integrator tylko wskazuje kandydatów na duplikaty (`rdzen/duplikaty.py`, raport `--duplikaty`) i niczego nie usuwa. Scalanie odbywa się w portalu przy budowie Wykazu AED (`mcod/resources/aed_dedup.py`: klucz mocny producent + numer seryjny, klucz słaby marka/model i odległość między różnymi zasobami; pary trafiają do statystyk i logu zadania). Integrator nie powiela tej logiki.
