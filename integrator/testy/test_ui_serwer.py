import base64
import http.client
import importlib.util
import json
import sys
import threading
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

_spec = importlib.util.spec_from_file_location("serwer_ui", HERE / "ui" / "serwer.py")
serwer = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(serwer)

PRZYKLAD = (ROOT / "format_danych" / "przyklady" / "aed_punkty_przyklad.csv").read_bytes()
WYKAZ = (ROOT / "demo" / "wynik" / "zestawienie_aed.csv").read_bytes()
OSM = (HERE / "dane_przykladowe" / "01_integrator_osm" / "osm_overpass_krakow.json").read_bytes()
INDEX_HTML = (HERE / "ui" / "index.html").read_text("utf-8")

MINIMUM = {"nazwa_lokalizacji": "Apteka", "miejscowosc": "Legionowo", "opis_lokalizacji": "Przy kasie",
           "typ_dostepu": "publiczny", "dostepny_24_7": "true",
           "szerokosc_geograficzna": "52.4011", "dlugosc_geograficzna": "20.9284"}


class SerwerTestCase(unittest.TestCase):
    httpd = None
    port = None

    @classmethod
    def setUpClass(cls):
        cls.httpd = serwer.ThreadingHTTPServer((serwer.HOST, 0), serwer.Handler)
        cls.port = cls.httpd.server_address[1]
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def zadanie(self, metoda, sciezka, cialo=None):
        c = http.client.HTTPConnection(serwer.HOST, self.port, timeout=15)
        naglowki = {"Content-Type": "application/json"} if cialo is not None else {}
        c.request(metoda, sciezka, body=json.dumps(cialo) if cialo is not None else None, headers=naglowki)
        r = c.getresponse()
        dane = r.read()
        c.close()
        return r.status, r.getheader("Content-Type"), dane

    def json(self, metoda, sciezka, cialo=None):
        kod, _, dane = self.zadanie(metoda, sciezka, cialo)
        return kod, json.loads(dane.decode("utf-8"))


class TestStrona(SerwerTestCase):
    def test_index_odpowiada_200_z_charset(self):
        kod, typ, dane = self.zadanie("GET", "/")
        self.assertEqual(kod, 200)
        self.assertIn("text/html", typ)
        self.assertIn("charset=utf-8", typ)
        self.assertIn("Integrator AED", dane.decode("utf-8"))

    def test_nieznana_strona_404(self):
        kod, c = self.json("GET", "/nie-ma")
        self.assertEqual(kod, 404)
        self.assertIn("blad", c)

    def test_strona_bez_zasobow_zewnetrznych(self):
        # offline: żaden atrybut src/href ani url() nie może wskazywać na internet
        for fragment in ('src="http', "src='http", 'href="http', "href='http", "url(http", "url('http"):
            self.assertNotIn(fragment, INDEX_HTML, fragment)
        self.assertIn("data:font", INDEX_HTML)  # czcionka osadzona w pliku


