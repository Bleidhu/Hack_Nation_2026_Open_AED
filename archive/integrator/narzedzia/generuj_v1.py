#!/usr/bin/env python3
"""
Generuje pliki formatu danych z jednego źródła prawdy (integrator/importer.py + format_danych/zrodla_wzorca):
schematy, słowniki, szablony CSV, wzorcowy_zakres_danych.xlsx i próbki danych.

    python format_danych/narzedzia/generuj.py

Tylko biblioteka standardowa Pythona.
"""
from __future__ import annotations

import csv
import io
import json
import shutil
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

D = Path(__file__).resolve().parents[1]
ROOT = D.parent
sys.path.insert(0, str(ROOT / "integrator"))
import importer as imp  # noqa: E402

PLAN = D / "zrodla_wzorca"
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FIKCJA = "PRZYKŁAD – dane fikcyjne"


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, "utf-8", newline="")


def write_json(path: Path, obj):
    write(path, json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def write_csv(path: Path, header: list[str], rows: list[list], delim=",", encoding="utf-8"):
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=delim, lineterminator="\r\n")
    w.writerow(header)
    w.writerows(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(buf.getvalue().encode(encoding))


# ------------------------------------------------------------------ słowniki
def slowniki() -> dict:
    s = json.loads((PLAN / "slowniki_wartosci.json").read_text("utf-8"))
    s.update({
        "typ_obszaru": {"opis": "Rodzaj AED obszarowego/mobilnego", "wartosci": [
            {"wartosc": "flota_pojazdow", "opis": "AED w pojazdach (tramwaje, autobusy, taksówki) – zasięg tras"},
            {"wartosc": "patrol_mobilny", "opis": "Patrol z AED (WOPR, straż miejska, ochrona) – obszar patrolowania"},
            {"wartosc": "wydarzenie", "opis": "Wydarzenie masowe – AED na czas wydarzenia (aktywny_od/do)"},
            {"wartosc": "teren_obiektu", "opis": "Duży teren (kampus, park, stok, plaża) z kilkoma AED / punktem informacji"},
            {"wartosc": "trasa", "opis": "Trasa (szlak, pociąg, prom) – geometria liniowa + bufor"},
            {"wartosc": "inne", "opis": "Inny rodzaj zasięgu"}]},
        "status_programu": {"opis": "Status programu AED obszarowego", "wartosci": [
            {"wartosc": "aktywny"}, {"wartosc": "w_realizacji"}, {"wartosc": "planowany"}, {"wartosc": "zakonczony"}]},
        "typ_organizacji": {"opis": "Rodzaj organizacji w tabeli organizacji", "wartosci": [{"wartosc": v} for v in imp.ORG_ENUMS["typ_organizacji"]]},
        "typ_zdarzenia": {"opis": "Aktualizacja stanu AED (tabela aktualizacji)", "wartosci": [
            {"wartosc": "uzycie", "opis": "AED użyty – niedostępny do potwierdzenia sprawności"},
            {"wartosc": "wymaga_serwisu", "opis": "Usterka (np. niski poziom baterii, brak elektrod)"},
            {"wartosc": "w_serwisie", "opis": "Urządzenie zabrane do serwisu – niedostępne"},
            {"wartosc": "po_serwisie", "opis": "Serwis zakończony – sprawny (tylko dysponent / firma serwisująca)"},
            {"wartosc": "sprawny", "opis": "Potwierdzenie sprawności bez serwisu (tylko dysponent / serwis)"}]},
        "rola": {"opis": "Rola zgłaszającego aktualizację", "wartosci": [
            {"wartosc": "obywatel", "opis": "Osoba postronna – rola deklarowana"},
            {"wartosc": "dysponent", "opis": "Właściciel / opiekun AED"},
            {"wartosc": "serwis", "opis": "Firma serwisująca AED"},
            {"wartosc": "zrm", "opis": "Zespół Ratownictwa Medycznego"},
            {"wartosc": "dyspozytor", "opis": "Dyspozytor 112 / dyspozytor medyczny"},
            {"wartosc": "sluzby", "opis": "PSP, OSP, Policja, Straż Miejska, WOPR, GOPR/TOPR"}]},
        "problemy": {"opis": "Rodzaje usterek (lista oddzielona |)", "wartosci": [
            {"wartosc": "niski_poziom_baterii"}, {"wartosc": "kontrolka_bledu"}, {"wartosc": "brak_lub_przeterminowane_elektrody"},
            {"wartosc": "brak_urzadzenia"}, {"wartosc": "uszkodzona_szafka_lub_alarm"}, {"wartosc": "brak_dostepu_zamkniete"},
            {"wartosc": "uszkodzone_urzadzenie"}, {"wartosc": "inne"}]},
    })
    return s


def simple_schema(name: str, title: str, spec, enums) -> dict:
    fields = []
    for n, t, req, desc, ex in spec:
        f = {"name": n, "type": t, "description": desc, "x-wymagalnosc": req}
        c = {}
        if req == "W":
            c["required"] = True
        if n in enums:
            c["enum"] = enums[n]
        if c:
            f["constraints"] = c
        if ex:
            f["example"] = ex
        fields.append(f)
    return {"name": name, "title": title, "version": "1.0.0", "fields": fields, "missingValues": [""]}


AKTUALIZACJE_SPEC = [
    ("aed_ref", "string", "Z", "Identyfikator AED z API (aed_ref) – podaj to pole albo id_aed", "PL-AED-0000001"),
    ("id_aed", "string", "Z", "Identyfikator ze zbioru krajowego (PL-AED-NNNNNNN)", "PL-AED-0000001"),
    ("typ_zdarzenia", "string", "W", "Słownik typ_zdarzenia", "po_serwisie"),
    ("data_zdarzenia", "datetime", "Z", "Czas zdarzenia ISO 8601 (dla użycia)", "2026-11-21T14:05:00"),
    ("rola", "string", "Z", "Słownik rola (z kluczem organizacji rola jest potwierdzana)", "serwis"),
    ("problemy", "string", "O", "Lista oddzielona | ze słownika problemy", "niski_poziom_baterii"),
    ("opis", "string", "O", "Opis – bez danych osobowych", "Wymiana elektrod i baterii"),
    ("data_przegladu", "date", "O", "Data przeglądu serwisowego", "2026-11-21"),
    ("data_waznosci_elektrod", "date", "O", "Nowa data ważności elektrod", "2028-11-30"),
    ("data_waznosci_baterii", "date", "O", "Nowa data ważności baterii", "2030-11-30"),
    ("numer_protokolu", "string", "O", "Numer protokołu serwisowego", "SRV/2026/1188"),
    ("numer_zdarzenia", "string", "O", "Numer zdarzenia CPR/SWD PRM (bez danych pacjenta)", "CPR-2026-112-000123"),
    ("przewidywany_powrot", "date", "O", "Dla w_serwisie: kiedy AED wróci", "2026-11-28"),
]


# ------------------------------------------------------------------ XLSX (stdlib)
def col_letter(i: int) -> str:
    s = ""
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


def sheet_xml(rows: list[list]) -> str:
    out = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
           '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">',
           '<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>',
           "<sheetData>"]
    for ri, row in enumerate(rows, 1):
        cells = []
        for ci, v in enumerate(row):
            ref = f"{col_letter(ci)}{ri}"
            style = ' s="1"' if ri == 1 else ""
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                cells.append(f'<c r="{ref}"{style}><v>{v}</v></c>')
            else:
                cells.append(f'<c r="{ref}" t="inlineStr"{style}><is><t xml:space="preserve">{escape(str(v))}</t></is></c>')
        out.append(f'<row r="{ri}">{"".join(cells)}</row>')
    out.append("</sheetData></worksheet>")
    return "".join(out)


