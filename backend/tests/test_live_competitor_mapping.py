from app.schemas.market import CompetitorMappingRequest
from app.services.market import live_competitor_mapping as mapping


def setup_function(_function):
    """Keep legacy unit tests hermetic; multi-provider tests opt in explicitly."""
    import os
    os.environ["VYAPARSATHI_MULTISOURCE_COMPETITORS_ENABLED"] = "false"


def _request() -> CompetitorMappingRequest:
    return CompetitorMappingRequest(
        latitude=28.6139,
        longitude=77.2090,
        state_name="Example State",
        district_name="Example District",
        block_name="Example Block",
        category_id="CAT-001",
    )


def _demographics(*, include_age_segments: bool = True) -> mapping.DemographicSnapshot:
    segments = {"working_population": 5000}
    if include_age_segments:
        segments.update({"age_18_24": 2000, "age_25_44": 4000})
    return mapping.DemographicSnapshot(
        total_population=10000,
        households=2400,
        working_population=5000,
        segments=segments,
        source_name="Official population API",
        source_url="https://public.example.gov/demographics",
    )


class _FakeDemographicsApi:
    def fetch(self, request: CompetitorMappingRequest) -> mapping.DemographicSnapshot:
        assert request.block_name == "Example Block"
        return _demographics()


class _FakeOverpassClient:
    def resolve_block(self, latitude: float, longitude: float, block_name: str) -> mapping.BlockBoundary:
        assert (latitude, longitude, block_name) == (28.6139, 77.209, "Example Block")
        return mapping.BlockBoundary(osm_area_id=3600123, name=block_name, admin_level="6")

    def mapped_competitors(self, block, osm_tags):
        assert block.osm_area_id == 3600123
        assert list(osm_tags) == [{"amenity": "restaurant"}]
        return [
            {"type": "node", "id": 1, "lat": 28.61, "lon": 77.20, "tags": {"name": "A", "amenity": "restaurant"}},
            {"type": "node", "id": 1, "lat": 28.61, "lon": 77.20, "tags": {"name": "A", "amenity": "restaurant"}},
            {"type": "way", "id": 2, "center": {"lat": 28.62, "lon": 77.21}, "tags": {"name": "B", "amenity": "restaurant"}},
        ]

    def commercial_features(self, block):
        return [
            {"type": "node", "id": 11},
            {"type": "node", "id": 12},
            {"type": "node", "id": 13},
            {"type": "node", "id": 14},
            {"type": "node", "id": 15},
        ]


def test_live_mapping_uses_only_source_records_and_normalizes_density(monkeypatch):
    monkeypatch.setattr(mapping, "PublicDemographicsApi", _FakeDemographicsApi)
    monkeypatch.setattr(mapping, "OverpassClient", _FakeOverpassClient)

    response = mapping.analyze_live_competitor_mapping(_request())

    assert response.status == "AVAILABLE"
    assert response.mapped_competitor_count == 2
    assert len(response.mapped_competitors) == 2
    assert response.competitors_per_1000_residents == 0.2
    assert response.demographics.weighted_target_population_proxy == 3800.0
    assert response.competitors_per_1000_target_customers == 0.5263
    assert response.economic_context.mapped_commercial_features == 5
    assert response.economic_context.competitors_per_100_commercial_features == 40.0
    assert {source.source_id for source in response.data_provenance} == {
        "PUBLIC_BLOCK_DEMOGRAPHICS",
        "OSM_OVERPASS_LIVE",
    }


def test_live_mapping_does_not_fall_back_to_seeded_demographics(monkeypatch):
    class _UnavailableCensusApi:
        def fetch(self, request: CompetitorMappingRequest):
            raise mapping.LiveDataUnavailable("The official Census district resource is unavailable.")

    monkeypatch.setattr(mapping, "PublicDemographicsApi", _UnavailableCensusApi)

    response = mapping.analyze_live_competitor_mapping(_request())

    assert response.status == "INSUFFICIENT"
    assert response.mapped_competitor_count is None
    assert response.demographics is None
    assert "No seeded or synthetic data was used" in response.limitations[-1]


def test_target_customer_density_is_unavailable_when_the_public_record_lacks_segments(monkeypatch):
    class _SegmentLimitedDemographicsApi:
        def fetch(self, request: CompetitorMappingRequest) -> mapping.DemographicSnapshot:
            return _demographics(include_age_segments=False)

    monkeypatch.setattr(mapping, "PublicDemographicsApi", _SegmentLimitedDemographicsApi)
    monkeypatch.setattr(mapping, "OverpassClient", _FakeOverpassClient)

    response = mapping.analyze_live_competitor_mapping(_request())

    assert response.status == "AVAILABLE"
    assert response.competitors_per_1000_target_customers is None
    assert any("target-segment" in limitation for limitation in response.limitations)


