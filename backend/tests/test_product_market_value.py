from app.schemas.market import ProductMarketValueRequest
from app.services.market import product_market_value as market_value


def _request(reference_price=None) -> ProductMarketValueRequest:
    return ProductMarketValueRequest(
        state_name="Maharashtra",
        district_name="Pune",
        block_name="Haveli",
        category_id="CAT-001",
        reference_price=reference_price,
    )


class _FakePurchasingPowerApi:
    def fetch(self, request: ProductMarketValueRequest) -> market_value.RegionalPurchasingPower:
        return market_value.RegionalPurchasingPower(
            index=90,
            baseline=100,
            geographic_scope="state (rural)",
            observed_at="2023-24",
            source_name="Official Government purchasing-capacity table",
            source_url="https://public.example.gov/purchasing-power",
        )


def test_product_market_value_uses_verified_affordability_formula_without_a_price_api(monkeypatch):
    monkeypatch.setattr(market_value, "PublicPurchasingPowerApi", _FakePurchasingPowerApi)

    response = market_value.analyze_product_market_value(_request(100))

    assert response.status == "AVAILABLE"
    assert response.purchasing_power.index == 90
    assert response.recommendation.adjustment_factor == 0.9
    assert response.recommendation.relative_position_percent == 90.0
    assert response.recommendation.reference_price == 100
    assert response.recommendation.adjusted_reference_price == 90
    assert {source.source_id for source in response.data_provenance} == {
        "PUBLIC_PURCHASING_POWER"
    }
    assert all("MARKET_PRICE" not in item for item in response.limitations)


def test_product_market_value_returns_a_multiplier_when_no_reference_price_is_entered(monkeypatch):
    monkeypatch.setattr(market_value, "PublicPurchasingPowerApi", _FakePurchasingPowerApi)

    response = market_value.analyze_product_market_value(_request())

    assert response.status == "AVAILABLE"
    assert response.recommendation.adjustment_factor == 0.9
    assert response.recommendation.adjusted_reference_price is None
    assert any("rather than an invented rupee price" in item for item in response.methodology)


def test_official_mpce_proxy_uses_exact_resource_and_all_india_rural_baseline():
    result = market_value.PublicPurchasingPowerApi().fetch(_request())

    assert result.index == 4145
    assert result.baseline == 4122
    assert result.source_id == market_value.MPCE_RESOURCE_ID
    assert result.geographic_scope == "state (rural)"
    assert "proxy" in result.basis
