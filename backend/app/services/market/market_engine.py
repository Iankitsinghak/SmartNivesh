import json
from typing import Optional
from app.schemas.common import DataProvenance
from app.schemas.location import Location
from app.schemas.business import BusinessCategory
from app.schemas.market import (
    MarketAnalysisRequest, MarketAnalysisResponse, MarketOpportunityGap, RadiusAnalysis
)
from app.utils.provenance import DataClassification, ConfidenceLevel
from app.utils.normalization import get_generic_level, clamp_score
from app.core.constants import MARKET_GAP_WEIGHTS, OPPORTUNITY_SCORE_WEIGHTS
from app.services.location.resolver import get_location
from app.services.market.demographic_engine import get_demographics, analyze_demographics
from app.services.market.poi_engine import analyze_pois
from app.services.market.competition_engine import analyze_competition
from app.services.market.business_activity_engine import analyze_business_activity
from app.services.market.demand_engine import analyze_demand
from app.services.market.distribution_engine import analyze_distribution
from app.services.market.seasonality_engine import analyze_seasonality
from app.services.market.purchasing_power_engine import analyze_purchasing_power

def get_business_category(category_id: str) -> Optional[BusinessCategory]:
    try:
        with open("data/business_categories.json", "r") as f:
            cats = json.load(f)
            for c in cats:
                if c["category_id"] == category_id:
                    return BusinessCategory(**c)
    except Exception:
        pass
    return None

def analyze_market(request: MarketAnalysisRequest) -> MarketAnalysisResponse:
    # 1. Resolve Location and Category
    location = get_location(request.location_id)
    if not location:
        raise ValueError("Location not found")
        
    category = get_business_category(request.category_id)
    if not category:
        raise ValueError("Business Category not found")

    lat, lon = location.latitude, location.longitude
    provenance = []

    # 2. Demographic Analysis
    demographics = get_demographics(request.location_id)
    demographic_result = analyze_demographics(demographics, category)
    if demographics:
        provenance.append(DataProvenance(
            source_id="DEMO_DB_01",
            source_name="Local Demographics DB",
            data_type=DataClassification.SEEDED_DEMO,
            confidence=ConfidenceLevel.HIGH
        ))

    # 3. POI Analysis
    poi_result = analyze_pois(lat, lon, category, request.radius_km)
    provenance.append(DataProvenance(
        source_id="POI_DB_01",
        source_name="Local Places DB",
        data_type=DataClassification.SEEDED_DEMO,
        confidence=ConfidenceLevel.MEDIUM
    ))

    # 4. Business Activity Analysis
    activity_result = analyze_business_activity(lat, lon, category, request.radius_km)

    # 5. Competition Analysis
    competition_result = analyze_competition(lat, lon, category, request.radius_km)
    
    # 6. Demand Engine
    demand_result = analyze_demand(
        demographic_fit_score=demographic_result["demographic_fit"],
        poi_result=poi_result,
        activity_result=activity_result
    )

    # 7. Distribution Engine
    distribution_result = analyze_distribution(category)

    # 8. Seasonality Engine
    seasonality_result = analyze_seasonality(category)

    # 9. Purchasing Power Engine
    purchasing_power_result = analyze_purchasing_power(lat, lon)

    # 10. Market Opportunity Gap
    # Market Opportunity Gap = 0.45 * Demand + 0.25 * Growth + 0.20 * Dist - 0.10 * Comp
    demand_contr = demand_result.demand_score * MARKET_GAP_WEIGHTS["demand"]
    growth_contr = 50.0 * MARKET_GAP_WEIGHTS["demand_growth"] # Growth unavailable, use 50 (neutral)
    dist_contr = distribution_result.distribution_score * MARKET_GAP_WEIGHTS["distribution_availability"]
    comp_deduction = competition_result.competition_score * abs(MARKET_GAP_WEIGHTS["competition"])

    gap_score = clamp_score(demand_contr + growth_contr + dist_contr - comp_deduction)
    market_gap = MarketOpportunityGap(
        gap_score=round(gap_score, 2),
        demand_contribution=round(demand_contr, 2),
        growth_contribution=round(growth_contr, 2),
        distribution_contribution=round(dist_contr, 2),
        competition_deduction=round(comp_deduction, 2)
    )

    # 11. Final Overall Market Score
    # We only have market-side data right now (no capital, skills, risk etc)
    # So we'll calculate a pure market score using proportional market weights.
    overall_score = clamp_score(
        (demand_result.demand_score * 0.60) +
        (gap_score * 0.40)
    )

    return MarketAnalysisResponse(
        location=location,
        business_category=category,
        radius_analysis=RadiusAnalysis(
            radius_0_2_km={"pois": len(poi_result.within_2km), "competitors": competition_result.near_competitors},
            radius_2_5_km={"pois": len(poi_result.within_5km)},
            radius_5_10_km={"pois": len(poi_result.within_10km)}
        ),
        poi_analysis=poi_result,
        business_activity=activity_result,
        competition=competition_result,
        demand=demand_result,
        distribution=distribution_result,
        seasonality=seasonality_result,
        purchasing_power=purchasing_power_result,
        market_gap=market_gap,
        customer_potential=get_generic_level(demographic_result["demographic_fit"]),
        market_opportunity_level=get_generic_level(overall_score),
        overall_score=round(overall_score, 2),
        confidence=ConfidenceLevel.MEDIUM,
        data_provenance=provenance
    )
