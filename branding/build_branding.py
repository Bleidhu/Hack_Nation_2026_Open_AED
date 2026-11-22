#!/usr/bin/env python3
"""
Znak akcji „Dane (prze)życie”: logotypy, materiały akcji i księga znaku.

Znak: czerwona linia migotania komór (od lewej) i zielony rytm zatokowy (od prawej)
spotykają się na środku znaku. Na miejsce spotkania nałożony jest folder z danymi,
więc przejście od chaosu do miarowego rytmu dzieje się w jego środku.

    uv run --with fonttools python branding/build_branding.py   → logo/*.svg, materialy/*.svg, ksiega_znaku.html
    bash branding/render.sh                                      → logo/*.png|jpg|pdf, ksiega_znaku.pdf

Tekst w plikach logo jest zamieniony na krzywe krojem Atkinson Hyperlegible (SIL OFL 1.1, fonty/).
"""
from __future__ import annotations

import itertools
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

HERE = Path(__file__).resolve().parent
LOGO = HERE / "logo"
MAT = HERE / "materialy"

BOLD = TTFont(HERE / "fonty" / "AtkinsonHyperlegible-Bold.ttf")
REG = TTFont(HERE / "fonty" / "AtkinsonHyperlegible-Regular.ttf")

# ---------------------------------------------------------------- kolory
KOLORY = [
    # nazwa, hex, rola
    ("Granat danych", "#0E2A47", "folder, nazwa akcji, tekst; tło wersji negatywowej"),
    ("Zieleń rytmu", "#007A45", "rytm zatokowy, „(prze)” na jasnym tle; kolor oznakowania AED"),
    ("Czerwień migotania", "#C8102E", "linia migotania komór; akcent, max 10% powierzchni"),
    ("Mięta tła", "#F2F7F4", "tło jasne, wnętrze folderu, plansze"),
    ("Żółć sygnału", "#FFC629", "„(prze)” i wyróżnienia WYŁĄCZNIE na granacie"),
]
KOLORY_CIEMNE = [
    ("Czerwień jasna", "#FF7A85", "migotanie na granacie"),
    ("Zieleń jasna", "#4ADE9A", "rytm na granacie"),
]
GRANAT, ZIELEN, CZERWIEN, MIETA, ZOLC = (k[1] for k in KOLORY)
CZERWIEN_JASNA, ZIELEN_JASNA = (k[1] for k in KOLORY_CIEMNE)
BIALY, CZARNY = "#FFFFFF", "#000000"

NAZWA = "Dane (prze)życie"
NAZWA_A, NAZWA_PRZE, NAZWA_B = "Dane ", "(prze)", "życie"
HASLO = "Twoje dane – czyjeś życie."
HASHTAG = "#DanePrzeżycie"
PODTYTUL = "Weź dane do serca"


def lum(h):
    h = h.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4  # noqa: E731
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def kontrast(a, b):
    la, lb = sorted([lum(a), lum(b)], reverse=True)
    return (la + 0.05) / (lb + 0.05)


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def cmyk(h):
    r, g, b = (c / 255 for c in rgb(h))
    k = 1 - max(r, g, b)
    if k >= 1:
        return (0, 0, 0, 100)
    return tuple(round(100 * v) for v in ((1 - r - k) / (1 - k), (1 - g - k) / (1 - k), (1 - b - k) / (1 - k), k))


# ---------------------------------------------------------------- tekst → krzywe
def tekst(txt, font, size, x, y, fill, tracking=0.0, anchor="start"):
    """Zwraca (<path>, szerokość). y = linia bazowa."""
    gs = font.getGlyphSet()
    cmap = font.getBestCmap()
    hmtx = font["hmtx"]
    s = size / font["head"].unitsPerEm
    w = sum(hmtx[cmap[ord(c)]][0] * s for c in txt) + tracking * (len(txt) - 1)
    x0 = x - (w / 2 if anchor == "middle" else w if anchor == "end" else 0)
    pen = SVGPathPen(gs)
    cx = 0.0
    for ch in txt:
        g = cmap[ord(ch)]
        gs[g].draw(TransformPen(pen, (s, 0, 0, -s, x0 + cx, y)))
        cx += hmtx[g][0] * s + tracking
    return f'<path fill="{fill}" d="{pen.getCommands()}"/>', w


def szer(txt, font, size):
    return tekst(txt, font, size, 0, 0, "#000")[1]


def svg(vb, body, title, desc, w=None):
    x, y, ww, hh = vb
    width = w or ww
    height = width * hh / ww
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x:.1f} {y:.1f} {ww:.1f} {hh:.1f}" '
            f'width="{width:.0f}" height="{height:.0f}" role="img" aria-labelledby="t d">'
            f'<title id="t">{title}</title><desc id="d">{desc}</desc>{body}</svg>\n')


# ---------------------------------------------------------------- znak (układ 150 × 94, środek x = 120)
Y = 71  # linia izoelektryczna = środek korpusu folderu
CX = 120  # środek znaku: tu kończy się migotanie i zaczyna rytm
# Linie wychodzą poza folder (krawędzie x = 74 i 166) o ok. 25 j., czyli ¼ szerokości folderu.
# migotanie komór: nieregularne fale o zmiennej amplitudzie i okresie, wygasające ku środkowi
VF = (f"M49 {Y} Q53 55 57 {Y} Q61 87 65 {Y} Q70 58 75 {Y} Q80 83 86 {Y} Q91 62 96 {Y} "
      f"Q101 79 106 {Y} Q111 65 115 {Y} H{CX}")
# rytm zatokowy: pełne pobudzenie (P, QRS, T) w folderze i zespół QRS następnego poza nim = miarowy rytm
SINUS = (f"M{CX} {Y} H123 Q127 {Y - 8} 131 {Y} H133 L135 {Y + 4} L139 {Y - 26} L143 {Y + 9} L146 {Y} H150 "
         f"Q156 {Y - 12} 162 {Y} H174 L176 {Y + 4} L180 {Y - 26} L184 {Y + 9} L187 {Y} H191")
# folder nałożony na środek znaku: korpus 92 × 70, zakładka po lewej
FOLDER = ("M83 24 H107 L117 36 H157 A9 9 0 0 1 166 45 V97 A9 9 0 0 1 157 106 H83 "
          "A9 9 0 0 1 74 97 V33 A9 9 0 0 1 83 24 Z")
ZNAK_VB = (45, 18, 150, 94)
SW = 6.0  # grubość linii znaku
PRZERWA = 3.5  # prześwit między linią sygnału a nałożonym konturem folderu

_ids = itertools.count(1)


