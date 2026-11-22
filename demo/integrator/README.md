# Przykładowe wyniki integratora

Wszystkie pliki generuje **jedno polecenie** z katalogu głównego repo (offline, na plikach z repozytorium):

```bash
python integrator/generuj_demo.py
```

| Plik | Co pokazuje |
|---|---|
| `warszawa_wzorcowy_v2.csv` | Odpowiedź API `get_scb_lokalizacja_defibrylatorow` m.st. Warszawy (przykład z dokumentacji zbioru 39512) przepisana na 41 kolumn wzorca v2. Jeden wiersz, licencja CC BY 4.0, dysponent jawny. |
| `raport_warszawa.json` | Raport walidacji tego importu: 1 wiersz poprawny, pochodzenie i licencja. |
| `raport_duplikatow.json` | Kandydaci na duplikaty we wzorcowym pliku przykładowym: para w tym samym punkcie o różnych nazwach, oznaczona „mało prawdopodobny” (wiele AED w jednym miejscu to osobne wiersze). Nic nie jest scalane. |
| `raport_porownania_osm.json` | Porównanie wykazu AED z portalu (`demo/wynik/zestawienie_aed.csv`, 32 wiersze) z próbką OSM (Kraków, 6 elementów): `w obu 0 · tylko w wykazie 32 · tylko w OSM 6` – spójne, bo wykaz obejmuje Legionowo i Warszawę. Raport ma oznaczenie ODbL: tylko do użytku lokalnego. |
| `statystyka_gdansk.json` | Baza pojazdów ZTM w Gdańsku (zasób 31843): 503 pojazdy, 278 z AED (156 autobusów, 122 tramwaje). Zero wierszy punktowych z jednoznacznym powodem: dane flotowe, nie punkty. |

Do samodzielnego przejścia całego przepłydu (wgranie pliku, mapowanie, walidacja, duplikaty,
porównanie z OSM, dopisanie rekordu) służy lokalny interfejs: `python integrator/ui/serwer.py`
i otwórz `http://127.0.0.1:8765/` (bez internetu, pliki nie opuszczają komputera).
