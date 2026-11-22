"""Wpisuje adresy wersji live (tunel ngrok) do WERSJA_LIVE.md. Tylko biblioteka standardowa, Python 3.8+.

    python demo/ustaw_link_live.py --portal https://xxxx.ngrok-free.dev --sprawdz   # cała wersja live pod jednym adresem
    python demo/ustaw_link_live.py --prototyp https://aaaa.ngrok-free.app --dostawca https://bbbb.ngrok-free.app
    python demo/ustaw_link_live.py https://xxxx.ngrok-free.app                      # sam prototyp (jak dawniej)
    python demo/ustaw_link_live.py --wyczysc                                        # powrót do placeholderów

--portal to adres bramy demo/brama_live.py wystawionej przez ngrok (jeden adres dla wszystkiego): frontend portalu
z Wykazem AED, API pod /api, panel pod /admin/, prototyp pod /demo/index.html, serwer dostawcy pod /dostawca.
Gdy podano --portal, adresy prototypu i dostawcy skrypt wylicza sam (chyba że podano je jawnie).
Numery zbioru i zasobu Wykazu AED skrypt odczytuje z /api/aed-aggregated (gdy się nie uda: --zbior, --zasob).
Przyjmowane są tylko adresy https. Skrypt zmienia wyłącznie blok między znacznikami w WERSJA_LIVE.md.
"""
import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
PLIK = ROOT / "WERSJA_LIVE.md"
POCZATEK = "<!-- POCZATEK BLOKU ADRESOW (generuje demo/ustaw_link_live.py, nie edytować ręcznie) -->"
KONIEC = "<!-- KONIEC BLOKU ADRESOW -->"
DANE = re.compile(r"<!-- adresy: (\{.*?\}) -->")
PLACEHOLDER_PORTAL = "https://<adres-tunelu>.ngrok-free.dev"
PLACEHOLDER_PROTOTYP = PLACEHOLDER_PORTAL + "/demo/index.html"
PLACEHOLDER_DOSTAWCA = PLACEHOLDER_PORTAL + "/dostawca"
DOMYSLNY_ZBIOR, DOMYSLNY_ZASOB = 4216, 40258
PUSTE = {"portal": None, "prototyp": None, "dostawca": None, "aktualizacja": None, "zbior": None, "zasob": None}
NAGLOWKI = {"ngrok-skip-browser-warning": "1", "User-Agent": "ustaw-link-live/1.1"}

PORTAL = (  # (ścieżka; {z} = zbiór, {r} = zasób), nazwa, co sprawdzić
    ("/live/", "Strona startowa wersji live", "odnośniki do wszystkich elementów poniżej"),
    ("/pl/dataset/{z}", "Portal: zbiór Wykaz AED", "zbiór zbiorczy budowany co noc z zasobów zbiorów oznaczonych `standard = AED`"),
    ("/pl/dataset/{z}/resource/{r}/table", "Portal: Wykaz AED, tabela", "tabela zasobu zbiorczego (wyszukiwanie, sortowanie, filtry portalu)"),
    ("/pl/dataset/{z}/resource/{r}/map", "Portal: Wykaz AED, mapa", "mapa portalu włączona przez `geo` w schemacie zasobu (szerokość, długość, etykieta)"),
    ("/api/resources/{r}/data?per_page=20", "API: dane Wykazu AED", "JSON:API `/resources/{id}/data`; odnośniki w odpowiedzi prowadzą pod ten sam adres"),
    ("/api/aed-aggregated", "API: `/aed-aggregated`", "numer zbioru i zasobu Wykazu AED (odpowiednik `/dga-aggregated`)"),
    ("/api/resources/{r}/file", "API: pobranie CSV Wykazu AED", "plik CSV zasobu zbiorczego, ten sam bajt w bajt co w portalu lokalnie"),
    ("/admin/", "Panel administracyjny", "logowanie do panelu dostawcy i administratora (dane logowania zespół przekazuje osobno)"),
)
ENDPOINTY = (
    ("/opis.xml", "Opis zbioru w XML (poprawny)", "XML zgodny z `aed_opis_zbioru.xsd`: metadane, link do `aed.csv` na tym samym hoście i suma md5"),
    ("/aed.csv", "Plik CSV z danymi", "CSV zgodny ze wzorcem (42 kolumny, 7 rekordów fikcyjnych); jego md5 jest równe `<md5>` z opisu"),
    ("/opis_bledny_md5.xml", "Opis z błędną sumą md5", "zgodny z XSD, ale md5 nie pasuje do CSV: portal odrzuca import"),
    ("/opis_bledny_xsd.xml", "Opis niezgodny z XSD", "portal odrzuca import już na walidacji schematu"),
    ("/aed_opis_zbioru.xsd", "Schemat XSD opisu zbioru", "ten sam plik co `format_danych/schemat/aed_opis_zbioru.xsd`"),
    ("/stan", "Stan serwera", "JSON `{\"stan\": \"ok\", ...}`: serwer działa i odpowiada kodem 200"),
)