def znak(c_folder=GRANAT, c_vf=CZERWIEN, c_sinus=ZIELEN, c_wnetrze=MIETA, wnetrze=True, dx_folder=0) -> str:
    """Folder leży na sygnale: jego kontur ma prześwit (maska), więc znak działa na każdym tle.
    dx_folder służy tylko do przykładu niedozwolonego użycia w księdze."""
    mid = f"dp-m{next(_ids)}"
    x, y, w, h = ZNAK_VB
    t = f' transform="translate({dx_folder} 0)"' if dx_folder else ""
    maska = (f'<mask id="{mid}" maskUnits="userSpaceOnUse" x="{x}" y="{y}" width="{w}" height="{h}">'
             f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#fff"/>'
             f'<path d="{FOLDER}"{t} fill="none" stroke="#000" stroke-width="{SW + 2 * PRZERWA}"/></mask>')
    tlo = f'<path d="{FOLDER}"{t} fill="{c_wnetrze}"/>' if wnetrze else ""
    return (f'<defs>{maska}</defs><g fill="none" stroke-linecap="round" stroke-linejoin="round">{tlo}'
            f'<g mask="url(#{mid})" stroke-width="{SW}"><path d="{VF}" stroke="{c_vf}"/><path d="{SINUS}" stroke="{c_sinus}"/></g>'
            f'<path d="{FOLDER}"{t} stroke="{c_folder}" stroke-width="{SW}"/></g>')


def umiesc(x, y, szerokosc, **kw) -> str:
    """Znak z lewym górnym rogiem w (x, y) i zadaną szerokością."""
    s = szerokosc / ZNAK_VB[2]
    return (f'<g transform="translate({x - ZNAK_VB[0] * s:.2f} {y - ZNAK_VB[1] * s:.2f}) scale({s:.4f})">'
            f'{znak(**kw)}</g>')


# sygnet (małe rozmiary): ten sam folder, a w nim całe przejście: fala migotania → jedno pobudzenie
SYG_FOLDER = "M18 14 H42 L52 26 H82 A10 10 0 0 1 92 36 V80 A10 10 0 0 1 82 90 H18 A10 10 0 0 1 8 80 V24 A10 10 0 0 1 18 14 Z"
SYG_Y = 60
SYG_VF = f"M20 {SYG_Y} Q25 47 30 {SYG_Y} Q35 73 40 {SYG_Y} Q44 51 48 {SYG_Y} H50"
SYG_RYTM = f"M50 {SYG_Y} H55 L58 {SYG_Y + 5} L64 {SYG_Y - 24} L70 {SYG_Y + 9} L73 {SYG_Y} H80"
SYG_VB = (2, 8, 96, 88)
SYG_SW = 7.0


def sygnet(c_folder=GRANAT, c_vf=CZERWIEN, c_sinus=ZIELEN, c_wnetrze=MIETA, wnetrze=True) -> str:
    tlo = f' fill="{c_wnetrze}"' if wnetrze else ""
    return (f'<g fill="none" stroke-linecap="round" stroke-linejoin="round">'
            f'<path d="{SYG_FOLDER}"{tlo} stroke="{c_folder}" stroke-width="{SYG_SW + 1}"/>'
            f'<g stroke-width="{SYG_SW}"><path d="{SYG_VF}" stroke="{c_vf}"/><path d="{SYG_RYTM}" stroke="{c_sinus}"/></g></g>')


# ---------------------------------------------------------------- zestawy kolorów
PALETY = {
    "kolor": dict(znak=dict(), txt=GRANAT, prze=ZIELEN, haslo=GRANAT, tlo=None),
    "negatyw": dict(znak=dict(c_folder=MIETA, c_vf=CZERWIEN_JASNA, c_sinus=ZIELEN_JASNA, c_wnetrze=GRANAT),
                    txt=BIALY, prze=ZOLC, haslo=MIETA, tlo=GRANAT),
    "mono-granat": dict(znak=dict(c_folder=GRANAT, c_vf=GRANAT, c_sinus=GRANAT, wnetrze=False),
                        txt=GRANAT, prze=GRANAT, haslo=GRANAT, tlo=None),
    "czarne": dict(znak=dict(c_folder=CZARNY, c_vf=CZARNY, c_sinus=CZARNY, wnetrze=False),
                   txt=CZARNY, prze=CZARNY, haslo=CZARNY, tlo=None),
    "biale": dict(znak=dict(c_folder=BIALY, c_vf=BIALY, c_sinus=BIALY, wnetrze=False),
                  txt=BIALY, prze=BIALY, haslo=BIALY, tlo=None),
}


def wordmark(x, y, size, p, haslo=True, anchor="start"):
    """Nazwa w jednym wierszu (+ hasło). „(prze)” lżejszym krojem i innym kolorem: widać oba odczytania."""
    w1, w2, w3 = szer(NAZWA_A, BOLD, size), szer(NAZWA_PRZE, REG, size), szer(NAZWA_B, BOLD, size)
    w = w1 + w2 + w3
    x0 = x - w / 2 if anchor == "middle" else x
    body = (tekst(NAZWA_A, BOLD, size, x0, y, p["txt"])[0] + tekst(NAZWA_PRZE, REG, size, x0 + w1, y, p["prze"])[0]
            + tekst(NAZWA_B, BOLD, size, x0 + w1 + w2, y, p["txt"])[0])
    if haslo:
        hs = size * 0.42
        ph, wh = tekst(HASLO, REG, hs, x if anchor == "middle" else x0 + size * 0.03, y + size * 0.66, p["haslo"], anchor=anchor)
        body, w = body + ph, max(w, wh)
    return body, w


def _tlo(vb, p, rx=0):
    if not p["tlo"]:
        return ""
    x, y, w, h = vb
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{p["tlo"]}"/>'


def logo_poziome(paleta="kolor", haslo=False):
    p = PALETY[paleta]
    zx, zy, zw, zh = ZNAK_VB
    size = 50
    wx = zx + zw + 16
    base = zy + zh / 2 + 0.34 * size - (11 if haslo else 0)
    wm, w = wordmark(wx, base, size, p, haslo=haslo)
    pad = 14 if p["tlo"] else 0
    vb = (zx - pad, zy - pad, wx + w + 2 - zx + 2 * pad, zh + 2 * pad)
    return vb, _tlo(vb, p, 10) + znak(**p["znak"]) + wm


def logo_kwadrat(paleta="kolor", W=400.0, pad=30.0):
    """Układ pionowy zbliżony do kwadratu (naklejki, awatary, plakaty): znak, nazwa w dwóch wierszach, hasło."""
    p = PALETY[paleta]
    maxw = W - 2 * pad
    zw = min(maxw, 0.62 * W)
    zh = ZNAK_VB[3] * zw / ZNAK_VB[2]
    w2_100 = szer(NAZWA_PRZE, REG, 100) + szer(NAZWA_B, BOLD, 100)
    size = min(96.0, 100 * maxw / w2_100)
    hs = min(size * 0.36, 100 * maxw / szer(HASLO, REG, 100))
    y1 = pad + zh + 26 + size * 0.72
    y2 = y1 + size * 1.02
    y3 = y2 + hs * 2.0
    H = y3 + pad
    l1 = tekst(NAZWA_A.strip(), BOLD, size, W / 2, y1, p["txt"], anchor="middle")[0]
    wp, wz = szer(NAZWA_PRZE, REG, size), szer(NAZWA_B, BOLD, size)
    x2 = W / 2 - (wp + wz) / 2
    l2 = tekst(NAZWA_PRZE, REG, size, x2, y2, p["prze"])[0] + tekst(NAZWA_B, BOLD, size, x2 + wp, y2, p["txt"])[0]
    l3 = tekst(HASLO, REG, hs, W / 2, y3, p["haslo"], anchor="middle")[0]
    zn = umiesc((W - zw) / 2, pad, zw, **p["znak"])
    vb = (0, 0, W, H)
    return vb, _tlo(vb, p, 28) + zn + l1 + l2 + l3


