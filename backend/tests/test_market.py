import pytest
from app.schemas.market import MarketAnalysisRequest
from app.services.market.market_engine import analyze_market

def test_overall_market_analysis():
    request = MarketAnalysisRequest(
        location_id="LOC-001",
        category_id="CAT-001",
        radius_km=10.0
    )
    
    response = analyze_market(request)
    
    # Check that location and category are resolved
    assert response.location.location_id == "LOC-001"
    assert response.business_category.category_id == "CAT-001"
    
    # Check that POI analysis runs
    assert response.poi_analysis.within_2km is not None
    
    # Check that Market Gap works
    assert response.market_gap.gap_score >= 0.0
    assert response.market_gap.gap_score <= 100.0
    
    # Check provenance
    assert len(response.data_provenance) >= 2
    
    # Since Demographics seeded data matches working population, score > 0
    assert response.demand.signals["demographic_fit"] > 0
    
def test_unknown_location_fails_gracefully():
    request = MarketAnalysisRequest(
        location_id="LOC-UNKNOWN",
        category_id="CAT-001"
    )
    
    with pytest.raises(ValueError, match="Location not found"):
        analyze_market(request)
