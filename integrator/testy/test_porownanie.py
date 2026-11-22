import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

from rdzen.porownanie import OZNACZENIE, porownaj  # noqa: E402

WYKAZ_CSV = HERE.parent / "demo" / "wynik" / "zestawienie_aed.csv"
OSM_KRAKOW = (HERE / "dane_przykladowe" / "01_integrator_osm" / "osm_overpass_krakow.json").read_bytes()

M10 = 0.0000898  # ~10 m w stopach szerokości geograficznej


def wiersz_wykazu(lat, lon, **kw):
    r = {"szerokosc_geograficzna": str(lat), "dlugosc_geograficzna": str(lon), "nazwa_lokalizacji": "",
         "opis_lokalizacji": "", "kondygnacja": "", "id_zrodlowe": "W-1", "id_aed": "PL-000001",
         "zrodlo_danych": "Wykaz", "__wiersz": kw.pop("wiersz", None)}
    r.update(kw)
    return r


def wiersz_osm(lat, lon, **kw):
    r = {"szerokosc_geograficzna": str(lat), "dlugosc_geograficzna": str(lon), "nazwa_lokalizacji": "",
         "opis_lokalizacji": "", "kondygnacja": "", "id_zrodlowe": "osm:node/1",
         "zrodlo_url": "https://www.openstreetmap.org/node/1"}
    r.update(kw)
    return r


class TestPorownanie(unittest.TestCase):
    def test_punkt_dopasowany(self):
        w = [wiersz_wykazu(50.06, 19.94, nazwa_lokalizacji="Szpital św. Ludwika")]
        o = [wiersz_osm(50.06 + M10, 19.94, nazwa_lokalizacji="Szpital św. Ludwika", id_zrodlowe="osm:node/7")]
        rap = porownaj(w, o)
        self.assertEqual(len(rap["w_obu"]), 1)
        p = rap["w_obu"][0]
        self.assertEqual(p["wykaz"]["id_aed"], "PL-000001")
        self.assertEqual(p["osm"]["id_zrodlowe"], "osm:node/7")
        self.assertEqual(p["pewnosc"], "duza")
        self.assertLessEqual(p["odleglosc_m"], 25)
        self.assertEqual(rap["tylko_w_wykazie"], [])
        self.assertEqual(rap["tylko_w_osm"], [])

    def test_punkt_tylko_w_wykazie_i_tylko_w_osm(self):
        w = [wiersz_wykazu(50.06, 19.94, nazwa_lokalizacji="Szkoła")]
        o = [wiersz_osm(50.07, 19.95, nazwa_lokalizacji="Inny punkt", id_zrodlowe="osm:node/9")]
        rap = porownaj(w, o)
        self.assertEqual(rap["w_obu"], [])
        self.assertEqual(len(rap["tylko_w_wykazie"]), 1)
        self.assertEqual(len(rap["tylko_w_osm"]), 1)
        self.assertEqual(rap["tylko_w_osm"][0]["id_zrodlowe"], "osm:node/9")
        # minimum do sprawdzenia: bez nazwy i opisu z OSM
        self.assertNotIn("nazwa_lokalizacji", rap["tylko_w_osm"][0])

    def test_punkt_w_promieniu_rozna_kondygnacja(self):
        w = [wiersz_wykazu(50.06, 19.94, kondygnacja="parter")]
        o = [wiersz_osm(50.06 + M10, 19.94, kondygnacja="3")]
        rap = porownaj(w, o)
        self.assertEqual(rap["w_obu"], [])
        self.assertEqual(len(rap["pary_do_sprawdzenia"]), 1)
        self.assertEqual(rap["pary_do_sprawdzenia"][0]["powod"], "różna kondygnacja")
        self.assertEqual(len(rap["tylko_w_wykazie"]), 1)
        self.assertEqual(len(rap["tylko_w_osm"]), 1)

    def test_oznaczenie_licencyjne_w_raporcie(self):
        rap = porownaj([wiersz_wykazu(50.06, 19.94)], [])
        self.assertEqual(rap["oznaczenie"], OZNACZENIE)
        self.assertIn("ODbL", rap["oznaczenie"])
        self.assertIn("nie do publikacji", rap["oznaczenie"])

    def test_wiersze_nie_sa_modyfikowane(self):
        w = [wiersz_wykazu(50.06, 19.94, nazwa_lokalizacji="A")]
        o = [wiersz_osm(50.06 + M10, 19.94, nazwa_lokalizacji="A")]
        przed = [copy.deepcopy(w), copy.deepcopy(o)]
        porownaj(w, o)
        self.assertEqual([w, o], przed)

    def test_podsumowanie_sie_zgadza(self):
        w = [wiersz_wykazu(50.06, 19.94, nazwa_lokalizacji="A"),
             wiersz_wykazu(50.09, 19.99, nazwa_lokalizacji="B")]
        o = [wiersz_osm(50.06 + M10, 19.94, nazwa_lokalizacji="A"),
             wiersz_osm(50.08, 19.97, nazwa_lokalizacji="C"),
             wiersz_osm("", "", nazwa_lokalizacji="bez współrzędnych")]
        s = porownaj(w, o)["podsumowanie"]
        self.assertEqual(s["wiersze_wykazu"], 2)
        self.assertEqual(s["wiersze_osm"], 3)
        self.assertEqual(s["w_obu"], 1)
        self.assertEqual(s["tylko_w_wykazie"], 1)
        self.assertEqual(s["tylko_w_osm"], 2)
        self.assertEqual(s["bez_wspolrzednych"], {"wykaz": 0, "osm": 1})

    def test_dopasowanie_jedno_do_jednego_najblizszym(self):
        # dwa wiersze wykazu i jeden punkt OSM: dopasowany bliższy, dalszy zostaje w wykazie
        w = [wiersz_wykazu(50.06, 19.94, nazwa_lokalizacji="A", id_zrodlowe="W-a"),
             wiersz_wykazu(50.06 + 2 * M10, 19.94, nazwa_lokalizacji="A", id_zrodlowe="W-b")]
        o = [wiersz_osm(50.06 + M10, 19.94, nazwa_lokalizacji="A")]
        rap = porownaj(w, o)
        self.assertEqual(len(rap["w_obu"]), 1)
        self.assertEqual(len(rap["tylko_w_wykazie"]), 1)


