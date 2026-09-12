from app.services.location import external_geo


def test_google_geocoder_is_used_without_exposing_key(monkeypatch):
    external_geo.geocode_administrative_area.cache_clear()
    monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "test-secret")
    monkeypatch.setenv("VYAPARSATHI_GOOGLE_MAPS_ENABLED", "true")
    monkeypatch.setenv("VYAPARSATHI_OPENROUTESERVICE_ENABLED", "false")

    def fake_request(url, **kwargs):
        assert "test-secret" in url
        return {"results": [{"place_id": "place-1", "geometry": {"location": {"lat": 30.1, "lng": 77.2}}}]}

    monkeypatch.setattr(external_geo, "_json_request", fake_request)
    point = external_geo.geocode_administrative_area("Uttar Pradesh", "Saharanpur", "Behat")
    assert point.latitude == 30.1
    assert point.longitude == 77.2
    assert point.provider == "Google Geocoding"


def test_google_places_mapping_request_is_bounded(monkeypatch):
    monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "test-secret")
    monkeypatch.setenv("VYAPARSATHI_GOOGLE_MAPS_ENABLED", "true")

    def fake_request(url, **kwargs):
        assert kwargs["body"]["pageSize"] == 20
        assert kwargs["body"]["locationBias"]["circle"]["radius"] == 10_000
        return {"places": [{"id": "a", "businessStatus": "OPERATIONAL"}, {"id": "b", "businessStatus": "CLOSED_PERMANENTLY"}]}

    monkeypatch.setattr(external_geo, "_json_request", fake_request)
    places = external_geo.google_places_for_category("Restaurant", 30.1, 77.2, "UP", "Saharanpur", "Behat")
    assert [item["id"] for item in places] == ["a"]


def test_openrouteservice_route_summary(monkeypatch):
    external_geo.route_summary.cache_clear()
    monkeypatch.setenv("OPENROUTESERVICE_API_KEY", "test-token")
    monkeypatch.setenv("VYAPARSATHI_OPENROUTESERVICE_ENABLED", "true")

    def fake_request(url, **kwargs):
        assert kwargs["headers"]["Authorization"] == "test-token"
        return {"features": [{"properties": {"summary": {"distance": 5500, "duration": 900}}}]}

    monkeypatch.setattr(external_geo, "_json_request", fake_request)
    route = external_geo.route_summary(30.1, 77.2, 30.2, 77.3)
    assert route.distance_km == 5.5
    assert route.duration_minutes == 15
