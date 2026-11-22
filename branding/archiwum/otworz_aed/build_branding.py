#!/usr/bin/env python3
"""
Buduje wstępny znak „Otwórz AED” i księgę znaku.

Wymaga: fonttools (pip install fonttools) – tekst w logo zamieniany jest na krzywe,
więc pliki SVG wyglądają tak samo na każdym komputerze.

    python build_branding.py      → logo/*.svg, ksiega_znaku.html
    bash render.sh                → logo/*.png|jpg|pdf, ksiega_znaku.pdf (Chrome headless)
"""
from __future__ import annotations

from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

HERE = Path(__file__).resolve().parent
LOGO = HERE / "logo"
LOGO.mkdir(exist_ok=True)

BOLD = TTFont(HERE / "fonty" / "AtkinsonHyperlegible-Bold.ttf")
REG = TTFont(HERE / "fonty" / "AtkinsonHyperlegible-Regular.ttf")

# ---------------------------------------------------------------- kolory
KOLORY = [
    # nazwa, hex, rola
    ("Zieleń AED", "#007A45", "kolor główny – sygnet, „AED”, przyciski"),
    ("Granat danych", "#0E2A47", "kolor tekstu, kabłąk kłódki, tła ciemne"),
    ("Czerwień pulsu", "#C8102E", "akcent – alerty, „niesprawny”, max 10% powierzchni"),
    ("Mięta tła", "#F2F7F4", "tło jasne, karty, plansze"),
    ("Żółć sygnału", "#FFC629", "wyróżnienia WYŁĄCZNIE na granacie (kontrast 9,3:1)"),
]
ZIELEN, GRANAT, CZERWIEN, MIETA, ZOLC = (k[1] for k in KOLORY)
BIALY = "#FFFFFF"

NAZWA = "Otwórz AED"
HASLO = "Pokaż, gdzie jest. Powiedz, czy działa."
HASLO_KROTKIE = "dane na ratunek"


def lum(h):
    h = h.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
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


# ---------------------------------------------------------------- sygnet
# Serce-pinezka (wydłużony dół = pinezka mapy), błyskawica jako prześwit (evenodd),
# kabłąk otwartej kłódki nad lewym płatem.
SERCE = ("M50 116C41 100 4 70 4 36C4 18 16 6 30 6C40 6 46 11 50 19"
         "C54 11 60 6 70 6C84 6 96 18 96 36C96 70 59 100 50 116Z")
BLYSK = "M57 22L33 60L48 60L42 92L68 50L53 50L62 22Z"
KABLAK = "M28 22V-8A22 22 0 0 1 72 -8V-1"
SYG_VB = (0, -36, 100, 154)  # x, y, w, h


def sygnet(c_serce=ZIELEN, c_kablak=GRANAT, dx=0.0, dy=0.0, skala=1.0, obrys=False):
    t = f'transform="translate({dx:.2f} {dy:.2f}) scale({skala:.4f})"'
    if obrys:
        return (f'<g {t} fill="none" stroke="{c_serce}" stroke-width="2.5">'
                f'<path d="{KABLAK}" stroke="{c_kablak}"/><path d="{SERCE} {BLYSK}"/></g>')
    return (f'<g {t}><path d="{KABLAK}" fill="none" stroke="{c_kablak}" stroke-width="9" stroke-linecap="round"/>'
            f'<path fill="{c_serce}" fill-rule="evenodd" d="{SERCE} {BLYSK}"/></g>')


def svg(vb, body, title, desc, w=None):
    x, y, ww, hh = vb
    width = w or ww
    height = width * hh / ww
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x:.1f} {y:.1f} {ww:.1f} {hh:.1f}" '
            f'width="{width:.0f}" height="{height:.0f}" role="img" aria-labelledby="t d">'
            f'<title id="t">{title}</title><desc id="d">{desc}</desc>{body}</svg>\n')


ALT = "Logo akcji Otwórz AED: zielone serce w kształcie pinezki z białą błyskawicą i otwartym kabłąkiem kłódki"


# ---------------------------------------------------------------- warianty logo
def zbuduj_poziome(**kw):
    sx, sy, sw, sh = SYG_VB
    c_serce = kw.get("c_serce", ZIELEN)
    c_kablak = kw.get("c_kablak", GRANAT)
    c_txt = kw.get("c_txt", GRANAT)
    c_aed = kw.get("c_aed", ZIELEN)
    haslo = kw.get("haslo", False)
    size = 74
    cap = 0.668 * size
    base = 41 + cap / 2 + (-14 if haslo else 0)
    p1, w1 = tekst("Otwórz", BOLD, size, 122, base, c_txt)
    p2, w2 = tekst("AED", BOLD, size, 122 + w1 + 0.27 * size, base, c_aed)
    body = sygnet(c_serce, c_kablak) + p1 + p2
    width = 122 + w1 + 0.27 * size + w2
    if haslo:
        p3, w3 = tekst(HASLO, REG, 26.5, 123, base + 44, c_txt)
        body += p3
        width = max(width, 123 + w3)
    return (sx, sy, width + 4, sh), body


