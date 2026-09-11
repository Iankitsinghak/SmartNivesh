import asyncio
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Response
from app.schemas.market import (
    CompetitorMappingRequest,
    CompetitorMappingResponse,
    AdministrativeLocationRequest,
    AdministrativeLocationResponse,
    IndiaAdministrativeOptionsResponse,
    MarketAnalysisRequest,
    MarketAnalysisResponse,
    ProductMarketValueRequest,
    ProductMarketValueResponse,
)
from app.services.market.market_engine import analyze_market
from app.services.market.live_competitor_mapping import (
    analyze_live_competitor_mapping,
    get_india_administrative_options,
    resolve_administrative_location,
)
from app.services.market.product_market_value import analyze_product_market_value

router = APIRouter(prefix="/api/market", tags=["Market Intelligence"])

from app.services.market.lookup_jobs import lookup


@router.post('/competitor-lookup')
async def competitor_lookup(request: CompetitorMappingRequest):
    return await lookup('competitors', request.model_dump(), lambda: analyze_live_competitor_mapping(request), 3600)


@router.post('/resolve-administrative-location', response_model=AdministrativeLocationResponse)
async def resolve_administrative_location_endpoint(request: AdministrativeLocationRequest):
    return await asyncio.to_thread(
        resolve_administrative_location, request.state_name, request.district_name, request.block_name
    )


@router.get('/administrative-lookup/{level}')
async def administrative_lookup(level: Literal['state', 'district', 'block'], parent_id: Optional[str] = None,
                                state_name: Optional[str] = None, district_name: Optional[str] = None):
    args = [level, parent_id, state_name, district_name]
    return await lookup('administrative', args, lambda: get_india_administrative_options(*args), 86400)

@router.post("/analyze", response_model=MarketAnalysisResponse)
async def analyze_market_endpoint(request: MarketAnalysisRequest):
    """
    Analyzes the local area market for a selected business category at a given location.
    Provides highly structured, evidence-backed deterministic metrics without AI generation.
    """
    try:
        response = await asyncio.to_thread(analyze_market, request)
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error: " + str(e))


@router.post("/competitor-map", response_model=CompetitorMappingResponse)
async def competitor_mapping_endpoint(request: CompetitorMappingRequest):
    """Map category competitors using official Census files and live OSM records."""
    return await asyncio.to_thread(analyze_live_competitor_mapping, request)


@router.post("/product-market-value", response_model=ProductMarketValueResponse)
async def product_market_value_endpoint(request: ProductMarketValueRequest):
    """Return an evidence-gated regional price reference for a selected category."""
    return await asyncio.to_thread(analyze_product_market_value, request)


@router.get("/india-administrative/{level}", response_model=IndiaAdministrativeOptionsResponse)
async def india_administrative_options_endpoint(
    level: Literal["state", "district", "block"],
    response: Response,
    parent_id: Optional[str] = None,
    state_name: Optional[str] = None,
    district_name: Optional[str] = None,
):
    """Load India's live State → District → Block hierarchy from Overpass."""
    result = await asyncio.to_thread(
        get_india_administrative_options, level, parent_id, state_name, district_name
    )
    if result.status == "AVAILABLE":
        response.headers["Cache-Control"] = "private, max-age=3600, stale-while-revalidate=86400"
    return result
