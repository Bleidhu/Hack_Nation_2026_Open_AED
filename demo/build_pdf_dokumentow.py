"""Składa PDF z warstwą tekstową z instrukcji dla jury i dodatkowych informacji.

Uruchomienie z katalogu głównego repo:

    uv run --with markdown-it-py python demo/build_pdf_dokumentow.py

albo `python demo/build_pdf_dokumentow.py`: gdy brakuje biblioteki `markdown-it-py`, skrypt sam uruchomi się
ponownie przez `uv run --with markdown-it-py`. Wynik w katalogu głównym repo:

    INSTRUKCJA_DLA_JURY.md     → INSTRUKCJA_DLA_JURY.pdf
    DODATKOWE_INFORMACJE.md    → DODATKOWE_INFORMACJE.pdf

Markdown (CommonMark z tabelami) zamieniany jest na HTML z krojem Atkinson Hyperlegible (osadzonym z branding/fonty/)
i kolorami akcji „Dane (prze)życie”, a HTML drukowany do PDF przez Edge lub Chrome w trybie headless. PDF z przeglądarki
ma prawdziwą warstwę tekstową (tekst da się zaznaczyć, przeszukać i odczytać czytnikiem ekranu), tytuł z <title>
i język z lang="pl". Względne odnośniki do plików repo prowadzą w PDF do repozytorium na GitHubie (tekst odnośnika
bez zmian), kotwice #… zostają wewnątrz dokumentu. Przeglądarkę można wskazać zmienną środowiskową CHROME.

Skrypt można uruchamiać wielokrotnie: po każdej zmianie markdownów wystarczy go powtórzyć.
"""

import base64
import html
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO_URL = "https://github.com/Bleidhu/Hack_Nation_2026_Open_AED"
BRANCH = "main"
DOCUMENTS = ["INSTRUKCJA_DLA_JURY.md", "DODATKOWE_INFORMACJE.md"]
FONTS = ROOT / "branding" / "fonty"

try:
    from markdown_it import MarkdownIt
except ImportError:  # pragma: no cover - ścieżka bez zależności
    if os.environ.get("BUILD_PDF_REEXEC") or not shutil.which("uv"):
        sys.exit("Brak biblioteki markdown-it-py. Uruchom: uv run --with markdown-it-py python demo/build_pdf_dokumentow.py")
    env = dict(os.environ, BUILD_PDF_REEXEC="1")
    cmd = ["uv", "run", "--with", "markdown-it-py", "python", str(Path(__file__).resolve())] + sys.argv[1:]
    sys.exit(subprocess.call(cmd, cwd=str(ROOT), env=env))

BROWSER_CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]
BROWSER_NAMES = ["msedge", "microsoft-edge", "google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"]

CSS = """
@font-face { font-family: 'Atkinson Hyperlegible'; font-weight: 400; src: url(data:font/ttf;base64,{REGULAR}) format('truetype'); }
@font-face { font-family: 'Atkinson Hyperlegible'; font-weight: 700; src: url(data:font/ttf;base64,{BOLD}) format('truetype'); }
:root { --granat: #0E2A47; --zielen: #007A45; --czerwien: #C8102E; --mieta: #F2F7F4; --linia: #B9C7D3; }
@page {
  size: A4;
  margin: 18mm 17mm 20mm 17mm;
  @bottom-left { content: "Dane (prze)życie · {SHORT}"; font: 8.5pt 'Atkinson Hyperlegible', sans-serif; color: #4A5D70; }
  @bottom-right { content: "strona " counter(page) " z " counter(pages); font: 8.5pt 'Atkinson Hyperlegible', sans-serif; color: #4A5D70; }
}
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { margin: 0; background: #fff; color: #14202B; font: 10.5pt/1.45 'Atkinson Hyperlegible', 'Segoe UI', Arial, sans-serif; }
.bar { height: 5px; background: linear-gradient(90deg, var(--granat) 0 70%, var(--zielen) 70% 92%, var(--czerwien) 92%); margin-bottom: 10mm; }
.note { color: #4A5D70; font-size: 9pt; margin: -2mm 0 6mm; }
h1, h2, h3, h4 { color: var(--granat); line-height: 1.2; break-after: avoid; page-break-after: avoid; }
h1 { font-size: 20pt; margin: 0 0 4mm; }
h2 { font-size: 14pt; margin: 8mm 0 3mm; padding-bottom: 1.5mm; border-bottom: 2px solid var(--zielen); }
h3 { font-size: 12pt; margin: 6mm 0 2mm; }
p { margin: 0 0 2.5mm; orphans: 3; widows: 3; }
ul, ol { margin: 0 0 2.5mm; padding-left: 6mm; }
li { margin: 0 0 1.2mm; }
li > ul, li > ol { margin-top: 1.2mm; }
a { color: #005A33; text-decoration: underline; text-decoration-thickness: 0.5pt; text-underline-offset: 0.3em; text-decoration-skip-ink: none; }
a code { color: inherit; }
strong { color: #0B2238; }
code { font-family: Consolas, 'Cascadia Mono', 'DejaVu Sans Mono', monospace; font-size: 0.88em; background: var(--mieta);
       padding: 0 0.25em; border-radius: 2px; overflow-wrap: anywhere; }
pre { background: var(--mieta); border-left: 3px solid var(--zielen); padding: 2.5mm 3.5mm; margin: 1mm 0 3mm;
      white-space: pre-wrap; overflow-wrap: anywhere; break-inside: avoid; }
pre code { background: none; padding: 0; font-size: 8.8pt; line-height: 1.4; }
table { width: 100%; border-collapse: collapse; margin: 2mm 0 4mm; font-size: 9pt; line-height: 1.35; }
thead { display: table-header-group; }
tr { break-inside: avoid; page-break-inside: avoid; }
th, td { border: 0.6pt solid var(--linia); padding: 1.6mm 2mm; text-align: left; vertical-align: top; overflow-wrap: break-word; }
th { background: var(--granat); color: #fff; font-weight: 700; }
tbody tr:nth-child(even) td { background: #F7FAF8; }
td code { font-size: 0.92em; }
"""


