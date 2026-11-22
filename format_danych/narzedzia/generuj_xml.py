"""Generuje minimalne przykłady XML zewnętrznego dostawcy (fikcyjne dane) do format_danych/przyklady/xml/.

aed_poprawny.xml  : 6 rekordów zgodnych z aed_punkty.xsd,
aed_bledny.xml    : ten sam plik z trzema celowymi błędami (brak pola wymaganego, wartość spoza słownika,
                    współrzędna tekstem).
Uruchomienie: python format_danych/narzedzia/generuj_xml.py (tylko biblioteka standardowa).
"""
from pathlib import Path
from xml.sax.saxutils import escape

CEL = Path(__file__).resolve().parent.parent / "przyklady" / "xml"
DYSPONENT = {
    "dysponent_nazwa": "Miejski Zakład Przykład (PRZYKŁAD)",
    "dysponent_regon": "123456785",
    "zrodlo_danych": "dysponent",
    "zrodlo_url": "https://dostawca.example.pl/aed",
    "data_aktualizacji": "2026-11-20T08:00:00",
}
# (id, nazwa, miejscowość, ulica, nr, kod, szer., dł., opis, wewnątrz, typ_dostępu, 24/7, status)
REKORDY = [
    ("OL-001", "Urząd Miasta – hol główny", "Olsztyn", "Plac Jana Pawła II", "1", "10-101", "53.778420", "20.480120",
     "Parter, hol główny, na lewo od portierni", "true", "publiczny", "false", "sprawny"),
    ("OL-002", "Dworzec – hala odpraw", "Olsztyn", "Partyzantów", "6", "10-402", "53.783060", "20.493770",
     "Hala odpraw, przy kasach biletowych", "true", "publiczny", "true", "sprawny"),
    ("OL-003", "Szkoła Podstawowa nr 7 – sala gimnastyczna", "Olsztyn", "Szkolna", "5A", "10-502", "53.790110", "20.470950",
     "Korytarz przy wejściu do sali gimnastycznej", "true", "ograniczony", "false", "sprawny"),
    ("EL-001", "Hala sportowa – wejście główne", "Elbląg", "Moniuszki", "2", "82-300", "54.156610", "19.404270",
     "Na zewnątrz, szafka przy wejściu głównym", "false", "publiczny", "true", "w_serwisie"),
    ("EL-002", "Biblioteka Miejska – recepcja", "Elbląg", "Rynek Staromiejski", "1", "82-300", "54.159800", "19.402500",
     "Parter, recepcja", "true", "ograniczony", "false", "nieznany"),
    ("EL-003", "Basen miejski – kasa", "Elbląg", "Agrykola", "9", "82-300", "54.171230", "19.407880",
     "Przy kasie, w szafce z alarmem", "true", "ograniczony", "false", "sprawny"),
]
POLA = ["id_zrodlowe", "nazwa_lokalizacji", "miejscowosc", "nazwa_ulicy", "numer_budynku", "kod_pocztowy",
        "szerokosc_geograficzna", "dlugosc_geograficzna", "opis_lokalizacji", "wewnatrz_budynku",
        "typ_dostepu", "dostepny_24_7", "status_urzadzenia"]


def rekord(r):
    pola = dict(zip(POLA, r))
    pola.update(DYSPONENT)
    return "  <aed>\n" + "".join(f"    <{k}>{escape(v)}</{k}>\n" for k, v in pola.items()) + "  </aed>\n"


def plik(rekordy):
    return '<?xml version="1.0" encoding="UTF-8"?>\n<wykaz>\n' + "".join(rekordy) + "</wykaz>\n"


if __name__ == "__main__":
    CEL.mkdir(parents=True, exist_ok=True)
    dobre = [rekord(r) for r in REKORDY]
    (CEL / "aed_poprawny.xml").write_text(plik(dobre), encoding="utf-8", newline="\n")
    zle = list(dobre)
    zle[1] = zle[1].replace("    <typ_dostepu>publiczny</typ_dostepu>\n", "")  # brak pola wymaganego
    zle[2] = zle[2].replace("<status_urzadzenia>sprawny<", "<status_urzadzenia>dziala<")  # spoza słownika
    zle[3] = zle[3].replace("<szerokosc_geograficzna>54.156610<", "<szerokosc_geograficzna>pięćdziesiąt cztery<")  # tekst
    (CEL / "aed_bledny.xml").write_text(plik(zle), encoding="utf-8", newline="\n")
    print("Zapisano", CEL)
