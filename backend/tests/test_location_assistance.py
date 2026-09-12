from app.services.location import external_geo


def test_mappls_autosuggest_normalizes_only_public_fields(monkeypatch):
    external_geo.mappls_autosuggest.cache_clear()
    monkeypatch.setenv("MAPPLS_ACCESS_TOKEN", "test-token")
    monkeypatch.setattr(external_geo, "_json_request", lambda *_args, **_kwargs: {
        "suggestedLocations": [
            {"type": "VILLAGE", "placeName": "Dangal", "placeAddress": "Kanksa, Paschim Bardhaman District, West Bengal", "eLoc": "IZ98I1"},
            {"type": "POI", "placeName": "Ignored", "eLoc": "NOPE"},
        ]
    })

    result = external_geo.mappls_autosuggest("Kanksa", "VLG")

    assert len(result) == 1
    assert result[0].type == "VILLAGE"
    assert result[0].eloc == "IZ98I1"
    external_geo.mappls_autosuggest.cache_clear()