def test_census_adapter_aggregates_exact_cd_block_rows_and_keeps_resource_uuid(monkeypatch):
    mapping.clear_census_district_cache()
    resource_id = "0b2c5c21-0110-479d-a17d-448ba5ebb041"
    html = (
        f'<script>window.__NUXT__={{post:{{uuid:"{resource_id}",'
        'field_datafile_url:"https:\\u002F\\u002Fcensusindia.gov.in\\u002Fdatagov'
        '\\u002FTDVD_Files\\u002Fsample.csv"}},catalog:{uuid:"'
        f'{mapping.CENSUS_VILLAGE_AMENITIES_CATALOG_ID}"}}}};</script>'
    ).encode()
    csv_body = (
        'State Name,District Name,CD Block Name,Total  Households ,Total Population of Village\n'
        'Maharashtra,Nashik,Surgana,10,50\n'
        'Maharashtra,Nashik,Surgana,20,70\n'
        'Maharashtra,Nashik,Other,999,999\n'
    ).encode()

    def fetch(url, *, accept, maximum_bytes):
        return html if url.startswith(mapping.CENSUS_RESOURCE_PREFIX) else csv_body

    monkeypatch.setattr(mapping, "_fetch_public_bytes", fetch)
    request = CompetitorMappingRequest(
        latitude=20,
        longitude=73,
        state_name="Maharashtra",
        district_name="Nashik",
        block_name="Surgana",
        category_id="CAT-001",
    )
    result = mapping.PublicDemographicsApi().fetch(request)

    assert result.total_population == 120
    assert result.households == 30
    assert result.source_id == resource_id
    assert "summed 2 rural village rows" in result.source_notes
    mapping.clear_census_district_cache()


def test_census_resource_slug_ignores_osm_district_suffix():
    request = CompetitorMappingRequest(
        latitude=20,
        longitude=73,
        state_name="Maharashtra",
        district_name="Nashik District",
        block_name="Surgana",
        category_id="CAT-001",
    )

    assert mapping.PublicDemographicsApi()._resource_page_url(request).endswith(
        "/village-amenities-nashik-district-maharashtra-2011"
    )


def test_micro_enterprise_categories_have_unique_ids_and_live_osm_mapping_rules():
    categories = mapping.json.loads(mapping._data_path("business_categories.json").read_text(encoding="utf-8"))
    ids = [category["category_id"] for category in categories]

    assert len(ids) == len(set(ids))
    assert len(categories) >= 19
    assert all(category.get("osm_competitor_tags") for category in categories)


def test_india_administrative_options_are_parent_scoped(monkeypatch):
    class _FakeHierarchyClient:
        def administrative_options(self, level, parent_id=None):
            assert level == "district"
            assert parent_id == "relation:123"
            return [
                mapping.IndiaAdministrativeOption(
                    id="relation:456",
                    name="Verified District",
                    admin_level="5",
                    latitude=28.6,
                    longitude=77.2,
                )
            ]

    monkeypatch.setattr(mapping, "OverpassClient", _FakeHierarchyClient)

    response = mapping.get_india_administrative_options("district", "relation:123")

    assert response.status == "AVAILABLE"
    assert response.options[0].name == "Verified District"
    assert response.data_provenance[0].source_id == "OSM_OVERPASS_LIVE"


def test_india_administrative_options_require_parent_selection():
    response = mapping.get_india_administrative_options("block")

    assert response.status == "INSUFFICIENT"
    assert response.options == []
    assert "parent" in response.limitations[0]


def test_state_lookup_uses_indexed_india_state_tags_and_short_timeout():
    client = object.__new__(mapping.OverpassClient)
    captured = {}

    def query(query_text, *, timeout_seconds=None):
        captured["query"] = query_text
        captured["timeout"] = timeout_seconds
        return [
            {
                "type": "relation",
                "id": 123,
                "tags": {"name": "Verified State", "admin_level": "4"},
                "center": {"lat": 28.6, "lon": 77.2},
            }
        ]

    client.query = query
    options = client.administrative_options("state")

    assert '["ISO3166-2"~"^IN-"]' in captured["query"]
    assert "area[\"ISO3166-1\"" not in captured["query"]
    assert captured["timeout"] == 5
    assert options[0].id == "relation:123"


def test_administrative_options_cache_recent_live_response(monkeypatch):
    mapping.clear_administrative_options_cache()
    calls = 0

    class _FakeHierarchyClient:
        def administrative_options(self, level, parent_id=None):
            nonlocal calls
            calls += 1
            return [
                mapping.IndiaAdministrativeOption(
                    id="relation:789",
                    name="Cached District",
                    admin_level="5",
                    latitude=28.6,
                    longitude=77.2,
                )
            ]

    monkeypatch.setattr(mapping, "OverpassClient", _FakeHierarchyClient)
    first = mapping.get_india_administrative_options("district", "relation:999")
    second = mapping.get_india_administrative_options("district", "relation:999")

    assert first.status == "AVAILABLE"
    assert second.status == "AVAILABLE"
    assert calls == 1
    assert any("cache" in limitation for limitation in second.limitations)
    mapping.clear_administrative_options_cache()
