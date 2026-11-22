# Prezentacja

- [`dane_przezycie_prezentacja.pdf`](dane_przezycie_prezentacja.pdf): wersja do czytania (19 slajdów).
- [`dane_przezycie_prezentacja.pptx`](dane_przezycie_prezentacja.pptx): wersja edytowalna (PowerPoint).

| Wymaganie (`references/zadanie_konkursowe.pdf` §4) | Slajdy |
|---|---|
| min. 5 slajdów z dowodami na realizację wymagań technicznych (zrzuty ekranu) | 8–14: zrzuty z portalu uruchomionego lokalnie (podpisy jak w [`../demo/zrzuty/README.md`](../demo/zrzuty/README.md)) |
| opis funkcjonalności, w tym kroków użytkownika | 2–3 (problem i źródła), 4–6 (z potrzeb do pól wzorca), 7 (mechanizm), 8–9 (kroki dostawcy), 10 (scalanie), 11–13 (kroki odbiorcy) |
| lista ograniczeń | 16 |
| akcja promocyjna: nazwa, hasło, logotyp, korzyści dla dysponentów | 1, 17, 18 |
| dodatki: integrator danych i deduplikacja (poza portalem) | 15 |
| zakres użycia AI (`regulamin_zadania.pdf` §2 ust. 8) | 19 |

Liczby na slajdach pochodzą z plików w [`../demo/wynik/`](../demo/wynik/) (`testy.txt`, `statystyki_agregacji.json`) i [`../demo/integrator/`](../demo/integrator/README.md) (slajd 15). Krój w prezentacji to Atkinson Hyperlegible z księgi znaku. PDF ma go osadzonego; w PPTX bez zainstalowanego kroju PowerPoint podstawi inny, więc do czytania służy PDF (krój: branding/fonty/).

## Regeneracja

```bash
npm install pptxgenjs@3.12.0                      # w dowolnym katalogu
NODE_PATH=<ten katalog>/node_modules node prezentacja/build_prezentacja.js
powershell -File prezentacja/eksport_pdf.ps1      # PDF przez PowerPoint (Windows)
```
