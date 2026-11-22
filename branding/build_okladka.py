#!/usr/bin/env python3
"""
Okładka zgłoszenia HackNation (800 × 600 px, 4:3): znak akcji „Dane (prze)życie”, hasło
i podpis „Wykaz AED w portalu dane.gov.pl”. Geometria znaku, kolory i krój pochodzą
z build_branding.py, więc okładka jest zgodna z księgą znaku (wersja negatywowa na granacie).

    uv run --with fonttools --with pillow python branding/build_okladka.py

Wynik: branding/okladka/okladka_800x600.svg, .png i .jpg. PNG renderuje Chrome lub Edge
w trybie headless (zmienna CHROME wskazuje inną przeglądarkę), JPG powstaje z PNG (Pillow).
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_branding as bb  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / "okladka"
W, H = 800, 600
NEG = bb.PALETY["negatyw"]

PRZEGLADARKI = [
    os.environ.get("CHROME", ""),
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "google-chrome",
    "chromium",
]


def okladka():
    b = f'<rect width="{W}" height="{H}" fill="{bb.GRANAT}"/>'
    # znak (negatyw): wyśrodkowany u góry
    zw = 270
    zh = bb.ZNAK_VB[3] * zw / bb.ZNAK_VB[2]
    zy = 52
    b += bb.umiesc((W - zw) / 2, zy, zw, **NEG["znak"])
    # nazwa akcji
    y = zy + zh + 82
    wm, _ = bb.wordmark(W / 2, y, 70, NEG, haslo=False, anchor="middle")
    b += wm
    # hasło: „Twoje dane – ” biel, „czyjeś życie.” żółć (wyróżnienie na granacie, jak w poście)
    y += 62
    hs = 35
    t1, t2 = "Twoje dane – ", "czyjeś życie."
    w1, w2 = bb.szer(t1, bb.BOLD, hs), bb.szer(t2, bb.BOLD, hs)
    x0 = (W - w1 - w2) / 2
    b += bb.tekst(t1, bb.BOLD, hs, x0, y, bb.BIALY)[0] + bb.tekst(t2, bb.BOLD, hs, x0 + w1, y, bb.ZOLC)[0]
    # separator
    y += 44
    b += f'<rect x="{W / 2 - 40}" y="{y}" width="80" height="3" rx="1.5" fill="{bb.ZIELEN_JASNA}"/>'
    # co to jest
    y += 58
    t = "Wykaz AED w portalu dane.gov.pl"
    b += bb.tekst(t, bb.BOLD, bb.dopasuj(t, bb.BOLD, 34, W - 120), W / 2, y, bb.BIALY, anchor="middle")[0]
    y += 40
    t = "Jeden wykaz defibrylatorów z danych wielu dysponentów"
    b += bb.tekst(t, bb.REG, bb.dopasuj(t, bb.REG, 22, W - 120), W / 2, y, bb.MIETA, anchor="middle")[0]
    # stopka
    t = "HackNation 2026 · Misja AED – Dane na ratunek · #DanePrzeżycie"
    b += bb.tekst(t, bb.REG, 16, W / 2, H - 26, bb.MIETA, anchor="middle")[0]
    return (0, 0, W, H), b


def przegladarka():
    for p in PRZEGLADARKI:
        if p and (Path(p).exists() or shutil.which(p)):
            return p
    raise SystemExit("Brak Chrome/Edge; ustaw zmienną CHROME.")


def main():
    OUT.mkdir(exist_ok=True)
    vb, body = okladka()
    opis = ("Granatowa okładka: znak akcji Dane (prze)życie, hasło Twoje dane – czyjeś życie "
            "i podpis Wykaz AED w portalu dane.gov.pl")
    svg = bb.svg(vb, body, "Okładka: Dane (prze)życie, Wykaz AED w portalu dane.gov.pl", opis)
    p_svg = OUT / "okladka_800x600.svg"
    p_svg.write_text(svg, encoding="utf-8")

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "o.svg").write_text(svg, encoding="utf-8")
        (tmp / "o.html").write_text(
            '<!doctype html><html><head><meta charset="utf-8"><style>html,body{margin:0;background:#0E2A47;overflow:hidden}'
            f'img{{display:block;width:{W}px;height:{H}px}}</style></head><body><img src="o.svg" alt=""></body></html>',
            encoding="utf-8")
        shot = tmp / "o.png"
        subprocess.run([przegladarka(), "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        "--force-device-scale-factor=1", f"--window-size={W},{H}", f"--screenshot={shot}",
                        (tmp / "o.html").as_uri()], check=False, capture_output=True, timeout=120)
        img = Image.open(shot).convert("RGB")
        if img.size != (W, H):  # niektóre wersje Chrome dokładają pasek okna: przytnij do treści
            img = img.crop((0, 0, W, H))
    img.save(OUT / "okladka_800x600.png", optimize=True)
    img.save(OUT / "okladka_800x600.jpg", quality=92, optimize=True)
    for f in ("okladka_800x600.png", "okladka_800x600.jpg"):
        with Image.open(OUT / f) as im:
            assert im.size == (W, H), (f, im.size)
        print(f"OK: okladka/{f} {W}x{H}, {(OUT / f).stat().st_size / 1024:.0f} kB")


if __name__ == "__main__":
    main()
