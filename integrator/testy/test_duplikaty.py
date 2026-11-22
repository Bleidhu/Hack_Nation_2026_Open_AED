import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

import importer  # noqa: E402
from rdzen.duplikaty import znajdz_kandydatow  # noqa: E402

PRZYKLAD = (HERE.parent / "format_danych" / "przyklady" / "aed_punkty_przyklad.csv").read_bytes()


def wiersz(lat, lon, **kw):
    r = {"szerokosc_geograficzna": str(lat), "dlugosc_geograficzna": str(lon), "nazwa_lokalizacji": "",
         "opis_lokalizacji": "", "kondygnacja": "", "id_zrodlowe": "", "zrodlo_danych": "Źródło",
         "dysponent_nazwa": "", "__wiersz": kw.pop("wiersz", None)}
    r.update(kw)
    return r


# Warszawa: ~0,0000898 stopnia szerokości to 10 m, ~0,000898 to 100 m.
M10 = 0.0000898
M100 = 0.000898


class TestDuplikaty(unittest.TestCase):
    def test_dwa_punkty_10_m_ta_sama_nazwa_kandydat(self):
        a = wiersz(52.23, 21.01, nazwa_lokalizacji="Apteka Pod Orłem", dysponent_nazwa="Miejski Ośrodek")
        b = wiersz(52.23 + M10, 21.01, nazwa_lokalizacji="Apteka Pod Orłem", dysponent_nazwa="Miejski Ośrodek")
        rap = znajdz_kandydatow([a, b])
        self.assertEqual(len(rap["pary"]), 1)
        p = rap["pary"][0]
        self.assertLessEqual(p["odleglosc_m"], 25)
        self.assertEqual(p["pewnosc"], "prawdopodobny")
        self.assertEqual(p["przyczyna"], "ta_sama_instytucja")
        self.assertEqual(p["powody_niskiej_pewnosci"], [])

    def test_rozne_kondygnacje_niska_pewnosc(self):
        a = wiersz(52.23, 21.01, nazwa_lokalizacji="Urząd", kondygnacja="parter")
        b = wiersz(52.23 + M10, 21.01, nazwa_lokalizacji="Urząd", kondygnacja="1")
        p = znajdz_kandydatow([a, b])["pary"][0]
        self.assertEqual(p["pewnosc"], "maloprawdopodobny")
        self.assertIn("różna kondygnacja", p["powody_niskiej_pewnosci"])

    def test_punkty_100_m_od_siebie_bak_kandydata(self):
        a = wiersz(52.23, 21.01, nazwa_lokalizacji="Szkoła")
        b = wiersz(52.23 + M100, 21.01, nazwa_lokalizacji="Szkoła")
        self.assertEqual(znajdz_kandydatow([a, b])["pary"], [])

    def test_ten_sam_rekord_dwa_razy_nie_duplikat(self):
        a = wiersz(52.23, 21.01, id_zrodlowe="A-1")
        b = wiersz(52.23, 21.01, id_zrodlowe="A-1")
        self.assertEqual(znajdz_kandydatow([a, b])["pary"], [])
        # to samo id, ale inne źródło danych → nadal kandydat
        b2 = dict(a, zrodlo_danych="Inne źródło")
        self.assertEqual(len(znajdz_kandydatow([a, b2])["pary"]), 1)

    def test_niskie_podobienstwo_obniza_pewnosc(self):
        a = wiersz(52.23, 21.01, nazwa_lokalizacji="Szkoła podstawowa nr 5")
        b = wiersz(52.23 + M10, 21.01, nazwa_lokalizacji="Stadion miejski")
        p = znajdz_kandydatow([a, b])["pary"][0]
        self.assertEqual(p["pewnosc"], "maloprawdopodobny")
        self.assertTrue(any("podobieństwo" in x for x in p["powody_niskiej_pewnosci"]))

    def test_wiersze_nie_sa_modyfikowane(self):
        a = wiersz(52.23, 21.01, nazwa_lokalizacji="Szkoła")
        b = wiersz(52.23 + M10, 21.01, nazwa_lokalizacji="Szkoła")
        przed = [copy.deepcopy(a), copy.deepcopy(b)]
        znajdz_kandydatow([a, b])
        self.assertEqual([a, b], przed)

    def test_wiersze_bez_wspolrzednych_i_poza_polska_pominiete(self):
        a = wiersz("", "", nazwa_lokalizacji="Szkoła")
        b = wiersz(52.23, 21.01, nazwa_lokalizacji="Szkoła")
        c = wiersz(10.0, 10.0, nazwa_lokalizacji="Szkoła")  # poza Polską
        rap = znajdz_kandydatow([a, b, c])
        self.assertEqual(rap["pary"], [])
        self.assertEqual(rap["wiersze_ze_wspolrzednymi"], 1)

    def test_raport_jest_deterministyczny(self):
        w = [wiersz(52.23 + M10 * i, 21.01, nazwa_lokalizacji=f"Punkt {i}", wiersz=i + 2) for i in range(6)]
        r1 = znajdz_kandydatow(w)
        r2 = znajdz_kandydatow(list(reversed(w)))
        klucz = lambda p: tuple(sorted((p["pochodzenie_a"]["wiersz"], p["pochodzenie_b"]["wiersz"])))
        self.assertEqual([klucz(p) for p in r1["pary"]], sorted(klucz(p) for p in r1["pary"]))
        self.assertEqual(sorted(map(klucz, r1["pary"])), sorted(map(klucz, r2["pary"])))

    def test_podsumowanie_liczy_kategorie(self):
        a = wiersz(52.23, 21.01, nazwa_lokalizacji="Dworzec", dysponent_nazwa="PKP")
        b = wiersz(52.23 + M10, 21.01, nazwa_lokalizacji="Dworzec", dysponent_nazwa="PKP")
        c = wiersz(52.23 + M100, 21.01, nazwa_lokalizacji="Dworzec")
        s = znajdz_kandydatow([a, b, c])["podsumowanie"]
        self.assertEqual(s["kandydaci"], 1)
        self.assertEqual(s["prawdopodobne"], 1)
        self.assertEqual(s["maloprawdopodobne"], 0)
        self.assertEqual(s["ta_sama_instytucja"], 1)
        self.assertEqual(s["rozne_instytucje"], 0)


class TestDuplikatyCLI(unittest.TestCase):
    def test_opcja_duplikaty(self):
        with tempfile.TemporaryDirectory() as d:
            zrodlo = Path(d) / "a.csv"
            zrodlo.write_bytes(PRZYKLAD)
            raport = Path(d) / "dup.json"
            r = subprocess.run([sys.executable, str(HERE / "importer.py"), str(zrodlo), "--licencja", "CC0 1.0",
                                "--duplikaty", str(raport)], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(r.returncode, 0, r.stderr)
            rap = json.loads(raport.read_text("utf-8"))
            self.assertIn("pary", rap)
            self.assertIn("podsumowanie", rap)
            self.assertIn("uwaga", rap)
            self.assertIn("kandydaci na duplikaty", r.stdout)


if __name__ == "__main__":
    unittest.main()