class TestApiImport(SerwerTestCase):
    def test_import_csv_z_licencja_dla_portalu(self):
        kod, c = self.json("POST", "/api/import",
                           {"plik": base64.b64encode(PRZYKLAD).decode(), "plik_nazwa": "a.csv",
                            "cel": "portal", "licencja": "CC0 1.0"})
        self.assertEqual(kod, 200)
        self.assertEqual(c["liczba_wierszy"], 8)
        self.assertTrue(c["pochodzenie"]["do_publikacji"])
        self.assertTrue(c["csv"].startswith("id_zrodlowe,nazwa_lokalizacji"))
        self.assertIn("duplikaty", c)
        self.assertIn("mapowanie", c)

    def test_import_osm_dla_portalu_odmowa(self):
        kod, c = self.json("POST", "/api/import",
                           {"plik": base64.b64encode(OSM).decode(), "plik_nazwa": "osm.json",
                            "preset": "osm", "cel": "portal"})
        self.assertEqual(kod, 400)
        self.assertIn("Odmowa", c["blad"])

    def test_import_osm_lokalnie_bez_csv_wynikowego(self):
        kod, c = self.json("POST", "/api/import",
                           {"plik": base64.b64encode(OSM).decode(), "plik_nazwa": "osm.json",
                            "preset": "osm", "cel": "lokalny"})
        self.assertEqual(kod, 200)
        self.assertFalse(c["pochodzenie"]["do_publikacji"])
        self.assertIsNone(c["csv"])  # pobranie CSV tylko, gdy cel portal przechodzi kontrolę
        self.assertEqual(c["mapowanie"]["typ_zrodla"], "osm")

    def test_import_gdansk_zwroci_statystyke(self):
        gdansk = (ROOT / "references" / "dane_gov_pl_aed" / "gdansk_ztm"
                  / "zasob_31843_baza_pojazdow.json").read_bytes()
        kod, c = self.json("POST", "/api/import",
                           {"plik": base64.b64encode(gdansk).decode(), "plik_nazwa": "baza.json",
                            "preset": "gdansk", "cel": "portal"})
        self.assertEqual(kod, 200)
        self.assertEqual(c["raport"]["gdansk"]["pojazdy_z_aed"], 278)

    def test_import_zly_format(self):
        kod, c = self.json("POST", "/api/import",
                           {"plik": base64.b64encode(b"to nie jest tablica").decode(),
                            "plik_nazwa": "x.json", "cel": "portal"})
        self.assertEqual(kod, 400)

    def test_import_bez_pliku(self):
        kod, c = self.json("POST", "/api/import", {"cel": "portal"})
        self.assertEqual(kod, 400)

    def test_plik_ponad_limit_413(self):
        duzy = base64.b64encode(b"x" * (serwer.LIMIT_BAJTOW + 1024)).decode()
        kod, c = self.json("POST", "/api/import", {"plik": duzy, "plik_nazwa": "duzy.csv", "cel": "portal"})
        self.assertEqual(kod, 413)


class TestApiPorownaj(SerwerTestCase):
    def test_porownanie_wykazu_z_osm(self):
        kod, c = self.json("POST", "/api/porownaj",
                           {"wykaz": base64.b64encode(WYKAZ).decode(),
                            "osm": base64.b64encode(OSM).decode(), "osm_nazwa": "osm.json"})
        self.assertEqual(kod, 200)
        s = c["podsumowanie"]
        wiersze = len([w for w in WYKAZ.decode("utf-8").splitlines()[1:] if w.strip()])
        self.assertEqual(s["wiersze_wykazu"], wiersze)
        self.assertEqual(s["w_obu"], 0)
        self.assertIn("ODbL", c["oznaczenie"])

    def test_klucze_odpowiedzi_zgodne_z_tabelami_strony(self):
        # tabele zakładki „Porównanie z OSM” czytają te pola; pusta kolumna id lub nazwy oznacza rozjazd kluczy
        kod, c = self.json("POST", "/api/porownaj",
                           {"wykaz": base64.b64encode(WYKAZ).decode(),
                            "osm": base64.b64encode(OSM).decode(), "osm_nazwa": "osm.json"})
        self.assertEqual(kod, 200)
        self.assertTrue(c["tylko_w_wykazie"])
        for t in c["tylko_w_wykazie"]:
            for pole in ("id_aed", "id_zrodlowe", "nazwa_lokalizacji", "zrodlo_danych"):
                self.assertIn(pole, t)
            self.assertTrue(t["id_aed"] or t["id_zrodlowe"])
            self.assertTrue(t["nazwa_lokalizacji"])
        for t in c["tylko_w_osm"]:
            for pole in ("id_zrodlowe", "zrodlo_url", "szerokosc_geograficzna", "dlugosc_geograficzna"):
                self.assertIn(pole, t)
        for fragment in ("t.id_aed || t.id_zrodlowe", "t.nazwa_lokalizacji", "t.zrodlo_danych",
                         "p.wykaz.id_aed || p.wykaz.id_zrodlowe", "t.zrodlo_url"):
            self.assertIn(fragment, INDEX_HTML, fragment)

    def test_porownanie_bez_pliku_odmowa(self):
        kod, c = self.json("POST", "/api/porownaj", {"wykaz": base64.b64encode(WYKAZ).decode()})
        self.assertEqual(kod, 400)


