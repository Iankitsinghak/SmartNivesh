from fastapi import FastAPI
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from app.api.finance import router as finance_router
from app.api.market import router as market_router
from app.api.risks import router as risks_router
from app.api.schemes import router as schemes_router
from app.api.location import router as location_router
from app.api.assistant import router as assistant_router

app = FastAPI(
    title="SmartNivesh Backend API",
    description="GOLD STATE Architecture: Data-driven rural enterprise decision-support platform.",
    version="1.0.0"
)

app.include_router(market_router)
app.include_router(finance_router)
app.include_router(risks_router)
app.include_router(schemes_router)
app.include_router(location_router)
app.include_router(assistant_router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}
