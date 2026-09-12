# GramVyapar / VyaparSathi

Local decision-support web application for planning rural enterprises in India. It is a modular monolith: React/Vite frontend and FastAPI backend.

## Implemented engines

- **Local Area Intelligence:** local State → District → Sub-district Census 2011 lookup, population/household evidence, data status, affordability positioning, OSM/Google competitor-provider fallbacks, optional openrouteservice travel time, SWOT/risk evidence and a complete report section.
- **Financial Intelligence:** deterministic project-cost, margin and loan modelling; revenue/cost/profit; working capital; decimal-safe EMI and repayment; Repayment Coverage; break-even where inputs permit; conservative/base/optimistic scenarios; feasibility flags and a conservative financing recommendation.

The engines label values as `CALCULATED`, `ESTIMATED`, `ASSUMPTION` or `UNKNOWN`. They do not fabricate missing market, population-radius, revenue or cost values.

## Local run

```bash
cd backend
python3 -m pip install -r requirements.txt
python3 -m uvicorn app.main:app --reload
```

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

## Data and optional provider configuration

The supplied Census 2011 PCA workbook is imported into `backend/data/census_2011.sqlite` for fast local reads. That database is intentionally ignored by Git.

Copy `backend/.env.example` to `backend/.env` and configure credentials locally. Do not commit that file. Google requires its Geocoding API and Places API to be enabled in the associated Google Cloud project. Openrouteservice supplies a geocoding/routing fallback when configured.

Exact 5 km/10 km population figures remain `UNKNOWN` unless village/grid population geometry is supplied; a sub-district total cannot accurately be converted into a radius population.

## Tests

```bash
cd backend && pytest -q
cd frontend && npm run build
```

Important API endpoints include:

- `POST /api/market/local-demographics`
- `POST /api/market/analyze`
- `POST /api/market/competitor-map`
- `POST /api/finance/analyze`
- `POST /api/finance/roadmap`
- `POST /api/schemes/route`