class AdresBlad(ValueError):
    pass


def sprawdz_adres(adres: str, rola: str) -> str:
    """Zwraca adres bez końcowego ukośnika; AdresBlad, gdy to nie jest poprawny adres https."""
    adres = (adres or "").strip()
    if not adres:
        raise AdresBlad(f"{rola}: pusty adres")
    if re.search(r"\s", adres):
        raise AdresBlad(f"{rola}: adres zawiera spację ({adres})")
    czesci = urlsplit(adres)
    if czesci.scheme != "https":
        raise AdresBlad(f"{rola}: wymagany adres https:// (podano {adres})")
    if not czesci.hostname or "." not in czesci.hostname or "<" in adres or ">" in adres:
        raise AdresBlad(f"{rola}: niepoprawna nazwa hosta ({adres})")
    if czesci.query or czesci.fragment:
        raise AdresBlad(f"{rola}: adres nie może mieć parametrów ani kotwicy ({adres})")
    if rola == "dostawca" and re.search(r"\.(xml|csv|xsd)$", czesci.path, re.IGNORECASE):
        raise AdresBlad(f"dostawca: podaj sam adres serwera, bez pliku (np. https://{czesci.netloc})")
    if rola == "portal" and czesci.path not in ("", "/"):
        raise AdresBlad(f"portal: podaj sam adres tunelu, bez ścieżki (np. https://{czesci.netloc})")
    return adres.rstrip("/")


def _link(adres: Optional[str], placeholder: str, sciezka: str = "") -> str:
    if adres:
        return f"<{adres}{sciezka}>"
    return f"`{placeholder}{sciezka}`"


def zbuduj_blok(dane: Dict[str, Optional[str]]) -> str:
    portal, prot, dost, akt = dane.get("portal"), dane.get("prototyp"), dane.get("dostawca"), dane.get("aktualizacja")
    z, r = dane.get("zbior") or DOMYSLNY_ZBIOR, dane.get("zasob") or DOMYSLNY_ZASOB
    if portal or prot or dost:
        stan = "adresy wpisane; tunel działa tylko wtedy, gdy zespół ma go włączonego"
    else:
        stan = "nieaktywna (adresy nie są jeszcze wpisane); proszę korzystać z wersji offline"
    linie = [
        POCZATEK,
        "<!-- adresy: " + json.dumps(dane, ensure_ascii=False, sort_keys=True) + " -->",
        "",
        f"**Stan:** {stan}.  ",
        f"**Ostatnia aktualizacja adresów:** {akt or 'brak'}",
        "",
        "| Co | Adres | Co sprawdzić |",
        "|---|---|---|",
    ]
    for sciezka, nazwa, opis in PORTAL:
        s = sciezka.format(z=z, r=r)
        linie.append(f"| {nazwa} | {_link(portal, PLACEHOLDER_PORTAL, s)} | {opis} |")
    linie.append(f"| Prototyp (klikalny proces i Wykaz AED) | {_link(prot, PLACEHOLDER_PROTOTYP)} | ta sama strona co `demo/index.html` z repozytorium |")
    for sciezka, nazwa, opis in ENDPOINTY:
        linie.append(f"| Serwer dostawcy: {nazwa} | {_link(dost, PLACEHOLDER_DOSTAWCA, sciezka)} | {opis} |")
    linie += ["", KONIEC]
    return "\n".join(linie)


def wczytaj_dane(tekst: str) -> Dict[str, Optional[str]]:
    m = DANE.search(tekst)
    dane = dict(PUSTE)
    if m:
        dane.update(json.loads(m.group(1)))
    return dane


def podmien_blok(tekst: str, blok: str) -> str:
    i, j = tekst.find(POCZATEK), tekst.find(KONIEC)
    if i < 0 or j < i:
        raise AdresBlad("w pliku nie ma znaczników bloku adresów (POCZATEK/KONIEC BLOKU ADRESOW)")
    return tekst[:i] + blok + tekst[j + len(KONIEC):]


def sprawdz_dostepnosc(adres: str) -> str:
    """Próba pobrania (GET, 20 s). Nagłówek ngrok-skip-browser-warning omija stronę ostrzegawczą darmowego ngroka."""
    zadanie = urllib.request.Request(adres, headers=NAGLOWKI)
    try:
        with urllib.request.urlopen(zadanie, timeout=20) as odp:
            return f"{odp.status} {odp.headers.get('Content-Type', '')}".strip()
    except urllib.error.HTTPError as e:
        return f"BŁĄD {e.code}"
    except (urllib.error.URLError, OSError) as e:
        return f"BŁĄD {getattr(e, 'reason', e)}"


