# Wystawienie dema przez ngrok (opcjonalnie, ostrożnie)

Wdrożenia są **dodatkiem**. Nic w ocenie od nich nie zależy: wszystkie dowody są plikami w repozytorium, a prototyp działa z dysku. Tunel włączaj tylko na czas oceny i wyłącz zaraz po niej.

## Co wolno wystawiać

| Co | Po co | Uwagi |
|---|---|---|
| `demo/serwer_zewnetrzny.py` (tylko GET, 3 pliki, dane fikcyjne) | „zewnętrzny serwer dostawcy” z adresem https, jakiego wymaga portal | bezpieczne: nie ma zapisu, logowania ani danych osobowych |
| statyczny prototyp (`python -m http.server`) | podgląd `demo/index.html` pod adresem https | tylko pliki statyczne |
| **portal (Django, panel, API)** | nie wystawiamy | konto administratora z hasłem testowym, brak utwardzenia, ryzyko awarii w czasie oceny |

## Zewnętrzny serwer dostawcy przez ngrok

```bash
python demo/serwer_zewnetrzny.py            # http na porcie 8099 (ngrok dostarcza https)
ngrok http 8099                             # w drugim terminalu; skopiuj adres https://….ngrok-free.app
python manage.py import_aed_xml https://….ngrok-free.app/aed.xml --organizacja <ID>   # w portalu
```

Portal przyjmuje tylko linki https, a ngrok daje certyfikat zaufany, więc nie trzeba `--https`.

**Nie sprawdzone na tym komputerze (brak ngroka).** Znane ryzyko: darmowy ngrok może pokazywać przeglądarkom stronę ostrzegawczą zamiast pliku. Portal pobiera plik jak przeglądarka (losowy User-Agent), więc przy stronie ostrzegawczej walidacja linku się nie powiedzie. Wtedy użyj płatnego/własnej domeny albo (bezpieczniej) zostań przy lokalnym `--https` z Dockera (`https://host.docker.internal:8099/aed.xml`), który przetestowaliśmy i z którego pochodzą zrzuty.

## Prototyp przez ngrok

```bash
python -m http.server 8080 --directory .    # katalog główny repo, żeby działały linki względne
ngrok http 8080                              # prototyp: https://….ngrok-free.app/demo/index.html
```

## Statyczna strona (GitHub Pages)

Workflow `.github/workflows/pages.yml` publikuje `demo/`, `format_danych/`, `branding/`, `prezentacja/` i kilka plików `.md`. Nie publikuje portalu. Uruchomienie: Settings → Pages → Source: GitHub Actions, potem Actions → „Prototyp na GitHub Pages” → Run workflow. Wymaga zgody właściciela repozytorium.
