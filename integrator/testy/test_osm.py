import csv
import io
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

import importer  # noqa: E402
from adaptery.osm import wczytaj  # noqa: E402
from rdzen.wzorzec import FIELDS  # noqa: E402

PROBKI = HERE / "dane_przykladowe" / "01_integrator_osm"
OVERPASS = (PROBKI / "osm_overpass_krakow.json").read_bytes()
GEOJSON = (PROBKI / "osm_przyklad.geojson").read_bytes()

XML = """<?xml version="1.0"?>
<osm version="0.6"><meta osm_base="2026-11-20T10:00:00Z"/>
<node id="7" lat="52.1" lon="21.0"><tag k="emergency" v="defibrillator"/><tag k="name" v="Urząd"/><tag k="addr:city" v="Warszawa"/></node>
<way id="8"><center lat="52.2" lon="21.1"/><tag k="emergency" v="defibrillator"/><tag k="surface" v="x"/></way>
<way id="9"><tag k="emergency" v="defibrillator"/></way>
</osm>""".encode("utf-8")


def run(data, name, **kw):
    return importer.run(data, name, preset="osm", cel=kw.pop("cel", "lokalny"), **kw)


class TestOsm(unittest.TestCase):
    def test_obie_probki_daja_csv_v2_i_raport(self):
        for data, name in ((OVERPASS, "o.json"), (GEOJSON, "o.geojson")):
            res = run(data, name)
            self.assertGreater(len(res["rekordy"]), 0)
            self.assertEqual(res["raport"]["odrzucone"], 0, res["raport"]["bledy"])
            rows = list(csv.reader(io.StringIO(importer.to_csv(res["rekordy"]), newline="")))
            self.assertEqual(rows[0], FIELDS)
            self.assertEqual(len(rows) - 1, len(res["rekordy"]))
            self.assertIn("tagi_bez_odpowiednika", res["raport"]["osm"])

    def test_pochodzenie_status_i_id(self):
        res = run(OVERPASS, "o.json")
        r = res["rekordy"][0]
        self.assertEqual(r["id_zrodlowe"], "osm:node/900000001")
        self.assertEqual(r["zrodlo_danych"], "openstreetmap")
        self.assertEqual(r["status_urzadzenia"], "nieznany")
        self.assertEqual(r["data_aktualizacji"], "2026-11-21T06:00:00")
        self.assertEqual(r["zrodlo_url"], "https://www.openstreetmap.org/node/900000001")
        self.assertEqual(res["pochodzenie"]["licencja"], "ODbL 1.0")

    def test_24_7_i_dostep(self):
        recs = {r["id_zrodlowe"]: r for r in run(OVERPASS, "o.json")["rekordy"]}
        r3 = recs["osm:node/900000003"]
        self.assertEqual((r3["dostepny_24_7"], r3["godziny_dostepnosci"]), ("true", ""))
        self.assertEqual(recs["osm:node/900000001"]["typ_dostepu"], "ograniczony")

    def test_xml_way_center_i_pominiecie_bez_srodka(self):
        rows, meta = wczytaj(XML, "x.osm")
        self.assertEqual([r["@id"] for r in rows], ["osm:node/7", "osm:way/8"])
        self.assertEqual(meta["timestamp_osm_base"], "2026-11-20T10:00:00")
        self.assertEqual([p["id"] for p in meta["pominiete"]], ["way/9"])
        res = run(XML, "x.osm")
        self.assertEqual(res["raport"]["osm"]["tagi_bez_odpowiednika"], {"surface": 1})

    def test_adresu_brak_to_ostrzezenie_nie_blad_lokalnie(self):
        res = run(OVERPASS, "o.json")
        self.assertTrue(any(w["pole"] == "miejscowosc" for w in res["raport"]["ostrzezenia"]))

    def test_portal_bez_zmiany_konfiguracji_odrzucone(self):
        from rdzen.licencje import LicencjaBlad
        with self.assertRaises(LicencjaBlad):
            run(OVERPASS, "o.json", cel="portal")

    def test_cudze_dane_w_formacie_osm_z_wlasna_licencja(self):
        res = run(OVERPASS, "o.json", licencja="CC BY 4.0", cel="portal")
        self.assertTrue(res["pochodzenie"]["do_publikacji"])
        self.assertEqual(res["raport"]["pochodzenie"]["licencja"], "CC BY 4.0")
        # dla portalu walidacja jest ścisła: brak adresu to błąd
        self.assertGreater(res["raport"]["odrzucone"], 0)

    def test_zly_format(self):
        with self.assertRaises(ValueError):
            wczytaj(json.dumps({"a": 1}).encode(), "x.json")


if __name__ == "__main__":
    unittest.main()
