import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

from rdzen.rekord import (RekordBlad, dopisz, propozycja_id, sprawdz_rekord, wczytaj_istniejace, zbuduj)  # noqa: E402
from rdzen.wzorzec import FIELDS  # noqa: E402
from rdzen.zapis import to_csv  # noqa: E402

MINIMUM = {"nazwa_lokalizacji": "Apteka Pod Orłem", "miejscowosc": "Legionowo",
           "szerokosc_geograficzna": "52,4011", "dlugosc_geograficzna": "20.9284",
           "opis_lokalizacji": "Przy kasie", "typ_dostepu": "publiczny", "dostepny_24_7": "TAK"}


def rekord(**nadpisanie):
    pola = dict(MINIMUM)
    pola.update(nadpisanie)
    return zbuduj(pola, prefiks="LEG", istniejace_id=set())


class TestZbuduj(unittest.TestCase):
    def test_minimum_buduje_rekord_z_domyslnymi(self):
        r = rekord()
        self.assertEqual(r["nazwa_lokalizacji"], "Apteka Pod Orłem")
        self.assertEqual(r["dostepny_24_7"], "true")  # TAK znormalizowane
        self.assertEqual(r["szerokosc_geograficzna"], "52.4011")  # przecinek dziesiętny
        self.assertEqual(r["id_zrodlowe"], "LEG-0001")  # propozycja zamiast losowego id
        self.assertEqual(r["status_urzadzenia"], "nieznany")
        self.assertEqual(r["poziom_weryfikacji"], "niezweryfikowany")
        self.assertRegex(r["data_aktualizacji"], r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")

    def test_id_dostawcy_ma_pierwszenstwo(self):
        self.assertEqual(rekord(id_zrodlowe="MOJ-17")["id_zrodlowe"], "MOJ-17")

    def test_propozycja_id_liczy_dalej_wolny_numer(self):
        self.assertEqual(propozycja_id("MOJ", {"MOJ-0001", "MOJ-0003"}), "MOJ-0002")
        self.assertEqual(propozycja_id("MOJ", {"MOJ-0001", "MOJ-0002"}), "MOJ-0003")

    def test_aliasy_statusu_z_aplikacji_mobilnej(self):
        self.assertEqual(rekord(status_urzadzenia="sprawny")["status_urzadzenia"], "sprawny")
        self.assertEqual(rekord(status_urzadzenia="uzyty")["status_urzadzenia"], "niesprawny")
        self.assertEqual(rekord(status_urzadzenia="w_serwisie")["status_urzadzenia"], "w_serwisie")
        self.assertEqual(rekord(status_urzadzenia="wymaga_serwisu")["status_urzadzenia"], "w_serwisie")

    def test_nieznane_pole_odmowa(self):
        with self.assertRaises(RekordBlad):
            zbuduj({"nazwa_lokalizacji": "X", "pole_znikad": "1"})


class TestSprawdzRekord(unittest.TestCase):
    def test_brak_minimum_odrzucony_z_powodem(self):
        w = sprawdz_rekord(rekord(nazwa_lokalizacji="", miejscowosc=""), [])
        self.assertTrue(w["bledy"])
        self.assertTrue(any(e["pole"] == "nazwa_lokalizacji" and "pole wymagane" in e["komunikat"] for e in w["bledy"]))
        self.assertTrue(any(e["pole"] == "miejscowosc" and "pole wymagane" in e["komunikat"] for e in w["bledy"]))

    def test_wspolrzedne_poza_polska_odrzucone(self):
        w = sprawdz_rekord(rekord(szerokosc_geograficzna="10.0", dlugosc_geograficzna="10.0"), [])
        self.assertTrue(any("poza zakresem" in e["komunikat"] for e in w["bledy"]))

    def test_wartosc_spoza_slownika_odrzucona(self):
        w = sprawdz_rekord(rekord(typ_dostepu="dla wszystkich"), [])
        self.assertTrue(any("wartość spoza słownika" in e["komunikat"] for e in w["bledy"]))

    def test_duplikat_id_w_pliku_odrzucony(self):
        istniejace = [{"id_zrodlowe": "MOJ-17", "szerokosc_geograficzna": "52.4011",
                       "dlugosc_geograficzna": "20.9284", "zrodlo_danych": ""}]
        w = sprawdz_rekord(rekord(id_zrodlowe="MOJ-17"), istniejace)
        self.assertTrue(any("identyfikator już istnieje" in e["komunikat"] for e in w["bledy"]))

    def test_kandydat_na_duplikat_wzgledem_istniejacych(self):
        istniejace = [{"id_zrodlowe": "LEG-0001", "nazwa_lokalizacji": "Apteka Pod Orłem",
                       "szerokosc_geograficzna": "52.4011", "dlugosc_geograficzna": "20.9284",
                       "zrodlo_danych": "LEG"}]
        nowy = rekord(id_zrodlowe="LEG-0002", szerokosc_geograficzna="52.40119", dlugosc_geograficzna="20.9284")
        w = sprawdz_rekord(nowy, istniejace)
        self.assertEqual(w["bledy"], [])
        self.assertEqual(len(w["kandydaci"]), 1)
        self.assertEqual(w["kandydaci"][0]["pochodzenie_a"]["id_zrodlowe"], "LEG-0001")

    def test_ten_sam_punkt_inna_kondygnacja_niezmienia_bledow(self):
        istniejace = [{"id_zrodlowe": "LEG-0001", "nazwa_lokalizacji": "Apteka", "kondygnacja": "parter",
                       "szerokosc_geograficzna": "52.4011", "dlugosc_geograficzna": "20.9284", "zrodlo_danych": "LEG"}]
        nowy = rekord(id_zrodlowe="LEG-0002", kondygnacja="1", szerokosc_geograficzna="52.4011",
                      dlugosc_geograficzna="20.9284")
        w = sprawdz_rekord(nowy, istniejace)
        self.assertEqual(len(w["kandydaci"]), 1)
        self.assertEqual(w["kandydaci"][0]["pewnosc"], "maloprawdopodobny")


class TestDopisz(unittest.TestCase):
    def test_dopisanie_zmienia_tyko_jeden_wiersz(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "aed.csv"
            r1 = rekord(id_zrodlowe="LEG-0001")
            r2 = rekord(id_zrodlowe="LEG-0002", nazwa_lokalizacji="Szkoła nr 2")
            p.write_text(to_csv([r1, r2]), "utf-8", newline="")
            przed = p.read_bytes()
            dopisz(p, rekord(id_zrodlowe="LEG-0003", nazwa_lokalizacji="Dom kultury"))
            po = p.read_bytes()
            self.assertTrue(po.startswith(przed))  # reszta pliku bajt w bajt
            self.assertEqual(po[len(przed):].count(b"\r\n"), 1)  # dokładnie jeden nowy wiersz
            wiersze = wczytaj_istniejace(p)
            self.assertEqual(len(wiersze), 3)
            self.assertEqual(wiersze[-1]["id_zrodlowe"], "LEG-0003")

    def test_nowy_plik_dostaje_naglowek(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "nowy.csv"
            dopisz(p, rekord(id_zrodlowe="LEG-0001"))
            tekst = p.read_bytes().decode("utf-8")
            self.assertEqual(tekst.splitlines()[0], ",".join(FIELDS))
            self.assertEqual(len(wczytaj_istniejace(p)), 1)

    def test_plik_bez_koncowego_crlf_nie_psuje_sie(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "aed.csv"
            r1 = rekord(id_zrodlowe="LEG-0001")
            tekst = to_csv([r1]).rstrip("\r\n")  # bez końcowego CRLF
            p.write_bytes(tekst.encode("utf-8"))
            dopisz(p, rekord(id_zrodlowe="LEG-0002"))
            self.assertEqual(len(wczytaj_istniejace(p)), 2)


class TestDodajCLI(unittest.TestCase):
    def test_dodaj_nowy_plik(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "nowy.csv"
            r = subprocess.run([sys.executable, str(HERE / "importer.py"), "dodaj", str(p),
                                "--nazwa_lokalizacji", "Apteka Pod Orłem", "--miejscowosc", "Legionowo",
                                "--opis_lokalizacji", "Przy kasie", "--typ_dostepu", "publiczny",
                                "--dostepny_24_7", "true", "--szerokosc_geograficzna", "52.4011",
                                "--dlugosc_geograficzna", "20.9284", "--status_urzadzenia", "uzyty",
                                "--prefiks-id", "LEG"], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("dopisano LEG-0001", r.stdout)
            w = wczytaj_istniejace(p)
            self.assertEqual(len(w), 1)
            self.assertEqual(w[0]["status_urzadzenia"], "niesprawny")  # alias z aplikacji mobilnej

    def test_dodaj_bez_minimum_odmowa(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "nowy.csv"
            r = subprocess.run([sys.executable, str(HERE / "importer.py"), "dodaj", str(p),
                                "--nazwa_lokalizacji", "Tylko nazwa"], capture_output=True, text=True, encoding="utf-8")
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("rekord odrzucony", r.stdout + r.stderr)
            self.assertFalse(p.exists())  # nic nie zapisano

    def test_dodaj_duplikat_wymaga_potwierdzenia(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "aed.csv"
            subprocess.run([sys.executable, str(HERE / "importer.py"), "dodaj", str(p),
                            "--nazwa_lokalizacji", "Apteka", "--miejscowosc", "Legionowo",
                            "--opis_lokalizacji", "Przy kasie", "--typ_dostepu", "publiczny",
                            "--dostepny_24_7", "true", "--szerokosc_geograficzna", "52.4011",
                            "--dlugosc_geograficzna", "20.9284", "--prefiks-id", "LEG"],
                           capture_output=True, encoding="utf-8")
            # drugi punkt 10 m od pierwszego, ta sama nazwa → kandydat bez zapisu
            r = subprocess.run([sys.executable, str(HERE / "importer.py"), "dodaj", str(p),
                                "--nazwa_lokalizacji", "Apteka", "--miejscowosc", "Legionowo",
                                "--opis_lokalizacji", "Przy kasie", "--typ_dostepu", "publiczny",
                                "--dostepny_24_7", "true", "--szerokosc_geograficzna", "52.40119",
                                "--dlugosc_geograficzna", "20.9284", "--prefiks-id", "LEG"],
                           capture_output=True, text=True, encoding="utf-8")
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("możliwy duplikat", r.stdout)
            self.assertIn("--tak", r.stdout + r.stderr)
            self.assertEqual(len(wczytaj_istniejace(p)), 1)
            # po potwierdzeniu zapis następuje
            r2 = subprocess.run(r.args + ["--tak"], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(r2.returncode, 0, r2.stderr)
            self.assertEqual(len(wczytaj_istniejace(p)), 2)


if __name__ == "__main__":
    unittest.main()
