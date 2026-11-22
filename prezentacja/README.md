# Prezentacja

- [`dane_przezycie_prezentacja.pdf`](dane_przezycie_prezentacja.pdf): wersja do czytania (28 slajdów).
- [`dane_przezycie_prezentacja.pptx`](dane_przezycie_prezentacja.pptx): wersja edytowalna (PowerPoint).

| Wymaganie (`references/zadanie_konkursowe.pdf` §4) | Slajdy |
|---|---|
| min. 5 slajdów z dowodami na realizację wymagań technicznych (zrzuty ekranu) | 8–9, 11–14, 16–21: zrzuty z portalu uruchomionego lokalnie (podpisy jak w [`../demo/zrzuty/README.md`](../demo/zrzuty/README.md)) |
| opis funkcjonalności, w tym kroków użytkownika | 2–3 (problem i źródła), 4–6 (z potrzeb do pól wzorca), 7 (mechanizm), 8–9 (kroki dostawcy), 10–13 (integracja przez API: opis XML, XSD, CSV, md5), 14 (scalanie), 15–17 (deduplikacja), 18–20 (kroki odbiorcy) |
| lista ograniczeń | 25 |
| akcja promocyjna: nazwa, hasło, logotyp, korzyści dla dysponentów | 1, 26–27 |
| dodatek: integrator danych (poza portalem, krok 2), w tym zrzuty lokalnego interfejsu i terminala | 22–24 |
| zakres użycia AI (`regulamin_zadania.pdf` §2 ust. 8) | 28 |

Liczby na slajdach pochodzą z plików w [`../demo/wynik/`](../demo/wynik/) (`testy.txt`, `weryfikacja.txt`, `raport_agregacji.txt`, `import_opisu.json`) i [`../demo/integrator/`](../demo/integrator/README.md) (slajdy 22–24). Liczby testów i plików są stałymi na początku `build_prezentacja.js` (`TESTY_PASSED`, `TESTY_SKIPPED`, `KONTROLE`, `PLIKI_NOWE`). Slajdy z plikami zrzutów `16`–`19` i `21`–`22` (opis XML, import, zbiór z opisu, wykaz po deduplikacji, API i tabela z numerem seryjnym) oraz `integrator_01`–`04` skrypt dodaje tylko wtedy, gdy pliki są w `demo/zrzuty/`; numery slajdów w tej tabeli liczy przy budowie. Krój w prezentacji to Atkinson Hyperlegible z księgi znaku. PDF ma go osadzonego; w PPTX bez zainstalowanego kroju PowerPoint podstawi inny, więc do czytania służy PDF (krój: branding/fonty/).

## Regeneracja

```bash
npm install pptxgenjs@3.12.0 jszip                # w dowolnym katalogu
NODE_PATH=<ten katalog>/node_modules node prezentacja/build_prezentacja.js   # PPTX i ten README
powershell -File prezentacja/eksport_pdf.ps1      # PDF przez PowerPoint (Windows)
```
