#!/usr/bin/env python3
"""
Szkice koncepcji akcji „Dane (prze)życie” (do wyboru przez zespół).

Znak: chaotyczny sygnał wchodzi do pół-folderu z danymi (wykaz) i wychodzi jako rytm zatokowy.
  A – wejście: linia płaska (asystolia) + wykaz w folderze   [propozycja wyjściowa zespołu]
  B – wejście: migotanie komór (VF) + pusty folder
  C – wejście: migotanie komór (VF) + wykaz w folderze       [rekomendacja: AED leczy VF, nie asystolię]
Sygnet (małe rozmiary): folder + jedno uderzenie serca.

    uv run --with fonttools python branding/koncepcje_dane_przezycie/build_koncepcje.py
    → *.svg, porownanie.html (render PNG: Edge/Chrome headless, polecenie w README)

Tekst zamieniany na krzywe krojem Atkinson Hyperlegible (SIL OFL) z ../fonty.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from build_branding import BOLD, CZERWIEN, GRANAT, MIETA, REG, ZIELEN, ZOLC, kontrast, svg, tekst  # noqa: E402

BIALY = "#FFFFFF"
# Na ciemnym tle czerwień i zieleń z palety mają za mały kontrast z granatem (<3:1, WCAG 1.4.11),
# więc wersje negatywowe dostają jaśniejsze odpowiedniki.
CZERWIEN_JASNA = "#FF7A85"
ZIELEN_JASNA = "#4ADE9A"

NAZWA_A, NAZWA_PRZE, NAZWA_B = "Dane ", "(prze)", "życie"
HASLO = "Twoje dane – czyjeś życie."

# ---------------------------------------------------------------- geometria znaku (układ 240 × 120, linia bazowa y=65)
Y = 65
FLATLINE = f"M2 {Y} H80"
# migotanie komór: nieregularne fale o zmiennej amplitudzie
VF = (f"M2 {Y} Q6 52 10 {Y} Q15 80 20 {Y} Q24 55 28 {Y} Q33 84 38 {Y} Q42 49 46 {Y} "
      f"Q51 75 56 {Y} Q60 50 64 {Y} Q69 79 74 {Y} Q77 59 80 {Y}")
# rytm zatokowy: P, QRS, T
SINUS = (f"M160 {Y} H166 Q171 57 176 {Y} H180 L182 70 L187 32 L192 77 L195 {Y} H201 "
         f"Q209 52 217 {Y} H238")
# pół-folder: kontur z przerwami na wejście (lewa krawędź) i wyjście (prawa krawędź)
FOLDER_DOL = "M82 74 V92 A8 8 0 0 0 90 100 H150 A8 8 0 0 0 158 92 V74"
FOLDER_GORA = "M158 56 V44 A8 8 0 0 0 150 36 H121 L113 26 H90 A8 8 0 0 0 82 34 V56"
# front teczki (połowa folderu) – półprzezroczysta płaszczyzna dolnej połowy
FRONT = "M82 70 H158 V92 A8 8 0 0 1 150 100 H90 A8 8 0 0 1 82 92 Z"
# wykaz: trzy wiersze tabeli; środkowy na wysokości sygnału = chaos staje się uporządkowanym wierszem
WYKAZ = [(98, 50, 142), (92, Y, 148), (98, 80, 136)]


def znak(wejscie: str, wykaz: bool, c_folder=GRANAT, c_we=CZERWIEN, c_wy=ZIELEN, c_front=ZIELEN, sw=6.0) -> str:
    rows = "".join(f'<path d="M{x1} {y} H{x2}" stroke="{c_folder}" stroke-width="{sw * 0.7:.1f}" stroke-linecap="round"/>'
                   for x1, y, x2 in WYKAZ) if wykaz else ""
    return (f'<g fill="none" stroke-linecap="round" stroke-linejoin="round">'
            f'<path d="{FRONT}" fill="{c_front}" fill-opacity="0.14" stroke="none"/>'
            f'<path d="{FOLDER_DOL}" stroke="{c_folder}" stroke-width="{sw}"/>'
            f'<path d="{FOLDER_GORA}" stroke="{c_folder}" stroke-width="{sw}"/>'
            f'{rows}'
            f'<path d="{wejscie}" stroke="{c_we}" stroke-width="{sw}"/>'
            f'<path d="{SINUS}" stroke="{c_wy}" stroke-width="{sw}"/></g>')


ZNAK_VB = (0, 20, 240, 86)

# sygnet: sam folder z jednym uderzeniem (bez przerw – czytelny od 16 px)
SYG_FOLDER = "M14 46 V80 A8 8 0 0 0 22 88 H78 A8 8 0 0 0 86 80 V34 A8 8 0 0 0 78 26 H52 L44 16 H22 A8 8 0 0 0 14 24 Z"
SYG_RYTM = "M24 58 H38 L43 66 L50 36 L57 74 L61 58 H76"
SYG_VB = (6, 8, 88, 88)


def sygnet(c_folder=GRANAT, c_rytm=ZIELEN, sw=8.0) -> str:
    return (f'<g fill="none" stroke-linecap="round" stroke-linejoin="round">'
            f'<path d="{SYG_FOLDER}" stroke="{c_folder}" stroke-width="{sw}"/>'
            f'<path d="{SYG_RYTM}" stroke="{c_rytm}" stroke-width="{sw}"/></g>')


def wordmark(x, y, size, c_txt=GRANAT, c_prze=ZIELEN, haslo=True, c_haslo=GRANAT):
    """Zwraca (svg, szerokość). „(prze)” lżejszym krojem i kolorem – widać oba odczytania."""
    p1, w1 = tekst(NAZWA_A, BOLD, size, x, y, c_txt)
    p2, w2 = tekst(NAZWA_PRZE, REG, size, x + w1, y, c_prze)
    p3, w3 = tekst(NAZWA_B, BOLD, size, x + w1 + w2, y, c_txt)
    body, w = p1 + p2 + p3, w1 + w2 + w3
    if haslo:
        ph, wh = tekst(HASLO, REG, size * 0.42, x, y + size * 0.62, c_haslo)
        body, w = body + ph, max(w, wh)
    return body, w


def lockup_poziomy(wejscie, wykaz, ciemny=False):
    c = dict(c_folder=MIETA, c_we=CZERWIEN_JASNA, c_wy=ZIELEN_JASNA, c_front=ZIELEN_JASNA) if ciemny else {}
    tlo = f'<rect x="-20" y="0" width="760" height="130" fill="{GRANAT}"/>' if ciemny else ""
    wm, w = wordmark(262, 70, 46, c_txt=BIALY if ciemny else GRANAT, c_prze=ZOLC if ciemny else ZIELEN,
                     c_haslo=MIETA if ciemny else GRANAT)
    return tlo + znak(wejscie, wykaz, **c) + wm, (-20 if ciemny else 0, 0, 262 + w + (20 if ciemny else 6), 130)


def lockup_pionowy(wejscie, wykaz):
    wm, w = wordmark(0, 0, 40)
    sc = 1.3
    zx = (w - 240 * sc) / 2
    body = f'<g transform="translate({zx:.1f} -25) scale({sc})">{znak(wejscie, wykaz)}</g><g transform="translate(0 150)">{wm}</g>'
    return body, (-10, 0, w + 20, 185)


def szer(txt, font, size):
    return tekst(txt, font, size, 0, 0, "#000")[1]


def lockup_kwadrat(ciemny=False, naklejka=False, W=400.0, pad=28.0):
    """Układ zbliżony do kwadratu (naklejki): znak u góry, nazwa w dwóch wierszach, hasło. Zwraca (svg, viewBox)."""
    c_txt, c_prze, c_has = (BIALY, ZOLC, MIETA) if ciemny else (GRANAT, ZIELEN, GRANAT)
    c = dict(c_folder=MIETA, c_we=CZERWIEN_JASNA, c_wy=ZIELEN_JASNA, c_front=ZIELEN_JASNA) if ciemny else {}
    maxw = W - 2 * pad
    s = maxw / ZNAK_VB[2]
    zh = ZNAK_VB[3] * s
    # wspólny rozmiar obu wierszy nazwy, dopasowany do szerokości dłuższego wiersza
    w2_100 = szer(NAZWA_PRZE, REG, 100) + szer(NAZWA_B, BOLD, 100)
    size = min(96.0, 100 * maxw / w2_100)
    hs = min(size * 0.36, 100 * maxw / szer(HASLO, REG, 100))
    y1 = pad + zh + 40 + size * 0.72
    y2 = y1 + size * 1.04
    y3 = y2 + hs * 2.1
    H = y3 + pad * 1.25
    l1, _ = tekst(NAZWA_A.strip(), BOLD, size, W / 2, y1, c_txt, anchor="middle")
    wp, wz = szer(NAZWA_PRZE, REG, size), szer(NAZWA_B, BOLD, size)
    x2 = W / 2 - (wp + wz) / 2
    l2a, _ = tekst(NAZWA_PRZE, REG, size, x2, y2, c_prze)
    l2b, _ = tekst(NAZWA_B, BOLD, size, x2 + wp, y2, c_txt)
    l3, _ = tekst(HASLO, REG, hs, W / 2, y3, c_has, anchor="middle")
    tlo = ""
    if ciemny or naklejka:
        tlo = (f'<rect x="3" y="3" width="{W - 6:.1f}" height="{H - 6:.1f}" rx="36" fill="{GRANAT if ciemny else BIALY}"'
               + (f' stroke="{ZIELEN}" stroke-width="6"' if naklejka else "") + "/>")
    zn = f'<g transform="translate({pad:.1f} {pad - ZNAK_VB[1] * s:.1f}) scale({s:.4f})">{znak(VF, True, **c)}</g>'
    return tlo + zn + l1 + l2a + l2b + l3, (0, 0, W, H)


WARIANTY = [
    ("A", "Linia płaska → rytm zatokowy, folder z wykazem", FLATLINE, True,
     "Wersja wyjściowa zespołu. Uwaga merytoryczna: linia płaska = asystolia, rytm niedefibrylacyjny – AED go nie leczy."),
    ("B", "Migotanie komór → rytm zatokowy, pusty folder", VF, False,
     "Poprawne medycznie (AED przerywa migotanie komór). Folder bez treści słabiej mówi „dane / wykaz”."),
    ("C", "Migotanie komór → rytm zatokowy, folder z wykazem", VF, True,
     "REKOMENDACJA. Podwójna metafora: chaos komór → miarowy rytm oraz rozproszone dane → jeden standardowy wykaz."),
]


def zapisz(nazwa, body, vb, title, desc, w=None):
    (HERE / nazwa).write_text(svg(vb, body, title, desc, w), encoding="utf-8")


def main():
    pliki = []
    for kod, tytul, we, wyk, _ in WARIANTY:
        zapisz(f"znak_{kod}.svg", znak(we, wyk), ZNAK_VB, f"Znak Dane (prze)życie – wariant {kod}", tytul)
        body, vb = lockup_poziomy(we, wyk)
        zapisz(f"logo_poziome_{kod}.svg", body, vb, "Logo Dane (prze)życie", f"{tytul}; hasło: {HASLO}")
        body, vb = lockup_poziomy(we, wyk, ciemny=True)
        zapisz(f"logo_poziome_{kod}_negatyw.svg", body, vb, "Logo Dane (prze)życie – negatyw", tytul)
        pliki += [f"znak_{kod}.svg", f"logo_poziome_{kod}.svg", f"logo_poziome_{kod}_negatyw.svg"]
    body, vb = lockup_pionowy(VF, True)
    zapisz("logo_pionowe_C.svg", body, vb, "Logo Dane (prze)życie – układ pionowy", "Wariant C nad nazwą i hasłem")
    for nazwa, kw in (("logo_kwadrat_C.svg", {}), ("logo_kwadrat_C_negatyw.svg", {"ciemny": True}),
                      ("naklejka_kwadrat_C.svg", {"naklejka": True})):
        body, vb = lockup_kwadrat(**kw)
        zapisz(nazwa, body, vb, "Logo Dane (prze)życie – układ kwadratowy", f"Wariant C, nazwa w dwóch wierszach; hasło: {HASLO}")
        pliki.append(nazwa)
        print(f"  {nazwa}: proporcje {vb[2]:.0f} × {vb[3]:.0f} ({vb[3] / vb[2]:.2f})")
    zapisz("sygnet.svg", sygnet(), SYG_VB, "Sygnet Dane (prze)życie", "Folder z jednym uderzeniem serca")
    zapisz("sygnet_negatyw.svg", f'<rect x="6" y="8" width="88" height="88" rx="16" fill="{GRANAT}"/>'
           + sygnet(MIETA, ZIELEN_JASNA), SYG_VB, "Sygnet – negatyw", "Folder z jednym uderzeniem serca na granacie")
    pliki += ["logo_pionowe_C.svg", "sygnet.svg", "sygnet_negatyw.svg"]

    # kontrasty elementów graficznych (WCAG 1.4.11: min. 3:1)
    pary = [("folder granat / biel", GRANAT, BIALY), ("wejście czerwień / biel", CZERWIEN, BIALY),
            ("wyjście zieleń / biel", ZIELEN, BIALY), ("folder mięta / granat", MIETA, GRANAT),
            ("wejście czerwień jasna / granat", CZERWIEN_JASNA, GRANAT), ("wyjście zieleń jasna / granat", ZIELEN_JASNA, GRANAT),
            ("(prze) żółć / granat", ZOLC, GRANAT), ("(prze) zieleń / biel (tekst 4,5:1)", ZIELEN, BIALY)]
    kontrasty = [(n, round(kontrast(a, b), 2)) for n, a, b in pary]
    for n, k in kontrasty:
        assert k >= 3.0, (n, k)
    (HERE / "porownanie.html").write_text(plansza(kontrasty), encoding="utf-8")
    print("OK:", ", ".join(pliki), "+ porownanie.html")
    for n, k in kontrasty:
        print(f"  kontrast {n}: {k}:1")


def img(nazwa, w, tlo=BIALY):
    return f'<div class="kafel" style="background:{tlo}"><img src="{nazwa}" width="{w}" alt=""></div>'


def plansza(kontrasty) -> str:
    wiersze = ""
    for kod, tytul, _, _, uwaga in WARIANTY:
        rek = " rek" if kod == "C" else ""
        wiersze += (f'<section class="wariant{rek}"><h2>Wariant {kod}: {tytul}</h2><p>{uwaga}</p>'
                    f'<div class="rzad">{img(f"znak_{kod}.svg", 256)}{img(f"znak_{kod}.svg", 64)}{img(f"znak_{kod}.svg", 32)}{img(f"znak_{kod}.svg", 16)}'
                    f'<div class="podpis">256 · 64 · 32 · 16 px</div></div>'
                    f'<div class="rzad">{img(f"logo_poziome_{kod}.svg", 520)}{img(f"logo_poziome_{kod}_negatyw.svg", 520, GRANAT)}</div></section>')
    k = "".join(f"<li>{n}: <b>{v}:1</b></li>" for n, v in kontrasty)
    return f"""<!doctype html><html lang="pl"><head><meta charset="utf-8"><title>Dane (prze)życie – szkice znaku</title>
