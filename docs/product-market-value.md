# Local Price Positioning

`POST /api/market/product-market-value` returns a verified affordability
multiplier for every supported business category. It needs the selected India
hierarchy and category, with an optional entrepreneur-entered comparable
reference price:

```json
{
  "state_name": "Maharashtra",
  "district_name": "Pune",
  "block_name": "Haveli",
  "category_id": "CAT-007",
  "reference_price": 250
}
```

## Formula

```
affordability multiplier = state rural MPCE / All-India rural MPCE
MPCE-adjusted planning reference = entrepreneur-entered reference price × affordability multiplier
```

The multiplier is returned even when no reference price is supplied. In that
case the UI shows a percentage, not an invented rupee amount. If a reference
price is entered, the UI labels it as **USER INPUT** and returns the arithmetic
result separately as a calculated planning reference.

## Verified source

The formula uses data.gov.in resource UUID
`89bf5d50-cecf-4219-84d9-12b062c301e2`, **State/UT-wise Details of Average
Monthly Per Capita Consumption Expenditure (MPCE) in Rural and Urban Areas
during 2022-23 and 2023-24**. data.gov.in marks its sourced API as `NA`, so no
API key can make `api.data.gov.in/resource/{uuid}` available for this resource.
The reviewed 2023-24 table is versioned in
`backend/data/india_hces_2023_24_mpce.json` and cross-checked against the
official MoSPI HCES 2023-24 fact sheet.

MPCE is explicitly a **state-level rural consumption-expenditure proxy**. The
result is not an observed local price, a block-level willingness-to-pay estimate,
a demand forecast, or a guarantee of the optimal price. A reference price must
be supported by a current quotation, menu, or comparable local offer before it
is used in a business plan.

No generic market-price API, commodity mapping, seeded price, scraped price, or
synthetic price is used.
