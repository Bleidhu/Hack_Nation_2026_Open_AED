# Wersja live (tymczasowa)

> **Link jest tymczasowy i jest tylko dodatkiem.** Adresy niżej prowadzą przez tunel ngrok do komputera zespołu, na którym działa zmodyfikowany portal w Dockerze. Działają wyłącznie wtedy, gdy tunel jest włączony (uruchamiany na żądanie). **Główna ścieżka oceny działa offline**, bez tego linku: [`INSTRUKCJA_DLA_JURY.md`](INSTRUKCJA_DLA_JURY.md) i prototyp [`demo/index.html`](demo/index.html) otwarty z repozytorium lub z archiwum ZIP. Nic w ocenie nie zależy od wersji live.

<!-- POCZATEK BLOKU ADRESOW (generuje demo/ustaw_link_live.py, nie edytować ręcznie) -->
<!-- adresy: {"aktualizacja": "2026-11-22 10:27 (UTC+0100)", "dostawca": "https://thumb-abrasive-bovine.ngrok-free.dev/dostawca", "portal": "https://thumb-abrasive-bovine.ngrok-free.dev", "prototyp": "https://thumb-abrasive-bovine.ngrok-free.dev/demo/index.html", "zasob": 40258, "zbior": 4216} -->

**Stan:** adresy wpisane; tunel działa tylko wtedy, gdy zespół ma go włączonego.  
**Ostatnia aktualizacja adresów:** 2026-11-22 10:27 (UTC+0100)

| Co | Adres | Co sprawdzić |
|---|---|---|
| Strona startowa wersji live | <https://thumb-abrasive-bovine.ngrok-free.dev/live/> | odnośniki do wszystkich elementów poniżej |
| Portal: zbiór Wykaz AED | <https://thumb-abrasive-bovine.ngrok-free.dev/pl/dataset/4216> | zbiór zbiorczy budowany co noc z zasobów zbiorów oznaczonych `standard = AED` |
| Portal: Wykaz AED, tabela | <https://thumb-abrasive-bovine.ngrok-free.dev/pl/dataset/4216/resource/40258/table> | tabela zasobu zbiorczego (wyszukiwanie, sortowanie, filtry portalu) |
| Portal: Wykaz AED, mapa | <https://thumb-abrasive-bovine.ngrok-free.dev/pl/dataset/4216/resource/40258/map> | mapa portalu włączona przez `geo` w schemacie zasobu (szerokość, długość, etykieta) |
| API: dane Wykazu AED | <https://thumb-abrasive-bovine.ngrok-free.dev/api/resources/40258/data?per_page=20> | JSON:API `/resources/{id}/data`; odnośniki w odpowiedzi prowadzą pod ten sam adres |
| API: `/aed-aggregated` | <https://thumb-abrasive-bovine.ngrok-free.dev/api/aed-aggregated> | numer zbioru i zasobu Wykazu AED (odpowiednik `/dga-aggregated`) |
| API: pobranie CSV Wykazu AED | <https://thumb-abrasive-bovine.ngrok-free.dev/api/resources/40258/file> | plik CSV zasobu zbiorczego, ten sam bajt w bajt co w portalu lokalnie |
| Panel administracyjny | <https://thumb-abrasive-bovine.ngrok-free.dev/admin/> | logowanie do panelu dostawcy i administratora (dane logowania zespół przekazuje osobno) |
| Prototyp (klikalny proces i Wykaz AED) | <https://thumb-abrasive-bovine.ngrok-free.dev/demo/index.html> | ta sama strona co `demo/index.html` z repozytorium |
| Serwer dostawcy: Opis zbioru w XML (poprawny) | <https://thumb-abrasive-bovine.ngrok-free.dev/dostawca/opis.xml> | XML zgodny z `aed_opis_zbioru.xsd`: metadane, link do `aed.csv` na tym samym hoście i suma md5 |
| Serwer dostawcy: Plik CSV z danymi | <https://thumb-abrasive-bovine.ngrok-free.dev/dostawca/aed.csv> | CSV zgodny ze wzorcem (42 kolumny, 7 rekordów fikcyjnych); jego md5 jest równe `<md5>` z opisu |
| Serwer dostawcy: Opis z błędną sumą md5 | <https://thumb-abrasive-bovine.ngrok-free.dev/dostawca/opis_bledny_md5.xml> | zgodny z XSD, ale md5 nie pasuje do CSV: portal odrzuca import |
| Serwer dostawcy: Opis niezgodny z XSD | <https://thumb-abrasive-bovine.ngrok-free.dev/dostawca/opis_bledny_xsd.xml> | portal odrzuca import już na walidacji schematu |
| Serwer dostawcy: Schemat XSD opisu zbioru | <https://thumb-abrasive-bovine.ngrok-free.dev/dostawca/aed_opis_zbioru.xsd> | ten sam plik co `format_danych/schemat/aed_opis_zbioru.xsd` |
| Serwer dostawcy: Stan serwera | <https://thumb-abrasive-bovine.ngrok-free.dev/dostawca/stan> | JSON `{"stan": "ok", ...}`: serwer działa i odpowiada kodem 200 |

