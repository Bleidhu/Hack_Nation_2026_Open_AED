import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

import importer  # noqa: E402
from rdzen.licencje import LicencjaBlad, wczytaj_konfiguracje  # noqa: E402

PRZYKLAD = (HERE.parent / "format_danych" / "przyklady" / "aed_punkty_przyklad.csv").read_bytes()
OSM = (HERE / "dane_przykladowe" / "01_integrator_osm" / "osm_przyklad.geojson").read_bytes()


def run(data=PRZYKLAD, name="a.csv", preset="wzorzec", **kw):
    return importer.run(data, name, preset=preset, **kw)


class TestLicencje(unittest.TestCase):
    def test_odbl_dla_portalu_odmowa(self):
        with self.assertRaises(LicencjaBlad):
            run(OSM, "o.geojson", preset="osm", cel="portal")
        with self.assertRaises(LicencjaBlad):
            run(OSM, "o.geojson", preset="osm", licencja="ODbL-1.0", cel="portal")

    def test_odbl_lokalnie_z_ostrzezeniem(self):
        p = run(OSM, "o.geojson", preset="osm", cel="lokalny")["pochodzenie"]
        self.assertEqual(p["licencja"], "ODbL 1.0")
        self.assertEqual(p["atrybucja"], "© współtwórcy OpenStreetMap")
        self.assertFalse(p["do_publikacji"])
        self.assertIn("nie jest na liście", p["ostrzezenie"])

    def test_cc0_i_cc_by_dla_portalu(self):
        for lic in ("CC0 1.0", "cc0-1.0", "CC BY 4.0", "CC-BY-4.0"):
            self.assertTrue(run(licencja=lic, cel="portal")["pochodzenie"]["do_publikacji"], lic)

    def test_brak_licencji_dla_portalu_odmowa(self):
        with self.assertRaises(LicencjaBlad):
            run(cel="portal")

    def test_brak_licencji_lokalnie_ostrzezenie(self):
        self.assertFalse(run(cel="lokalny")["pochodzenie"]["do_publikacji"])

    def test_dopisanie_licencji_do_konfiguracji_przepuszcza(self):
        kfg = wczytaj_konfiguracje()
        kfg["dozwolone_licencje"].append("ODbL 1.0")
        res = run(OSM, "o.geojson", preset="osm", cel="portal", konfiguracja=kfg)
        self.assertTrue(res["pochodzenie"]["do_publikacji"])

    def test_cli_odmowa_ma_kod_niezerowy(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "o.geojson"
            f.write_bytes(OSM)
            r = subprocess.run([sys.executable, str(HERE / "importer.py"), str(f), "--preset", "osm"],
                               capture_output=True, text=True, encoding="utf-8")
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("Odmowa", r.stderr)


if __name__ == "__main__":
    unittest.main()
