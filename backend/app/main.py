from fastapi import FastAPI
from app.api.market import router as market_router

app = FastAPI(
    title="VyaparSathi Backend API",
    description="GOLD STATE Architecture: Data-driven rural enterprise decision-support platform.",
    version="1.0.0"
)

app.include_router(market_router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}