def odczytaj_identyfikatory(portal: str):
    """(zbiór, zasób) Wykazu AED z {portal}/api/aed-aggregated albo None."""
    try:
        zadanie = urllib.request.Request(portal + "/api/aed-aggregated", headers=NAGLOWKI)
        with urllib.request.urlopen(zadanie, timeout=20) as odp:
            dane = json.loads(odp.read().decode("utf-8"))
        return int(dane["dataset_id"]), int(dane["resource_id"])
    except (urllib.error.URLError, OSError, ValueError, KeyError, TypeError):
        return None


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Wpisuje adresy wersji live do WERSJA_LIVE.md.")
    ap.add_argument("adres", nargs="?", help="adres https prototypu (to samo co --prototyp)")
    ap.add_argument("--portal", help="adres https tunelu na bramę demo/brama_live.py (cała wersja live pod jednym adresem)")
    ap.add_argument("--prototyp", help="adres https prototypu (domyślnie przy --portal: <portal>/demo/index.html)")
    ap.add_argument("--dostawca", help="adres https serwera dostawcy (domyślnie przy --portal: <portal>/dostawca)")
    ap.add_argument("--zbior", type=int, help=f"numer zbioru Wykazu AED (domyślnie z /api/aed-aggregated, inaczej {DOMYSLNY_ZBIOR})")
    ap.add_argument("--zasob", type=int, help=f"numer zasobu Wykazu AED (domyślnie z /api/aed-aggregated, inaczej {DOMYSLNY_ZASOB})")
    ap.add_argument("--wyczysc", action="store_true", help="przywróć placeholdery (po wyłączeniu tunelu)")
    ap.add_argument("--sprawdz", action="store_true", help="po zapisie spróbuj pobrać wpisane adresy")
    ap.add_argument("--plik", type=Path, default=PLIK, help="plik do zmiany (domyślnie WERSJA_LIVE.md w katalogu głównym)")
    a = ap.parse_args(argv)
    if a.adres and a.prototyp:
        ap.error("adres prototypu podano dwa razy (pozycyjnie i przez --prototyp)")
    prototyp = a.adres or a.prototyp
    if a.wyczysc and (prototyp or a.dostawca or a.portal):
        ap.error("--wyczysc nie łączy się z adresami")
    if not (a.wyczysc or prototyp or a.dostawca or a.portal):
        ap.error("podaj --portal, adres prototypu, --dostawca albo --wyczysc")
    try:
        tekst = a.plik.read_text(encoding="utf-8")
        dane = wczytaj_dane(tekst)
        if a.wyczysc:
            dane = dict(PUSTE)
        else:
            if a.portal:
                dane["portal"] = sprawdz_adres(a.portal, "portal")
                dane["prototyp"] = dane["portal"] + "/demo/index.html"
                dane["dostawca"] = dane["portal"] + "/dostawca"
                ids = odczytaj_identyfikatory(dane["portal"])
                if ids:
                    dane["zbior"], dane["zasob"] = ids
            if prototyp:
                dane["prototyp"] = sprawdz_adres(prototyp, "prototyp")
            if a.dostawca:
                dane["dostawca"] = sprawdz_adres(a.dostawca, "dostawca")
            if a.zbior:
                dane["zbior"] = a.zbior
            if a.zasob:
                dane["zasob"] = a.zasob
            dane["aktualizacja"] = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M (UTC%z)")
        nowy = podmien_blok(tekst, zbuduj_blok(dane))
    except AdresBlad as e:
        print(f"Błąd: {e}. Plik nie został zmieniony.", file=sys.stderr)
        return 2
    a.plik.write_bytes(nowy.encode("utf-8"))
    print(f"Zapisano {a.plik}: portal = {dane['portal'] or '(placeholder)'}, prototyp = {dane['prototyp'] or '(placeholder)'}, "
          f"dostawca = {dane['dostawca'] or '(placeholder)'}, zbiór/zasób = {dane.get('zbior')}/{dane.get('zasob')}")
    if a.sprawdz:
        z, r = dane.get("zbior") or DOMYSLNY_ZBIOR, dane.get("zasob") or DOMYSLNY_ZASOB
        proby = []
        if dane["portal"]:
            proby += [(nazwa, dane["portal"] + s.format(z=z, r=r)) for s, nazwa, _ in PORTAL]
        if dane["prototyp"]:
            proby.append(("prototyp", dane["prototyp"]))
        if dane["dostawca"]:
            proby += [("dostawca /stan", dane["dostawca"] + "/stan"), ("dostawca /opis.xml", dane["dostawca"] + "/opis.xml")]
        wynik = 0
        for nazwa, adres in proby:
            stan = sprawdz_dostepnosc(adres)
            print(f"  {nazwa}: {adres} -> {stan}")
            wynik = wynik or (1 if stan.startswith("BŁĄD") else 0)
        return wynik
    return 0


if __name__ == "__main__":
    sys.exit(main())