<style>body{{font-family:Segoe UI,Arial,sans-serif;margin:24px;color:{GRANAT};background:#fff;max-width:1180px}}
h1{{margin:0 0 4px}}h2{{font-size:18px;margin:0 0 4px}}p{{margin:0 0 10px;font-size:14px}}
.wariant{{border:1px solid #d5dde5;border-radius:12px;padding:14px;margin:14px 0}}.rek{{border:3px solid {ZIELEN}}}
.rzad{{display:flex;gap:14px;align-items:center;flex-wrap:wrap;margin:8px 0}}.kafel{{padding:10px;border-radius:8px;border:1px solid #e3e8ee;line-height:0}}
.podpis{{font-size:12px;color:#55657a}}ul{{font-size:13px;columns:2}}</style></head><body>
<h1>Dane (prze)życie – szkice znaku</h1>
<p>Hasło: <b>{HASLO}</b> · Kolory z palety projektu (zieleń AED {ZIELEN}, granat {GRANAT}, czerwień {CZERWIEN}); na granacie jaśniejsze odpowiedniki dla kontrastu.
Koncepcja: chaotyczny sygnał wchodzi do pół-folderu z danymi (wykaz) i wychodzi jako rytm zatokowy.</p>
{wiersze}
<section class="wariant rek"><h2>Układ kwadratowy (naklejki) – wariant C</h2><p>Nazwa w dwóch wierszach, hasło pod spodem; proporcje zbliżone do 1:1. Ostatni kafel: makieta naklejki z zieloną ramką.</p>
<div class="rzad">{img("logo_kwadrat_C.svg", 300)}{img("logo_kwadrat_C_negatyw.svg", 300)}{img("naklejka_kwadrat_C.svg", 300, "#e9eef3")}</div>
<div class="rzad">{img("logo_kwadrat_C.svg", 120)}{img("logo_kwadrat_C.svg", 64)}<div class="podpis">120 · 64 px</div></div></section>
<section class="wariant"><h2>Sygnet do małych rozmiarów i układ pionowy</h2><p>Folder z jednym uderzeniem serca – favicon, awatar, naklejka. Układ pionowy dla wariantu C.</p>
<div class="rzad">{img("sygnet.svg", 128)}{img("sygnet.svg", 64)}{img("sygnet.svg", 32)}{img("sygnet.svg", 16)}{img("sygnet_negatyw.svg", 64)}{img("sygnet_negatyw.svg", 32)}<div class="podpis">128 · 64 · 32 · 16 px · negatyw</div></div>
<div class="rzad">{img("logo_pionowe_C.svg", 320)}</div></section>
<section class="wariant"><h2>Kontrast elementów (WCAG 2.1, min. 3:1 dla grafiki, 4,5:1 dla tekstu)</h2><ul>{k}</ul></section>
</body></html>
"""


if __name__ == "__main__":
    main()
