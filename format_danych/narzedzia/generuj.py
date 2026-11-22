#!/usr/bin/env python3
"""
Buduje paczkę „wzorcowy zakres danych AED v2” z jednego źródła prawdy (format_danych/zrodla_wzorca):

    python format_danych/zrodla_wzorca/generuj_dane.py   # najpierw źródło prawdy
    python format_danych/narzedzia/generuj.py

Wynik w format_danych/:
  schemat/   aed_punkty.tableschema.json, aed_zestawienie.tableschema.json, aed_punkty.csvw.json,
             kontekst.jsonld, slowniki.json, metadane_zbioru_dcat.json
  szablony/  aed_punkty_szablon.csv, aed_punkty_szablon.xlsx (jeden arkusz – POD 2021–2027 zał. 2 pkt 3.1)
  przyklady/ aed_punkty_przyklad.csv/.geojson, aed_zestawienie_przyklad.csv/.json
  wzorcowy_zakres_danych.xlsx – dokumentacja zakresu (deliverable konkursowy), nie plik do publikacji

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
ZW = D / "zrodla_wzorca"
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def czytaj_json(nazwa):
    return json.loads((ZW / nazwa).read_text("utf-8"))


def czytaj_csv(nazwa):
    return list(csv.reader(io.StringIO((ZW / nazwa).read_text("utf-8-sig"))))


def write_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", "utf-8", newline="")


def kopiuj(nazwa, cel: Path):
    cel.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ZW / nazwa, cel)


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
            # Wszystko jako tekst: kody (TERC, PNA, REGON, telefon) nie tracą zer wiodących.
            cells.append(f'<c r="{ref}" t="inlineStr"{style}><is><t xml:space="preserve">{escape(str(v))}</t></is></c>')
        out.append(f'<row r="{ri}">{"".join(cells)}</row>')
    out.append("</sheetData></worksheet>")
    return "".join(out)


def write_xlsx(path: Path, sheets: list[tuple[str, list[list]]]):
    path.parent.mkdir(parents=True, exist_ok=True)
    n = len(sheets)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml",
                   '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                   '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                   '<Default Extension="xml" ContentType="application/xml"/>'
                   '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
                   '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
                   + "".join(f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                             for i in range(1, n + 1)) + "</Types>")
        z.writestr("_rels/.rels", '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        z.writestr("xl/workbook.xml", '<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                   'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'
                   + "".join(f'<sheet name="{escape(s)}" sheetId="{i}" r:id="rId{i}"/>' for i, (s, _) in enumerate(sheets, 1)) + "</sheets></workbook>")
        z.writestr("xl/_rels/workbook.xml.rels", '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   + "".join(f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>'
                             for i in range(1, n + 1))
                   + f'<Relationship Id="rId{n + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>')
        z.writestr("xl/styles.xml", '<?xml version="1.0" encoding="UTF-8"?><styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                   '<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="11"/><name val="Calibri"/></font></fonts>'
                   '<fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill></fills>'
                   '<borders count="1"><border/></borders><cellStyleXfs count="1"><xf/></cellStyleXfs>'
                   '<cellXfs count="2"><xf/><xf fontId="1" applyFont="1"/></cellXfs></styleSheet>')
        for i, (_, rows) in enumerate(sheets, 1):
            z.writestr(f"xl/worksheets/sheet{i}.xml", sheet_xml(rows))


ZASADY = [
    ["zasada", "źródło"],
    ["Jeden wiersz = jedno urządzenie AED; kilka AED w jednym miejscu = kilka wierszy z różnym id_zrodlowe", "decyzja projektu (wzorzec v2)"],
    ["id_aed nadaje portal przy agregacji (PL-AED- + 12 znaków hex); dostawca podaje id_zrodlowe", "decyzja projektu (wzorzec v2)"],
    ["Puste status_urzadzenia = 'nieznany', puste poziom_weryfikacji = 'niezweryfikowany'; nigdy domyślnie 'sprawny'", "decyzja projektu (wzorzec v2)"],
    ["Kontakty (telefon, e-mail) wyłącznie instytucjonalne lub funkcyjne; dane firm z definicji bez danych osobowych", "Regulamin portalu §2 pkt 4; Standard bezpieczeństwa s. 11–15"],
    ["Dostawca jest administratorem danych osobowych, które publikuje; ocena skutków przed publikacją", "Regulamin §2 pkt 5; baza wiedzy: dane osobowe w portalu"],
    ["Bez zdjęć i treści naruszających prawa autorskie lub wizerunek", "Regulamin §7; Standard prawny s. 9"],
    ["Bez kodów do szafek, miejsca przechowywania klucza, imion i nazwisk w polach tekstowych", "decyzja projektu"],
    ["AED w lokalu mieszkalnym osoby fizycznej nie jest publikowany", "decyzja projektu"],
    ["Do zasobu zbiorczego tylko licencje CC0 1.0 i CC BY 4.0; OpenStreetMap (ODbL) wykluczony; zasób zbiorczy na CC BY 4.0 z atrybucją w wierszu", "decyzja projektu; Regulamin §5"],
    ["Informacja o źródle, czasie i przetworzeniu: kolumny pochodzenia i przetworzenie", "art. 15 ust. 1 pkt 1–2 ustawy z 11.08.2021"],
    ["Daty yyyy-mm-dd, data z czasem yyyy-mm-ddThh:mm:ss, true/false, kropka dziesiętna", "POD 2021–2027 zał. 2, s. 123"],
    ["REGON 9 lub 14 cyfr, telefon 9 cyfr (dopuszczalny prefiks +), bez spacji i łączników", "POD 2021–2027 zał. 2, s. 124"],
    ["Adres w osobnych polach, wartości literalnie wg TERYT", "POD 2021–2027 zał. 2, s. 124–125"],
    ["CSV RFC 4180: UTF-8, przecinek, CRLF, jeden nagłówek, bez pustych i powtórzonych kolumn", "POD 2021–2027 zał. 2, s. 126"],
    ["Arkusz XLSX: jeden nagłówek, bez scaleń i formuł, pojedynczy arkusz (plik szablony/aed_punkty_szablon.xlsx)", "POD 2021–2027 zał. 2, s. 123–124"],
]


def main():
    schemat = czytaj_json("schemat_tableschema.json")
    zestawienie = czytaj_json("schemat_zestawienia_tableschema.json")
    slowniki = czytaj_json("slowniki_wartosci.json")
    naglowek = [f["name"] for f in schemat["fields"]]

    # --- schemat/ ------------------------------------------------------------
    sch = D / "schemat"
    write_json(sch / "aed_punkty.tableschema.json", schemat)
    write_json(sch / "aed_zestawienie.tableschema.json", zestawienie)
    write_json(sch / "slowniki.json", slowniki)
    kopiuj("metadane_zbioru_dcat.json", sch / "metadane_zbioru_dcat.json")
    przyklad_json = czytaj_json("aed_zestawienie_przyklad.json")
    write_json(sch / "kontekst.jsonld", {"@context": przyklad_json["@context"]})
    typy = {"number": "decimal", "integer": "integer", "boolean": "boolean", "date": "date", "datetime": "dateTime"}
    write_json(sch / "aed_punkty.csvw.json", {
        "@context": "http://www.w3.org/ns/csvw", "url": "aed_punkty.csv",
        "dc:title": "Defibrylatory AED – plik dostawcy wg wzorcowego zakresu danych v2",
        "dialect": {"delimiter": ",", "encoding": "utf-8", "lineTerminators": ["\r\n"], "header": True},
        "tableSchema": {"primaryKey": "id_zrodlowe",
                        "columns": [{"name": f["name"], "titles": f["name"], "datatype": typy.get(f["type"], "string"),
                                     "dc:description": f.get("description", ""),
                                     "required": bool(f.get("constraints", {}).get("required"))} for f in schemat["fields"]]}})

    # --- szablony/ -----------------------------------------------------------
    kopiuj("aed_wzorzec_szablon.csv", D / "szablony" / "aed_punkty_szablon.csv")
    write_xlsx(D / "szablony" / "aed_punkty_szablon.xlsx", [("aed_punkty", [naglowek])])

    # --- przyklady/ ----------------------------------------------------------
    pr = D / "przyklady"
    kopiuj("aed_wzorzec_przyklad.csv", pr / "aed_punkty_przyklad.csv")
    kopiuj("aed_wzorzec_przyklad.geojson", pr / "aed_punkty_przyklad.geojson")
    kopiuj("aed_zestawienie_przyklad.csv", pr / "aed_zestawienie_przyklad.csv")
    kopiuj("aed_zestawienie_przyklad.json", pr / "aed_zestawienie_przyklad.json")

    # --- wzorcowy_zakres_danych.xlsx (dokumentacja zakresu) -------------------
    sk = czytaj_csv("slownik_kolumn.csv")
    zakres = [["lp", "kolumna", "typ", "wymagalność (W/Z/O)", "minimum agregacji", "grupa", "opis", "przykład", "słownik / wzorzec", "typ kolumny w portalu"]]
    wzorce = {f["name"]: f.get("constraints", {}) for f in schemat["fields"]}
    for lp, kol, typ, wym, mini, grupa, opis, przyk, slow, _reg, typ_p in sk[1:]:
        c = wzorce[kol]
        zakres.append([lp, kol, typ, wym, mini, grupa, opis, przyk, ", ".join(c.get("enum", [])) or c.get("pattern", ""), typ_p])
    przyklad = czytaj_csv("aed_wzorzec_przyklad.csv")
    slown = [["słownik", "kod", "etykieta"]] + [[k, w["kod"], w.get("etykieta", "")] for k, v in slowniki.items() for w in v["wartosci"]]
    zest = czytaj_csv("slownik_kolumn_zestawienia.csv")
    write_xlsx(D / "wzorcowy_zakres_danych.xlsx", [
        ("1_Zakres_wzorca", zakres),
        ("2_Szablon_z_przykladami", przyklad),
        ("3_Slowniki", slown),
        ("4_Zasob_zbiorczy", [["lp", "kolumna", "typ", "pochodzenie", "grupa", "opis", "przykład", "typ kolumny w portalu"]] + zest[1:]),
        ("5_Zasady", ZASADY),
    ])

    assert naglowek == przyklad[0] == czytaj_csv("aed_wzorzec_szablon.csv")[0] and len(naglowek) == 41
    assert len(zest) - 1 == 51
    print("Wygenerowano:", ", ".join(sorted(str(p.relative_to(D)) for p in D.rglob("*")
                                             if p.is_file() and not {"narzedzia", "zrodla_wzorca"} & set(p.parts))))


if __name__ == "__main__":
    main()
