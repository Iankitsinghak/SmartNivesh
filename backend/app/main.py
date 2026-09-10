from fastapi import FastAPI
from app.api.market import router as market_router
from app.api.finance import router as finance_router
from app.api.schemes import router as schemes_router

app = FastAPI(
    title="VyaparSathi Backend API",
    description="GOLD STATE Architecture: Data-driven rural enterprise decision-support platform.",
    version="1.0.0"
)

app.include_router(market_router)
app.include_router(finance_router)
app.include_router(schemes_router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}
