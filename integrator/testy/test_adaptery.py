import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import importer  # noqa: E402
from adaptery.gdansk import wczytaj as gdansk_wczytaj  # noqa: E402
from adaptery.warszawa import wczytaj as warszawa_wczytaj  # noqa: E402

DOKUMENTACJA = (ROOT / "references" / "dane_gov_pl_aed" / "warszawa_api" / "przyklad_wywolania.json").read_bytes()
GDANSK = (ROOT / "references" / "dane_gov_pl_aed" / "gdansk_ztm" / "zasob_31843_baza_pojazdow.json").read_bytes()

# mała fikstura wycięta z przykładu odpowiedzi (dokumentacja API Warszawy)
FEATURE = {
    "geometry": {"coordinates": [[21.0148748892902, 52.2086170695684]], "type": "Point"},
    "properties": {
        "defibrillator_id": "622",
        "device_access_description": "Poniedziałek: godz. 8:00-18:00; Wtorek-Piątek: godz. 8:00-16:00",
        "device_availability": "Ograniczona",
        "device_location": "Wewnątrz budynku",
        "device_manufacturer": "Medtronic",
        "device_public_access": "Publiczny",
        "location_building": "25/27",
        "location_city": "Warszawa",
        "location_description": "Przy wejściu na półpiętrze.",
        "location_object_name": "Urząd Dzielnicy Mokotów m.st. Warszawy",
        "location_postcode": "02-517",
        "location_street": "Rakowiecka",
    },
}


class TestWarszawa(unittest.TestCase):
    def test_odpowiedz_api_mapuje_sie_na_wzorzec_v2(self):
        res = importer.run(json.dumps([FEATURE]).encode("utf-8"), "odpowiedz.json", preset="warszawa")
        self.assertEqual(res["raport"]["poprawne"], 1)
        r = res["rekordy"][0]
        self.assertEqual(r["id_zrodlowe"], "622")
        self.assertEqual(r["nazwa_lokalizacji"], "Urząd Dzielnicy Mokotów m.st. Warszawy")
        self.assertEqual(r["miejscowosc"], "Warszawa")
        self.assertEqual(r["nazwa_ulicy"], "Rakowiecka")
        self.assertEqual(r["numer_budynku"], "25/27")
        self.assertEqual(r["kod_pocztowy"], "02-517")
        self.assertEqual(r["szerokosc_geograficzna"], "52.2086170695684")
        self.assertEqual(r["dlugosc_geograficzna"], "21.0148748892902")
        self.assertEqual(r["wewnatrz_budynku"], "true")
        self.assertEqual(r["typ_dostepu"], "publiczny")
        self.assertEqual(r["dostepny_24_7"], "false")
        self.assertEqual(r["godziny_dostepnosci"], "Poniedziałek: godz. 8:00-18:00; Wtorek-Piątek: godz. 8:00-16:00")
        self.assertEqual(r["producent"], "Medtronic")
        self.assertEqual(r["opis_lokalizacji"], "Przy wejściu na półpiętrze.")

    def test_licencja_i_dysponent_podane_jawnie(self):
        res = importer.run(json.dumps([FEATURE]).encode("utf-8"), "o.json", preset="warszawa")
        self.assertEqual(res["pochodzenie"]["licencja"], "CC BY 4.0")
        self.assertTrue(res["pochodzenie"]["do_publikacji"])
        self.assertEqual(res["rekordy"][0]["dysponent_nazwa"], "Urząd m.st. Warszawy")
        self.assertEqual(res["rekordy"][0]["zrodlo_danych"], "rejestr_publiczny")

    def test_przyklad_z_dokumentacji(self):
        rows, meta = warszawa_wczytaj(DOKUMENTACJA, "przyklad_wywolania.json")
        self.assertEqual(meta["format"], "warszawa-api")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["defibrillator_id"], "622")
        self.assertNotIn("attachment", rows[0])  # zdjęcie Base64 pomijane

    def test_brakujace_pola_zostaja_puste(self):
        f = {"geometry": {"coordinates": [21.0, 52.2], "type": "Point"},
             "properties": {"defibrillator_id": "1", "location_object_name": "Punkt",
                             "location_city": "Warszawa", "location_description": "Opis",
                             "device_public_access": "Publiczny", "device_availability": "Ograniczona"}}
        r = importer.run(json.dumps([f]).encode("utf-8"), "o.json", preset="warszawa")["rekordy"][0]
        self.assertEqual(r["nazwa_ulicy"], "")
        self.assertEqual(r["kod_pocztowy"], "")
        self.assertEqual(r["producent"], "")

    def test_nierozpoznany_plik_odmowa(self):
        with self.assertRaises(ValueError):
            warszawa_wczytaj(b'{"inny": "format"}', "x.json")


