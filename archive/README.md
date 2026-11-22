# Archiwum

Rzeczy przestarzałe albo niezgodne z finalnym kształtem zadania. Nic tutaj nie jest potrzebne
do uruchomienia portalu, integratora ani prototypu – kod i testy nie odwołują się do tego folderu.
Opis każdego pliku jest w `integrator/ARCHIWUM_V1.md` (w tym folderze).

## Co tu jest i dlaczego

| Rzecz | Dlaczego w archiwum |
|---|---|
| `integrator/wzorzec_v1/` | Zamrożony importer i schemat **wzorca v1** (44 kolumny z rozszerzeniami, m.in. `id_aed`, `id_pojazdu`). Zastąpiony wzorcem v2 (41 kolumn, `format_danych/`), zatwierdzonym w `docs/06_DECYZJE_STRUKTURA_DANYCH_AED.md`. Importer v1 wymagał adresu, przez co dane OSM w ogóle nie wchodziły. |
| `integrator/FORMAT_V1.md` | Opis formatu v1 ze ścieżkami starego układu (`../deliverable/`). Nieaktualny kontrakt kolumn. |
| `integrator/schemat/`, `integrator/szablony/` | Tabele **obszarowe**, organizacji i aktualizacji z koncepcji v1. Nie wchodzą do wzorca v2, a kolumna pojazdu została świadomie usunięta (`docs/06` §3: AED w pojazdach to dane flotowe, nie punkty). |
| `integrator/narzedzia/` | Generatory v1 z ścieżkami starego układu (`deliverable/narzedzia/...`) – od dawna nieuruchamialne. Pokazują tylko, jak powstały próbki. |
| `integrator/dane_przykladowe/00_format_v1/` | Próbki w formacie v1. Pozostałe próbki dostawców (`01_integrator_osm/` … `10_zgloszenia_obywateli/`) zostały w `integrator/dane_przykladowe/` i działają z importerem v2 (kolumny spoza v2 są ignorowane). |
| `integrator/openapi.yaml` | Szkic API z **poprzedniego demonstratora** (osobna usługa z importem, organizacjami i AED obszarowymi). Opisuje usługę, której nie ma w tym repo, a organizator podkreśla, że oceniana jest zmiana portalu, a nie osobna aplikacja. Zastąpione lokalnym UI (`integrator/ui/`). |
| `scratch/dalsze-kroki-zestawienie-aed.md` | Migawka planu fazy 1 z 22.11.2026, 1:30 – twierdzi m.in., że zadania 12–15 nie są zaczęte i że repo nie jest wypchnięte. Wszystkie te zadania są dawno zakończone, a stan repo jest opisany w `WYDANIA.md`. Została jako historia decyzji. |

## Czego tu nie ma (i celowo)

- `docs/` – dokumenty wiedzy z notkami o nieaktualnych fragmentach (np. odrzucona koncepcja
  „nowa flaga + migracja” w `docs/01`).
- `branding/archiwum/` – stara koncepcja „Otwórz AED” ma już własny podfolder w `branding/`.
- Pliki v1 generatorów formatu danych (`format_danych/narzedzia/`) – to są **generatory v2**, nie archiwum.

Powrót do rzeczy czynnych: [`../README.md`](../README.md), [`../INSTRUKCJA_DLA_JURY.md`](../INSTRUKCJA_DLA_JURY.md).
