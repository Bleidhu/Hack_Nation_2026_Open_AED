# Archiwum wzorca v1

Decyzja o strukturze danych v2 (`../docs/06_DECYZJE_STRUKTURA_DANYCH_AED.md`, 41 kolumn wzorca i 51 kolumn zasobu zbiorczego) zastąpiła wzorzec v1. Pliki v1 **nie są usuwane**: zostają jako ślad poprzedniej koncepcji i jako baza porównań. Nowy kod ich nie używa (poza `importer.py`, dopóki zadanie 02 nie przepnie go na v2).

| Plik / katalog | Co to jest | Dlaczego zostaje |
|---|---|---|
| `FORMAT_V1.md` | Opis wzorca v1 | Dokumentacja poprzedniej koncepcji |
| `wzorzec_v1/schemat_tableschema.json`, `wzorzec_v1/slowniki_wartosci.json` | Zamrożona kopia wzorca v1, z której czyta `importer.py` | Do zadania 02 `importer.py` na nich działa; potem zostają jako archiwum |
| `schemat/` | Tabele obszarowe, organizacji, aktualizacji, mapowania (v1) | Obszarowe AED, organizacje i aktualizacje nie wchodzą do v2; może się przydać przy decyzji o ich przywróceniu |
| `szablony/` | Szablony CSV v1 | Jak wyżej |
| `narzedzia/generuj_v1.py`, `generuj_zrodla.py` | Generatory v1 (ścieżki starego układu, nie uruchamiać) | Pokazują, jak powstały próbki |
| `openapi.yaml` | Szkic API z poprzedniego demonstratora | Propozycja, nie działająca usługa |
| `dane_przykladowe/` | Próbki dostawców i mapowania (v1) | Wejście do testów; mapowania zostaną przepięte w zadaniu 02 |

## Stan `importer.py` (22.11.2026)

Sprawdzone poleceniem `python importer.py <plik> [--mapowanie m.json]`:

- działa: CSV, TSV, GeoJSON (wejście), podpowiedź mapowania (`--podpowiedz`), raport walidacji;
- `00_format_v1/aed_punkty_przyklad.csv`: 8 wierszy, 7 poprawnych, 1 z ostrzeżeniem;
- `02_bank`: 3 wiersze, 2 poprawne, 1 z ostrzeżeniem;
- `03_siec_sklepow`: 4 wiersze, 3 poprawne, 1 odrzucony (brak `numer_budynku`, `dostepny_24_7`);
- `01_integrator_osm` (OSM, GeoJSON): 2 wiersze, **0 poprawnych**: OSM nie ma adresu (miejscowość, kod, numer), a v1 go wymaga. W v2 trzeba to rozstrzygnąć w zadaniu 04;
- nie działa lub nieaktualne: walidacja względem v1 (nie v2), brak blokady licencji ODbL, `id_aed` w v1 (w v2 nadaje go agregacja portalu), brak kolumn pochodzenia z licencją źródła.
- uwaga: składnia `list[str]` i `dict | None` działa tylko w adnotacjach (`from __future__ import annotations`), więc kod uruchomi się też na Pythonie 3.8.
- `importer_v1.py` w `wzorzec_v1/` to kopia starego importera (zmieniona tylko ścieżka bazowa); `importer.py` jest już wersją v2.

## Układ docelowy

```
integrator/
  importer.py     cienka powłoka CLI wywołująca rdzeń (zostaje)
  rdzen/          czyste funkcje: czytanie wejścia, mapowanie, normalizacja, walidacja, zapis
  adaptery/       Warszawa, Gdańsk (zadanie 05)
  ui/             lokalny UI (zadanie 09)
  testy/          python -m unittest
  wzorzec_v1/ …   archiwum (ten plik)
```

Podział funkcji `importer.py` na obszary (wyjściowa lista do przeniesienia bez zmiany zachowania):

- **czytanie wejścia:** `decode`, `read_xlsx`, `unescape_xml`, `read_input`, `geometry_point`;
- **mapowanie:** `SYNONYMS`, `suggest_mapping`, `pick`, `make_id`, `apply_mapping`, presety;
- **normalizacja:** `fold`, `norm_value`, `TRUE`/`FALSE`;
- **walidacja:** `validate_value`, `validate`, `_validate_table` (tabele v1: obszarowe, organizacje);
- **zapis:** `to_csv`, `to_geojson`, `wkt_to_geojson`, `areas_to_geojson`;
- **powłoka:** `run`, `main`.