def logo_znak(paleta="kolor"):
    p = PALETY[paleta]
    pad = 10 if p["tlo"] else 0
    x, y, w, h = ZNAK_VB
    vb = (x - pad, y - pad, w + 2 * pad, h + 2 * pad)
    return vb, _tlo(vb, p, 10) + znak(**p["znak"])


def logo_sygnet(paleta="kolor"):
    p = PALETY[paleta]
    kw = dict(p["znak"])
    if paleta == "negatyw":
        return SYG_VB, f'<rect x="2" y="8" width="96" height="88" rx="16" fill="{GRANAT}"/>' + sygnet(**kw)
    return SYG_VB, sygnet(**kw)


# ---------------------------------------------------------------- materiały akcji
def dopasuj(txt, font, size, maxw, tracking=0.0):
    w = szer(txt, font, size) + tracking * (len(txt) - 1)
    return size if w <= maxw else size * maxw / w


def odznaka():
    """Odznaka dysponenta, który opublikował dane AED według wzorca (koło Ø 300)."""
    R = 150
    b = (f'<circle r="{R}" fill="{GRANAT}"/><circle r="{R - 10}" fill="none" stroke="{ZOLC}" stroke-width="3"/>')
    b += umiesc(-68, -112, 136, **PALETY["negatyw"]["znak"])
    for txt, font, size, y, kol, tr in [("NASZE AED SĄ", BOLD, 27, 20, BIALY, 1.2),
                                        ("W WYKAZIE AED", BOLD, 27, 52, BIALY, 1.2),
                                        ("dane.gov.pl", REG, 18, 82, ZOLC, 0.3),
                                        (NAZWA, REG, 15, 108, MIETA, 0.2)]:
        polcieciwy = (R - 20) ** 2 - (y + 4) ** 2
        maxw = 2 * polcieciwy ** 0.5 - 14
        b += tekst(txt, font, dopasuj(txt, font, size, maxw, tr), 0, y, kol, tracking=tr, anchor="middle")[0]
    return (-R, -R, 2 * R, 2 * R), b


def qr_makieta(x, y, size, c):
    """Wzór podobny do kodu QR: WYŁĄCZNIE makieta, nie da się go zeskanować."""
    import random
    rnd = random.Random(7)
    n = 21
    m = size / n
    out = [f'<rect x="{x}" y="{y}" width="{size}" height="{size}" fill="#fff"/>']

    def finder(fx, fy):
        return (f'<rect x="{x + fx * m:.2f}" y="{y + fy * m:.2f}" width="{7 * m:.2f}" height="{7 * m:.2f}" fill="{c}"/>'
                f'<rect x="{x + (fx + 1) * m:.2f}" y="{y + (fy + 1) * m:.2f}" width="{5 * m:.2f}" height="{5 * m:.2f}" fill="#fff"/>'
                f'<rect x="{x + (fx + 2) * m:.2f}" y="{y + (fy + 2) * m:.2f}" width="{3 * m:.2f}" height="{3 * m:.2f}" fill="{c}"/>')
    for i in range(n):
        for j in range(n):
            if (i < 8 and j < 8) or (i > 12 and j < 8) or (i < 8 and j > 12):
                continue
            if rnd.random() < 0.45:
                out.append(f'<rect x="{x + i * m:.2f}" y="{y + j * m:.2f}" width="{m:.2f}" height="{m:.2f}" fill="{c}"/>')
    out += [finder(0, 0), finder(14, 0), finder(0, 14)]
    return "".join(out)


def naklejka():
    """Naklejka A6 na szafkę AED (148 × 105 mm; 1 mm = 2 jednostki)."""
    W, H = 296, 210
    b = (f'<defs><clipPath id="dp-nakl"><rect width="{W}" height="{H}" rx="10"/></clipPath></defs>'
         f'<g clip-path="url(#dp-nakl)"><rect width="{W}" height="{H}" fill="{BIALY}"/>'
         f'<rect y="116" width="{W}" height="{H - 116}" fill="{GRANAT}"/></g>'
         f'<rect x="1.5" y="1.5" width="{W - 3}" height="{H - 3}" rx="9" fill="none" stroke="{ZIELEN}" stroke-width="3"/>')
    b += umiesc(14, 14, 112)
    x = 140
    b += tekst("Ten AED jest", BOLD, dopasuj("Ten AED jest", BOLD, 21, W - x - 14), x, 42, GRANAT)[0]
    b += tekst("w Wykazie AED", BOLD, dopasuj("w Wykazie AED", BOLD, 21, W - x - 14), x, 66, GRANAT)[0]
    b += tekst("na dane.gov.pl", REG, 14, x, 86, ZIELEN)[0]
    b += tekst("ID: AED-PL-000001 · sprawdzony: 2026-11-15", REG, dopasuj("ID: AED-PL-000001 · sprawdzony: 2026-11-15", REG, 10.5, W - 28), 14, 106, GRANAT)[0]
    q = 72
    qx, qy = W - q - 16, 126
    col = qx - 14 - 16
    for txt, font, size, y, kol in [("Nie działa? Zamknięty?", BOLD, 17, 146, ZOLC),
                                    ("Zeskanuj kod i zgłoś.", REG, 14, 168, BIALY),
                                    (f"{NAZWA} · {HASLO}", REG, 10, 194, MIETA)]:
        b += tekst(txt, font, dopasuj(txt, font, size, col), 14, y, kol)[0]
    b += qr_makieta(qx, qy, q, GRANAT)
    b += tekst("makieta QR", REG, 7, qx + q / 2, qy + q + 9, BIALY, anchor="middle")[0]
    return (0, 0, W, H), b


def post_social():
    """Kwadratowa grafika do mediów społecznościowych (1080 × 1080 w skali 1:2)."""
    W = 540
    b = f'<rect width="{W}" height="{W}" fill="{GRANAT}"/>'
    zw = 260
    b += umiesc((W - zw) / 2, 60, zw, **PALETY["negatyw"]["znak"])
    y = 60 + ZNAK_VB[3] * zw / ZNAK_VB[2] + 70
    b += tekst("Twoje dane –", BOLD, 50, 60, y, BIALY)[0]
    b += tekst("czyjeś życie.", BOLD, 50, 60, y + 58, ZOLC)[0]
    t = "Opublikuj dane o swoich AED na dane.gov.pl."
    b += tekst(t, REG, dopasuj(t, REG, 24, W - 120), 60, y + 112, MIETA)[0]
    wm, _ = wordmark(60, W - 46, 26, PALETY["negatyw"], haslo=False)
    b += wm + tekst(HASHTAG, REG, 20, W - 60, W - 46, MIETA, anchor="end")[0]
    return (0, 0, W, W), b


