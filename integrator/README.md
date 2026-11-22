# Integrator danych AED: KROK 2 (dodatek)

> **To nie jest główny rezultat.** Główny rezultat to modyfikacja portalu w `../portal/` (krok 1). Integrator pomaga tylko tym dostawcom, którzy nie mają danych we wzorcowym formacie z `../format_danych/`.

## Rola w całości

```
dostawca z własnym eksportem (CSV/TSV/XLSX, inne nazwy kolumn, CP1250, OSM)
        │  plik mapowania JSON (raz, potem reużywany)
        ▼
integrator: mapowanie → normalizacja → walidacja (raport z numerami wierszy)
        │  CSV zgodny ze wzorcem, wystawiony pod https
        ▼
portal dane.gov.pl: zasób typu „link” z automatycznym odświeżaniem
        │  zbiór oznaczony jako zgodny ze wzorcem AED
        ▼
nocne zadanie portalu (krok 1) → krajowy zasób zbiorczy AED
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
- `openapi.yaml`: szkic API integratora z poprzedniego demonstratora (import, aktualizacje stanu, organizacje, AED obszarowe). Traktuj go jako propozycję, a nie działającą usługę w tym repo.

Przykładowe pliki dostawców wraz z mapowaniami są w `dane_przykladowe/` (bank, sieć sklepów, OSM, gmina, przewoźnik, kolej, serwis, ZRM). Adaptery Warszawy i Gdańska czytają realne pliki z `../references/dane_gov_pl_aed/` (odpowiedź API Warszawy, baza pojazdów ZTM Gdańska) – oba źródła nie dają dziś tabeli w portalu.

> **Stan: wzorzec v1.** Integrator, próbki, `schemat/` (tabele obszarowe, organizacji, aktualizacji, mapowania), `szablony/`, `narzedzia/` (generatory v1) i opis `FORMAT_V1.md` pochodzą sprzed decyzji o wzorcu v2 (`../docs/06_DECYZJE_STRUKTURA_DANYCH_AED.md`). Importer czyta zamrożoną kopię wzorca v1 z `wzorzec_v1/`. Generatory v1 w `narzedzia/` mają ścieżki starego układu i nie są uruchamiane. Przepięcie na v2 (41 kolumn, bez `id_aed`) należy do kroku 2.

> **Faza 2 (w toku):** plan w `../.scratch/integrator-faza2/`. Pliki v1 są opisane w `ARCHIWUM_V1.md` (nic nie usuwamy). Układ docelowy: `rdzen/` (czyste funkcje), `adaptery/`, `ui/`, `testy/`; `importer.py` zostaje cienką powłoką CLI. Cel: przepięcie na wzorzec v2 (`../format_danych/`).

## Zasady

- Dane OSM (ODbL) służą wyłącznie do porównań i nie trafiają do zbioru CC0.
- Licencji źródła nie zakładamy domyślnie: musi ją jawnie wskazać dostawca.
- Do zasobu zbiorczego trafiają **punkty**, a nie flota: baza pojazdów ZTM w Gdańsku (AED w autobusach i tramwajach) nie ma kolumny we wzorcu v2, więc adapter `gdansk` zwraca tylko statystykę (503 pojazdy, 278 z AED) i jednoznaczny powód, zamiast wierszy punktowych.