class TestApiDodaj(SerwerTestCase):
    def test_dodaj_nowy_plik(self):
        kod, c = self.json("POST", "/api/dodaj", {"pola": MINIMUM, "prefiks": "LEG"})
        self.assertEqual(kod, 200)
        self.assertEqual(c["bledy"], [])
        self.assertEqual(c["rekord"]["id_zrodlowe"], "LEG-0001")
        self.assertTrue(c["nowy_plik"].startswith("id_zrodlowe,nazwa_lokalizacji"))
        self.assertIn("Legionowo", c["nowy_plik"])

    def test_dodaj_do_istniejacego_pliku(self):
        istniejacy = base64.b64encode(PRZYKLAD).decode()
        kod, c = self.json("POST", "/api/dodaj", {"plik": istniejacy, "pola": MINIMUM, "prefiks": "LEG"})
        self.assertEqual(kod, 200)
        stare = PRZYKLAD.decode("utf-8")
        self.assertTrue(c["nowy_plik"].startswith(stare))  # stary plik nietknięty
        dodatkowe = 1 if stare.endswith("\r\n") else 2  # ewentualne domknięcie linii + nowy wiersz
        self.assertEqual(c["nowy_plik"].count("\r\n"), stare.count("\r\n") + dodatkowe)
        self.assertIn("LEG-0001", c["nowy_plik"])

    def test_dodaj_bez_minimum(self):
        kod, c = self.json("POST", "/api/dodaj", {"pola": {"nazwa_lokalizacji": "Tylko nazwa"}})
        self.assertEqual(kod, 200)
        self.assertTrue(c["bledy"])
        self.assertIsNone(c["nowy_plik"])

    def test_dodaj_kandydat_wymaga_potwierdzenia(self):
        pola_a = dict(MINIMUM)
        pola_b = dict(MINIMUM, id_zrodlowe="LEG-0002", szerokosc_geograficzna="52.40119")
        pierwszy = self.json("POST", "/api/dodaj", {"pola": pola_a, "prefiks": "LEG"})[1]
        plik = base64.b64encode(pierwszy["nowy_plik"].encode("utf-8")).decode()
        kod, c = self.json("POST", "/api/dodaj", {"plik": plik, "pola": pola_b, "prefiks": "LEG"})
        self.assertEqual(kod, 200)
        self.assertEqual(c["bledy"], [])
        self.assertTrue(c["kandydaci"])
        self.assertTrue(c.get("wymaga_potwierdzenia"))
        self.assertIsNone(c["nowy_plik"])
        # po potwierdzeniu zapis następuje
        kod2, c2 = self.json("POST", "/api/dodaj",
                             {"plik": plik, "pola": pola_b, "prefiks": "LEG", "wymus": True})
        self.assertEqual(kod2, 200)
        self.assertTrue(c2["nowy_plik"])
        self.assertIn("LEG-0002", c2["nowy_plik"])


class TestBezZapisuNaDysku(unittest.TestCase):
    def test_serwer_nie_zapisuje_na_dysku(self):
        zrodlo = (HERE / "ui" / "serwer.py").read_text("utf-8")
        for fragment in ("open(", "write_text", "write_bytes", "os.replace"):
            self.assertNotIn(fragment, zrodlo, fragment)
        self.assertIn(".read_bytes()", zrodlo)  # czyta tylko index.html


if __name__ == "__main__":
    unittest.main()
