# Demo Wykazu AED

## Weryfikacja agregacji bez bazy: `agreguj.py`

Jedno polecenie uruchamia **tę samą logikę agregacji co portal** (`portal/backend/mcod/resources/aed_aggregation.py`) bez Dockera, bazy i Django:

```bash
uv run --python 3.11 --with "pandas==1.5.3" --with "numpy<2" --with openpyxl python demo/agreguj.py
```

Wejście:
- migawka realnych zasobów AED z dane.gov.pl (`references/dane_gov_pl_aed/`, metadane z API w `metadane_api/`);
- przykład wzorca `format_danych/przyklady/aed_punkty_przyklad.csv`.

Skrypt przechodzi po zasobach każdego zbioru tak jak portal: pomija formaty nietabelaryczne i licencje spoza CC0 1.0 / CC BY 4.0, czyta CSV i XLSX funkcją portalu `read_tabular_bytes`, buduje wiersze funkcją `build_aggregate_rows` i odrzuca zasoby bez kolumn minimum wzorca. Wszystkie zbiory z migawki traktuje tak, jakby miały w „Polach niestandardowych” `standard = AED`.

Wynik (gotowy do przeczytania bez uruchamiania):
- `wynik/raport_agregacji.txt`: przyjęte i pominięte zasoby z powodami, liczby wierszy, zgodność przykładu z referencją;
- `wynik/zestawienie_aed.csv`: zasób zbiorczy (51 kolumn, RFC 4180), który portal opublikowałby jako Wykaz AED.

Co pokazuje wynik:
- **Legionowo** (zasób AED w zbiorze mieszanym „Zdrowie”) jest przyjęte: 24 punkty, nagłówki dopasowane aliasami.
- **Przykład wzorca** daje wiersze identyczne z `format_danych/przyklady/aed_zestawienie_przyklad.csv` (ten sam test wykonuje portal: `test_golden_matches_reference`).
- **Krosno, Przemyśl, Marki** są pominięte, bo nie mają kolumn minimum wzorca (Marki: cały wiersz w jednym polu). **Warszawa** i dodatkowe dystrybucje Przemyśla (XML, GeoJSON, JSON) są pominięte jako formaty nietabelaryczne. Takie zasoby wymagają dostosowania do wzorca u dostawcy albo integratora (krok 2).
- Gdańsk (pole `aed` w bazie pojazdów ZTM) to dane flotowe, a nie punkty, więc nie wchodzi do tej weryfikacji.
