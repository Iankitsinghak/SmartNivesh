import unittest

from app.services.location.radius import bounded_distance_decay, radius_band


class RadiusTests(unittest.TestCase):
    def test_supported_bands_are_explicit(self) -> None:
        self.assertEqual(radius_band(0), "0-2 km")
        self.assertEqual(radius_band(2), "0-2 km")
        self.assertEqual(radius_band(4.9), "2-5 km")
        self.assertEqual(radius_band(8), "5-10 km")
        self.assertIsNone(radius_band(10.1))

    def test_distance_decay_is_bounded_and_monotonic(self) -> None:
        self.assertEqual(bounded_distance_decay(0), 1)
        self.assertEqual(bounded_distance_decay(10), 0)
        self.assertGreater(bounded_distance_decay(2), bounded_distance_decay(8))


if __name__ == "__main__":
    unittest.main()
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