def zbuduj_pionowe(c_serce=ZIELEN, c_kablak=GRANAT, c_txt=GRANAT, c_aed=ZIELEN):
    size = 60
    gap = 0.27 * size
    _, w1 = tekst("Otwórz", BOLD, size, 0, 0, c_txt)
    _, w2 = tekst("AED", BOLD, size, 0, 0, c_aed)
    total = w1 + gap + w2
    W = max(total, 100) + 8
    cx = W / 2
    body = sygnet(c_serce, c_kablak, dx=cx - 50, dy=0)
    base = 118 + 22 + 0.668 * size
    x0 = cx - total / 2
    p1, _ = tekst("Otwórz", BOLD, size, x0, base, c_txt)
    p2, _ = tekst("AED", BOLD, size, x0 + w1 + gap, base, c_aed)
    p3, w3 = tekst(HASLO_KROTKIE, REG, 26, cx, base + 38, c_txt, tracking=0.6, anchor="middle")
    W = max(W, w3 + 8)
    body = sygnet(c_serce, c_kablak, dx=W / 2 - 50, dy=0)
    x0 = W / 2 - total / 2
    p1, _ = tekst("Otwórz", BOLD, size, x0, base, c_txt)
    p2, _ = tekst("AED", BOLD, size, x0 + w1 + gap, base, c_aed)
    p3, _ = tekst(HASLO_KROTKIE, REG, 26, W / 2, base + 38, c_txt, tracking=0.6, anchor="middle")
    return (0, -38, W, base + 38 + 12 + 38), body + p1 + p2 + p3


def dopasuj(txt, font, size, maxw, tracking=0.0):
    """Zmniejsza stopień pisma tak, żeby tekst zmieścił się w maxw."""
    _, w = tekst(txt, font, size, 0, 0, "#000", tracking)
    return size if w <= maxw else size * maxw / w


def zbuduj_odznake():
    """Odznaka dla dysponenta, który opublikował dane wg wzorca (okrąg)."""
    R = 150
    body = f'<circle cx="0" cy="0" r="{R}" fill="{GRANAT}"/><circle cx="0" cy="0" r="{R - 10}" fill="none" stroke="{ZOLC}" stroke-width="3"/>'
    body += sygnet(BIALY, ZOLC, dx=-31, dy=-90, skala=0.62)
    for txt, font, size, y, kol, tr in [("NASZ AED", BOLD, 28, 44, BIALY, 1.5),
                                        ("JEST NA MAPIE", BOLD, 28, 76, BIALY, 1.5),
                                        ("Otwórz AED · dane otwarte", REG, 15, 106, ZOLC, 0.3)]:
        polcieciwy = (R - 22) ** 2 - (y + 4) ** 2
        maxw = 2 * polcieciwy ** 0.5 - 16
        body += tekst(txt, font, dopasuj(txt, font, size, maxw, tr), 0, y, kol, tracking=tr, anchor="middle")[0]
    return (-R, -R, 2 * R, 2 * R), body


def qr_placeholder(x, y, size, c):
    """Wzór przypominający kod QR – WYŁĄCZNIE makieta, nie da się go zeskanować."""
    import random
    rnd = random.Random(7)
    n = 21
    m = size / n
    out = [f'<rect x="{x}" y="{y}" width="{size}" height="{size}" fill="#fff"/>']
    finder = lambda fx, fy: (
        f'<rect x="{x + fx * m}" y="{y + fy * m}" width="{7 * m}" height="{7 * m}" fill="{c}"/>'
        f'<rect x="{x + (fx + 1) * m}" y="{y + (fy + 1) * m}" width="{5 * m}" height="{5 * m}" fill="#fff"/>'
        f'<rect x="{x + (fx + 2) * m}" y="{y + (fy + 2) * m}" width="{3 * m}" height="{3 * m}" fill="{c}"/>')
    for i in range(n):
        for j in range(n):
            if (i < 8 and j < 8) or (i > 12 and j < 8) or (i < 8 and j > 12):
                continue
            if rnd.random() < 0.45:
                out.append(f'<rect x="{x + i * m:.2f}" y="{y + j * m:.2f}" width="{m:.2f}" height="{m:.2f}" fill="{c}"/>')
    out += [finder(0, 0), finder(14, 0), finder(0, 14)]
    return "".join(out)


