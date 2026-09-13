# VyaparSathi

## Evidence-led business planning for India's local entrepreneurs

VyaparSathi is a modular monolith with a React/Vite frontend and FastAPI backend. It is a decision-support platform for evaluating rural and local enterprise ideas, bringing location intelligence, market signals, financial modelling, government schemes, and risk checks into one explainable workflow so an entrepreneur can move from **“Is this viable here?”** to a practical next step.

![VyaparSathi architecture and decision flow](assets/vyaparsathi-architecture-flow.png)

> **Evidence-led inputs → deterministic scoring → explainable guidance**

## Why VyaparSathi

Small-business decisions are often made with fragmented data, informal estimates, and unclear financing assumptions. VyaparSathi makes the reasoning visible:

- **Local context:** understand the administrative area, population and household evidence around a proposed location.
- **Market reality:** inspect nearby businesses and points of interest using public-data and configured provider fallbacks.
- **Financial clarity:** model project cost, margins, working capital, repayment, break-even, and multiple scenarios.
- **Actionable guidance:** surface feasibility flags, relevant scheme routes, risks, limitations, and recommended next steps.

The platform is deliberately conservative. Every value is labelled `CALCULATED`, `ESTIMATED`, `ASSUMPTION`, or `UNKNOWN`; missing evidence is disclosed rather than invented.

## Product capabilities

### Local Area Intelligence

State → District → Sub-district Census 2011 lookup, population and household evidence, affordability positioning, competitor/provider discovery, optional OpenRouteService travel time, SWOT signals, and report-ready location analysis.

### Financial Intelligence

Deterministic project-cost, revenue, margin, working-capital, EMI, repayment-coverage, and break-even calculations, with conservative, base, and optimistic scenarios. Decimal-safe calculations support transparent financing recommendations.

### Explainable decision reports

The output keeps evidence, assumptions, confidence, limitations, and recommendations together. AI explanations are provider-agnostic and do not replace the deterministic scores.

## Architecture

VyaparSathi is a modular monolith with a React/Vite client and a FastAPI service:

| Layer | Technology | Responsibility |
| --- | --- | --- |
| Presentation | React, TypeScript, Vite | Entrepreneur console and decision workflow |
| Application | FastAPI, Python 3.11+, Pydantic | Validation, domain APIs, and orchestration |
| Intelligence | Python services | Location, market, finance, scheme, and risk analysis |
| Evidence | Census of India, OpenStreetMap/Overpass, HCES, public scheme data | Traceable public and configured provider inputs |

## Quick start

### 1. Start the backend

```bash
cd backend
python3 -m pip install -r requirements.txt
python3 -m uvicorn app.main:app --reload
```

### 2. Start the frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open [http://127.0.0.1:5173](http://127.0.0.1:5173).

## Configuration and data

Copy `backend/.env.example` to `backend/.env` and configure provider credentials locally. Never commit `.env` or API keys.

The supplied Census 2011 PCA workbook is imported into `backend/data/census_2011.sqlite` for fast local reads. The generated database is intentionally ignored by Git. Google Geocoding and Places API access is optional; OpenRouteService provides a geocoding and routing fallback when configured.

Exact 5 km and 10 km population figures remain `UNKNOWN` unless village or grid population geometry is available. A sub-district total cannot accurately be converted into a radius population.

## API surface

- `POST /api/market/local-demographics`
- `POST /api/market/analyze`
- `POST /api/market/competitor-map`
- `POST /api/finance/analyze`
- `POST /api/finance/roadmap`
- `POST /api/schemes/route`
- `GET /health`

## Verification

```bash
cd backend && pytest -q
cd frontend && npm run build
```

## Repository guide

```text
backend/    FastAPI application, services, data ingestion, and tests
frontend/   React/Vite application
data/       Seed datasets and public-data indexes
docs/       Product, intelligence, finance, and architecture notes
assets/     Architecture and project visuals
```

## Project status

VyaparSathi is an actively developed decision-support prototype. Provider availability, local datasets, and evidence scope can affect results; the product presents those boundaries explicitly so recommendations remain useful and honest.
