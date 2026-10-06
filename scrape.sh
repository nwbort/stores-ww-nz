#!/bin/bash
set -e

# Store locator sitemap, kept for cross-checking against the API
curl -sS -L --fail --compressed \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36" \
  -H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8" \
  -H "Accept-Language: en-NZ,en-GB;q=0.9,en-US;q=0.8,en;q=0.7" \
  'https://www.woolworths.co.nz/sitemaps/stores.xml' -o woolworths.co.nz-sitemaps-stores.xml \
  || echo "Warning: failed to download stores sitemap"

python3 fetch_stores.py
