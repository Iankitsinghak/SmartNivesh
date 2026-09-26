from app.schemas.business import BusinessCategory
from app.schemas.market import AlternativeRecommendationRequest
from app.services.market import alternative_recommendations as alternatives


def _request(count: int = 8) -> AlternativeRecommendationRequest:
    return AlternativeRecommendationRequest(
        latitude=28.6139,
        longitude=77.209,
        category_id="CURRENT",
        radius_km=10,
        current_mapped_competitor_count=count,
    )


def test_returns_three_lower_risk_categories_from_mapped_features(monkeypatch):
    configured = [
        BusinessCategory(category_id="CURRENT", name="Current", osm_competitor_tags=[{"amenity": "restaurant"}]),
        BusinessCategory(category_id="A", name="Alternative A", osm_competitor_tags=[{"shop": "bakery"}]),
        BusinessCategory(category_id="B", name="Alternative B", osm_competitor_tags=[{"shop": "tailor"}]),
        BusinessCategory(category_id="C", name="Alternative C", osm_competitor_tags=[{"shop": "bicycle"}]),
        BusinessCategory(category_id="D", name="Alternative D", osm_competitor_tags=[{"shop": "hardware"}]),
    ]

    class FakeOverpass:
        def mapped_competitors_nearby(self, latitude, longitude, radius_km, osm_tags):
            assert (latitude, longitude, radius_km) == (28.6139, 77.209, 10)
            assert {tuple(rule.items())[0] for rule in osm_tags} >= {
                ("shop", "bakery"), ("shop", "tailor"), ("shop", "bicycle"), ("shop", "hardware"),
            }
            return [
                {"type": "node", "id": 1, "tags": {"shop": "bakery"}},
                {"type": "node", "id": 2, "tags": {"shop": "bakery"}},
                {"type": "node", "id": 3, "tags": {"shop": "tailor"}},
                {"type": "node", "id": 4, "tags": {"shop": "hardware"}},
                {"type": "node", "id": 4, "tags": {"shop": "hardware"}},
            ]

    monkeypatch.setattr(alternatives, "_categories", lambda: configured)
    monkeypatch.setattr(alternatives, "OverpassClient", FakeOverpass)

    result = alternatives.recommend_lower_risk_categories(_request())

    assert result.status == "AVAILABLE"
    assert result.risk_level == "HIGH"
    assert result.current_market_risk_score == 80
    assert [item.category_id for item in result.alternatives] == ["C", "B", "D"]
    assert all(item.market_risk_score < result.current_market_risk_score for item in result.alternatives)
    assert all(item.fit_score > 45 for item in result.alternatives)


def test_does_not_query_alternatives_when_current_risk_is_not_high(monkeypatch):
    monkeypatch.setattr(alternatives, "OverpassClient", lambda: (_ for _ in ()).throw(AssertionError("must not query")))

    result = alternatives.recommend_lower_risk_categories(_request(count=6))

    assert result.status == "AVAILABLE"
    assert result.risk_level == "NOT_HIGH"
    assert result.alternatives == []
