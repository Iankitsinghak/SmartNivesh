# Opportunity Analysis API Contract

The service contract is represented by `OpportunityAnalysis`. A sufficient result contains an `Opportunity` with evidence and transparency metadata. An insufficient result contains no opportunity and returns:

```text
Insufficient evidence to identify a reliable opportunity from the available public data.
```

The API layer must orchestrate services only. It must not calculate scores, infer demand, or convert missing dataset records into claims of real-world absence.

## Live competitor mapping

POST /api/market/competitor-map accepts latitude, longitude, state_name,
district_name, block_name, and category_id. It returns an AVAILABLE result only
when live OpenStreetMap block/business data and exactly matched Census 2011
Village Amenities rows are available. Otherwise it returns an INSUFFICIENT
result with limitations and no competitor-density values.

See docs/competitor-mapping.md for the public-data contract and response
semantics.

The India dropdown hierarchy is loaded through:

- GET /api/market/india-administrative/state
- GET /api/market/india-administrative/district?parent_id=relation:<osm-id>
- GET /api/market/india-administrative/block?parent_id=relation:<osm-id>

## Product market value

POST /api/market/product-market-value accepts state_name, optional
district_name/block_name, category_id, and an optional entrepreneur-entered
reference_price. It returns the verified state rural-MPCE / All-India rural-MPCE
affordability multiplier for every supported category. When reference_price is
provided, it also returns that value multiplied by the verified factor.

No generic market-price API, commodity mapping, scraped price, or invented
category price is used. The response calls the result a calculated planning
reference, not an observed or optimal market price. See docs/product-market-value.md.

## Financial roadmap and scheme router

POST `/api/finance/roadmap` accepts available margin capital and optional,
self-declared enterprise-profile and cash-flow inputs. It returns:

- a 10% margin / 90% indicative project-finance structure;
- a published-term NSFDC repayment illustration when the project is within that
  scheme's published project-cost range;
- rule-gated routes for PMMY/MUDRA, PMEGP, PMFME and PM Vishwakarma; and
- a cash-flow and working-capital result only when the user supplies every
  required cost, revenue and reserve input.

The endpoint does not return a credit decision. It intentionally leaves
lender-set rates/tenures, unconfirmed programme availability and unmet profile
conditions uncalculated. See docs/financial-roadmap.md.