def write_xlsx(path: Path, sheets: list[tuple[str, list[list]]]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml",
                   '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                   '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                   '<Default Extension="xml" ContentType="application/xml"/>'
                   '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
                   '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
                   + "".join(f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                             for i in range(1, len(sheets) + 1)) + "</Types>")
        z.writestr("_rels/.rels", '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        z.writestr("xl/workbook.xml", '<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                   'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'
                   + "".join(f'<sheet name="{escape(n)}" sheetId="{i}" r:id="rId{i}"/>' for i, (n, _) in enumerate(sheets, 1)) + "</sheets></workbook>")
        z.writestr("xl/_rels/workbook.xml.rels", '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   + "".join(f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>'
                             for i in range(1, len(sheets) + 1))
                   + f'<Relationship Id="rId{len(sheets) + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>')
        z.writestr("xl/styles.xml", '<?xml version="1.0" encoding="UTF-8"?><styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                   '<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="11"/><name val="Calibri"/></font></fonts>'
                   '<fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill></fills>'
                   '<borders count="1"><border/></borders><cellStyleXfs count="1"><xf/></cellStyleXfs>'
                   '<cellXfs count="2"><xf/><xf fontId="1" applyFont="1"/></cellXfs></styleSheet>')
        for i, (_, rows) in enumerate(sheets, 1):
            z.writestr(f"xl/worksheets/sheet{i}.xml", sheet_xml(rows))


