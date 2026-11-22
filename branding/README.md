# Branding akcji „Dane (prze)życie”

| Plik | Co to |
|---|---|
| [`ksiega_znaku.pdf`](ksiega_znaku.pdf) | **księga znaku** (12 stron): koncepcja, budowa znaku, wersje, kolorystyka (HEX, RGB, CMYK, kontrast WCAG), pole ochronne, minimalna wielkość, niedozwolone użycia, typografia, zastosowania, pliki i prawa |
| [`logo/`](logo/) | **logotyp**: wersje pozioma, pozioma z hasłem, pionowa, znak i sygnet w **JPG, PNG (przezroczyste tło), PDF (wektorowy) i SVG** (format otwarty); negatywy w PNG i SVG; wersje jednobarwne w SVG |
| [`materialy/`](materialy/) | naklejka A6 na szafkę AED (SVG, PNG, PDF), odznaka dysponenta, post 1080 × 1080 px |
| [`AKCJA_DANE_PRZEZYCIE.md`](AKCJA_DANE_PRZEZYCIE.md) | nazwa, hasło, odbiorcy, mechanika, zachęty, harmonogram i teksty akcji |
| [`NAZWY_KAMPANII.md`](NAZWY_KAMPANII.md) | analiza 24 nazw według kryteriów jury |
| [`koncepcje_dane_przezycie/`](koncepcje_dane_przezycie/README.md) | szkice wariantów A, B i C, z których wyrósł znak finalny |
| [`archiwum/otworz_aed/`](archiwum/otworz_aed/README.md) | poprzednia, zastąpiona koncepcja „Otwórz AED” |
| `build_branding.py`, `render.sh`, `ksiega_znaku.html` | źródła: generator wszystkich SVG i księgi, eksport do PNG, JPG i PDF |
| [`fonty/`](fonty/) | Atkinson Hyperlegible (SIL OFL 1.1) z licencją |

## Regeneracja

```bash
uv run --with fonttools python branding/build_branding.py   # SVG + ksiega_znaku.html, sprawdza kontrasty WCAG
bash branding/render.sh                                      # PNG, JPG, PDF (Chrome headless, Windows)
```

Geometria znaku i kolory są zdefiniowane w jednym miejscu (`build_branding.py`), więc wszystkie pliki są ze sobą spójne. Tekst w logo jest zamieniony na krzywe.
