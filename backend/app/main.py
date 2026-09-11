from fastapi import FastAPI
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from app.api.finance import router as finance_router
from app.api.market import router as market_router
from app.api.risks import router as risks_router

app = FastAPI(
    title="VyaparSathi Backend API",
    description="GOLD STATE Architecture: Data-driven rural enterprise decision-support platform.",
    version="1.0.0"
)

app.include_router(market_router)
app.include_router(finance_router)
app.include_router(risks_router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}
