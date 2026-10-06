# Scheduled scraper

For Woolworths New Zealand store locations, via https://api.cdx.nz/site-location/api/v1/sites
(the API behind the store finder on https://www.woolworths.co.nz/).

One request returns every store with its address, coordinates, facilities and
trading hours, so `fetch_stores.py` writes everything in a single daily run:

- `api.cdx.nz-sites.json` — raw API response
- `woolworths.co.nz-stores.json` — summary list (id, name, division, suburb, state)
- `store-details/{id}.json` — one file per store
- `woolworths.co.nz-store-details.json` — all store details combined
