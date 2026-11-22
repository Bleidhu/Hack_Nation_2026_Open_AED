# Koncepcja akcji „Dane (prze)życie”: szkice do wyboru

Status: **szkice robocze, zamknięte** (22.11.2026). Znak finalny powstał z wariantu C, ale zmienił kompozycję: migotanie i rytm spotykają się na środku znaku, a folder jest na nie nałożony. Pliki finalne i księga znaku: [`../README.md`](../README.md).

## Nazwa i hasło

- **Nazwa:** *Dane (prze)życie*. Gra słów: „dane przeżycie”, „dane życie” i „dane” jak w dane.gov.pl. „(prze)” jest zapisane lżejszym krojem i innym kolorem, żeby było widać oba odczytania.
- **Hasło (wezwanie dla dysponentów):** *Twoje dane – czyjeś życie.*
- **Hashtag:** `#DanePrzeżycie` / `#DanePrzezycie`. W mowie używamy pełnej frazy, bo nawiasu nie słychać.

## Znak

Chaotyczny sygnał wchodzi do pół-folderu z danymi (wykaz) i wychodzi jako **rytm zatokowy**.

| Wariant | Wejście | Folder | Ocena |
|---|---|---|---|
| A | linia płaska (asystolia) | z wykazem | propozycja wyjściowa. **Merytorycznie błędna**: asystolia to rytm niedefibrylacyjny, AED jej nie leczy, a ratownik lub instruktor KPP w jury to zauważy |
| B | migotanie komór (VF) | pusty | poprawny medycznie, ale słabiej mówi „dane” i „wykaz” |
| **C** | **migotanie komór (VF)** | **z wykazem** | **rekomendacja.** Podwójna metafora: chaos komór zamienia się w miarowy rytm po defibrylacji, a rozproszone dane w jeden standardowy wykaz (słowa organizatora: „scalać w jedną standardową listę”) |

- **Sygnet** (`sygnet.svg`): folder z jednym uderzeniem serca, do faviconu, awatara i naklejki. Czytelny od 16 px. Pełny znak wymaga co najmniej ok. 120 px szerokości (do potwierdzenia w księdze znaku).
- **Kolory:** paleta projektu (zieleń AED `#007A45`, granat `#0E2A47`, czerwień `#C8102E`, żółć `#FFC629`). Na granacie stosujemy jaśniejsze odpowiedniki czerwieni (`#FF7A85`) i zieleni (`#4ADE9A`). Wszystkie pary spełniają WCAG 2.1: grafika ≥ 3:1, tekst ≥ 4,5:1 (wartości w `porownanie.html`).
- **Krój:** Atkinson Hyperlegible (SIL OFL). Tekst zamieniony na krzywe.

## Pliki

| Plik | Co to |
|---|---|
| `porownanie.html`, `porownanie.png` | plansza porównawcza: warianty w 256, 64, 32 i 16 px, logo poziome jasne i negatyw, sygnet, układ pionowy, kontrasty |
| `znak_{A,B,C}.svg` | sam znak |
| `logo_poziome_{A,B,C}.svg`, `…_negatyw.svg` | znak, nazwa i hasło |
| `logo_kwadrat_C.svg`, `…_negatyw.svg`, `naklejka_kwadrat_C.svg` | **układ kwadratowy (1:1) na naklejki**: znak u góry, nazwa w dwóch wierszach, hasło; wariant C |
| `logo_pionowe_C.svg` | układ pionowy wariantu C |
| `sygnet.svg`, `sygnet_negatyw.svg` | wersja do małych rozmiarów |
| `build_koncepcje.py` | generator (geometria i kolory w jednym miejscu) |

## Regeneracja

```bash
uv run --with fonttools python branding/koncepcje_dane_przezycie/build_koncepcje.py
# render planszy (Windows, Edge):
"/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" --headless=new --hide-scrollbars --window-size=1240,2380 \
  --screenshot="$(cygpath -w "$PWD/branding/koncepcje_dane_przezycie")\\porownanie.png" \
  "file:///$(cygpath -m "$PWD")/branding/koncepcje_dane_przezycie/porownanie.html"
```

Analiza alternatywnych nazw kampanii: `../NAZWY_KAMPANII.md`.

## Następne kroki (po wyborze wariantu)

1. Dopracowanie wybranego znaku: kerning nazwy, proporcje folderu i rytmu, wersje achromatyczne.
2. Nowa księga znaku (wymagania zadania):
   - opis koncepcji w 3–5 zdaniach;
   - kolorystyka (HEX, RGB, CMYK);
   - pole ochronne;
   - minimalny rozmiar (ustalony testem);
   - niedozwolone użycia.
3. Eksport: JPG, PNG, PDF i SVG (`render.sh`). Materiały akcji (naklejka „tu jest AED”, odznaka dysponenta) w nowej identyfikacji.
4. Decyzja, czy „Otwórz AED” zostaje jako hasło wezwania na naklejce, czy znika.
