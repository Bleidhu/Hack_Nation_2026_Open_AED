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
  - presety `wzorzec` i `osm`;
  - automatyczną podpowiedź mapowania;
  - normalizacje: przecinek dziesiętny, `TAK`/`NIE` → `true`/`false`, daty `dd.mm.rrrr` → ISO, kody pocztowe, telefony, zamienione współrzędne.

  Uruchomienie:
  ```bash
  python integrator/importer.py plik.csv --mapowanie mapowanie.json --wyjscie wynik.csv --raport raport.json
  python integrator/importer.py plik.csv --podpowiedz     # propozycja mapowania kolumn
  ```
- `openapi.yaml`: szkic API integratora z poprzedniego demonstratora (import, aktualizacje stanu, organizacje, AED obszarowe). Traktuj go jako propozycję, a nie działającą usługę w tym repo.

Przykładowe pliki dostawców wraz z mapowaniami są w `dane_przykladowe/` (bank, sieć sklepów, OSM, gmina, przewoźnik, kolej, serwis, ZRM).

> **Stan: wzorzec v1.** Integrator, próbki, `schemat/` (tabele obszarowe, organizacji, aktualizacji, mapowania), `szablony/`, `narzedzia/` (generatory v1) i opis `FORMAT_V1.md` pochodzą sprzed decyzji o wzorcu v2 (`../docs/06_DECYZJE_STRUKTURA_DANYCH_AED.md`). Importer czyta zamrożoną kopię wzorca v1 z `wzorzec_v1/`. Generatory v1 w `narzedzia/` mają ścieżki starego układu i nie są uruchamiane. Przepięcie na v2 (41 kolumn, bez `id_aed`) należy do kroku 2.

## Zasady

- Dane OSM (ODbL) służą wyłącznie do porównań i nie trafiają do zbioru CC0.
- Licencji źródła nie zakładamy domyślnie: musi ją jawnie wskazać dostawca.