def slugify(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def repo_link(href):
    """Względny odnośnik do pliku repo → adres na GitHubie; adresy absolutne i kotwice bez zmian."""
    if not href or href.startswith("#") or re.match(r"^[a-z][a-z0-9+.-]*:", href, re.I):
        return href
    path, _, anchor = href.partition("#")
    if path.startswith("./"):
        path = path[2:]
    if not path:
        return href
    is_dir = path.endswith("/") or (ROOT / path).is_dir()
    url = f"{REPO_URL}/{'tree' if is_dir else 'blob'}/{BRANCH}/{path.rstrip('/')}"
    return url + (f"#{anchor}" if anchor else "")


def render_markdown(text):
    md = MarkdownIt("commonmark", {"html": False}).enable("table")
    used = set()

    def heading_open(renderer, tokens, idx, options, env):
        inline = tokens[idx + 1]
        slug = slugify(inline.content) or "sekcja"
        base, n = slug, 2
        while slug in used:
            slug, n = f"{base}-{n}", n + 1
        used.add(slug)
        tokens[idx].attrSet("id", slug)
        return renderer.renderToken(tokens, idx, options, env)

    def link_open(renderer, tokens, idx, options, env):
        tokens[idx].attrSet("href", repo_link(tokens[idx].attrGet("href")))
        return renderer.renderToken(tokens, idx, options, env)

    md.add_render_rule("heading_open", heading_open)
    md.add_render_rule("link_open", link_open)
    return md.render(text)


def build_html(name):
    text = (ROOT / name).read_text(encoding="utf-8")
    title_match = re.search(r"^#\s+(.+)$", text, re.M)
    title = title_match.group(1).strip() if title_match else name
    short = "Instrukcja dla jury" if name.startswith("INSTRUKCJA") else "Dodatkowe informacje"
    fonts = {key: base64.b64encode((FONTS / f"AtkinsonHyperlegible-{key.title()}.ttf").read_bytes()).decode("ascii")
             for key in ("regular", "bold")}
    css = CSS.replace("{REGULAR}", fonts["regular"]).replace("{BOLD}", fonts["bold"]).replace("{SHORT}", short)
    body = render_markdown(text)
    note = (f'<p class="note">Wersja PDF pliku <code>{html.escape(name)}</code>. Odnośniki do plików prowadzą do repozytorium '
            f'<a href="{REPO_URL}">{html.escape(REPO_URL.replace("https://", ""))}</a>; '
            "te same pliki są w archiwum zgłoszenia pod tymi samymi ścieżkami.</p>")
    body = re.sub(r"(</h1>)", r"\1" + note.replace("\\", "\\\\"), body, count=1)
    return (f'<!doctype html>\n<html lang="pl">\n<head>\n<meta charset="utf-8">\n<title>{html.escape(title)}</title>\n'
            f'<meta name="author" content="Zespół Dane (prze)życie">\n<style>{css}</style>\n</head>\n'
            f'<body>\n<div class="bar" aria-hidden="true"></div>\n<main>\n{body}</main>\n</body>\n</html>\n')


def find_browser():
    env = os.environ.get("CHROME")
    if env and Path(env).is_file():
        return env
    for candidate in BROWSER_CANDIDATES:
        if Path(candidate).is_file():
            return candidate
    for name in BROWSER_NAMES:
        found = shutil.which(name)
        if found:
            return found
    sys.exit("Nie znaleziono Edge ani Chrome. Wskaż przeglądarkę zmienną CHROME=<ścieżka do msedge.exe lub chrome.exe>.")


def print_pdf(browser, html_path, pdf_path, profile_dir):
    if pdf_path.exists():
        pdf_path.unlink()
    cmd = [browser, "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
           "--disable-extensions", f"--user-data-dir={profile_dir}", "--no-pdf-header-footer",
           "--generate-pdf-document-outline", f"--print-to-pdf={pdf_path}", html_path.resolve().as_uri()]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180)
    if not pdf_path.exists() or pdf_path.stat().st_size == 0:
        sys.exit(f"Przeglądarka nie zapisała {pdf_path.name} ({browser}).")


def main():
    browser = find_browser()
    work = Path(tempfile.mkdtemp(prefix="pdf_dokumentow_"))
    try:
        for name in DOCUMENTS:
            html_path = work / (Path(name).stem + ".html")
            html_path.write_text(build_html(name), encoding="utf-8")
            pdf_path = ROOT / (Path(name).stem + ".pdf")
            print_pdf(browser, html_path, pdf_path, work / "profil")
            print(f"{pdf_path.name}: {pdf_path.stat().st_size / 1024:.0f} KB")
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