# ------------------------------------------------------------------ próbki
# folder docelowy każdej próbki w format_danych/dane_przykladowe/
FOLDER_PROBKI = {
    "aed_punkty_przyklad.csv": "00_format_docelowy", "aed_punkty_przyklad.geojson": "00_format_docelowy",
    "organizacje_przyklad.csv": "00_format_docelowy",
    "aed_obszarowe_przyklad.csv": "00_format_docelowy", "aed_obszarowe_przyklad.geojson": "00_format_docelowy",
    "osm_przyklad.geojson": "01_integrator_osm",
    "firma_bank_placowki_wlasny_format.csv": "02_bank", "mapowanie_bank_przyklad.json": "02_bank",
    "duzy_dostawca_siec_sklepow_eksport.tsv": "03_siec_sklepow", "mapowanie_siec_sklepow.json": "03_siec_sklepow",
    "aktualizacje_serwis_przyklad.csv": "06_serwis",
    "aktualizacje_zrm_112_przyklad.csv": "07_zrm_dyspozytor",
}


def probki(out: Path):
    # każdy plik ląduje w folderze swojego typu źródła (format_danych/dane_przykladowe/<typ>/)
    o = lambda name: out / FOLDER_PROBKI[name] / name
    # 1) punkty w naszym formacie (z plan_rozwiazania) + kolumny rozszerzeń
    res = imp.run((PLAN / "aed_wzorzec_przyklad.csv").read_bytes(), "x.csv", None, preset="wzorzec")
    write(o("aed_punkty_przyklad.csv"), imp.to_csv(res["rekordy"]))
    write_json(o("aed_punkty_przyklad.geojson"), imp.to_geojson(res["rekordy"]))

    # 2) organizacje (logo + strona www) – fikcyjne
    orgs = [
        ["bank-przyklad", "Bank Przykład S.A.", "firma", "000000000", "0000000000", "https://bank-przyklad.example",
         "https://bank-przyklad.example/logo.svg", "Logo Banku Przykład", "aed@bank-przyklad.example", "225550000", "3", "CC0-1.0", FIKCJA],
        ["siec-sklepow-przyklad", "Sieć Sklepów Przykład Sp. z o.o.", "firma", "", "", "https://sklepy-przyklad.example",
         "https://sklepy-przyklad.example/logo.png", "Logo Sieci Sklepów Przykład", "bhp@sklepy-przyklad.example", "", "4", "CC0-1.0", FIKCJA],
        ["mzk-przyklad", "Miejski Zakład Komunikacji Przykład", "przewoznik", "", "", "https://mzk-przyklad.example",
         "", "", "aed@mzk-przyklad.example", "523000000", "69", "CC0-1.0", FIKCJA],
        ["aedtech-serwis", "AED-Tech Serwis Sp. z o.o.", "firma", "", "", "https://aedtech.example", "", "",
         "serwis@aedtech.example", "", "", "CC0-1.0", FIKCJA + " – firma serwisująca"],
    ]
    write_csv(o("organizacje_przyklad.csv"), [f[0] for f in imp.ORG_FIELDS], orgs)

    # 3) firma – placówki we WŁASNYM formacie (średnik, polskie nagłówki) + mapowanie
    bank = [
        ["BP-001", "Oddział Bydgoszcz Centrum", "ul. Gdańska 10", "85-005", "Bydgoszcz", "53,1290", "18,0080", "TAK", "pn-pt 9-17", "hol, przy bankomatach", "TAK"],
        ["BP-002", "Oddział Bydgoszcz Fordon", "ul. Akademicka 5", "85-796", "Bydgoszcz", "53,1520", "18,1660", "NIE", "Mo-Fr 09:00-17:00", "obok wejścia, szafka z alarmem", "TAK"],
        ["BP-003", "Placówka Toruń Rynek", "Rynek Staromiejski 1", "87-100", "Toruń", "18,6040", "53,0100", "NIE", "Mo-Sa 10:00-18:00", "za ladą obsługi – poproś pracownika", "NIE"],
    ]
    write_csv(o("firma_bank_placowki_wlasny_format.csv"),
              ["Kod placówki", "Nazwa placówki", "Adres", "Kod", "Miasto", "Lat", "Lng", "Całodobowo", "Godziny otwarcia", "Gdzie AED", "Dostęp dla klientów"],
              bank, delim=";")
    write_json(o("mapowanie_bank_przyklad.json"), {
        "wersja": "1.0",
        "opis": "Mapowanie pliku placówek Banku Przykład na wzorzec AED (" + FIKCJA + ")",
        "kolumny": {
            "id_zrodlowe": {"z": "Kod placówki"},
            "nazwa_lokalizacji": {"z": "Nazwa placówki"},
            "cecha_ulicy": {"z": "Adres", "regex": "^(ul\\.|al\\.|pl\\.)", "mapa": {"*": "ul."}},
            "nazwa_ulicy": {"z": "Adres", "regex": "^(?:ul\\.|al\\.|pl\\.)?\\s*(.+?)\\s+\\d"},
            "numer_budynku": {"z": "Adres", "regex": "(\\d+[A-Za-z]?)\\s*$"},
            "kod_pocztowy": {"z": "Kod"},
            "miejscowosc": {"z": "Miasto"},
            "szerokosc_geograficzna": {"z": "Lat"},
            "dlugosc_geograficzna": {"z": "Lng"},
            "dostepny_24_7": {"z": "Całodobowo"},
            "godziny_dostepnosci": {"z": "Godziny otwarcia"},
            "opis_lokalizacji": {"z": "Gdzie AED"},
            "typ_dostepu": {"z": "Dostęp dla klientów", "mapa": {"TAK": "ograniczony", "NIE": "prywatny"}},
            "wewnatrz_budynku": {"stala": "true"},
            "zabezpieczenie": {"stala": "szafka_z_alarmem"},
            "status_urzadzenia": {"stala": "sprawny"},
            "dysponent_nazwa": {"stala": "Bank Przykład S.A."},
            "zrodlo_danych": {"stala": "dysponent"},
            "poziom_weryfikacji": {"stala": "zweryfikowany_przez_dysponenta"},
            "data_weryfikacji": {"stala": "2026-11-20"},
            "uwagi": {"stala": FIKCJA},
        },
        "organizacja_id": "bank-przyklad",
    })

    # 4) duży dostawca – eksport z systemu (CP1250, tabulator, inne nazwy)
    siec = [
        ["S-0101", "Market Przykład Bydgoszcz Wyżyny", "Bydgoszcz", "85-791", "Ogrody", "12", "53.12345", "18.04567", "kasa nr 1, ściana", "tak", "24/7", "2027-05-31", "2029-01-31", "2026-10-01"],
        ["S-0102", "Market Przykład Bydgoszcz Błonie", "Bydgoszcz", "85-822", "Szubińska", "60", "53.11890", "17.94120", "wejście główne", "tak", "Mo-Su 06:00-23:00", "2027-02-28", "2028-12-31", "2026-09-12"],
        ["S-0103", "Market Przykład Solec Kujawski", "Solec Kujawski", "86-050", "Toruńska", "3", "53.08710", "18.22650", "zaplecze – zapytaj obsługę", "nie", "Mo-Sa 07:00-21:00", "", "", ""],
        ["S-0104", "Market Przykład Nakło", "Nakło nad Notecią", "89-100", "Pocztowa", "", "53.14200", "17.60000", "przy wyjściu", "tak", "", "2026-01-31", "", ""],
    ]
    write_csv(o("duzy_dostawca_siec_sklepow_eksport.tsv"),
              ["NR_SKLEPU", "NAZWA", "MIASTO", "KOD_PNA", "ULICA", "NR", "GPS_N", "GPS_E", "MIEJSCE_AED", "DLA_KLIENTOW", "GODZINY", "ELEKTRODY_DO", "BATERIA_DO", "PRZEGLAD"],
              siec, delim="\t", encoding="cp1250")
    write_json(o("mapowanie_siec_sklepow.json"), {
        "wersja": "1.0", "opis": "Eksport z systemu sieci sklepów (TSV, CP1250) → wzorzec. " + FIKCJA,
        "kolumny": {
            "id_zrodlowe": {"z": "NR_SKLEPU"}, "nazwa_lokalizacji": {"z": "NAZWA"}, "miejscowosc": {"z": "MIASTO"},
            "kod_pocztowy": {"z": "KOD_PNA"}, "cecha_ulicy": {"stala": "ul."}, "nazwa_ulicy": {"z": "ULICA"}, "numer_budynku": {"z": "NR"},
            "szerokosc_geograficzna": {"z": "GPS_N"}, "dlugosc_geograficzna": {"z": "GPS_E"}, "opis_lokalizacji": {"z": "MIEJSCE_AED"},
            "typ_dostepu": {"z": "DLA_KLIENTOW", "mapa": {"tak": "ograniczony", "nie": "prywatny"}},
            "godziny_dostepnosci": {"z": "GODZINY"}, "dostepny_24_7": {"z": "GODZINY", "mapa": {"24/7": "true", "*": "false"}},
            "data_waznosci_elektrod": {"z": "ELEKTRODY_DO"}, "data_waznosci_baterii": {"z": "BATERIA_DO"},
            "data_ostatniego_przegladu": {"z": "PRZEGLAD"},
            "zabezpieczenie": {"stala": "szafka_otwarta"}, "status_urzadzenia": {"stala": "sprawny"}, "wewnatrz_budynku": {"stala": "true"},
            "dysponent_nazwa": {"stala": "Sieć Sklepów Przykład Sp. z o.o."}, "zrodlo_danych": {"stala": "dysponent"},
            "poziom_weryfikacji": {"stala": "zweryfikowany_przez_dysponenta"}, "data_weryfikacji": {"stala": "2026-11-19"},
            "uwagi": {"stala": FIKCJA},
        },
        "organizacja_id": "siec-sklepow-przyklad",
    })

    # 5) OSM – fragment w formacie OpenAEDMap/GeoJSON (fikcyjne punkty z tagami OSM)
    osm = {"type": "FeatureCollection", "features": [
        {"type": "Feature", "geometry": {"type": "Point", "coordinates": [18.0001, 53.1235]},
         "properties": {"@osm_id": 1, "@osm_type": "node", "emergency": "defibrillator", "access": "yes", "indoor": "no",
                        "opening_hours": "24/7", "defibrillator:location": "elewacja przy drzwiach", "operator": "Gmina Przykładowa",
                        "check_date": "2026-10-01", "note": FIKCJA}},
        {"type": "Feature", "geometry": {"type": "Point", "coordinates": [18.0102, 53.1301]},
         "properties": {"@osm_id": 2, "@osm_type": "node", "emergency": "defibrillator", "access": "customers", "indoor": "yes", "level": "0",
                        "defibrillator:location:pl": "recepcja hotelu", "operator": "Hotel Przykład", "note": FIKCJA}},
    ]}
    write_json(o("osm_przyklad.geojson"), osm)

    # 6) AED obszarowe
    areas = [
        ["PL-AEDO-00001", "Tramwaje MZK Przykład – cała sieć", "flota_pojazdow", "mzk-przyklad", "Miejski Zakład Komunikacji Przykład", "",
         "69", "120", "POLYGON((17.93 53.10, 18.12 53.10, 18.12 53.17, 17.93 53.17, 17.93 53.10))", "300", "https://mzk-przyklad.example/gtfs.zip",
         "https://mzk-przyklad.example/VehiclePositions.pb", "tramwaj", "1|2|3|4|5|6|7|8|9|10", "Mo-Su 05:00-23:30",
         "Zatrzymaj tramwaj lub podejdź do kabiny motorniczego – AED przy kabinie, motorniczy wezwie 112", "w_realizacji", "2026-12-01", "",
         "523000000", "https://mzk-przyklad.example/aed", "dysponent", "2026-11-21T10:00:00", FIKCJA],
        ["PL-AEDO-00002", "Patrol WOPR – plaża Przykładowo", "patrol_mobilny", "", "WOPR Przykład", "", "2", "", "LINESTRING(18.50 54.80, 18.56 54.79, 18.62 54.78)",
         "200", "", "", "patrol_pieszy|lodz", "", "Mo-Su 09:00-19:00", "Wieże ratownicze 1 i 2 – AED u ratownika; dzwoń 601 100 100 lub 112",
         "aktywny", "2026-06-20", "2026-08-31", "601100100", "", "dysponent", "2026-11-21T10:00:00", FIKCJA + " – sezonowy"],
        ["PL-AEDO-00003", "Bieg Przykładowy 2026 – trasa i strefa startu", "wydarzenie", "", "Fundacja Bieg Przykład", "", "6", "",
         "POLYGON((18.00 53.12, 18.02 53.12, 18.02 53.13, 18.00 53.13, 18.00 53.12))", "", "", "", "rower|patrol_pieszy", "",
         "", "Rowerowi ratownicy z AED co 2 km trasy; namiot medyczny przy starcie", "planowany", "2026-05-10", "2026-05-10", "", "",
         "dysponent", "2026-11-21T10:00:00", FIKCJA],
    ]
    area_cols = [f[0] for f in imp.AREA_FIELDS]
    write_csv(o("aed_obszarowe_przyklad.csv"), area_cols, areas)
    write_json(o("aed_obszarowe_przyklad.geojson"), imp.areas_to_geojson([dict(zip(area_cols, r)) for r in areas]))

    # 7) aktualizacje: firma serwisująca + ZRM/112 + dysponent
    upd_cols = [c[0] for c in AKTUALIZACJE_SPEC]
    write_csv(o("aktualizacje_serwis_przyklad.csv"), upd_cols, [
        ["", "PL-AED-0000001", "po_serwisie", "", "serwis", "", "Wymiana elektrod i baterii, test samokontroli OK", "2026-11-21", "2028-11-30", "2030-11-30", "SRV/2026/1188", "", ""],
        ["", "PL-AED-0000002", "w_serwisie", "", "serwis", "kontrolka_bledu", "Urządzenie zabrane – błąd autotestu", "", "", "", "SRV/2026/1189", "", "2026-11-28"],
        ["", "PL-AED-0000004", "wymaga_serwisu", "", "serwis", "brak_lub_przeterminowane_elektrody", "Elektrody tracą ważność 2026-12-15", "", "", "", "", "", ""],
    ])
    write_csv(o("aktualizacje_zrm_112_przyklad.csv"), upd_cols, [
        ["", "PL-AED-0000002", "uzycie", "2026-11-21T14:05:00", "zrm", "", "AED użyty przez świadków przed przyjazdem ZRM", "", "", "", "", "CPR-2026-000123", ""],
        ["", "PL-AED-0000006", "uzycie", "2026-11-21T16:40:00", "dyspozytor", "", "Dyspozytor 112 skierował świadka do AED", "", "", "", "", "CPR-2026-000131", ""],
    ])


