#!/bin/bash
set -e

# Store locator sitemap, kept for cross-checking against the API.
# www.woolworths.co.nz is behind bot protection that resets some clients,
# so try a few in turn.
SITEMAP_URL='https://www.woolworths.co.nz/sitemaps/stores.xml'
SITEMAP_FILE='woolworths.co.nz-sitemaps-stores.xml'
UA='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'

is_sitemap() { [ -s "$1" ] && grep -q '<urlset' "$1"; }

TMP=$(mktemp)
if curl -sS -L --fail --compressed --http1.1 -A "$UA" \
     -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' \
     -H 'Accept-Language: en-NZ,en-GB;q=0.9,en;q=0.8' \
     "$SITEMAP_URL" -o "$TMP" && is_sitemap "$TMP"; then
  echo "Sitemap: fetched with curl"
elif python3 -c "
import sys, urllib.request
req = urllib.request.Request(sys.argv[1], headers={'User-Agent': sys.argv[2], 'Accept': 'application/xml,*/*;q=0.8', 'Accept-Language': 'en-NZ,en;q=0.8'})
open(sys.argv[3], 'wb').write(urllib.request.urlopen(req, timeout=30).read())
" "$SITEMAP_URL" "$UA" "$TMP" && is_sitemap "$TMP"; then
  echo "Sitemap: fetched with urllib"
elif command -v google-chrome >/dev/null && \
     timeout 60 google-chrome --headless=new --disable-gpu --no-sandbox --user-agent="$UA" \
       --dump-dom "$SITEMAP_URL" > "$TMP" 2>/dev/null && is_sitemap "$TMP"; then
  echo "Sitemap: fetched with headless Chrome"
else
  echo "Warning: failed to download stores sitemap"
  head -c 500 "$TMP" || true
  echo
fi
if is_sitemap "$TMP"; then mv "$TMP" "$SITEMAP_FILE"; else rm -f "$TMP"; fi

python3 fetch_stores.py
