#!/usr/bin/env bash
# Eksport logo (PNG przezroczyste, JPG na białym, PDF wektorowy) i księgi znaku do PDF.
# Wymaga Google Chrome (lub Edge – zmień CHROME) i PowerShella (konwersja PNG → JPG).
set -euo pipefail
cd "$(dirname "$0")"
CHROME="${CHROME:-/c/Program Files/Google/Chrome/Application/chrome.exe}"
TMP="$(mktemp -d)"
W() { cygpath -w "$1"; }
U() { echo "file:///$(cygpath -m "$1")"; }
run() { "$CHROME" --headless=new --disable-gpu --hide-scrollbars --no-pdf-header-footer "$@" >/dev/null 2>&1 || true; }

# nazwa:szerokość_px_eksportu
for spec in otworz-aed_logo_poziome:2000 otworz-aed_logo_poziome_haslo:2400 otworz-aed_logo_pionowe:1200 otworz-aed_sygnet:800; do
  name="${spec%%:*}"; px="${spec##*:}"
  vb=$(grep -o 'viewBox="[^"]*"' "logo/$name.svg" | head -1 | sed 's/viewBox="//;s/"//')
  read -r _ _ vw vh <<<"$vb"
  h=$(python -c "print(round($px*$vh/$vw))")
  pad=$(python -c "print(round($px*0.06))")
  W2=$((px + 2*pad)); H2=$((h + 2*pad))
  cp "logo/$name.svg" "$TMP/$name.svg"
  for bg in transparent white; do
    cat >"$TMP/$name-$bg.html" <<EOF
<!doctype html><html><head><meta charset="utf-8"><style>
@page{size:${W2}px ${H2}px;margin:0}html,body{margin:0;background:$bg}
img{display:block;width:${px}px;height:${h}px;margin:${pad}px}</style></head>
<body><img src="$name.svg" alt=""></body></html>
EOF
  done
  run --window-size=$W2,$H2 --default-background-color=00000000 --screenshot="$(W "$PWD/logo/$name.png")" "$(U "$TMP/$name-transparent.html")"
  run --window-size=$W2,$H2 --screenshot="$(W "$TMP/$name-white.png")" "$(U "$TMP/$name-white.html")"
  run --print-to-pdf="$(W "$PWD/logo/$name.pdf")" "$(U "$TMP/$name-white.html")"
  powershell -NoProfile -Command "Add-Type -AssemblyName System.Drawing; \$i=[System.Drawing.Image]::FromFile('$(W "$TMP/$name-white.png")'); \$i.Save('$(W "$PWD/logo/$name.jpg")',[System.Drawing.Imaging.ImageFormat]::Jpeg); \$i.Dispose()"
  echo "✓ $name (${px}px)"
done

run --print-to-pdf="$(W "$PWD/ksiega_znaku.pdf")" "$(U "$PWD/ksiega_znaku.html")"
echo "✓ ksiega_znaku.pdf"
rm -rf "$TMP"
