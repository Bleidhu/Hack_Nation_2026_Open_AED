import hashlib
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

from rdzen.opis_xml import OpisBlad, zbuduj_opis  # noqa: E402

XSD = ROOT / "format_danych" / "schemat" / "aed_opis_zbioru.xsd"
PRZYKLAD_CSV = ROOT / "format_danych" / "przyklady" / "opis" / "aed_dostawcy.csv"
ARGS = dict(link_csv="https://dostawca.example.pl/aed.csv", tytul="Defibrylatory AED – Gmina", opis="Lokalizacje AED.",
            dysponent="Gmina Przykład", licencja="CC BY 4.0", czestotliwosc="daily",
            data_aktualizacji=datetime(2026, 11, 22, 6, 0, 0))


class TestOpisXml(unittest.TestCase):
    def setUp(self):
        self.csv = PRZYKLAD_CSV.read_bytes()

    def opis(self, **nad):
        return zbuduj_opis(self.csv, **{**ARGS, **nad})

    def test_struktura_i_md5(self):
        r = ET.fromstring(self.opis(regon="123456785", email="a@b.pl").encode("utf-8"))
        self.assertEqual(r.findtext("zasob/md5"), hashlib.md5(self.csv).hexdigest())
        self.assertEqual(r.findtext("licencja"), "CC BY 4.0")
        self.assertEqual(r.findtext("data_aktualizacji"), "2026-11-22T06:00:00")
        self.assertEqual(r.findtext("zasob/format"), "csv")
        self.assertEqual(r.findtext("dysponent_regon"), "123456785")
        self.assertEqual(r.findtext("zasob/liczba_rekordow"), "7")

    def test_pola_opcjonalne_pomijane(self):
        r = ET.fromstring(self.opis().encode("utf-8"))
        self.assertIsNone(r.find("dysponent_regon"))
        self.assertIsNone(r.find("kontakt_email"))

    def test_odrzuca_licencje_niedozwolone(self):
        for lic in ("ODbL 1.0", "CC BY-SA 4.0", ""):
            with self.assertRaises(OpisBlad):
                self.opis(licencja=lic)

    def test_odrzuca_link_http(self):
        with self.assertRaises(OpisBlad):
            self.opis(link_csv="http://dostawca.example.pl/aed.csv")

    def test_odrzuca_zla_czestotliwosc_i_regon(self):
        with self.assertRaises(OpisBlad):
            self.opis(czestotliwosc="hourly")
        with self.assertRaises(OpisBlad):
            self.opis(regon="123")

    def test_escape_znakow_specjalnych(self):
        r = ET.fromstring(self.opis(tytul='A & B <"x">', opis="a < b > c").encode("utf-8"))
        self.assertEqual(r.findtext("tytul"), 'A & B <"x">')
        self.assertEqual(r.findtext("opis"), "a < b > c")

    def test_csv_bez_minimum_kolumn(self):
        with self.assertRaises(OpisBlad):
            zbuduj_opis(b"a,b\r\n1,2\r\n", **ARGS)

    def test_zgodnosc_z_xsd(self):
        try:
            from lxml import etree
        except ImportError:
            self.skipTest("brak lxml")
        schema = etree.XMLSchema(etree.parse(str(XSD)))
        doc = etree.fromstring(self.opis(regon="123456785", email="a@b.pl").encode("utf-8"))
        self.assertTrue(schema.validate(doc), schema.error_log)

    def test_cli_zapisuje_opis_obok_csv(self):
        with tempfile.TemporaryDirectory() as d:
            plik = Path(d) / "aed.csv"
            plik.write_bytes(self.csv)
            baza = [sys.executable, str(HERE / "importer.py"), "opis", str(plik), "--link-csv", ARGS["link_csv"],
                    "--tytul", "T", "--opis", "O", "--dysponent", "D", "--czestotliwosc", "weekly"]
            p = subprocess.run(baza + ["--licencja", "CC0 1.0"], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(p.returncode, 0, p.stderr)
            r = ET.parse(Path(d) / "opis.xml").getroot()
            self.assertEqual(r.findtext("zasob/md5"), hashlib.md5(self.csv).hexdigest())
            self.assertEqual(r.findtext("zasob/tytul"), "Lokalizacje AED (CSV)")
            p = subprocess.run(baza + ["--licencja", "CC0 1.0", "--tytul-zasobu", "Punkty AED"], capture_output=True,
                               text=True, encoding="utf-8")
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual(ET.parse(Path(d) / "opis.xml").getroot().findtext("zasob/tytul"), "Punkty AED")
            p = subprocess.run(baza + ["--licencja", "ODbL"], capture_output=True, text=True, encoding="utf-8")
            self.assertNotEqual(p.returncode, 0)


if __name__ == "__main__":
    unittest.main()
