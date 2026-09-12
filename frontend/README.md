# VyaparSathi frontend

React + TypeScript interface for the local-area and financial-intelligence workflow.

## Run locally

1. From `backend/`, install dependencies and start the API:

   ```bash
   python3 -m pip install -r requirements.txt
   python3 -m uvicorn app.main:app --reload
   ```

2. From `frontend/`, install dependencies and start Vite:

   ```bash
   npm install
   npm run dev
   ```

3. Open `http://127.0.0.1:5173`.

The frontend proxies `/health` and `/api` to `http://127.0.0.1:8000`.

## What the workflow does

- Selects State → District → Sub-district from the supplied Census 2011 local database.
- Presents transparent population, household and affordability evidence with data status and limitations.
- Retrieves live map/route evidence when the relevant public provider is available; it never substitutes fabricated competitor data.
- Calculates project cost, margin, loan, EMI, repayment, working capital, break-even (where inputs allow), base/downside/upside scenarios, Repayment Coverage and a conservative financing recommendation.
- Displays the same evidence in a printable/downloadable report.

## Configuration

Copy `backend/.env.example` to `backend/.env` and keep credentials out of version control. Google Geocoding/Places and openrouteservice are optional provider integrations; the local Census and deterministic financial calculations work without them.
