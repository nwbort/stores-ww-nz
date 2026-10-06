#!/usr/bin/env python3
"""
Fetch Woolworths NZ store locations and details from the site-location API.

Unlike the Australian site, a single request to the NZ API returns every store
with its full details (address, coordinates, facilities, trading hours), so
there is no separate per-store details step.

Writes:
  api.cdx.nz-sites.json              raw API response
  woolworths.co.nz-stores.json       summary list: id, name, division, suburb, state
  store-details/{id}.json            one file per store (site + tradingHours)
  woolworths.co.nz-store-details.json  all store details combined, sorted by id

Usage:
  python3 fetch_stores.py
"""

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API_URL = "https://api.cdx.nz/site-location/api/v1/sites"
# Centre of the search; with a large maxResults the API returns every store
# ordered by distance from this point (central Auckland).
PARAMS = {
    "latitude": "-36.8523140333",
    "longitude": "174.7654210333",
    "maxResults": "2000",
}

RAW_JSON = "api.cdx.nz-sites.json"
STORES_JSON = "woolworths.co.nz-stores.json"
DETAILS_DIR = "store-details"
COMBINED_JSON = "woolworths.co.nz-store-details.json"

# Refuse to overwrite existing data if the response looks truncated
MIN_STORES = 100

MAX_RETRIES = 3
RETRY_BACKOFF = [5, 10, 20]  # seconds between retries

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-NZ,en-GB;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Origin": "https://www.woolworths.co.nz",
    "Referer": "https://www.woolworths.co.nz/",
    "sec-ch-ua": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "cross-site",
}


def fetch():
    url = f"{API_URL}?{urllib.parse.urlencode(PARAMS)}"
    last_error = None
    for attempt in range(MAX_RETRIES + 1):
        if attempt > 0:
            delay = RETRY_BACKOFF[min(attempt - 1, len(RETRY_BACKOFF) - 1)]
            print(f"Retrying in {delay}s ({last_error})")
            time.sleep(delay)

        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            last_error = f"HTTP {e.code}"
            if e.code not in (403, 429, 500, 502, 503, 504):
                break  # non-retryable
        except urllib.error.URLError as e:
            last_error = f"URL error: {e.reason}"
        except json.JSONDecodeError as e:
            last_error = f"invalid JSON: {e}"
            break
        except Exception as e:
            last_error = str(e)

    sys.exit(f"Error: failed to fetch {url}: {last_error}")


def detail_path(store_id):
    return os.path.join(DETAILS_DIR, f"{store_id}.json")


def main():
    data = fetch()

    site_details = data.get("siteDetail") if isinstance(data, dict) else None
    if not isinstance(site_details, list):
        sys.exit("Error: response has no siteDetail list")

    details = {}
    for entry in site_details:
        site = entry.get("site") or {}
        store_id = site.get("id")
        if store_id is None:
            continue
        details[int(store_id)] = entry

    if len(details) < MIN_STORES:
        sys.exit(f"Error: only {len(details)} stores returned, expected at least {MIN_STORES}")

    with open(RAW_JSON, "w") as f:
        json.dump(data, f, indent=2)

    stores = []
    for store_id in sorted(details):
        site = details[store_id]["site"]
        stores.append({
            "id": store_id,
            "name": site.get("name"),
            "division": site.get("division"),
            "suburb": site.get("suburb"),
            "state": site.get("state"),
        })
    with open(STORES_JSON, "w") as f:
        json.dump(stores, f, indent=2)
    print(f"Saved {len(stores)} stores to {STORES_JSON}")

    os.makedirs(DETAILS_DIR, exist_ok=True)
    for store_id, entry in details.items():
        with open(detail_path(store_id), "w") as f:
            json.dump(entry, f, indent=2)

    # Drop detail files for stores no longer returned by the API
    removed = 0
    for fname in os.listdir(DETAILS_DIR):
        if not fname.endswith(".json"):
            continue
        try:
            store_id = int(fname[:-5])
        except ValueError:
            continue
        if store_id not in details:
            os.remove(os.path.join(DETAILS_DIR, fname))
            removed += 1
    print(f"Wrote {len(details)} files to {DETAILS_DIR}/ ({removed} removed)")

    with open(COMBINED_JSON, "w") as f:
        json.dump([details[i] for i in sorted(details)], f, indent=2)
    print(f"Rebuilt {COMBINED_JSON} with {len(details)} stores.")


if __name__ == "__main__":
    main()
