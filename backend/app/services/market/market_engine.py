import json
from typing import Optional
from app.schemas.common import DataProvenance
from app.schemas.location import Location
from app.schemas.business import BusinessCategory
from app.schemas.market import (
    MarketAnalysisRequest, MarketAnalysisResponse, MarketOpportunityGap, RadiusAnalysis, SWOTAnalysis
)
from app.core.enums import DataClassification, ConfidenceLevel
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
from app.services.risk.risk_engine import analyze_risk

def build_swot(category, demand, competition, activity, distribution, seasonality, purchasing_power, market_gap, risk_summary) -> SWOTAnalysis:
    budget = f"{category.capital_min:,.0f}-{category.capital_max:,.0f} INR"
    strengths = [
        f"{category.name} has a defined startup budget of {budget}, keeping the plan grounded in the available capital band.",
        f"Local demand is {demand.demand_level.lower()} at {demand.demand_score:.0f}/100, with {activity.complementary_business_count} complementary businesses supporting nearby activity."
    ]
    weaknesses = []
    if distribution.distribution_score < 50:
        weaknesses.append(f"Distribution is {distribution.distribution_level.lower()} at {distribution.distribution_score:.0f}/100, which may increase sourcing effort within this budget.")
    else:
        weaknesses.append(f"The {budget} budget leaves limited room for expansion beyond the initial operating footprint.")
    if seasonality.low_periods:
        weaknesses.append(f"The category has a seasonal dip during {', '.join(seasonality.low_periods)}.")
    else:
        weaknesses.append("The initial budget may constrain stock, staffing, or service breadth during the launch period.")

    opportunities = [
        f"The market gap is {market_gap.gap_score:.0f}/100, leaving room to capture unmet local demand without exceeding the {budget} band.",
        f"Commercial activity is {activity.market_activity_level.lower()} at {activity.commercial_activity_score:.0f}/100, creating scope to build partnerships and repeat demand."
    ]
    
    threats = []
    
    # Add structured threats from risk analysis if available
    if risk_summary and risk_summary.get("identified_threat_count", 0) > 0:
        for threat_desc in risk_summary.get("threats_requiring_attention", []):
            threats.append(threat_desc)
    
    # Fallback: only add generic threats if no specific threats were identified
    if not threats:
        if competition.competition_score >= 60:
            threats.append(f"Competition is {competition.competition_level.lower()} at {competition.competition_score:.0f}/100 across {competition.mapped_competitors} mapped businesses.")
        else:
            threats.append("New competitors could reduce the available market gap as the location develops.")
        
        if purchasing_power.purchasing_power_score < 50:
            threats.append(f"Purchasing power is {purchasing_power.purchasing_power_level.lower()} at {purchasing_power.purchasing_power_score:.0f}/100, putting pressure on pricing and payback.")
        elif seasonality.low_periods:
            threats.append(f"Demand may soften during {', '.join(seasonality.low_periods)}, affecting cash flow against the startup budget.")
        else:
            threats.append("Supplier costs and local price competition could compress margins during early operations.")

    return SWOTAnalysis(strengths=strengths, weaknesses=weaknesses, opportunities=opportunities, threats=threats)

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

    # 11. Risk Analysis (with empty location as seed; no operational evidence)
    risk_result = analyze_risk(location, request.category_id, request.radius_km, operational_evidence=None)
    threat_summary = {
        "identified_threat_count": risk_result.summary.get("identified_threat_count", 0),
        "low_probability_threat_count": risk_result.summary.get("low_probability_threat_count", 0),
        "unknown_threat_count": risk_result.summary.get("unknown_threat_count", 0),
        "overall_status": risk_result.overall_status,
        "data_completeness": risk_result.summary.get("data_completeness", "INSUFFICIENT"),
        "threats_requiring_attention": [
            t.evidence_summary for t in risk_result.threats
            if t.status == "identified" and t.severity_level in ["critical", "high"]
        ],
    }

    swot = build_swot(
        category, demand_result, competition_result, activity_result,
        distribution_result, seasonality_result, purchasing_power_result, market_gap, threat_summary
    )

    # 12. Final Overall Market Score
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
        swot=swot,
        customer_potential=get_generic_level(demographic_result["demographic_fit"]),
        market_opportunity_level=get_generic_level(overall_score),
        overall_score=round(overall_score, 2),
        confidence=ConfidenceLevel.MEDIUM,
        data_provenance=provenance,
        threat_summary=threat_summary,
    )
