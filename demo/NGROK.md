# Wersja live przez ngrok (dodatek, uruchamiana na żądanie)

Nic w ocenie od niej nie zależy: wszystkie dowody są plikami w repozytorium, a prototyp działa z dysku. Aktualne adresy są w [`../WERSJA_LIVE.md`](../WERSJA_LIVE.md).

## Uruchomienie (PowerShell, portal w Dockerze już działa)

```powershell
ngrok config add-authtoken <TOKEN>                                    # jednorazowo; token zostaje w globalnym configu ngroka
powershell -ExecutionPolicy Bypass -File demo/uruchom_live.ps1        # start: serwer dostawcy, brama, tunel, wpis do WERSJA_LIVE.md
powershell -ExecutionPolicy Bypass -File demo/uruchom_live.ps1 -Zatrzymaj
```

Skrypt uruchamia w tle:
- serwer dostawcy `demo/serwer_zewnetrzny.py --https --port 8098`, jeśli jeszcze nie działa (zbiór z opisu XML w portalu wskazuje `https://host.docker.internal:8098`);
- bramę `demo/brama_live.py` na `127.0.0.1:8090`;
- `ngrok start --all --config "$env:LOCALAPPDATA\ngrok\ngrok.yml" --config demo/ngrok.yml`.

Potem odczytuje adres z API agenta (`http://127.0.0.1:4040/api/tunnels`) i wywołuje `python demo/ustaw_link_live.py --portal <adres> --sprawdz`. Dzienniki trafiają do `%TEMP%\aed_live\`.

## Dlaczego jeden tunel i brama

Darmowe konto ngrok ma jedną domenę (`*.ngrok-free.dev`). Kilka tuneli w jednej sesji dostaje ten sam adres, a ngrok rozkłada między nie ruch losowo (sprawdzone 22.11.2026). Dlatego tunel prowadzi do bramy (biblioteka standardowa Pythona), która rozdziela ruch po ścieżce:

| Ścieżka | Cel |
|---|---|
| `/` i `/pl/...` | frontend portalu (nginx, `Host: mcod.local`) |
| `/api/...` | API portalu (frontend przekazuje je do `api.mcod.local`) |
| `/admin/` oraz `/login/`, `/datasets/`, `/resources/`, … | panel (`Host: admin.mcod.local`) |
| `/demo/`, `/format_danych/`, `/branding/`, `/prezentacja/` | pliki z repozytorium (bez `demo/.cert` i plików ukrytych) |
| `/dostawca/...` | serwer dostawcy |
| `/live/` | strona startowa z odnośnikami |

Kod portalu i konfiguracja Dockera zostają bez zmian. Brama przepisuje adresy `https://(api.|admin.)mcod.local` w odpowiedziach HTML i JSON na adres publiczny. Usuwa też `Domain=mcod.local` z ciasteczek i podstawia lokalny `Referer` (CSRF Django). Blokuje konsolę debugera Werkzeug (`?__debugger__`) i zamienia strony błędów trybu DEBUG na zwykły komunikat. Pliki danych przechodzą bez zmian.

## Gdy zmieni się adres serwera dostawcy

Portal czyta zbiór z opisu XML pod adresem lokalnym (`https://host.docker.internal:8098/opis.xml`), więc tunel tego nie zmienia. Przepięcie zbioru na inny adres: `docker exec mcod-admin python manage.py import_aed_xml <nowy adres>/opis.xml --organizacja <ID>`. Przebudowa wykazu bez czekania na noc: `demo/wymus_harvest.py`.

## Bezpieczeństwo

Panel jest publiczny. Konto testowe portalu ma hasło opisane w `portal/backend/README.md`. Przed udostępnieniem adresu trzeba zmienić hasło albo uruchomić bramę z `-BezAdmina` albo z dodatkowym hasłem `$env:BRAMA_ADMIN_AUTH = "login:haslo"`. Portal działa w trybie deweloperskim (`DEBUG=True`, `runserver`, werkzeug `--debug`), więc tunel należy wyłączać zaraz po ocenie.
