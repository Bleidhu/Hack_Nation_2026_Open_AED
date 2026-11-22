"""Generuje przykład zewnętrznego dostawcy: opis zbioru w XML + CSV z sumą md5 (dane FIKCYJNE) do format_danych/przyklady/opis/.

aed_dostawcy.csv       CSV zgodny ze wzorcem v2 (42 kolumny), 7 rekordów; jeden z nich to to samo urządzenie
                       (ten sam producent i numer seryjny), które zgłasza też inny dostawca: pokazuje deduplikację
opis_poprawny.xml      opis zbioru zgodny z aed_opis_zbioru.xsd, md5 zgodne z CSV
opis_bledny_md5.xml    opis zgodny z XSD, ale md5 nie pasuje do CSV (import odrzucony)
opis_bledny_xsd.xml    opis niezgodny z XSD (brak tytułu, link http, licencja spoza listy)
W opisach link do CSV to adres przykładowy; serwer demo/serwer_zewnetrzny.py podstawia swój adres przy wydawaniu opisu.

Uruchomienie: python format_danych/narzedzia/generuj_opis.py (tylko biblioteka standardowa).
"""
import csv
import hashlib
import io
import json
import sys
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from generuj_xml import DYSPONENT, POLA, REKORDY  # noqa: E402

CEL = HERE.parent / "przyklady" / "opis"
ADRES_PRZYKLADOWY = "https://dostawca.example.pl"
MARKI = {  # id: (producent, model, numer seryjny)
    "OL-001": ("Philips", "HeartStart FRx", "FRX-2026-1101"),
    "OL-002": ("Zoll", "AED Plus", "ZP-2026-1102"),
    "OL-003": ("Defibtech", "Lifeline AED", "DL-2026-1103"),
    "EL-001": ("Physio-Control", "LIFEPAK CR2", "LP-2026-1104"),
    "EL-002": ("Zoll", "AED 3", ""),
    "EL-003": ("Philips", "HeartStart FRx", "FRX-2026-1106"),
}
# To samo urządzenie co CT-01 z przykładu wzorca (Bydgoszcz): ten sam producent i numer seryjny, inne id_zrodlowe.
KOPIA = ("BYD-HALA-A", "Hala A – Centrum Targowe (zgłoszenie dostawcy)", "Bydgoszcz", "Przykładowa", "187", "85-001",
         "53.150120", "18.017350", "Parter, przy wejściu głównym hali A", "true", "ograniczony", "false", "sprawny")


def kolumny():
    schema = json.loads((HERE.parent / "schemat" / "aed_punkty.tableschema.json").read_text(encoding="utf-8"))
    return [f["name"] for f in schema["fields"]]


def wiersze():
    out = []
    for r in list(REKORDY) + [KOPIA]:
        rec = dict(zip(POLA, r))
        rec.update(DYSPONENT)
        rec["producent"], rec["model"], rec["numer_seryjny"] = MARKI.get(r[0], ("Philips", "HeartStart FRx", "FRX-2026-0001"))
        out.append(rec)
    return out


def csv_bytes():
    nazwy = kolumny()
    buf = io.StringIO(newline="")
    writer = csv.DictWriter(buf, fieldnames=nazwy, lineterminator="\r\n", extrasaction="raise")
    writer.writeheader()
    for rec in wiersze():
        writer.writerow({k: rec.get(k, "") for k in nazwy})
    return buf.getvalue().encode("utf-8")


def opis(md5, link, licencja="CC BY 4.0", tytul="Defibrylatory AED – Miejski Zakład Przykład (PRZYKŁAD)"):
    tytul_xml = f"  <tytul>{escape(tytul)}</tytul>\n" if tytul else ""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<opis_zbioru>
{tytul_xml}  <opis>Lokalizacje defibrylatorów AED dysponenta (dane fikcyjne do demonstracji). Dane w pliku CSV zgodnym ze wzorcem AED v2.</opis>
  <dysponent_nazwa>Miejski Zakład Przykład (PRZYKŁAD)</dysponent_nazwa>
  <dysponent_regon>123456785</dysponent_regon>
  <kontakt_email>aed@dostawca.example.pl</kontakt_email>
  <licencja>{licencja}</licencja>
  <czestotliwosc_aktualizacji>daily</czestotliwosc_aktualizacji>
  <data_aktualizacji>2026-11-22T06:00:00</data_aktualizacji>
  <zasob>
    <tytul>Lokalizacje AED (CSV)</tytul>
    <link_csv>{link}</link_csv>
    <format>csv</format>
    <md5>{md5}</md5>
    <liczba_rekordow>{len(wiersze())}</liczba_rekordow>
  </zasob>
</opis_zbioru>
"""


if __name__ == "__main__":
    CEL.mkdir(parents=True, exist_ok=True)
    dane = csv_bytes()
    (CEL / "aed_dostawcy.csv").write_bytes(dane)
    md5 = hashlib.md5(dane).hexdigest()
    link = f"{ADRES_PRZYKLADOWY}/aed.csv"
    (CEL / "opis_poprawny.xml").write_text(opis(md5, link), encoding="utf-8", newline="\n")
    (CEL / "opis_bledny_md5.xml").write_text(opis("0" * 32, link), encoding="utf-8", newline="\n")
    (CEL / "opis_bledny_xsd.xml").write_text(
        opis(md5, link.replace("https://", "http://"), licencja="CC BY-SA 4.0", tytul=""), encoding="utf-8", newline="\n"
    )
    print("Zapisano", CEL, "md5", md5)