def zbuduj_naklejke():
    """Naklejka A6 na szafkę AED (148 × 105 mm; 1 mm = 2 jednostki)."""
    W, H = 296, 210
    b = (f'<defs><clipPath id="naklejka-clip"><rect width="{W}" height="{H}" rx="10"/></clipPath></defs>'
         f'<g clip-path="url(#naklejka-clip)"><rect width="{W}" height="{H}" fill="{ZIELEN}"/>'
         f'<rect y="112" width="{W}" height="{H - 112}" fill="{GRANAT}"/></g>')
    b += sygnet(BIALY, GRANAT, dx=20, dy=30, skala=0.5)
    x = 80
    for txt, font, size, y in [("Ten AED jest na mapie", BOLD, 22, 48),
                               ("Sprawdzony: 2026-11-15", REG, 14, 72),
                               ("ID: PL-AED-0000001", REG, 14, 92)]:
        b += tekst(txt, font, dopasuj(txt, font, size, W - x - 16), x, y, BIALY)[0]
    q = 74
    qx, qy = W - q - 18, 124
    col = qx - 20 - 20
    for txt, font, size, y, kol in [("Nie działa? Zamknięty?", BOLD, 17, 146, ZOLC),
                                    ("Zeskanuj kod i zgłoś.", REG, 14, 168, BIALY),
                                    ("Otwórz AED · dane.gov.pl", REG, 11, 194, BIALY)]:
        b += tekst(txt, font, dopasuj(txt, font, size, col), 20, y, kol)[0]
    b += qr_placeholder(qx, qy, q, GRANAT)
    b += tekst("makieta QR", REG, 7, qx + q / 2, qy + q + 9, BIALY, anchor="middle")[0]
    return (0, 0, W, H), b


def zapisz(nazwa, vb, body, title=f"Logo {NAZWA}", desc=ALT, w=None):
    (LOGO / nazwa).write_text(svg(vb, body, title, desc, w), encoding="utf-8")
    return vb, body


def main():
    warianty = {}
    vb, body = zbuduj_poziome()
    warianty["poziome"] = zapisz("otworz-aed_logo_poziome.svg", vb, body)
    vb, body = zbuduj_poziome(haslo=True)
    warianty["poziome_haslo"] = zapisz("otworz-aed_logo_poziome_haslo.svg", vb, body)
    vb, body = zbuduj_pionowe()
    warianty["pionowe"] = zapisz("otworz-aed_logo_pionowe.svg", vb, body)
    warianty["sygnet"] = zapisz("otworz-aed_sygnet.svg", SYG_VB, sygnet(), title="Sygnet Otwórz AED")
    vb, body = zbuduj_poziome(c_serce=GRANAT, c_kablak=GRANAT, c_txt=GRANAT, c_aed=GRANAT)
    warianty["mono"] = zapisz("otworz-aed_logo_poziome_mono-granat.svg", vb, body)
    vb, body = zbuduj_poziome(c_serce="#000000", c_kablak="#000000", c_txt="#000000", c_aed="#000000")
    warianty["czarne"] = zapisz("otworz-aed_logo_poziome_czarne.svg", vb, body)
    vb, body = zbuduj_poziome(c_serce=BIALY, c_kablak=BIALY, c_txt=BIALY, c_aed=BIALY)
    warianty["negatyw"] = zapisz("otworz-aed_logo_poziome_negatyw.svg", vb, body)
    vb, body = zbuduj_poziome(c_serce=BIALY, c_kablak=ZOLC, c_txt=BIALY, c_aed=BIALY)
    warianty["na_granacie"] = zapisz("otworz-aed_logo_poziome_na-granacie.svg", vb, body)
    warianty["odznaka"] = zapisz("otworz-aed_odznaka_dysponenta.svg", *zbuduj_odznake(),
                                 title="Odznaka: Nasz AED jest na mapie",
                                 desc="Okrągła granatowa odznaka z białym sygnetem i napisem Nasz AED jest na mapie")
    warianty["naklejka"] = zapisz("otworz-aed_naklejka_A6.svg", *zbuduj_naklejke(),
                                  title="Naklejka na szafkę AED",
                                  desc="Zielona naklejka: Ten AED jest na mapie, data sprawdzenia, ID i kod QR do zgłoszenia problemu")
    (HERE / "ksiega_znaku.html").write_text(ksiega(warianty), encoding="utf-8")
    print("OK:", ", ".join(sorted(p.name for p in LOGO.glob("*.svg"))))


