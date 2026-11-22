import ast
import csv
import io
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

import importer  # noqa: E402
from rdzen import wzorzec  # noqa: E402
from rdzen.mapowanie import suggest_mapping  # noqa: E402

ROOT = HERE.parent
PRZYKLAD = ROOT / "format_danych" / "przyklady" / "aed_punkty_przyklad.csv"


def _csv_cols(path):
    with open(path, encoding="utf-8", newline="") as f:
        return next(csv.reader(f))


class TestWzorzec(unittest.TestCase):
    def test_41_kolumn_w_kolejnosci_pliku(self):
        self.assertEqual(len(wzorzec.FIELDS), 41)
        self.assertEqual(wzorzec.FIELDS, _csv_cols(PRZYKLAD))

    def test_aliasy_zgodne_z_portalem(self):
        src = (ROOT / "portal/backend/mcod/resources/aed_constants.py").read_text("utf-8")
        for node in ast.parse(src).body:
            if isinstance(node, ast.AnnAssign) and node.target.id == "AED_HEADER_ALIASES":
                self.assertEqual(ast.literal_eval(node.value), wzorzec.HEADER_ALIASES)
                return
        self.fail("brak AED_HEADER_ALIASES w portalu")

    def test_normalize_header(self):
        self.assertEqual(wzorzec.normalize_header(" Szerokość (WGS84) "), "szerokosc_wgs84")


class TestPrzyklad(unittest.TestCase):
    def test_plik_wzorca_bez_bledow_i_bez_zmian_wartosci(self):
        data = PRZYKLAD.read_bytes()
        res = importer.run(data, PRZYKLAD.name, preset="wzorzec", cel="lokalny")
        self.assertEqual(res["raport"]["odrzucone"], 0, res["raport"]["bledy"])
        out = list(csv.DictReader(io.StringIO(importer.to_csv(res["rekordy"]), newline="")))
        src = list(csv.DictReader(io.StringIO(data.decode("utf-8"), newline="")))
        self.assertEqual(len(out), len(src))
        for a, b in zip(out, src):
            for k, v in b.items():
                if k not in ("status_urzadzenia", "poziom_weryfikacji"):  # puste -> wartości domyślne
                    self.assertEqual(a[k], v, k)

    def test_csv_crlf_i_naglowek(self):
        res = importer.run(PRZYKLAD.read_bytes(), PRZYKLAD.name, preset="wzorzec", cel="lokalny")
        text = importer.to_csv(res["rekordy"])
        self.assertTrue(text.startswith(",".join(wzorzec.FIELDS) + "\r\n"))
        self.assertNotIn("\n", text.replace("\r\n", ""))


class TestMapowanie(unittest.TestCase):
    CSV = ("Kod placówki;Nazwa;Miasto;Ulica;Szerokość;Długość;Opis;Dostęp;Całodobowo\n"
           "B1;Bank A;Szczecin;Wolności;53,4285;14,5528;Hol;publiczny;TAK\n"
           "B2;Bank B;Poznań;Półwiejska;52,4082;16,9335;;publiczny;NIE\n"
           "B3;Bank C;Kraków;Rynek;19,9450;50,0647;Parter;publiczny;nie\n").encode("utf-8")

    def test_podpowiedz_aliasy_i_synonimy(self):
        cols = suggest_mapping(["Kod placówki", "Nazwa", "Miasto", "Szerokość", "Długość", "Całodobowo"])["kolumny"]
        self.assertEqual(cols["id_zrodlowe"]["z"], "Kod placówki")
        self.assertEqual(cols["nazwa_lokalizacji"]["z"], "Nazwa")
        self.assertEqual(cols["szerokosc_geograficzna"]["z"], "Szerokość")
        self.assertEqual(cols["dostepny_24_7"]["z"], "Całodobowo")

    def test_normalizacja_domyslne_i_raport(self):
        res = importer.run(self.CSV, "x.csv", cel="lokalny")
        r1, r2, r3 = res["rekordy"]
        self.assertEqual((r1["szerokosc_geograficzna"], r1["dostepny_24_7"]), ("53.4285", "true"))
        self.assertEqual(r1["status_urzadzenia"], "nieznany")
        self.assertEqual(r1["poziom_weryfikacji"], "niezweryfikowany")
        self.assertEqual(r2["__status"], "odrzucony")  # brak opisu_lokalizacji
        self.assertEqual(r3["szerokosc_geograficzna"], "50.0647")  # zamienione współrzędne
        self.assertTrue(any(e["wiersz"] == 3 for e in res["raport"]["bledy"]))

    def test_brak_id_nadaje_stabilny_identyfikator(self):
        a = importer.run(b"nazwa,miasto,lat,lon\nX,Y,52.1,21.0\n", "a.csv", cel="lokalny")["rekordy"][0]
        b = importer.run(b"nazwa,miasto,lat,lon\nX,Y,52.1,21.0\n", "a.csv", cel="lokalny")["rekordy"][0]
        self.assertTrue(a["id_zrodlowe"].startswith("auto-"))
        self.assertEqual(a["id_zrodlowe"], b["id_zrodlowe"])


if __name__ == "__main__":
    unittest.main()
