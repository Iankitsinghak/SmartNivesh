# Data Sources

Every integrated dataset must be registered in `backend/data/data_sources.json` with its provider, public URL, access method, publication date, geographic coverage, limitations, and verification date.

## Live competitor mapping

The competitor-mapping endpoint uses live OpenStreetMap data through the
Overpass API and Census of India 2011 Village Amenities district CSVs. The
reviewed data.gov.in catalog UUID is
`007f2c63-cdb1-4c91-82ef-61716f0b0e76`; each result also preserves the exact
district-resource UUID. State, district, and CD-block names must all match.
The catalog has no consumable nationwide row API, so no data.gov.in key is
used. See backend/.env.example and docs/competitor-mapping.md.

The live endpoint never substitutes businesses.json or demographics.json when
a source is unavailable.

## Product market value

Product Market Value uses only the official MoSPI HCES 2023-24 state rural-MPCE
table (data.gov.in resource UUID `89bf5d50-cecf-4219-84d9-12b062c301e2`). It
calculates state rural MPCE / All-India rural MPCE for every supported category.
The ratio is explicitly a state-level rural consumption proxy, not a direct
block purchasing-power index or observed local price. See docs/product-market-value.md.

The service does not treat CPI by itself as household purchasing power, call a
generic market-price API, or infer a price when the entrepreneur has not entered
a comparable reference price.

## Financial roadmap and scheme router

The financial roadmap uses a dated, curated registry of official Government of
India scheme publications rather than a fabricated lending feed. The registry
is reviewed on the date returned with each route and links users directly to
the official government source. It contains no market-cost default, lender
quotation, personal eligibility decision, or synthetic subsidy calculation.

See docs/financial-roadmap.md for the source-by-source terms and controls.

The MVP treats mapped business and facility data as identified records, not a complete census. If a query returns zero providers, the system reports that no provider was identified in the available dataset. It does not claim that no provider exists.

The source registry is checked with:

```text
python backend/scripts/verify_data.py
```