<!-- KONIEC BLOKU ADRESOW -->

## Co jest wystawione

Wszystko pod jednym adresem (darmowe konto ngrok ma jedną domenę). Ruch rozdziela brama `demo/brama_live.py` według ścieżki:

- **Portal (frontend)**: strona zbioru Wykazu AED, tabela i mapa zasobu zbiorczego. To ten sam portal, z którego pochodzą zrzuty w `demo/zrzuty/`.
- **API portalu** pod `/api/...`, np. `/api/resources/<id>/data` i `/api/aed-aggregated`. Odnośniki w odpowiedziach JSON prowadzą pod ten sam publiczny adres. Plik CSV wykazu jest identyczny bajt w bajt z plikiem w portalu lokalnym.
- **Panel administracyjny** pod `/admin/`. Danych logowania nie ma w tym pliku, zespół przekazuje je osobno.
- **Prototyp** pod `/demo/index.html`, a pliki wzorca, znaku i prezentacji pod `/format_danych/`, `/branding/` i `/prezentacja/`.
- **Serwer dostawcy** pod `/dostawca/...` (`demo/serwer_zewnetrzny.py`): opis zbioru w XML, CSV, schematy i celowo błędne opisy. Tylko odczyt, dane fikcyjne.

Uwagi:
- Darmowy ngrok przy pierwszym wejściu z przeglądarki pokazuje stronę ostrzegawczą („You are about to visit…”). Wystarczy kliknąć „Visit Site”.
- Treści CMS (np. okno „Polityka prywatności i RODO”) są puste, bo lokalna instancja nie ma stron CMS. Okno zamyka się przyciskiem „Zamknij”. Tak samo zachowuje się portal lokalnie.

## Jak sprawdzić serwer dostawcy

1. Otworzyć „Opis zbioru w XML (poprawny)” z tabeli. Pole `<link_csv>` wskazuje `aed.csv` pod tym samym adresem (`…/dostawca/aed.csv`), a `<md5>` zawiera sumę kontrolną.
2. Pobrać CSV i policzyć md5 (`certutil -hashfile aed.csv MD5` w Windows, `md5sum aed.csv` w Linuksie). Wynik ma być równy `<md5>` z opisu.

## Dla zespołu

Uruchomienie i zatrzymanie: [`demo/NGROK.md`](demo/NGROK.md) (`powershell -File demo/uruchom_live.ps1`). Skrypt wpisuje adresy do tego pliku poleceniem `python demo/ustaw_link_live.py --portal https://….ngrok-free.dev --sprawdz`. Po wyłączeniu tunelu: `python demo/ustaw_link_live.py --wyczysc`.