# ---------------------------------------------------------------- zapis
ALT = ("Logo akcji Dane (prze)życie: czerwona linia migotania komór i zielony rytm serca spotykają się "
       "w środku granatowego folderu z danymi")

LOGOTYPY = [
    # plik, funkcja, argumenty, tytuł
    ("dane-przezycie_logo_poziome", logo_poziome, dict(), "Logo Dane (prze)życie"),
    ("dane-przezycie_logo_poziome_haslo", logo_poziome, dict(haslo=True), "Logo Dane (prze)życie z hasłem"),
    ("dane-przezycie_logo_pionowe", logo_kwadrat, dict(), "Logo Dane (prze)życie, układ pionowy"),
    ("dane-przezycie_znak", logo_znak, dict(), "Znak Dane (prze)życie"),
    ("dane-przezycie_sygnet", logo_sygnet, dict(), "Sygnet Dane (prze)życie"),
    ("dane-przezycie_logo_poziome_negatyw", logo_poziome, dict(paleta="negatyw", haslo=True), "Logo Dane (prze)życie, negatyw"),
    ("dane-przezycie_logo_pionowe_negatyw", logo_kwadrat, dict(paleta="negatyw"), "Logo Dane (prze)życie, układ pionowy, negatyw"),
    ("dane-przezycie_sygnet_negatyw", logo_sygnet, dict(paleta="negatyw"), "Sygnet Dane (prze)życie, negatyw"),
    ("dane-przezycie_logo_poziome_mono-granat", logo_poziome, dict(paleta="mono-granat", haslo=True), "Logo Dane (prze)życie, granat"),
    ("dane-przezycie_logo_poziome_czarne", logo_poziome, dict(paleta="czarne", haslo=True), "Logo Dane (prze)życie, czerń"),
    ("dane-przezycie_logo_poziome_biale", logo_poziome, dict(paleta="biale", haslo=True), "Logo Dane (prze)życie, biel"),
]
MATERIALY = [
    ("dane-przezycie_naklejka_A6", naklejka, "Naklejka na szafkę AED",
     "Naklejka: Ten AED jest w Wykazie AED na dane.gov.pl, ID, data sprawdzenia i kod QR do zgłoszenia problemu"),
    ("dane-przezycie_odznaka_dysponenta", odznaka, "Odznaka dysponenta",
     "Okrągła granatowa odznaka ze znakiem akcji i napisem Nasze AED są w Wykazie AED, dane.gov.pl"),
    ("dane-przezycie_post_1080", post_social, "Grafika do mediów społecznościowych",
     "Granatowa grafika ze znakiem akcji i hasłem Twoje dane – czyjeś życie"),
]


def main():
    LOGO.mkdir(exist_ok=True)
    MAT.mkdir(exist_ok=True)
    W = {}
    for nazwa, f, kw, tytul in LOGOTYPY:
        vb, body = f(**kw)
        (LOGO / f"{nazwa}.svg").write_text(svg(vb, body, tytul, ALT), encoding="utf-8")
        W[nazwa.removeprefix("dane-przezycie_")] = (vb, body)
    for nazwa, f, tytul, opis in MATERIALY:
        vb, body = f()
        (MAT / f"{nazwa}.svg").write_text(svg(vb, body, tytul, opis), encoding="utf-8")
        W[nazwa.removeprefix("dane-przezycie_")] = (vb, body)

    # WCAG 1.4.11 (grafika ≥ 3:1) i 1.4.3 (tekst ≥ 4,5:1)
    pary = [("folder i nazwa: granat / biel", GRANAT, BIALY, 4.5), ("migotanie: czerwień / biel", CZERWIEN, BIALY, 3),
            ("rytm: zieleń / biel", ZIELEN, BIALY, 3), ("„(prze)”: zieleń / biel", ZIELEN, BIALY, 4.5),
            ("granat / mięta (wnętrze folderu)", GRANAT, MIETA, 4.5), ("migotanie: czerwień / mięta", CZERWIEN, MIETA, 3),
            ("rytm: zieleń / mięta", ZIELEN, MIETA, 3),
            ("folder: mięta / granat", MIETA, GRANAT, 4.5), ("migotanie: czerwień jasna / granat", CZERWIEN_JASNA, GRANAT, 3),
            ("rytm: zieleń jasna / granat", ZIELEN_JASNA, GRANAT, 3), ("„(prze)”: żółć / granat", ZOLC, GRANAT, 4.5),
            ("hasło: mięta / granat", MIETA, GRANAT, 4.5)]
    kontrasty = []
    for n, a, b, prog in pary:
        k = kontrast(a, b)
        assert k >= prog, (n, round(k, 2), prog)
        kontrasty.append((n, a, b, k, prog))
    (HERE / "ksiega_znaku.html").write_text(ksiega(W, kontrasty), encoding="utf-8")
    print("OK:", len(LOGOTYPY), "logotypów,", len(MATERIALY), "materiałów, ksiega_znaku.html")
    for n, _, _, k, prog in kontrasty:
        print(f"  {n}: {k:.2f}:1 (min. {prog}:1)")


# ---------------------------------------------------------------- księga znaku
def inline(v, w=None, h=None, style="", label=ALT):
    vb, body = v
    x, y, ww, hh = vb
    size = (f'width="{w}"' if w else "") + (f' height="{h}"' if h else "")
    return (f'<svg viewBox="{x:.1f} {y:.1f} {ww:.1f} {hh:.1f}" {size} style="{style}" '
            f'role="img" aria-label="{label}">{body}</svg>')


X_OCHR = 23  # moduł pola ochronnego x = ¼ szerokości folderu (92 j.)
MINIMA = [
    # wersja, klucz W, druk (szerokość mm), ekran (szerokość px), uwagi
    ("Pozioma", "logo_poziome", 60, 220, "znak ma wtedy 60 px; poniżej użyj sygnetu"),
    ("Pozioma z hasłem", "logo_poziome_haslo", 65, 240, "hasło ma wtedy ok. 9 px / 6,5 pt"),
    ("Pionowa (z hasłem)", "logo_pionowe", 40, 140, "naklejki, awatary, plakaty"),
    ("Znak", "znak", 18, 64, "przy 40 px fale migotania zlewają się w jedną linię"),
    ("Sygnet", "sygnet", 6, 16, "favicon, znacznik na mapie, ikona aplikacji"),
]
STRON = 12