# ---------------------------------------------------------------- księga znaku
def inline(v, w=None, h=None, style="", obrys_vb=None):
    vb, body = v
    x, y, ww, hh = vb
    size = (f'width="{w}"' if w else "") + (f' height="{h}"' if h else "")
    return (f'<svg viewBox="{x:.1f} {y:.1f} {ww:.1f} {hh:.1f}" {size} style="{style}" '
            f'role="img" aria-label="{ALT}">{body}</svg>')


def ksiega(W):
    poz = W["poziome"]
    vb = poz[0]
    x_unit = 23  # x = 1/4 szerokości sygnetu (92 j.) ≈ 23 j.

    # pole ochronne – rysunek
    px, py, pw, ph = vb
    m = x_unit
    ochr = (f'<svg viewBox="{px - m - 4} {py - m - 4} {pw + 2 * m + 8} {ph + 2 * m + 8}" width="620" role="img" '
            f'aria-label="Schemat pola ochronnego wokół logo">'
            f'<rect x="{px - m}" y="{py - m}" width="{pw + 2 * m}" height="{ph + 2 * m}" fill="{MIETA}" stroke="{CZERWIEN}" stroke-dasharray="6 4" stroke-width="1.5"/>'
            f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" fill="#fff" stroke="#9aa" stroke-width="0.8"/>'
            f'{poz[1]}'
            + "".join(
                f'<g><rect x="{gx}" y="{gy}" width="{m}" height="{m}" fill="{CZERWIEN}" fill-opacity=".18" stroke="{CZERWIEN}" stroke-width=".8"/>'
                f'<text x="{gx + m / 2}" y="{gy + m / 2 + 5}" font-size="14" text-anchor="middle" fill="{CZERWIEN}" font-family="Atkinson Hyperlegible">x</text></g>'
                for gx, gy in [(px - m, py + ph / 2 - m / 2), (px + pw, py + ph / 2 - m / 2), (px + pw / 2 - m / 2, py - m), (px + pw / 2 - m / 2, py + ph)])
            + '</svg>')

    karty_kolorow = ""
    for nazwa, hx, rola in KOLORY:
        r, g, b = rgb(hx)
        c, mm, yy, k = cmyk(hx)
        txt = BIALY if lum(hx) < 0.3 else GRANAT
        kb = kontrast(hx, BIALY)
        kg = kontrast(hx, GRANAT)
        karty_kolorow += f"""
        <div class="kolor">
          <div class="probka" style="background:{hx};color:{txt}">{nazwa}</div>
          <dl>
            <dt>HEX</dt><dd>{hx}</dd>
            <dt>RGB</dt><dd>{r} {g} {b}</dd>
            <dt>CMYK*</dt><dd>{c} {mm} {yy} {k}</dd>
            <dt>Kontrast</dt><dd>z bielą {kb:.1f}:1 · z granatem {kg:.1f}:1</dd>
          </dl>
          <p class="rola">{rola}</p>
        </div>"""

    def zly(opis, inner, bg="#fff"):
        return (f'<figure class="zle"><div class="pole" style="background:{bg}">{inner}</div>'
                f'<figcaption><span class="x" aria-hidden="true">✕</span> {opis}</figcaption></figure>')

    vb_p, body_p = poz
    xv, yv, wv, hv = vb_p
    _, body_zle_kolory = zbuduj_poziome(c_serce="#7B2CBF", c_kablak="#F72585", c_txt="#3A86FF", c_aed="#7B2CBF")
    obrys = sygnet(obrys=True)
    zle = "".join([
        zly("Nie rozciągaj ani nie ściskaj znaku", inline(poz, w=150, style="transform:scaleX(1.5);transform-origin:center")),
        zly("Nie obracaj znaku", inline(poz, w=190, style="transform:rotate(-14deg)")),
        zly("Nie zmieniaj kolorów", f'<svg viewBox="{xv} {yv} {wv} {hv}" width="230">{body_zle_kolory}</svg>'),
        zly("Nie dodawaj cieni, poświat ani gradientów", inline(poz, w=230, style="filter:drop-shadow(6px 6px 3px rgba(0,0,0,.55))")),
        zly("Nie umieszczaj na tle o niskim kontraście", inline(poz, w=230), bg="#3D9A6A"),
        zly("Nie używaj samego konturu", f'<svg viewBox="{SYG_VB[0]} {SYG_VB[1]} {SYG_VB[2]} {SYG_VB[3]}" width="70">{obrys}</svg>'),
        zly("Nie zmieniaj kroju pisma ani układu", f'<svg viewBox="0 -36 330 154" width="230">{sygnet()}<text x="112" y="70" font-family="Comic Sans MS, cursive" font-size="44" fill="{GRANAT}">otwórz aed!</text></svg>'),
        zly("Nie wstawiaj znaku w zdjęcie bez jednolitego tła", inline(poz, w=230),
            bg="repeating-linear-gradient(45deg,#7a9 0 14px,#c96 14px 28px,#467 28px 42px)"),
    ])

    font_css = """
    @font-face{font-family:'Atkinson Hyperlegible';src:url('fonty/AtkinsonHyperlegible-Regular.ttf') format('truetype');font-weight:400}
    @font-face{font-family:'Atkinson Hyperlegible';src:url('fonty/AtkinsonHyperlegible-Bold.ttf') format('truetype');font-weight:700}
    """

    return f"""<!doctype html>
<html lang="pl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Księga znaku Otwórz AED</title>
<style>
{font_css}
:root{{--zielen:{ZIELEN};--granat:{GRANAT};--czerwien:{CZERWIEN};--mieta:{MIETA};--zolc:{ZOLC}}}
@page{{size:297mm 210mm;margin:0}}
*{{box-sizing:border-box}}
html,body{{margin:0;background:#fff;color:var(--granat);font-family:'Atkinson Hyperlegible',Arial,sans-serif;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
.strona{{width:297mm;height:210mm;padding:16mm 18mm 14mm;position:relative;overflow:hidden;page-break-after:always;break-after:page}}
.strona:last-child{{page-break-after:auto}}
.stopka{{position:absolute;left:18mm;right:18mm;bottom:8mm;display:flex;justify-content:space-between;font-size:9pt;opacity:.75}}
h1{{font-size:30pt;margin:0 0 6mm;line-height:1.1}}
h2{{font-size:22pt;margin:0 0 6mm;line-height:1.15}}
h2 small{{display:block;font-size:10pt;font-weight:400;letter-spacing:.12em;text-transform:uppercase;color:var(--zielen);margin-bottom:2mm}}
p{{font-size:11.5pt;line-height:1.5;margin:0 0 3mm;max-width:165mm}}
.okladka{{background:var(--mieta);display:flex;flex-direction:column;justify-content:center;padding-left:28mm}}
.okladka .meta{{margin-top:12mm;font-size:11pt;line-height:1.6}}
.badge{{display:inline-block;background:var(--czerwien);color:#fff;font-weight:700;font-size:9pt;padding:1.5mm 3mm;border-radius:2mm;letter-spacing:.06em}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:10mm;align-items:center}}
.koncepcja{{font-size:13pt;line-height:1.6;max-width:none}}
.hasla li{{font-size:12pt;margin-bottom:2mm}}
.warianty{{display:grid;grid-template-columns:repeat(3,1fr);gap:6mm}}
.warianty figure{{margin:0;border:1px solid #d5e1da;border-radius:3mm;padding:5mm;display:flex;flex-direction:column;justify-content:space-between;min-height:58mm}}
.warianty figure .pole{{flex:1;display:flex;align-items:center;justify-content:center;border-radius:2mm}}
figcaption{{font-size:9.5pt;margin-top:3mm;line-height:1.35}}
.kolory{{display:grid;grid-template-columns:repeat(5,1fr);gap:5mm}}
.probka{{height:34mm;border-radius:3mm;padding:3mm;font-weight:700;font-size:11pt;display:flex;align-items:flex-end;border:1px solid #d5e1da}}
dl{{display:grid;grid-template-columns:auto 1fr;gap:1mm 3mm;font-size:9pt;margin:3mm 0 2mm}}
dt{{font-weight:700}} dd{{margin:0}}
.rola{{font-size:9pt;line-height:1.35}}
.zle-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:5mm}}
.zle{{margin:0}}
.zle .pole{{height:38mm;border:1px solid #d5e1da;border-radius:3mm;display:flex;align-items:center;justify-content:center;overflow:hidden;position:relative}}
.zle .pole::after{{content:"";position:absolute;inset:0;background:linear-gradient(to top right,transparent calc(50% - 1.5px),{CZERWIEN} calc(50% - 1.5px),{CZERWIEN} calc(50% + 1.5px),transparent calc(50% + 1.5px));opacity:.85}}
.x{{color:var(--czerwien);font-weight:700}}
.min{{display:flex;gap:14mm;align-items:flex-end;margin-top:6mm}}
.min figure{{margin:0;text-align:left}}
table{{border-collapse:collapse;font-size:10.5pt;margin-top:4mm}}
th,td{{border-bottom:1px solid #d5e1da;padding:2mm 4mm 2mm 0;text-align:left;vertical-align:top}}
th{{font-weight:700}}
.typo-a{{font-size:44pt;font-weight:700;line-height:1}}
.typo-b{{font-size:20pt;line-height:1.2}}
.abc{{font-size:13pt;letter-spacing:.03em;line-height:1.6;margin-top:3mm}}
.zast{{display:grid;grid-template-columns:1.2fr 1fr 1fr;gap:8mm;align-items:start}}
.zast figure{{margin:0}}
.uwaga{{background:var(--mieta);border-left:2mm solid var(--zielen);padding:4mm 5mm;font-size:10.5pt;line-height:1.5;border-radius:1mm}}
</style></head><body>

<section class="strona okladka">
  {inline(W["poziome_haslo"], w=820)}
  <div class="meta">
    <strong style="font-size:20pt">Księga znaku</strong><br>
    Akcja promocyjna dla zadania „Misja AED – Dane na ratunek” · HackNation 2026<br>
    Wersja 0.1 (wstępna) · 2026-11-21 &nbsp; <span class="badge">SZKIC DO DALSZYCH PRAC</span>
  </div>
</section>

<section class="strona">
  <h2><small>01 · Koncepcja</small>Serce, pinezka i otwarta kłódka</h2>
  <div class="grid2">
    <div>
      <p class="koncepcja">Znak łączy trzy elementy: serce, pinezkę mapy i otwartą kłódkę. Serce z błyskawicą to powszechnie rozpoznawany symbol defibrylatora, więc znak działa bez słów. Wydłużony dół serca zamienia je w pinezkę, bo każdy AED ma być na mapie, z dokładnym położeniem. Otwarty kabłąk kłódki mówi o dwóch rzeczach naraz: o otwartych danych publikowanych na dane.gov.pl i o szafce, której nikt nie zamyka na klucz. Zieleń nawiązuje do międzynarodowego oznakowania AED, a granat do rzetelności danych publicznych.</p>
      <h3 style="margin:8mm 0 2mm;font-size:13pt">Nazwa i hasło</h3>
      <ul class="hasla">
        <li><strong>Nazwa akcji:</strong> {NAZWA}</li>
        <li><strong>Hasło główne:</strong> {HASLO}</li>
        <li><strong>Podpis pod znakiem:</strong> {HASLO_KROTKIE}</li>
        <li><strong>Tag w dane.gov.pl:</strong> OtworzAED</li>
      </ul>
    </div>
    <div style="display:flex;justify-content:center">{inline(W["sygnet"], w=260)}</div>
  </div>
  <div class="stopka"><span>Otwórz AED · Księga znaku v0.1</span><span>2</span></div>
</section>

<section class="strona">
  <h2><small>02 · Wersje znaku</small>Kiedy której wersji używać</h2>
  <div class="warianty">
    <figure><div class="pole">{inline(W["poziome"], w=250)}</div><figcaption><strong>Podstawowa pozioma.</strong> Domyślna wersja na stronach, w prezentacjach i pismach.</figcaption></figure>
    <figure><div class="pole">{inline(W["pionowe"], h=150)}</div><figcaption><strong>Pionowa z podpisem.</strong> Plakaty, roll-upy, okładki – gdy miejsca jest więcej w pionie.</figcaption></figure>
    <figure><div class="pole">{inline(W["sygnet"], h=140)}</div><figcaption><strong>Sygnet.</strong> Ikona aplikacji, znacznik na mapie, awatar, favicon. Tylko gdy nazwa akcji jest obok lub znana z kontekstu.</figcaption></figure>
    <figure><div class="pole" style="background:#fff">{inline(W["mono"], w=250)}</div><figcaption><strong>Monochromatyczna (granat / czerń).</strong> Druk jednobarwny, pieczątki, faks, grawer.</figcaption></figure>
    <figure><div class="pole" style="background:{ZIELEN}">{inline(W["negatyw"], w=250)}</div><figcaption><strong>Negatyw.</strong> Biały znak na zieleni AED lub ciemnym zdjęciu z jednolitym fragmentem.</figcaption></figure>
    <figure><div class="pole" style="background:{GRANAT}">{inline(W["na_granacie"], w=250)}</div><figcaption><strong>Na granacie.</strong> Biały znak z kabłąkiem w żółci sygnału – materiały dla dysponentów, odznaka.</figcaption></figure>
  </div>
  <div class="stopka"><span>Otwórz AED · Księga znaku v0.1</span><span>3</span></div>
</section>

<section class="strona">
  <h2><small>03 · Kolorystyka</small>Pięć kolorów, sprawdzonych pod WCAG</h2>
  <div class="kolory">{karty_kolorow}</div>
  <p style="margin-top:6mm;font-size:9.5pt;max-width:none">* Wartości CMYK przeliczone matematycznie z RGB – przed drukiem trzeba je potwierdzić wydrukiem próbnym (proofem) i dobrać odpowiedniki Pantone. Kontrast liczony wg WCAG 2.2: tekst zwykły wymaga min. 4,5:1, duży 3:1. Zieleń, granat i czerwień spełniają 4,5:1 na białym tle; żółci sygnału nie używamy na jasnym tle.</p>
  <div class="stopka"><span>Otwórz AED · Księga znaku v0.1</span><span>4</span></div>
</section>

<section class="strona">
  <h2><small>04 · Pole ochronne</small>Wokół znaku zostawiamy wolne miejsce</h2>
  <div class="grid2" style="grid-template-columns:1.4fr 1fr">
    <div>{ochr}</div>
    <div>
      <p>Moduł <strong>x</strong> to ¼ szerokości sygnetu (serca). Z każdej strony znaku zostawiamy co najmniej <strong>1x</strong> wolnej przestrzeni. W polu ochronnym nie może być tekstu, innych logotypów, krawędzi kadru ani elementów grafiki.</p>
      <p>Przy zestawieniu z logotypami partnerów (np. instytucji publikującej zbiór) odstęp między znakami wynosi co najmniej <strong>2x</strong>, a znaki mają taką samą wysokość optyczną.</p>
      <p>Pole ochronne liczymy od skrajnych punktów znaku: górnej krawędzi kabłąka, czubka pinezki i końca słowa „AED”.</p>
    </div>
  </div>
  <div class="stopka"><span>Otwórz AED · Księga znaku v0.1</span><span>5</span></div>
</section>

<section class="strona">
  <h2><small>05 · Minimalna wielkość</small>Poniżej tych rozmiarów znak traci czytelność</h2>
  <table>
    <tr><th>Wersja</th><th>Druk (szerokość)</th><th>Ekran (szerokość)</th><th>Uwagi</th></tr>
    <tr><td>Podstawowa pozioma</td><td>30 mm</td><td>120 px</td><td>Poniżej – użyj samego sygnetu</td></tr>
    <tr><td>Pozioma z hasłem</td><td>55 mm</td><td>220 px</td><td>Hasło musi mieć min. 7 pt / 12 px</td></tr>
    <tr><td>Pionowa z podpisem</td><td>25 mm</td><td>100 px</td><td></td></tr>
    <tr><td>Sygnet</td><td>8 mm (wysokość)</td><td>24 px (wysokość)</td><td>24 px = minimalny cel dotykowy z WCAG 2.2 (2.5.8)</td></tr>
  </table>
  <div class="min">
    <figure>{inline(W["poziome"], w=113)}<figcaption>30 mm</figcaption></figure>
    <figure>{inline(W["pionowe"], w=95)}<figcaption>25 mm</figcaption></figure>
    <figure>{inline(W["sygnet"], h=30)}<figcaption>8 mm</figcaption></figure>
  </div>
  <div class="stopka"><span>Otwórz AED · Księga znaku v0.1</span><span>6</span></div>
</section>

<section class="strona">
  <h2><small>06 · Niedozwolone użycia</small>Czego nie robimy ze znakiem</h2>
  <div class="zle-grid">{zle}</div>
  <div class="stopka"><span>Otwórz AED · Księga znaku v0.1</span><span>7</span></div>
</section>

<section class="strona">
  <h2><small>07 · Typografia</small>Atkinson Hyperlegible – krój dla czytelności</h2>
  <div class="grid2" style="align-items:start">
    <div>
      <div class="typo-a">Otwórz AED</div>
      <div class="typo-b" style="margin-top:4mm">Pokaż, gdzie jest. Powiedz, czy działa.</div>
      <div class="abc">AĄBCĆDEĘFGHIJKLŁMNŃOÓPQRSŚTUVWXYZŹŻ<br>aąbcćdeęfghijklłmnńoópqrsśtuvwxyzźż<br>0123456789 · 52.228751 · 2026-11-21</div>
    </div>
    <div>
      <p><strong>Atkinson Hyperlegible</strong> (Braille Institute, licencja SIL Open Font License 1.1) powstał z myślą o osobach słabowidzących: litery łatwo pomylić (I, l, 1; O, 0) są wyraźnie różne. To pasuje do akcji, której materiały czyta się w stresie, często z telefonu. Pełne polskie znaki diakrytyczne.</p>
      <p><strong>Odmiany:</strong> Bold (700) – nagłówki, nazwa akcji; Regular (400) – tekst ciągły, hasło.</p>
      <p><strong>Zastępczo:</strong> Arial / system-ui, gdy osadzenie fontu jest niemożliwe (np. e-mail).</p>
      <p>W plikach logo tekst jest zamieniony na krzywe, więc znak nie zależy od zainstalowanych fontów.</p>
    </div>
  </div>
  <div class="stopka"><span>Otwórz AED · Księga znaku v0.1</span><span>8</span></div>
</section>

<section class="strona">
  <h2><small>08 · Zastosowania</small>Znak w działaniu</h2>
  <div class="zast">
    <figure>{inline(W["naklejka"], w=380)}<figcaption><strong>Naklejka A6 na szafkę AED.</strong> Data sprawdzenia, ID ze zbioru krajowego i kod QR do zgłoszenia „nie działa / zamknięty”. (Kod QR na makiecie jest nieprawdziwy.)</figcaption></figure>
    <figure>{inline(W["odznaka"], w=210)}<figcaption><strong>Odznaka dysponenta.</strong> Dla instytucji, która opublikowała dane wg wzorca. Do użycia na stronie www, w stopce e-maila i przy wejściu do budynku.</figcaption></figure>
    <figure><div style="display:flex;gap:6mm;align-items:center">
      <svg viewBox="0 0 120 120" width="100" role="img" aria-label="Awatar: sygnet na zielonym kole"><circle cx="60" cy="60" r="60" fill="{ZIELEN}"/>{sygnet(BIALY, GRANAT, dx=31, dy=31, skala=0.58)}</svg>
      <svg viewBox="0 0 40 52" width="40" role="img" aria-label="Znacznik mapy: sprawny AED">{sygnet(ZIELEN, GRANAT, dx=4, dy=12, skala=0.32)}</svg>
      <svg viewBox="0 0 40 52" width="40" role="img" aria-label="Znacznik mapy: niesprawny AED">{sygnet("#8A97A3", CZERWIEN, dx=4, dy=12, skala=0.32)}</svg>
    </div><figcaption><strong>Awatar i znaczniki na mapie.</strong> Sprawny AED – zieleń; niesprawny lub nieznany – szarość z czerwonym kabłąkiem. Kolor nigdy nie jest jedynym nośnikiem informacji: znacznik ma też etykietę tekstową (WCAG 1.4.1).</figcaption></figure>
  </div>
  <div class="stopka"><span>Otwórz AED · Księga znaku v0.1</span><span>9</span></div>
</section>

<section class="strona">
  <h2><small>09 · Pliki i prawa</small>Co jest w paczce</h2>
  <table>
    <tr><th>Plik</th><th>Formaty</th><th>Zastosowanie</th></tr>
    <tr><td>otworz-aed_logo_poziome</td><td>SVG, PNG (przezroczyste), JPG, PDF</td><td>wersja podstawowa</td></tr>
    <tr><td>otworz-aed_logo_poziome_haslo</td><td>SVG, PNG, JPG, PDF</td><td>z hasłem akcji</td></tr>
    <tr><td>otworz-aed_logo_pionowe</td><td>SVG, PNG, JPG, PDF</td><td>plakaty</td></tr>
    <tr><td>otworz-aed_sygnet</td><td>SVG, PNG, JPG, PDF</td><td>ikona, awatar, mapa</td></tr>
    <tr><td>…_mono-granat, …_czarne, …_negatyw, …_na-granacie</td><td>SVG</td><td>wersje achromatyczne i odwrócone</td></tr>
    <tr><td>otworz-aed_odznaka_dysponenta, otworz-aed_naklejka_A6</td><td>SVG</td><td>materiały akcji</td></tr>
  </table>
  <div class="uwaga" style="margin-top:8mm;max-width:200mm">
    <strong>Prawa.</strong> Znak jest autorskim projektem zespołu (kształty narysowane od zera, bez gotowych ikon). Krój Atkinson Hyperlegible jest na licencji SIL OFL 1.1 – pozwala na użycie komercyjne i osadzanie; licencja leży w folderze <em>fonty/</em>. Znak nie kopiuje znaku bezpieczeństwa AED wg ILCOR / ISO 7010 (brak krzyża, inny kształt), więc nie myli się z oznakowaniem urządzenia.<br>
    <strong>Status.</strong> Wersja wstępna do przeglądu w zespole: kerning, grubość kabłąka w małych rozmiarach i odpowiedniki Pantone do dopracowania.
  </div>
  <div class="stopka"><span>Otwórz AED · Księga znaku v0.1</span><span>10</span></div>
</section>
</body></html>
"""


if __name__ == "__main__":
    main()