class TestGdansk(unittest.TestCase):
    def test_nie_tworzy_wierszy_zwraca_statystyke(self):
        res = importer.run(GDANSK, "baza_pojazdow.json", preset="gdansk")
        self.assertEqual(res["rekordy"], [])
        g = res["raport"]["gdansk"]
        self.assertEqual(g["pojazdy"], 503)
        self.assertEqual(g["pojazdy_z_aed"], 278)
        self.assertEqual(g["rozbicie_typow"], {"Autobus": 156, "Tramwaj": 122})
        self.assertIn("flotowe", g["powod"])
        self.assertIn("nie ma kolumny pojazdu", g["powod"])

    def test_licencja_cc_by_dla_statystyki(self):
        res = importer.run(GDANSK, "b.json", preset="gdansk")
        self.assertEqual(res["pochodzenie"]["licencja"], "CC BY 4.0")
        self.assertTrue(res["pochodzenie"]["do_publikacji"])

    def test_nierozpoznany_plik_odmowa(self):
        with self.assertRaises(ValueError):
            gdansk_wczytaj(b'{"results": []}', "x.json")


class TestBezSieciITokenow(unittest.TestCase):
    """Kryterium: nigdzie nie ma tokenu ani wywołania sieci."""

    ZAKAZANE = ("requests", "urllib", "http.client", "socket", "urlopen", "Authorization", "token_uzytkownika")

    def test_adaptery_nie_lacza_sie_z_siecia(self):
        for p in sorted((HERE / "adaptery").glob("*.py")):
            s = p.read_text("utf-8")
            for z in self.ZAKAZANE:
                self.assertNotIn(z, s, f"{p.name}: {z}")


class TestAdapteryCLI(unittest.TestCase):
    def test_cli_gdansk(self):
        with tempfile.TemporaryDirectory() as d:
            zrodlo = Path(d) / "baza.json"
            zrodlo.write_bytes(GDANSK)
            raport = Path(d) / "r.json"
            r = subprocess.run([sys.executable, str(HERE / "importer.py"), str(zrodlo), "--preset", "gdansk",
                                "--raport", str(raport)], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("pojazdy 503, z AED 278", r.stdout)
            self.assertIn("wierszy punktowych: 0", r.stdout)
            g = json.loads(raport.read_text("utf-8"))["gdansk"]
            self.assertEqual(g["pojazdy_z_aed"], 278)

    def test_cli_warszawa(self):
        with tempfile.TemporaryDirectory() as d:
            zrodlo = Path(d) / "odpowiedz.json"
            zrodlo.write_bytes(json.dumps([FEATURE]).encode("utf-8"))
            wyjscie = Path(d) / "w.csv"
            r = subprocess.run([sys.executable, str(HERE / "importer.py"), str(zrodlo), "--preset", "warszawa",
                                "--wyjscie", str(wyjscie)], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("Urząd Dzielnicy Mokotów m.st. Warszawy", wyjscie.read_text("utf-8"))


if __name__ == "__main__":
    unittest.main()
