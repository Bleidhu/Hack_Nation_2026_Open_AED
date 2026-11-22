"""Składa kopie plików do zgłoszenia w ZGLOSZENIE/ (oryginały zostają na swoich miejscach).

Uruchomienie z katalogu głównego repo, po `python demo/build_demo.py` (biblioteka standardowa i git):

    python demo/zloz_zgloszenie.py

ZGLOSZENIE/README.md jest pisane ręcznie i skrypt go nie zmienia. Względne odnośniki w kopiach są przepisane tak,
żeby prowadziły do oryginałów w repo.
"""

import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "ZGLOSZENIE"
ORIGINAL_COMMIT = "a1adc22"
GENERATED = ["INSTRUKCJA_DLA_JURY.md", "DODATKOWE_INFORMACJE.md", "ZMIANY_W_PORTALU.md", "prototyp", "wzorcowy_zakres_danych.xlsx", "kod", "dane",
             "prezentacja", "logotyp", "ksiega_znaku.pdf", "wideo", "INSTRUKCJA_DLA_JURY.pdf", "DODATKOWE_INFORMACJE.pdf"]
LOGOTYPY = ["dane-przezycie_logo_poziome", "dane-przezycie_logo_poziome_haslo", "dane-przezycie_logo_pionowe",
            "dane-przezycie_znak", "dane-przezycie_sygnet"]


def relink_markdown(text, prefix):
    return re.sub(r"\]\((?!https?:|#)([^)]+)\)", lambda m: f"]({prefix}{m.group(1)})", text)


def copy_markdown(name):
    text = (ROOT / name).read_text(encoding="utf-8")
    (OUT / name).write_text(relink_markdown(text, "../"), encoding="utf-8", newline="\n")


def copy_prototype():
    target = OUT / "prototyp"
    html = (ROOT / "demo" / "index.html").read_text(encoding="utf-8")
    (target / "wynik").mkdir(parents=True)
    (target / "index.html").write_text(html.replace('href="../', 'href="../../'), encoding="utf-8", newline="\n")
    shutil.copytree(ROOT / "demo" / "zrzuty", target / "zrzuty")
    for path in sorted((ROOT / "demo" / "wynik").iterdir()):  # logi, statystyki i CSV, do których linkuje prototyp
        if path.is_file():
            shutil.copy2(path, target / "wynik" / path.name)
    shutil.copytree(ROOT / "demo" / "integrator", target / "integrator")  # dodatek: wyniki integratora


def write_portal_patch():
    (OUT / "kod").mkdir()
    patch = subprocess.run(
        ["git", "diff", ORIGINAL_COMMIT, "HEAD", "--", "portal/backend"], cwd=ROOT, check=True, capture_output=True
    ).stdout
    (OUT / "kod" / "zmiany_portalu_wzgledem_oryginalu.patch").write_bytes(patch)


def main():
    OUT.mkdir(exist_ok=True)
    for name in GENERATED:
        path = OUT / name
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()
    copy_markdown("INSTRUKCJA_DLA_JURY.md")
    copy_markdown("DODATKOWE_INFORMACJE.md")
    copy_markdown("ZMIANY_W_PORTALU.md")
    for name in ("INSTRUKCJA_DLA_JURY.pdf", "DODATKOWE_INFORMACJE.pdf"):  # PDF z warstwą tekstową: demo/build_pdf_dokumentow.py
        if (ROOT / name).exists():
            shutil.copy2(ROOT / name, OUT / name)
        else:
            print(f"Uwaga: brak {name}, najpierw uruchom: python demo/build_pdf_dokumentow.py")
    copy_prototype()
    shutil.copy2(ROOT / "format_danych" / "wzorcowy_zakres_danych.xlsx", OUT / "wzorcowy_zakres_danych.xlsx")
    (OUT / "dane").mkdir()
    shutil.copy2(ROOT / "demo" / "wynik" / "zestawienie_aed.csv", OUT / "dane" / "wykaz_aed_wynik_agregacji.csv")
    shutil.copytree(ROOT / "format_danych" / "przyklady" / "xml", OUT / "dane" / "xml")  # przykłady XML dostawcy
    shutil.copy2(ROOT / "format_danych" / "schemat" / "aed_punkty.xsd", OUT / "dane" / "aed_punkty.xsd")
    shutil.copytree(ROOT / "format_danych" / "przyklady" / "opis", OUT / "dane" / "opis")  # opis zbioru XML + CSV + md5
    shutil.copy2(ROOT / "format_danych" / "schemat" / "aed_opis_zbioru.xsd", OUT / "dane" / "aed_opis_zbioru.xsd")
    write_portal_patch()
    (OUT / "prezentacja").mkdir()
    for ext in ("pdf", "pptx"):
        shutil.copy2(ROOT / "prezentacja" / f"dane_przezycie_prezentacja.{ext}", OUT / "prezentacja")
    (OUT / "logotyp").mkdir()
    for name in LOGOTYPY:
        for ext in ("jpg", "png", "pdf", "svg"):
            shutil.copy2(ROOT / "branding" / "logo" / f"{name}.{ext}", OUT / "logotyp")
    shutil.copy2(ROOT / "branding" / "ksiega_znaku.pdf", OUT / "ksiega_znaku.pdf")
    (OUT / "wideo").mkdir()  # film z nagraniem portalu (źródła: video/)
    shutil.copy2(ROOT / "demo" / "wideo" / "dane_przezycie_wykaz_aed.mp4", OUT / "wideo")
    files = sorted(p.relative_to(OUT).as_posix() for p in OUT.rglob("*") if p.is_file())
    print(f"ZGLOSZENIE/: {len(files)} plików")


if __name__ == "__main__":
    main()
