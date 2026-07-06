#!/bin/zsh
# Publica ep102_color_review.html en R2 para que lo vea cualquiera.
# Sube las imagenes locales, reescribe las rutas a URLs publicas y sube el HTML.
# Uso:  ./publish_ep102_review.sh
set -e
cd "$(dirname "$0")"

WORKER="https://convoy-upload.valentin-e9a.workers.dev/upload"
SRC="ep102_color_review.html"
HTML_KEY="convoy/ep102_review/CVY26_001_102_Color_Review.html"
MAP="/tmp/ep102_asset_map.txt"

echo "→ subiendo imagenes locales a R2…"
> "$MAP"
# extrae rutas locales (src="./…") del HTML
grep -oE 'src="\./[^"]+"' "$SRC" | sed 's/^src="\.\///;s/"$//' | sort -u | while read -r f; do
  [ -f "$f" ] || { echo "  ⚠ falta $f"; continue; }
  base=$(basename "$f")
  case "$f" in *.png) ct=image/png;; *.jpeg|*.jpg) ct=image/jpeg;; *) ct=application/octet-stream;; esac
  key="convoy/ep102_review/$base"
  url=$(curl -s -X POST -F "file=@${f};type=${ct}" -F "key=${key}" "$WORKER" | sed -n 's/.*"url":"\([^"]*\)".*/\1/p')
  [ -n "$url" ] && printf "./%s\t%s\n" "$f" "$url" >> "$MAP" && echo "  ✓ $f"
done

echo "→ reescribiendo rutas y subiendo HTML…"
python3 - "$SRC" "$MAP" <<'PY'
import sys
src, mapf = sys.argv[1], sys.argv[2]
h = open(src, encoding='utf-8').read()
for line in open(mapf):
    loc, url = line.rstrip('\n').split('\t')
    h = h.replace('src="'+loc+'"', 'src="'+url+'"')
open('ep102_color_review_PUBLISHED.html','w',encoding='utf-8').write(h)
import re
left = re.findall(r'src="\./[^"]+"', h)
print('  rutas locales restantes:', left or 'ninguna')
PY

url=$(curl -s -X POST -F "file=@ep102_color_review_PUBLISHED.html;type=text/html; charset=utf-8" -F "key=${HTML_KEY}" "$WORKER" | sed -n 's/.*"url":"\([^"]*\)".*/\1/p')
echo
echo "✅ PUBLICADO:"
echo "$url"
