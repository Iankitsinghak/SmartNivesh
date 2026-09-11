# Live Competitor Mapping

POST /api/market/competitor-map produces a block-scoped mapping result from
live public records only. It never reads the demo business or demographics
JSON files.

## Inputs

    {
      "latitude": 28.6139,
      "longitude": 77.2090,
      "state_name": "Maharashtra",
      "district_name": "Nashik",
      "block_name": "Exact administrative block name",
      "category_id": "CAT-001"
    }

The submitted coordinate and block name must resolve to exactly one
OpenStreetMap administrative area at a configured block-level administrative
level (6 or 7 by default). A vague locality name is not treated as a block.

The frontend loads the administrative selection in three live steps:

1. India states
2. Districts within the selected state
3. Blocks within the selected district

The selected block's live OpenStreetMap center is passed to the mapping
request, so users do not enter free-form coordinates or block names.

### Dropdown responsiveness

The hierarchy uses an indexed state query instead of an India-wide containment
scan. Successful live responses are cached in the backend (state: seven days,
district: one day, block: six hours by default) and in the current browser
session. Cached entries retain the original live-retrieval timestamp in their
provenance and are never replaced with seeded or demo locations.

Administrative requests have a separate, short public-source timeout (five
seconds by default) so an overloaded public Overpass instance fails promptly
and the interface offers a retry action. The timeouts and cache lifetimes are
deployment settings documented in backend/.env.example.

## Sources and methodology

- OpenStreetMap via the Overpass API verifies the administrative area, maps
  comparable businesses using category-specific OSM tags, and counts observed
  commercial features (shop, office, banks, marketplaces, and commercial land
  use).
- Block demographics come from the official **Village Amenities, Census 2011**
  catalog on data.gov.in, catalog UUID
  `007f2c63-cdb1-4c91-82ef-61716f0b0e76`. The selected state and district resolve
  one district resource page; its exact resource UUID is preserved in response
  provenance. Village population and household rows are summed only where
  `State Name`, `District Name`, and `CD Block Name` match the selection.
- The response reports observed competitors per 1,000 residents, and, only
  when all configured target-segment fields are available, per 1,000 weighted
  target customers. It also reports competitors per 100 observed commercial
  features as the local economic-activity context.

The data.gov.in catalog does **not** provide one nationwide row API or a
consumable Catalog API. Its files are maintained on the Census of India source
server. Consequently, no data.gov.in API key is used for block demographics.
District CSVs are cached for 30 days by default because Census 2011 is a static,
decadal source.

The service returns status: INSUFFICIENT if either source is unavailable, the
block cannot be verified, or the demographic record cannot be matched. It does
not use the application's seed fixtures as a fallback.

The application reads these settings from its process environment. The
backend/.env.example file is a reference template; deployment tooling must
inject the values before starting Uvicorn.

## Response semantics

mapped_competitor_count is an observed OpenStreetMap count, not a claim that
every business in the block has been captured. competitors_per_1000_residents
uses Census 2011 rural village population aggregated by CD block. Statutory-town
residents are excluded, and 2011 CD-block boundaries may differ from current OSM
boundaries. The commercial-feature ratio is calculated from observed OSM
records. Neither measure estimates unrecorded or informal businesses.

## Category mapping

Live OSM category rules are configuration in
backend/data/business_categories.json:

- Restaurant: amenity=restaurant
- Hotel: tourism=hotel
- Cosmetics: shop=cosmetics

New categories need explicit OSM tags before they can be mapped. This avoids
silently classifying unrelated businesses as competitors.
