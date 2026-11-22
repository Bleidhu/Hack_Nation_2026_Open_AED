# Wideo: Wykaz AED w portalu dane.gov.pl

Film (1920×1080, 60 kl./s, ok. 1 min 14 s, bez dźwięku) dokumentuje realizację zadania „Misja AED – Dane na ratunek”. Składa się z nagrań działającego portalu. Powstał zestawem `demo-video-kit`: Playwright nagrywa prawdziwą przeglądarkę, a Remotion składa film z kadrowaniem, kursorem, napisami i kartami.

## Co pokazuje film

| Część | Nagranie | Wymaganie z treści zadania |
|---|---|---|
| Otwarcie | karta: Wykaz AED, logotyp akcji „Dane (prze)życie” | §2, §3: integracja danych w jednym zbiorze, akcja promocyjna |
| 1/2 Dostawca | panel portalu: zbiór z `standard = AED` w „Polach niestandardowych”, podpowiedź pod polem, lista zasobów AED z walidacją | §5: zgodność z zasadami portalu (metadana bez migracji, zwykły potok zasobów) |
| 2/2 Odbiorca | front portalu: zasób „Wykaz defibrylatorów AED” (CSV i JSON-LD, tabela, mapa) oraz `GET /1.4/aed-aggregated` | §2: jeden zbiór; §5: formaty odczytywalne maszynowo, API |
| Zamknięcie | co oddajemy: Wykaz AED (0 migracji, 192 testy), wzorcowy zakres XLSX, logotyp i księga znaku, instrukcja dla jury | §4: lista elementów zgłoszenia |

## Uczciwość nagrania

- **Wszystkie ujęcia to nagrania prawdziwych stron**, czyli portalu z naszymi zmianami uruchomionego lokalnie w Dockerze. Nic nie jest makietą ani dorysowanym wynikiem.
- **Montaż jest jawny:**
  - jedno cięcie skraca czekanie na mapę i ma na ekranie napis „Pominięto … s czekania”;
  - cięcie przy zmianie ekranu (przejście do API) jest oznaczone przygaszeniem obrazu.
  Karta końcowa mówi o tym wprost.
- Nagranie było spowolnione 5× i przeliczone z powrotem do czasu rzeczywistego. Czekanie na serwer nagrywano w czasie rzeczywistym.
- Kursor jest dorysowany ze zapisu ruchów myszy, a kliknięcia i pisanie były prawdziwe.
- Nagranie niczego nie zapisuje w portalu. Formularz zbioru jest tylko przewijany, a wyszukiwanie zasobów to zapytanie GET.
- Widoczne dane konta: lokalne konto administratora środowiska testowego (`admin@mcod.local`, „test admin”). Prywatnych danych nie ma.
- Kafelki mapy w scenie 2 pobiera przeglądarka z serwera OpenStreetMap, tak jak u każdego użytkownika portalu.

## Przycięcie z 22.11.2026: bez przejścia przez prototyp

Z filmu usunięto kartę 03 i scenę `Prototyp` (przejście przez `demo/index.html`, klatki 3942–6025 starego filmu, 34,7 s). Film przechodzi od odpowiedzi `/aed-aggregated` wprost do zamknięcia. `src/Demo.tsx` nie zawiera już tych części, a `src/copy.ts` ma znaczniki `1/2` i `2/2`, dwa chipy w otwarciu i notę końcową bez prototypu. Pliki sceny `Prototyp` zostały w repozytorium.

Nagrań z `public/captures/` nie ma w repozytorium, więc przycięty film złożono w Remotion z poprzedniego pliku MP4: otwarcie i zamknięcie wyrenderowano na nowo z `src/copy.ts`, klatki 384–3941 (karta 01, Dostawca, karta 02, Odbiorca) wzięto bez zmian, a na znaczniki `1/3` i `2/3` nałożono `1/2` i `2/2` w tym samym miejscu i z tym samym wejściem. Pełne odtworzenie poniżej daje ten sam układ filmu.

## Jak odtworzyć

Wymagania: Node.js 20+, Microsoft Edge (Windows) lub Chromium, portal uruchomiony według `portal/backend/README.md` z danymi z `demo/scenariusz/przygotuj_dane.py` (zbiór 4211, zbiór zbiorczy 4216, zasób 40247; inne identyfikatory ustawisz zmiennymi `AED_SOURCE_DATASET`, `AED_MAIN_DATASET` i `AED_MAIN_RESOURCE`).

```bash
cd video
npm install
node tools/doctor.mjs                                  # musi skończyć się „Ready.”
DEMO_CAPTURE_DEBUG=out/debug node capture/scenes.mjs   # nagrania → public/captures/
node tools/events.mjs                                  # znaczniki i zrzuty przy znacznikach
npx tsc --noEmit
node tools/stills.mjs --every 2                        # klatki kontrolne → out/stills/
node tools/render.mjs --concurrency 4                  # → out/demo.mp4
node tools/qa.mjs                                      # kontrola pliku → out/qa/
```

Rekonesans przed nagraniem (zrzuty ekranów bez nagrywania): `node capture/zwiad.mjs`.

## Pliki

| Ścieżka | Co to jest |
|---|---|
| `capture/scenes.mjs` | sceny `dostawca` i `odbiorca` w filmie oraz `prototyp` poza filmem (Playwright, znaczniki dla kamery i napisów) |
| `capture/portal.mjs` | adresy portalu lokalnego, identyfikatory, logowanie, wybór Edge |
| `capture/lib.mjs` | nagrywarka z kitu (screencast CDP w 2×, zwolnione tempo, dziennik zdarzeń) |
| `src/copy.ts` | wszystkie napisy filmu (scenariusz) |
| `src/scenes/*.tsx` | sceny: cięcia, kamera, napisy i obwódki wyliczone ze znaczników |
| `src/theme.ts`, `src/chrome.tsx` | wygląd w barwach akcji „Dane (prze)życie” (granat `#0E2A47`, zieleń `#007A45`, Atkinson Hyperlegible) |
| `public/fonts/`, `public/marka/` | krój Atkinson Hyperlegible (SIL OFL) i logotyp z `branding/logo/` |
| `tools/` | narzędzia kitu: doctor, events, stills, render, qa |

## Zmiany względem szablonu kitu

Na tej maszynie nie ma systemowego FFmpeg, więc narzędzia używają ffmpeg i ffprobe dołączonych do Remotion (`tools/ff.mjs`). Tej kompilacji brakuje kilku filtrów, dlatego:
- nagrywarka ustawia stałą liczbę klatek opcją `-r` zamiast filtra `fps`;
- arkusze kontrolne składa Chromium, a nie filtr `tile`;
- `qa.mjs` wykrywa puste klatki, cięcia i bezruch na pomniejszonych klatkach w skali szarości, liczonych w Node (zamiast `blackdetect`, `freezedetect` i `select`).

Pełny FFmpeg wskażesz zmiennymi `FFMPEG` i `FFPROBE`.

Inne zmiany:
- `launch()` przyjmuje dodatkowe argumenty przeglądarki i `ignoreHTTPSErrors`;
- `chromePath()` na Windows znajduje systemowy Edge lub Chrome;
- nagrywarka odrzuca klatki screencastu o złym rozmiarze, bo Edge czasem oddaje klatkę w skali 1×. Liczbę odrzuconych klatek wypisuje w logu.

Remotion jest bezpłatny dla osób prywatnych i organizacji do trzech osób; większe firmy potrzebują licencji firmowej.