def main():
    sch = D / "schemat"
    write_json(sch / "aed_punkty.tableschema.json", imp.SCHEMA)
    write_json(sch / "aed_obszarowe.tableschema.json", simple_schema("aed-obszarowe", "AED obszarowe i mobilne", imp.AREA_FIELDS, imp.AREA_ENUMS))
    write_json(sch / "organizacje.tableschema.json", simple_schema("organizacje", "Organizacje (dysponenci, firmy) – logo i strona www", imp.ORG_FIELDS, imp.ORG_ENUMS))
    write_json(sch / "aktualizacje.tableschema.json", simple_schema("aktualizacje", "Aktualizacje stanu AED (użycie, serwis)", AKTUALIZACJE_SPEC,
                                                                     {"typ_zdarzenia": ["uzycie", "wymaga_serwisu", "w_serwisie", "po_serwisie", "sprawny"],
                                                                      "rola": ["obywatel", "dysponent", "serwis", "zrm", "dyspozytor", "sluzby"]}))
    write_json(sch / "slowniki.json", slowniki())
    shutil.copy(PLAN / "metadane_zbioru_dcat.json", sch / "metadane_zbioru_dcat.json")
    write_json(sch / "aed_punkty.csvw.json", {
        "@context": "http://www.w3.org/ns/csvw", "url": "aed_punkty.csv", "dc:title": "Defibrylatory AED w Polsce – zbiór krajowy",
        "dc:license": {"@id": "https://creativecommons.org/publicdomain/zero/1.0/"},
        "dialect": {"delimiter": ",", "encoding": "utf-8", "lineTerminators": ["\r\n"], "header": True},
        "tableSchema": {"primaryKey": "id_aed", "aboutUrl": "https://dane.gov.pl/aed/{id_aed}",
                        "columns": [{"name": f["name"], "titles": f["name"], "datatype": {"number": "decimal", "integer": "integer", "boolean": "boolean",
                                     "date": "date", "datetime": "dateTime"}.get(f["type"], "string"), "dc:description": f.get("description", ""),
                                     "required": bool(f.get("constraints", {}).get("required"))} for f in imp.SCHEMA["fields"]]}})
    write_json(sch / "kontekst.jsonld", {"@context": {
        "schema": "https://schema.org/", "xsd": "http://www.w3.org/2001/XMLSchema#", "aed": "https://dane.gov.pl/aed/def#",
        "id_aed": "@id", "nazwa_lokalizacji": "schema:name", "opis_lokalizacji": "schema:description",
        "szerokosc_geograficzna": {"@id": "schema:latitude", "@type": "xsd:decimal"}, "dlugosc_geograficzna": {"@id": "schema:longitude", "@type": "xsd:decimal"},
        "miejscowosc": "schema:addressLocality", "kod_pocztowy": "schema:postalCode", "nazwa_ulicy": "schema:streetAddress",
        "godziny_dostepnosci": "schema:openingHours", "dysponent_nazwa": "schema:provider", "telefon_kontaktowy": "schema:telephone",
        "email_kontaktowy": "schema:email", "producent": "schema:manufacturer", "model": "schema:model",
        "data_aktualizacji": {"@id": "schema:dateModified", "@type": "xsd:dateTime"}, "zdjecie_url": {"@id": "schema:image", "@type": "@id"},
        "typ_dostepu": "aed:typDostepu", "dostepny_24_7": {"@id": "aed:dostepny247", "@type": "xsd:boolean"},
        "status_urzadzenia": "aed:status", "poziom_weryfikacji": "aed:poziomWeryfikacji",
        "data_weryfikacji": {"@id": "aed:dataWeryfikacji", "@type": "xsd:date"}, "organizacja_id": {"@id": "schema:brand", "@type": "@id"},
        "id_obszaru": {"@id": "aed:obszar", "@type": "@id"}}})
    write_json(sch / "mapowanie.schema.json", {
        "$schema": "https://json-schema.org/draft/2020-12/schema", "title": "Plik mapowania kolumn na wzorzec AED", "type": "object",
        "required": ["kolumny"],
        "properties": {
            "wersja": {"type": "string"}, "opis": {"type": "string"}, "organizacja_id": {"type": "string"},
            "licencja_zrodla": {"type": "string", "description": "np. ODbL-1.0 dla OSM – wyklucza ze zbioru krajowego CC0"},
            "domyslne": {"type": "object", "additionalProperties": {"type": "string"}},
            "kolumny": {"type": "object", "propertyNames": {"enum": imp.FIELDS}, "additionalProperties": {
                "type": "object", "properties": {
                    "z": {"oneOf": [{"type": "string"}, {"type": "array", "items": {"type": "string"}}],
                          "description": "Kolumna źródła (lub lista – pierwsza niepusta)"},
                    "stala": {"type": "string", "description": "Wartość stała dla wszystkich wierszy"},
                    "mapa": {"type": "object", "additionalProperties": {"type": "string"}, "description": "Przekodowanie wartości; klucz * = domyślna"},
                    "regex": {"type": "string", "description": "Wyrażenie regularne; pierwsza grupa = wartość"}},
                "oneOf": [{"required": ["z"]}, {"required": ["stala"]}]}}}})

    sz = D / "szablony"
    write_csv(sz / "aed_punkty_szablon.csv", imp.FIELDS, [])
    write_csv(sz / "aed_obszarowe_szablon.csv", [f[0] for f in imp.AREA_FIELDS], [])
    write_csv(sz / "organizacje_szablon.csv", [f[0] for f in imp.ORG_FIELDS], [])
    write_csv(sz / "aktualizacje_szablon.csv", [c[0] for c in AKTUALIZACJE_SPEC], [])

    # XLSX – wzorcowy zakres danych
    slow = slowniki()
    zakres = [["lp", "kolumna", "typ", "wymagalność (W/Z/O)", "grupa", "opis", "przykład", "słownik / wzorzec"]]
    plan_cols = {r["kolumna"]: r for r in csv.DictReader(io.StringIO((PLAN / "slownik_kolumn.csv").read_text("utf-8-sig")))}
    for i, f in enumerate(imp.SCHEMA["fields"], 1):
        pc = plan_cols.get(f["name"], {})
        c = f.get("constraints", {})
        zakres.append([i, f["name"], f["type"], f.get("x-wymagalnosc", ""), f.get("x-grupa", ""), f.get("description", ""),
                       pc.get("przyklad", ""), ", ".join(c.get("enum", [])) or c.get("pattern", "")])
    szablon = [imp.FIELDS] + [[r.get(k, "") for k in imp.FIELDS] for r in csv.DictReader(io.StringIO(imp.to_csv(
        imp.run((PLAN / "aed_wzorzec_przyklad.csv").read_bytes(), "x.csv", None, preset="wzorzec")["rekordy"])))][:3]
    slown = [["słownik", "wartość", "opis"]]
    for k, v in slow.items():
        for w in v.get("wartosci", []):
            slown.append([k, w if isinstance(w, str) else w.get("wartosc", ""), "" if isinstance(w, str) else w.get("opis", "")])
    tab = lambda spec: [["kolumna", "typ", "wymagalność", "opis", "przykład"]] + [list(x) for x in spec]
    write_xlsx(D / "wzorcowy_zakres_danych.xlsx", [
        ("1_Zakres_AED_punkty", zakres), ("2_Szablon_AED_punkty", szablon), ("3_Slowniki", slown),
        ("4_AED_obszarowe", tab(imp.AREA_FIELDS)), ("5_Organizacje", tab(imp.ORG_FIELDS)), ("6_Aktualizacje_stanu", tab(AKTUALIZACJE_SPEC))])

    probki(D / "dane_przykladowe")
    print("Wygenerowano:", ", ".join(sorted(str(p.relative_to(D)) for p in D.rglob("*") if p.is_file() and "narzedzia" not in p.parts)))


if __name__ == "__main__":
    main()