class TestPorownanieCLI(unittest.TestCase):
    def test_porownanie_z_przykladow_offline(self):
        self.assertTrue(WYKAZ_CSV.exists(), "brak demo/wynik/zestawienie_aed.csv – uruchom demo/build_demo.py")
        with tempfile.TemporaryDirectory() as d:
            osm = Path(d) / "krakow.json"
            osm.write_bytes(OSM_KRAKOW)
            raport = Path(d) / "porownanie.json"
            r = subprocess.run([sys.executable, str(HERE / "importer.py"), str(WYKAZ_CSV),
                                "--porownaj-z-osm", str(osm), "--raport", str(raport)],
                               capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(r.returncode, 0, r.stderr)
            rap = json.loads(raport.read_text("utf-8"))
            s = rap["podsumowanie"]
            self.assertEqual(s["wiersze_wykazu"] + 0, s["w_obu"] + s["tylko_w_wykazie"])
            self.assertEqual(s["wiersze_osm"], s["w_obu"] + s["tylko_w_osm"])
            self.assertIn("ODbL", rap["oznaczenie"])
            self.assertIn("tylko w OSM", r.stdout)

    def test_bez_raportu_odmowa(self):
        with tempfile.TemporaryDirectory() as d:
            osm = Path(d) / "krakow.json"
            osm.write_bytes(OSM_KRAKOW)
            r = subprocess.run([sys.executable, str(HERE / "importer.py"), str(WYKAZ_CSV),
                                "--porownaj-z-osm", str(osm)], capture_output=True, text=True, encoding="utf-8")
            self.assertNotEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
