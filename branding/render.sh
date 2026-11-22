#!/usr/bin/env bash
# Eksport logo „Dane (prze)życie” (PNG z przezroczystym tłem, JPG na białym tle, PDF wektorowy)
# i księgi znaku do PDF. Najpierw: uv run --with fonttools python build_branding.py
# Wymaga Google Chrome (lub Edge: ustaw CHROME) i PowerShella (konwersja PNG → JPG).
set -euo pipefail
cd "$(dirname "$0")"
CHROME="${CHROME:-/c/Program Files/Google/Chrome/Application/chrome.exe}"
TMP="$(mktemp -d)"
W() { cygpath -w "$1"; }
U() { echo "file:///$(cygpath -m "$1")"; }
run() { "$CHROME" --headless=new --disable-gpu --hide-scrollbars --no-pdf-header-footer "$@" >/dev/null 2>&1 || true; }

# ścieżka:szerokość_px:formaty (p = PNG, j = JPG, d = PDF):margines (1 = pole ochronne, 0 = grafika z własnym tłem)
for spec in logo/dane-przezycie_logo_poziome:2400:pjd:1 logo/dane-przezycie_logo_poziome_haslo:2400:pjd:1 \
            logo/dane-przezycie_logo_pionowe:1600:pjd:1 logo/dane-przezycie_znak:1600:pjd:1 logo/dane-przezycie_sygnet:512:pjd:1 \
            logo/dane-przezycie_logo_poziome_negatyw:2400:p:0 logo/dane-przezycie_logo_pionowe_negatyw:1600:p:0 \
            logo/dane-przezycie_sygnet_negatyw:512:p:0 materialy/dane-przezycie_post_1080:1080:p:0 \
            materialy/dane-przezycie_naklejka_A6:1748:pd:0 materialy/dane-przezycie_odznaka_dysponenta:1200:p:0; do
  IFS=: read -r path px fmt margin <<<"$spec"
  name="$(basename "$path")"
  vb=$(grep -o 'viewBox="[^"]*"' "$path.svg" | head -1 | sed 's/viewBox="//;s/"//')
  read -r _ _ vw vh <<<"$vb"
  h=$(python -c "print(round($px*$vh/$vw))")
  pad=$(python -c "print(round($px*0.06*$margin))")
  W2=$((px + 2*pad)); H2=$((h + 2*pad))
  cp "$path.svg" "$TMP/$name.svg"
  for bg in transparent white; do
    cat >"$TMP/$name-$bg.html" <<EOF
<!doctype html><html><head><meta charset="utf-8"><style>
@page{size:${W2}px ${H2}px;margin:0}html,body{margin:0;background:$bg}
img{display:block;width:${px}px;height:${h}px;margin:${pad}px}</style></head>
<body><img src="$name.svg" alt=""></body></html>
EOF
  done
  [[ $fmt == *p* ]] && run --window-size=$W2,$H2 --default-background-color=00000000 --screenshot="$(W "$PWD/$path.png")" "$(U "$TMP/$name-transparent.html")"
  if [[ $fmt == *j* ]]; then
    run --window-size=$W2,$H2 --screenshot="$(W "$TMP/$name-white.png")" "$(U "$TMP/$name-white.html")"
    powershell -NoProfile -Command "Add-Type -AssemblyName System.Drawing; \$i=[System.Drawing.Image]::FromFile('$(W "$TMP/$name-white.png")'); \$i.Save('$(W "$PWD/$path.jpg")',[System.Drawing.Imaging.ImageFormat]::Jpeg); \$i.Dispose()"
  fi
  [[ $fmt == *d* ]] && run --print-to-pdf="$(W "$PWD/$path.pdf")" "$(U "$TMP/$name-white.html")"
  echo "✓ $path ($fmt, ${px}px)"
done

run --print-to-pdf="$(W "$PWD/ksiega_znaku.pdf")" "$(U "$PWD/ksiega_znaku.html")"
echo "✓ ksiega_znaku.pdf"
rm -rf "$TMP"