def ksiega(W, kontrasty) -> str:
    def stopka(n):
        return f'<div class="stopka"><span>{NAZWA} · Księga znaku v1.0</span><span>{n} / {STRON}</span></div>'

    # 02 budowa znaku: znak z osiami i opisem elementów
    def kolko(n, cx, cy, px, py):
        return (f'<line x1="{px}" y1="{py}" x2="{cx}" y2="{cy}" stroke="{GRANAT}" stroke-width=".8" stroke-dasharray="2 2"/>'
                f'<circle cx="{px}" cy="{py}" r="2.2" fill="{GRANAT}"/>'
                f'<circle cx="{cx}" cy="{cy}" r="8" fill="{GRANAT}"/>'
                f'<text x="{cx}" y="{cy + 4}" font-size="11" font-weight="700" text-anchor="middle" fill="#fff">{n}</text>')
    budowa = (f'<svg viewBox="36 -26 168 172" width="100%" style="max-height:120mm" role="img" aria-label="Budowa znaku: migotanie komór, folder, '
              f'punkt spotkania w środku folderu, rytm zatokowy">'
              f'<line x1="{CX}" y1="-8" x2="{CX}" y2="130" stroke="#8aa0b4" stroke-width=".7" stroke-dasharray="4 3"/>'
              f'<line x1="40" y1="{Y}" x2="200" y2="{Y}" stroke="#8aa0b4" stroke-width=".7" stroke-dasharray="4 3"/>'
              f'{znak()}'
              + kolko(1, 58, 132, 61, 80) + kolko(2, 96, -14, 96, 26) + kolko(3, CX + 22, 132, CX, Y)
              + kolko(4, 186, -14, 180, 47)
              + '</svg>')

    # 06 pole ochronne
    vb, body = W["logo_poziome"]
    px, py, pw, ph = vb
    m = X_OCHR
    kw = "".join(
        f'<g><rect x="{gx:.1f}" y="{gy:.1f}" width="{m}" height="{m}" fill="{CZERWIEN}" fill-opacity=".16" stroke="{CZERWIEN}" stroke-width=".8"/>'
        f'<text x="{gx + m / 2:.1f}" y="{gy + m / 2 + 5:.1f}" font-size="14" text-anchor="middle" fill="{CZERWIEN}">x</text></g>'
        for gx, gy in [(px - m, py + ph / 2 - m / 2), (px + pw, py + ph / 2 - m / 2), (px + pw / 2 - m / 2, py - m),
                       (px + pw / 2 - m / 2, py + ph)])
    ochr = (f'<svg viewBox="{px - m - 4} {py - m - 4} {pw + 2 * m + 8} {ph + 2 * m + 8}" width="100%" role="img" '
            f'aria-label="Pole ochronne: z każdej strony logo co najmniej jeden moduł x">'
            f'<rect x="{px - m}" y="{py - m}" width="{pw + 2 * m}" height="{ph + 2 * m}" fill="{MIETA}" stroke="{CZERWIEN}" '
            f'stroke-dasharray="6 4" stroke-width="1.5"/><rect x="{px}" y="{py}" width="{pw}" height="{ph}" fill="#fff" '
            f'stroke="#9aa" stroke-width=".8"/>{body}{kw}'
            f'<g transform="translate(74 {ZNAK_VB[1] + ZNAK_VB[3] + 4})"><path d="M0 0 V6 M92 0 V6 M0 3 H92" stroke="{GRANAT}" stroke-width=".8" fill="none"/>'
            f'<text x="46" y="16" font-size="9" text-anchor="middle" fill="{GRANAT}">szerokość folderu = 4x</text></g></svg>')

    # 05 kolorystyka
    def karta(nazwa, hx, rola):
        r, g, b = rgb(hx)
        c, mm, yy, k = cmyk(hx)
        txt = BIALY if lum(hx) < 0.3 else GRANAT
        return (f'<div class="kolor"><div class="probka" style="background:{hx};color:{txt}">{nazwa}</div>'
                f'<dl><dt>HEX</dt><dd>{hx}</dd><dt>RGB</dt><dd>{r} {g} {b}</dd><dt>CMYK*</dt><dd>{c} {mm} {yy} {k}</dd></dl>'
                f'<p class="rola">{rola}</p></div>')
    karty = "".join(karta(*k) for k in KOLORY)
    karty_c = "".join(karta(*k) for k in KOLORY_CIEMNE)
    tab_k = "".join(f'<tr><td><span class="kropka" style="background:{a}"></span><span class="kropka" style="background:{b}"></span>{n}</td>'
                    f'<td>{k:.1f}:1</td><td>{prog:g}:1</td></tr>' for n, a, b, k, prog in kontrasty)

    # 08 niedozwolone użycia
    def zly(opis, inner, bg="#fff"):
        return (f'<figure class="zle"><div class="pole" style="background:{bg}">{inner}</div>'
                f'<figcaption><span class="x" aria-hidden="true">✕</span> {opis}</figcaption></figure>')
    zx, zy, zw, zh = ZNAK_VB
    zn = W["znak"]
    lp = W["logo_poziome"]

    def zsvg(body, w=190):
        return f'<svg viewBox="{zx} {zy} {zw} {zh}" width="{w}">{body}</svg>'
    inny_kroj = (f'<svg viewBox="{zx} 18 520 94" width="230">{znak()}<text x="{zx + zw + 16}" y="80" font-family="Georgia, serif" '
                 f'font-style="italic" font-size="44" fill="{GRANAT}">dane przeżycie!</text></svg>')
    zle = "".join([
        zly("Nie rozciągaj ani nie ściskaj znaku", inline(zn, w=120, style="transform:scaleX(1.6)")),
        zly("Nie obracaj znaku", inline(zn, w=170, style="transform:rotate(-12deg)")),
        zly("Nie odbijaj znaku: rytm przeszedłby w migotanie", inline(zn, w=190, style="transform:scaleX(-1)")),
        zly("Nie zamieniaj kolorów linii", zsvg(znak(c_vf=ZIELEN, c_sinus=CZERWIEN))),
        zly("Nie przesuwaj folderu ze środka znaku", zsvg(znak(dx_folder=-24))),
        zly("Nie umieszczaj na tle o niskim kontraście", inline(lp, w=230), bg="#3D9A6A"),
        zly("Nie dodawaj cieni, poświat ani gradientów", inline(lp, w=230, style="filter:drop-shadow(5px 5px 3px rgba(0,0,0,.55))")),
        zly("Nie zmieniaj kroju ani zapisu nazwy", inny_kroj),
    ])

    minima = "".join(f'<tr><td>{n}</td><td>{mm} mm</td><td>{px_} px</td><td>{u}</td></tr>' for n, _, mm, px_, u in MINIMA)
    minima_fig = "".join(f'<figure>{inline(W[k], style=f"width:{mm}mm;height:auto")}<figcaption>{n}: {mm} mm</figcaption></figure>'
                         for n, k, mm, _, _ in MINIMA)
    test_px = "".join(f'<span>{inline(W["znak"], w=s)}<br>{s} px</span>' for s in (120, 64, 40))
    test_px += "".join(f'<span>{inline(W["sygnet"], w=s)}<br>{s} px</span>' for s in (32, 16))

    font_css = """
    @font-face{font-family:'Atkinson Hyperlegible';src:url('fonty/AtkinsonHyperlegible-Regular.ttf') format('truetype');font-weight:400}
    @font-face{font-family:'Atkinson Hyperlegible';src:url('fonty/AtkinsonHyperlegible-Bold.ttf') format('truetype');font-weight:700}
    """
    return f"""<!doctype html>
<html lang="pl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Księga znaku {NAZWA}</title>
<style>
{font_css}
@page{{size:297mm 210mm;margin:0}}
*{{box-sizing:border-box}}
html,body{{margin:0;background:#fff;color:{GRANAT};font-family:'Atkinson Hyperlegible',Arial,sans-serif;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
.strona{{width:297mm;height:210mm;padding:15mm 18mm 14mm;position:relative;overflow:hidden;page-break-after:always;break-after:page}}
.strona:last-child{{page-break-after:auto}}
.stopka{{position:absolute;left:18mm;right:18mm;bottom:8mm;display:flex;justify-content:space-between;font-size:9pt;color:#3b5068}}
h1{{font-size:30pt;margin:0 0 6mm;line-height:1.1}}
h2{{font-size:22pt;margin:0 0 6mm;line-height:1.15}}
h2 small{{display:block;font-size:10pt;font-weight:400;letter-spacing:.12em;text-transform:uppercase;color:{ZIELEN};margin-bottom:2mm}}
h3{{font-size:13pt;margin:6mm 0 2mm}}
p,li{{font-size:11.5pt;line-height:1.5;margin:0 0 3mm}}
ul{{margin:0;padding-left:5mm}}
.okladka{{background:{MIETA};display:flex;flex-direction:column;justify-content:center;padding-left:26mm}}
.okladka .meta{{margin-top:12mm;font-size:11pt;line-height:1.6}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:10mm;align-items:center}}
.koncepcja{{font-size:13pt;line-height:1.6}}
.legenda li{{list-style:none;margin-bottom:3mm;padding-left:9mm;position:relative}}
.legenda li b.n{{position:absolute;left:0;top:.5mm;width:6mm;height:6mm;border-radius:50%;background:{GRANAT};color:#fff;font-size:9pt;display:flex;align-items:center;justify-content:center}}
.warianty{{display:grid;grid-template-columns:repeat(3,1fr);gap:6mm}}
.warianty figure{{margin:0;border:1px solid #d5e1da;border-radius:3mm;padding:5mm;display:flex;flex-direction:column;justify-content:space-between;min-height:62mm}}
.warianty .pole{{flex:1;display:flex;align-items:center;justify-content:center;border-radius:2mm;padding:3mm}}
figcaption{{font-size:9.5pt;margin-top:3mm;line-height:1.35}}
.kolory{{display:grid;grid-template-columns:repeat(7,1fr);gap:4mm}}
.probka{{height:26mm;border-radius:3mm;padding:2.5mm;font-weight:700;font-size:10pt;display:flex;align-items:flex-end;border:1px solid #d5e1da}}
dl{{display:grid;grid-template-columns:auto 1fr;gap:.5mm 2mm;font-size:8.5pt;margin:2.5mm 0 1.5mm}}
dt{{font-weight:700}} dd{{margin:0}}
.rola{{font-size:8.5pt;line-height:1.3;margin:0}}
.kropka{{display:inline-block;width:3.2mm;height:3.2mm;border-radius:50%;border:1px solid #9aa;margin-right:1mm;vertical-align:-0.4mm}}
.zle-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:5mm}}
.zle{{margin:0}}
.zle .pole{{height:40mm;border:1px solid #d5e1da;border-radius:3mm;display:flex;align-items:center;justify-content:center;overflow:hidden;position:relative}}
.zle .pole::after{{content:"";position:absolute;inset:0;background:linear-gradient(to top right,transparent calc(50% - 1.5px),{CZERWIEN} calc(50% - 1.5px),{CZERWIEN} calc(50% + 1.5px),transparent calc(50% + 1.5px));opacity:.85}}
.x{{color:{CZERWIEN};font-weight:700}}
.min{{display:flex;gap:10mm;align-items:flex-end;margin-top:6mm;flex-wrap:wrap}}
.min figure{{margin:0}}
.test{{display:flex;gap:8mm;align-items:flex-end;font-size:9pt;margin-top:5mm}}
.test span{{text-align:center}}
table{{border-collapse:collapse;font-size:10.5pt;margin-top:3mm}}
th,td{{border-bottom:1px solid #d5e1da;padding:1.8mm 5mm 1.8mm 0;text-align:left;vertical-align:top}}
th{{font-weight:700}}
.mala td,.mala th{{font-size:9pt;padding:1.2mm 4mm 1.2mm 0}}
.typo-a{{font-size:44pt;line-height:1}}
.typo-b{{font-size:20pt;line-height:1.2}}
.abc{{font-size:13pt;letter-spacing:.03em;line-height:1.6;margin-top:3mm}}
.zast{{display:grid;grid-template-columns:1.25fr .8fr 1fr;gap:8mm;align-items:start}}
.zast figure{{margin:0}}
.uwaga{{background:{MIETA};border-left:2mm solid {ZIELEN};padding:4mm 5mm;font-size:10.5pt;line-height:1.5;border-radius:1mm}}
</style></head><body>

<section class="strona okladka">
  {inline(W["logo_poziome_haslo"], w=860)}
  <div class="meta">
    <strong style="font-size:20pt">Księga znaku</strong><br>
    Akcja zachęcająca dysponentów defibrylatorów AED do publikowania danych w portalu dane.gov.pl<br>
    Zadanie „Misja AED – Dane na ratunek” · HackNation 2026 · wersja 1.0 · 2026-11-22
  </div>
</section>

<section class="strona">
  <h2><small>01 · Koncepcja</small>Z chaosu w rytm: w sercu i w danych</h2>
  <div class="grid2" style="grid-template-columns:1.15fr 1fr;align-items:start">
    <div>
      <p class="koncepcja">Nazwa „{NAZWA}” czyta się na dwa sposoby: „dane przeżycie” i „dane życie”, a „dane” to także dane.gov.pl. W znaku czerwona linia migotania komór, czyli rytmu, który przerywa defibrylator AED, spotyka się na środku z zielonym, miarowym rytmem serca. Miejsce spotkania przykrywa folder z danymi, bo najbliższy AED da się szybko znaleźć dopiero wtedy, gdy rozproszone dane trafią do jednego wykazu. Chaos zamienia się w porządek dwa razy: w sercu po defibrylacji i w danych po publikacji według jednego wzorca. Zieleń nawiązuje do oznakowania AED, czerwień do zagrożenia życia, a granat do rzetelności danych publicznych.</p>
    </div>
    <div>
      <h3 style="margin-top:0">Komunikacja</h3>
      <table class="mala">
        <tr><th>Nazwa akcji</th><td>{NAZWA}</td></tr>
        <tr><th>Hasło</th><td>{HASLO}</td></tr>
        <tr><th>Wezwanie do dysponentów</th><td>{PODTYTUL}. Opublikuj swoje AED na dane.gov.pl.</td></tr>
        <tr><th>Hashtag</th><td>{HASHTAG} (w adresach i tagach bez znaków diakrytycznych: #DanePrzezycie)</td></tr>
        <tr><th>W mowie</th><td>pełna fraza „Dane przeżycie”; nawias jest tylko w zapisie</td></tr>
      </table>
      <div style="margin-top:8mm">{inline(W["znak"], w=330)}</div>
    </div>
  </div>
  {stopka(2)}
</section>

<section class="strona">
  <h2><small>02 · Budowa znaku</small>Dwie linie spotykają się w środku folderu</h2>
  <div class="grid2" style="grid-template-columns:1.5fr 1fr">
    <div>{budowa}</div>
    <ul class="legenda">
      <li><b class="n">1</b><strong>Migotanie komór</strong> (czerwień). Nieregularne fale o zmiennej wysokości i odstępach. To rytm, który AED rozpoznaje i przerywa wyładowaniem. Fale słabną ku środkowi.</li>
      <li><b class="n">2</b><strong>Folder z danymi</strong> (granat), nałożony na linię. Kontur folderu ma prześwit, więc widać, że leży na sygnale. To zbiór danych w portalu i Wykaz AED.</li>
      <li><b class="n">3</b><strong>Punkt spotkania</strong> na przecięciu pionowej osi znaku i linii izoelektrycznej: w środku folderu i w środku znaku. Tu migotanie przechodzi w rytm.</li>
      <li><b class="n">4</b><strong>Rytm zatokowy</strong> (zieleń). Pełne pobudzenie (załamek P, zespół QRS, załamek T) w folderze i zespół QRS następnego pobudzenia za folderem: rytm się powtarza.</li>
    </ul>
  </div>
  <p style="font-size:9.5pt;max-width:none">Wszystkie elementy znaku mają tę samą grubość linii: 1/25 szerokości znaku. Linia izoelektryczna przechodzi przez środek korpusu folderu. Pierwsze pobudzenie powstaje jeszcze w folderze: rytm wraca dzięki danym.</p>
  {stopka(3)}
</section>

<section class="strona">
  <h2><small>03 · Wersje znaku</small>Kiedy której wersji używać</h2>
  <div class="warianty">
    <figure><div class="pole">{inline(W["logo_poziome"], w=270)}</div><figcaption><strong>Pozioma.</strong> Wersja podstawowa: strony www, pisma, prezentacje, stopki.</figcaption></figure>
    <figure><div class="pole">{inline(W["logo_poziome_haslo"], w=270)}</div><figcaption><strong>Pozioma z hasłem.</strong> Materiały kampanii, banery, nagłówki listów do dysponentów.</figcaption></figure>
    <figure><div class="pole">{inline(W["logo_pionowe"], h=150)}</div><figcaption><strong>Pionowa (z hasłem).</strong> Naklejki, plakaty, roll-upy, awatary: gdy miejsce jest zbliżone do kwadratu.</figcaption></figure>
    <figure><div class="pole">{inline(W["znak"], w=220)}</div><figcaption><strong>Znak.</strong> Element graficzny bez nazwy, gdy nazwa akcji jest obok w tekście.</figcaption></figure>
    <figure><div class="pole">{inline(W["sygnet"], h=110)}</div><figcaption><strong>Sygnet.</strong> Małe rozmiary: favicon, ikona aplikacji, znacznik na mapie. Całe przejście mieści się w folderze.</figcaption></figure>
    <figure><div class="pole" style="background:{GRANAT}">{inline(W["logo_poziome_negatyw"], w=270)}</div><figcaption><strong>Negatyw na granacie.</strong> Czerwień i zieleń zastępujemy jaśniejszymi odpowiednikami, żeby zachować kontrast.</figcaption></figure>
  </div>
  {stopka(4)}
</section>

<section class="strona">
  <h2><small>04 · Wersje kolorystyczne</small>Pełny kolor, negatyw i wersje jednobarwne</h2>
  <div class="warianty">
    <figure><div class="pole" style="background:{GRANAT};padding:0">{inline(W["logo_pionowe_negatyw"], h=170)}</div><figcaption><strong>Negatyw, układ pionowy.</strong> „(prze)” w żółci sygnału, tylko na granacie.</figcaption></figure>
    <figure><div class="pole">{inline(W["logo_poziome_mono-granat"], w=270)}</div><figcaption><strong>Jednobarwna granatowa.</strong> Druk jednokolorowy, dokumenty urzędowe. Migotanie i rytm różnią się kształtem, nie tylko kolorem.</figcaption></figure>
    <figure><div class="pole">{inline(W["logo_poziome_czarne"], w=270)}</div><figcaption><strong>Czarna.</strong> Faks, pieczątka, grawer, druk czarno-biały.</figcaption></figure>
    <figure><div class="pole" style="background:{ZIELEN}">{inline(W["logo_poziome_biale"], w=270)}</div><figcaption><strong>Biała.</strong> Na zieleni AED, granacie albo jednolitym, ciemnym fragmencie zdjęcia.</figcaption></figure>
    <figure><div class="pole" style="background:{GRANAT}">{inline(W["sygnet_negatyw"], h=110)}</div><figcaption><strong>Sygnet, negatyw.</strong> Ikona aplikacji i awatar w mediach społecznościowych.</figcaption></figure>
    <figure><div class="pole" style="background:{MIETA}">{inline(W["logo_poziome_haslo"], w=270)}</div><figcaption><strong>Pełny kolor na mięcie.</strong> Plansze, tła stron, karty informacyjne.</figcaption></figure>
  </div>
  {stopka(5)}
</section>

<section class="strona">
  <h2><small>05 · Kolorystyka</small>Pięć kolorów podstawowych i dwa na ciemne tło</h2>
  <div class="kolory">{karty}{karty_c}</div>
  <div class="grid2" style="grid-template-columns:1.3fr 1fr;align-items:start;margin-top:5mm">
    <table class="mala"><tr><th>Para kolorów (WCAG 2.1)</th><th>Kontrast</th><th>Wymagane</th></tr>{tab_k}</table>
    <p style="font-size:9pt">* CMYK przeliczony matematycznie z RGB. Przed drukiem potwierdź go wydrukiem próbnym i dobierz odpowiedniki Pantone.<br><br>
    Progi: elementy graficzne min. 3:1 (WCAG 1.4.11), tekst min. 4,5:1 (WCAG 1.4.3). Na granacie czerwień i zieleń podstawowa mają za mały kontrast, dlatego negatyw używa ich jaśniejszych odpowiedników. Żółci sygnału nie stosujemy na jasnym tle.</p>
  </div>
  {stopka(6)}
</section>

<section class="strona">
  <h2><small>06 · Pole ochronne</small>Wokół znaku zostawiamy wolne miejsce</h2>
  <div class="grid2" style="grid-template-columns:1.5fr 1fr">
    <div>{ochr}</div>
    <div>
      <p>Moduł <strong>x</strong> to ¼ szerokości folderu. Z każdej strony logo zostawiamy co najmniej <strong>1x</strong> wolnego miejsca. W polu ochronnym nie może być tekstu, innych logotypów, krawędzi kadru ani elementów grafiki.</p>
      <p>Pole ochronne mierzymy od skrajnych punktów znaku: początku linii migotania, końca rytmu, górnej krawędzi zakładki folderu i końca nazwy.</p>
      <p>Obok logotypów partnerów (np. dane.gov.pl lub dysponenta) odstęp między znakami wynosi co najmniej <strong>2x</strong>, a znaki mają tę samą wysokość optyczną.</p>
    </div>
  </div>
  {stopka(7)}
</section>

<section class="strona">
  <h2><small>07 · Minimalna wielkość</small>Poniżej tych rozmiarów znak traci czytelność</h2>
  <table><tr><th>Wersja</th><th>Druk (szerokość)</th><th>Ekran (szerokość)</th><th>Uwagi</th></tr>{minima}</table>
  <div class="min">{minima_fig}</div>
  <p style="font-size:9.5pt;max-width:none;margin-top:5mm">Progi ustalono testem ekranowym: pliki SVG wyświetlone w przeglądarce w skali 1:1 (96 dpi) w malejących rozmiarach. Kryteria: fale migotania nie zlewają się w jedną linię, a hasło ma co najmniej 9 px. Rozmiary do druku przeliczono z pikseli z zaokrągleniem w górę; przed drukiem nakładu potwierdź je wydrukiem próbnym. Rysunki powyżej mają rozmiar minimalny przy wydruku księgi w skali 100%. Poniżej progu znaku stosujemy sygnet. Próbki z testu (znak 120, 64 i 40 px, sygnet 32 i 16 px):</p>
  <div class="test">{test_px}</div>
  {stopka(8)}
</section>

<section class="strona">
  <h2><small>08 · Niedozwolone użycia</small>Czego nie robimy ze znakiem</h2>
  <div class="zle-grid">{zle}</div>
  <p style="font-size:9.5pt;max-width:none;margin-top:5mm">Kierunek znaku ma znaczenie: migotanie zawsze po lewej, rytm zawsze po prawej, a punkt spotkania zawsze w środku folderu. Odwrócenie lub zamiana kolorów zmienia przekaz na przeciwny.</p>
  {stopka(9)}
</section>

<section class="strona">
  <h2><small>09 · Typografia</small>Atkinson Hyperlegible: krój zaprojektowany dla czytelności</h2>
  <div class="grid2" style="align-items:start">
    <div>
      <div class="typo-a"><b>Dane</b> (prze)<b>życie</b></div>
      <div class="typo-b" style="margin-top:4mm">{HASLO}</div>
      <div class="abc">AĄBCĆDEĘFGHIJKLŁMNŃOÓPQRSŚTUVWXYZŹŻ<br>aąbcćdeęfghijklłmnńoópqrsśtuvwxyzźż<br>0123456789 · 52.228751 · 2026-11-22</div>
    </div>
    <div>
      <p><strong>Atkinson Hyperlegible</strong> (Braille Institute, licencja SIL Open Font License 1.1) powstał z myślą o osobach słabowidzących. Znaki łatwe do pomylenia (I, l, 1; O, 0) wyraźnie się różnią. Materiały akcji czyta się w pośpiechu i często na telefonie, więc czytelność jest ważniejsza od ozdobności. Krój ma pełne polskie znaki.</p>
      <p><strong>Odmiany:</strong> Bold (700) na nazwę akcji i nagłówki, Regular (400) na „(prze)”, hasło i tekst ciągły.</p>
      <p><strong>Zapis nazwy:</strong> „Dane” i „życie” pogrubione, „(prze)” w odmianie Regular i w kolorze akcentu. W tekście ciągłym piszemy „{NAZWA}” bez wyróżnień.</p>
      <p><strong>Zastępczo:</strong> Arial lub system-ui, gdy nie da się osadzić fontu (np. e-mail). W plikach logo tekst jest zamieniony na krzywe.</p>
    </div>
  </div>
  {stopka(10)}
</section>

<section class="strona">
  <h2><small>10 · Zastosowania</small>Znak na materiałach akcji</h2>
  <div class="zast">
    <figure>{inline(W["naklejka_A6"], w=390, label="Naklejka A6 na szafkę AED")}<figcaption><strong>Naklejka A6 na szafkę AED.</strong> Informuje, że urządzenie jest w Wykazie AED, podaje jego identyfikator i datę sprawdzenia. Kod QR prowadzi do zgłoszenia „nie działa / zamknięty” (na makiecie kod jest nieprawdziwy).</figcaption></figure>
    <figure>{inline(W["odznaka_dysponenta"], w=220, label="Odznaka dysponenta")}<figcaption><strong>Odznaka dysponenta.</strong> Dla instytucji, która opublikowała dane według wzorcowego zakresu. Na stronę www, do stopki e-maila i przy wejściu do budynku.</figcaption></figure>
    <figure>{inline(W["post_1080"], w=250, label="Grafika do mediów społecznościowych")}<figcaption><strong>Post w mediach społecznościowych</strong> (1080 × 1080 px). Hasło jako główny komunikat, logo i hashtag w stopce.</figcaption></figure>
  </div>
  {stopka(11)}
</section>

<section class="strona">
  <h2><small>11 · Pliki i prawa</small>Co jest w paczce</h2>
  <table>
    <tr><th>Plik (folder logo/)</th><th>Formaty</th><th>Zastosowanie</th></tr>
    <tr><td>dane-przezycie_logo_poziome</td><td>SVG, PNG (przezroczyste tło), JPG, PDF</td><td>wersja podstawowa</td></tr>
    <tr><td>dane-przezycie_logo_poziome_haslo</td><td>SVG, PNG, JPG, PDF</td><td>z hasłem akcji</td></tr>
    <tr><td>dane-przezycie_logo_pionowe</td><td>SVG, PNG, JPG, PDF</td><td>naklejki, plakaty, awatary</td></tr>
    <tr><td>dane-przezycie_znak, dane-przezycie_sygnet</td><td>SVG, PNG, JPG, PDF</td><td>element graficzny, ikona, favicon</td></tr>
    <tr><td>…_negatyw, …_mono-granat, …_czarne, …_biale</td><td>SVG (negatywy także PNG)</td><td>wersje kolorystyczne</td></tr>
    <tr><td>materialy/: naklejka_A6, odznaka_dysponenta, post_1080</td><td>SVG</td><td>materiały akcji</td></tr>
  </table>
  <div class="uwaga" style="margin-top:7mm;max-width:225mm">
    <strong>Prawa.</strong> Znak jest autorskim projektem zespołu: kształty narysowano od zera, bez gotowych ikon i grafik. Krój Atkinson Hyperlegible jest na licencji SIL OFL 1.1, która pozwala na użycie komercyjne i osadzanie (tekst licencji w folderze <em>fonty/</em>). Znak nie naśladuje znaku bezpieczeństwa AED według ILCOR i ISO 7010 (serce z błyskawicą i krzyżem), więc nie myli się z oznakowaniem urządzenia.<br>
    <strong>Źródło.</strong> Wszystkie pliki generuje skrypt <em>build_branding.py</em> z jednej definicji geometrii i kolorów; eksport do PNG, JPG i PDF: <em>render.sh</em>.
  </div>
  {stopka(12)}
</section>
</body></html>
"""


if __name__ == "__main__":
    main()
