import pytest
from app.services.market.competition_engine import analyze_competition
from app.schemas.business import BusinessCategory

# Using the seeded data:
# LOC-001 is at 28.7041, 77.1025
# CAT-001 (Restaurant) has CAT-001 as competitor
# Seeded competitors:
# BUS-001 (Restaurant): 28.7060, 77.1040 (Very close)
# BUS-003 (Restaurant): 28.8000, 77.2000 (Far away > 10km)

def test_competition_distance_weighting():
    category = BusinessCategory(
        category_id="CAT-001",
        name="Restaurant",
        competitor_categories=["CAT-001"]
    )
    
    # Test at LOC-001
    result = analyze_competition(lat=28.7041, lon=77.1025, category=category, radius_km=15.0)
    
    # Should find 2 mapped competitors (BUS-001, BUS-003) within 15km
    assert result.mapped_competitors == 2
    
    # Only 1 is near (<2km)
    assert result.near_competitors == 1
    
    # The score should not be maxed out since we only have 1 close and 1 far
    # 5 close = 100 score. 1 close = ~20, 1 far = ~1. So ~21.
    assert 15.0 < result.competition_score < 30.0

def test_no_competitors():
    category = BusinessCategory(
        category_id="CAT-999",
        name="Unknown",
        competitor_categories=["CAT-999"]
    )
    
    result = analyze_competition(lat=28.7041, lon=77.1025, category=category)
    assert result.mapped_competitors == 0
    assert result.competition_score == 0.0
