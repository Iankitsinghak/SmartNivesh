# VyaparSathi frontend

A Vite + React + TypeScript console for exercising the FastAPI market intelligence endpoints.

## Run locally

1. Start the backend from `backend/`:
   `uvicorn app.main:app --reload`
2. Install and start the frontend from `frontend/`:
   `npm install`
   `npm run dev`
3. Open `http://localhost:5173`.

The Vite dev server proxies `/health` and `/api` to `http://127.0.0.1:8000`. The first scan uses the seeded `LOC-001` location and `CAT-001` restaurant category.
