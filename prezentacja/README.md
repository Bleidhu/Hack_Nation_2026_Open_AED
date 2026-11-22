# Prezentacja

- [`dane_przezycie_prezentacja.pdf`](dane_przezycie_prezentacja.pdf): wersja do czytania (14 slajdów).
- [`dane_przezycie_prezentacja.pptx`](dane_przezycie_prezentacja.pptx): wersja edytowalna (PowerPoint).

| Wymaganie (`references/zadanie_konkursowe.pdf` §4) | Slajdy |
|---|---|
| min. 5 slajdów z dowodami na realizację wymagań technicznych (zrzuty ekranu) | 4–10: zrzuty z portalu uruchomionego lokalnie (podpisy jak w [`../demo/zrzuty/README.md`](../demo/zrzuty/README.md)) |
| opis funkcjonalności, w tym kroków użytkownika | 3 (proces), 4–5 (kroki dostawcy), 6 (portal), 7–9 (kroki odbiorcy), 11 (wzorcowy zakres) |
| lista ograniczeń | 13 |
| akcja promocyjna: nazwa, hasło, logotyp | 1, 12 |
| zakres użycia AI (`regulamin_zadania.pdf` §2 ust. 8) | 14 |

Liczby na slajdach pochodzą z plików w [`../demo/wynik/`](../demo/wynik/) (`testy.txt`, `statystyki_agregacji.json`). Krój w prezentacji to Atkinson Hyperlegible z księgi znaku. PDF ma go osadzonego; w PPTX bez zainstalowanego kroju PowerPoint podstawi inny, więc do czytania służy PDF (krój: branding/fonty/).

## Regeneracja

```bash
npm install pptxgenjs@3.12.0                      # w dowolnym katalogu
NODE_PATH=<ten katalog>/node_modules node prezentacja/build_prezentacja.js
powershell -File prezentacja/eksport_pdf.ps1      # PDF przez PowerPoint (Windows)
```
