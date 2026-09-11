"""
Risk analysis tests.

Verify threat analyzers, evidence validation, score bounds,
freshness checks, deterministic output, and API behavior.
"""

import pytest
from datetime import date, datetime, timedelta
from uuid import uuid4

from app.core.enums import Confidence, ThreatStatus
from app.schemas.location import Location, LocationHierarchy
from app.schemas.risk import OperationalEvidence
from app.services.risk.risk_engine import (
    analyze_buyer_concentration_threat,
    analyze_risk,
    analyze_seasonality_threat,
    analyze_supply_chain_bottleneck_threat,
    calculate_coefficient_of_variation,
    calculate_hhi,
    score_from_cv,
    score_from_stockout_frequency,
)
from app.services.risk.validation import (
    check_buyer_concentration_evidence_sufficiency,
    check_seasonality_evidence_sufficiency,
    check_supply_chain_evidence_sufficiency,
    validate_operational_evidence,
)


def create_test_location():
    """Create a test location with Pydantic model."""
    return Location(
        location_id="TEST-001",
        latitude=20.0,
        longitude=78.0,
        hierarchy=LocationHierarchy(
            state="State",
            district="District",
            village_town="Test"
        )
    )


class TestEvidenceValidation:
    """Validate operational evidence structure and data quality."""

    def test_valid_operational_evidence_passes(self):
        evidence = OperationalEvidence(
            observation_period_days=12,
            observation_start_date="2025-01-01",
            observation_end_date="2025-12-31",
            data_classification="BUSINESS_OWNED",
            seasonal_observations={"Jan": 100, "Feb": 90, "Mar": 110},
            supplier_count=3,
            lead_time_variability_coefficient=0.25,
        )
        valid, errors = validate_operational_evidence(evidence)
        assert valid
        assert len(errors) == 0

    def test_invalid_date_format_rejected(self):
        evidence = OperationalEvidence(
            observation_period_days=12,
            observation_start_date="2025-01-01",
            observation_end_date="invalid-date",
            data_classification="BUSINESS_OWNED",
        )
        valid, errors = validate_operational_evidence(evidence)
        assert not valid
        assert len(errors) > 0

    def test_end_date_before_start_rejected(self):
        evidence = OperationalEvidence(
            observation_period_days=12,
            observation_start_date="2025-12-31",
            observation_end_date="2025-01-01",
            data_classification="BUSINESS_OWNED",
        )
        valid, errors = validate_operational_evidence(evidence)
        assert not valid
        assert any("after" in e for e in errors)

    def test_stale_evidence_rejected(self):
        # Evidence older than 2 years
        old_end_date = (date.today() - timedelta(days=800)).isoformat()
        evidence = OperationalEvidence(
            observation_period_days=365,
            observation_start_date="2021-01-01",
            observation_end_date=old_end_date,
            data_classification="BUSINESS_OWNED",
        )
        valid, errors = validate_operational_evidence(evidence)
        assert not valid
        assert any("stale" in e.lower() for e in errors)

    def test_negative_supplier_count_rejected(self):
        evidence = OperationalEvidence(
            observation_period_days=6,
            observation_start_date="2024-01-01",
            observation_end_date="2024-06-30",
            data_classification="BUSINESS_OWNED",
            supplier_count=-1,
        )
        valid, errors = validate_operational_evidence(evidence)
        assert not valid
        assert any("non-negative" in e for e in errors)

    def test_invalid_percentage_rejected(self):
        evidence = OperationalEvidence(
            observation_period_days=6,
            observation_start_date="2024-01-01",
            observation_end_date="2024-06-30",
            data_classification="BUSINESS_OWNED",
            top_buyer_share=1.5,  # > 1.0
        )
        valid, errors = validate_operational_evidence(evidence)
        assert not valid
        assert any("0.0-1.0" in e for e in errors)


class TestSeasonalityAnalysis:
    """Test seasonal demand threat analysis."""

    def test_insufficient_evidence_returns_unknown(self):
        location = create_test_location()
        threat = analyze_seasonality_threat(location, None)
        assert threat.status == ThreatStatus.UNKNOWN.value
        assert threat.severity_score is None
        assert len(threat.missing_data_for_confidence) > 0

    def test_stable_demand_low_severity(self):
        location = create_test_location()
        evidence = OperationalEvidence(
            observation_period_days=12,
            observation_start_date="2024-01-01",
            observation_end_date="2024-12-31",
            data_classification="BUSINESS_OWNED",
            seasonal_observations={"Jan": 100, "Feb": 101, "Mar": 99, "Apr": 102, "May": 98, "Jun": 100, 
                                   "Jul": 101, "Aug": 99, "Sep": 100, "Oct": 102, "Nov": 98, "Dec": 100},
        )
        threat = analyze_seasonality_threat(location, evidence)
        assert threat.status in [ThreatStatus.LOW.value, ThreatStatus.IDENTIFIED.value]
        assert threat.severity_score is not None
        assert threat.severity_score < 50  # Low seasonality

    def test_highly_seasonal_demand_high_severity(self):
        location = create_test_location()
        evidence = OperationalEvidence(
            observation_period_days=12,
            observation_start_date="2024-01-01",
            observation_end_date="2024-12-31",
            data_classification="BUSINESS_OWNED",
            seasonal_observations={"Jan": 10, "Feb": 15, "Mar": 20, "Apr": 25, "May": 30, "Jun": 35,
                                   "Jul": 100, "Aug": 120, "Sep": 110, "Oct": 80, "Nov": 30, "Dec": 15},
        )
        threat = analyze_seasonality_threat(location, evidence)
        assert threat.status == ThreatStatus.IDENTIFIED.value
        assert threat.severity_score is not None
        assert threat.severity_score >= 70  # High seasonality

    def test_seasonality_includes_mitigations(self):
        location = create_test_location()
        evidence = OperationalEvidence(
            observation_period_days=12,
            observation_start_date="2024-01-01",
            observation_end_date="2024-12-31",
            data_classification="BUSINESS_OWNED",
            seasonal_observations={"Jan": 10, "Feb": 20, "Mar": 100, "Apr": 90, "May": 110, "Jun": 100,
                                   "Jul": 150, "Aug": 140, "Sep": 120, "Oct": 80, "Nov": 60, "Dec": 50},
        )
        threat = analyze_seasonality_threat(location, evidence)
        assert len(threat.mitigation_recommendations) > 0


class TestSupplyChainAnalysis:
    """Test supply-chain bottleneck threat analysis."""

    def test_insufficient_evidence_returns_unknown(self):
        location = create_test_location()
        threat = analyze_supply_chain_bottleneck_threat(location, None)
        assert threat.status == ThreatStatus.UNKNOWN.value
        assert threat.severity_score is None

    def test_single_supplier_high_severity(self):
        location = create_test_location()
        evidence = OperationalEvidence(
            observation_period_days=6,
            observation_start_date="2024-01-01",
            observation_end_date="2024-06-30",
            data_classification="BUSINESS_OWNED",
            supplier_count=1,
            lead_time_variability_coefficient=0.2,
            stockout_frequency_per_year=1,
        )
        threat = analyze_supply_chain_bottleneck_threat(location, evidence)
        assert threat.status == ThreatStatus.IDENTIFIED.value
        assert threat.severity_score is not None
        assert threat.severity_score >= 55  # High concentration risk (supplier concentration heavily weighted)

    def test_multiple_suppliers_low_severity(self):
        location = create_test_location()
        evidence = OperationalEvidence(
            observation_period_days=6,
            observation_start_date="2024-01-01",
            observation_end_date="2024-06-30",
            data_classification="BUSINESS_OWNED",
            supplier_count=5,
            lead_time_variability_coefficient=0.1,
            stockout_frequency_per_year=0,
            average_fulfillment_rate=0.99,
        )
        threat = analyze_supply_chain_bottleneck_threat(location, evidence)
        assert threat.severity_score is not None
        assert threat.severity_score < 50

    def test_supply_chain_includes_mitigations(self):
        location = create_test_location()
        evidence = OperationalEvidence(
            observation_period_days=6,
            observation_start_date="2024-01-01",
            observation_end_date="2024-06-30",
            data_classification="BUSINESS_OWNED",
            supplier_count=2,
            lead_time_variability_coefficient=0.4,
            stockout_frequency_per_year=3,
        )
        threat = analyze_supply_chain_bottleneck_threat(location, evidence)
        assert len(threat.mitigation_recommendations) > 0


class TestBuyerConcentrationAnalysis:
    """Test buyer concentration threat analysis."""

    def test_insufficient_evidence_returns_unknown(self):
        location = create_test_location()
        threat = analyze_buyer_concentration_threat(location, None)
        assert threat.status == ThreatStatus.UNKNOWN.value
        assert threat.severity_score is None

    def test_high_buyer_concentration_identified(self):
        location = create_test_location()
        evidence = OperationalEvidence(
            observation_period_days=6,
            observation_start_date="2024-01-01",
            observation_end_date="2024-06-30",
            data_classification="BUSINESS_OWNED",
            buyer_count=5,
            top_buyer_share=0.60,  # 60% from one buyer
        )
        threat = analyze_buyer_concentration_threat(location, evidence)
        assert threat.status == ThreatStatus.IDENTIFIED.value
        assert threat.severity_score is not None
        assert threat.severity_score >= 70

    def test_diversified_buyers_low_severity(self):
        location = create_test_location()
        evidence = OperationalEvidence(
            observation_period_days=6,
            observation_start_date="2024-01-01",
            observation_end_date="2024-06-30",
            data_classification="BUSINESS_OWNED",
            buyer_count=50,
            top_buyer_share=0.10,  # 10% from largest buyer
            top_3_buyer_share=0.25,
        )
        threat = analyze_buyer_concentration_threat(location, evidence)
        assert threat.severity_score is not None
        assert threat.severity_score < 50

    def test_buyer_concentration_includes_mitigations(self):
        location = create_test_location()
        evidence = OperationalEvidence(
            observation_period_days=6,
            observation_start_date="2024-01-01",
            observation_end_date="2024-06-30",
            data_classification="BUSINESS_OWNED",
            buyer_count=8,
            top_buyer_share=0.70,
        )
        threat = analyze_buyer_concentration_threat(location, evidence)
        assert len(threat.mitigation_recommendations) > 0


class TestStatisticsFunctions:
    """Test helper statistical functions."""

    def test_coefficient_of_variation_low(self):
        values = [100, 101, 99, 102, 98, 100]
        cv = calculate_coefficient_of_variation(values)
        assert cv is not None
        assert cv < 0.05

    def test_coefficient_of_variation_high(self):
        values = [10, 50, 100, 200, 150, 30]
        cv = calculate_coefficient_of_variation(values)
        assert cv is not None
        assert cv > 0.50

    def test_hhi_concentrated_market(self):
        # One dominant buyer: 80%, others 20%
        shares = [0.80, 0.10, 0.10]
        hhi = calculate_hhi(shares)
        # HHI = (80)^2 + (10)^2 + (10)^2 = 6400 + 100 + 100 = 6600
        assert hhi > 6000  # High concentration (> 2500 is DOJ threshold)

    def test_hhi_fragmented_market(self):
        # 10 equal buyers
        shares = [0.10] * 10
        hhi = calculate_hhi(shares)
        # HHI = 10 * (10)^2 = 1000
        assert hhi < 1500  # Low concentration

    def test_score_from_cv(self):
        assert score_from_cv(0.10) < 30
        assert 40 < score_from_cv(0.20) < 60
        assert score_from_cv(0.50) > 70

    def test_score_from_stockout_frequency(self):
        assert score_from_stockout_frequency(0) < 30
        assert 40 < score_from_stockout_frequency(1.5) < 60
        assert score_from_stockout_frequency(6) > 80


class TestRiskOrchestration:
    """Test the full risk analysis orchestrator."""

    def test_risk_analysis_without_evidence(self):
        location = create_test_location()
        response = analyze_risk(location, "CAT-001", 10.0, operational_evidence=None)
        
        assert response.location_id == "TEST-001"
        assert response.category_id == "CAT-001"
        assert len(response.threats) == 3  # Three threat types
        assert response.summary["unknown_threat_count"] == 3
        assert response.overall_status == "INSUFFICIENT_DATA"

    def test_risk_analysis_with_valid_evidence(self):
        location = create_test_location()
        evidence = OperationalEvidence(
            observation_period_days=12,
            observation_start_date="2024-01-01",
            observation_end_date="2024-12-31",
            data_classification="BUSINESS_OWNED",
            seasonal_observations={"Jan": 50, "Feb": 60, "Mar": 100, "Apr": 90, "May": 110, "Jun": 100,
                                   "Jul": 150, "Aug": 140, "Sep": 120, "Oct": 80, "Nov": 60, "Dec": 50},
            supplier_count=3,
            lead_time_variability_coefficient=0.20,
            stockout_frequency_per_year=1.5,
            buyer_count=20,
            top_buyer_share=0.25,
            top_3_buyer_share=0.50,
        )
        response = analyze_risk(location, "CAT-001", 10.0, operational_evidence=evidence)
        
        assert len(response.threats) == 3
        assert response.summary["identified_threat_count"] + response.summary["low_probability_threat_count"] > 0
        assert response.overall_status in ["MANAGEABLE", "REQUIRES_ATTENTION"]
        assert response.data_confidence == "high"

    def test_threat_response_includes_all_fields(self):
        location = create_test_location()
        evidence = OperationalEvidence(
            observation_period_days=12,
            observation_start_date="2024-01-01",
            observation_end_date="2024-12-31",
            data_classification="BUSINESS_OWNED",
            seasonal_observations={"Jan": 10, "Feb": 20, "Mar": 100, "Apr": 90},
            supplier_count=2,
            lead_time_variability_coefficient=0.30,
            stockout_frequency_per_year=2,
            buyer_count=8,
            top_buyer_share=0.45,
        )
        response = analyze_risk(location, "CAT-001", 10.0, operational_evidence=evidence)
        
        for threat in response.threats:
            assert threat.threat_id
            assert threat.threat_type in ["seasonal_demand", "supply_chain_bottleneck", "buyer_concentration"]
            assert threat.status in ["identified", "low", "unknown"]
            assert threat.evidence_summary
            assert isinstance(threat.limitations, list)
            assert isinstance(threat.methodology, list)
            assert isinstance(threat.mitigation_recommendations, list)

    def test_deterministic_output_for_same_input(self):
        location = create_test_location()
        evidence = OperationalEvidence(
            observation_period_days=6,
            observation_start_date="2024-01-01",
            observation_end_date="2024-06-30",
            data_classification="BUSINESS_OWNED",
            seasonal_observations={"Q1": 100, "Q2": 150},
            supplier_count=3,
            lead_time_variability_coefficient=0.25,
            buyer_count=10,
            top_buyer_share=0.30,
        )
        
        response1 = analyze_risk(location, "CAT-001", 10.0, operational_evidence=evidence)
        response2 = analyze_risk(location, "CAT-001", 10.0, operational_evidence=evidence)
        
        # Compare threat scores
        for t1, t2 in zip(response1.threats, response2.threats):
            assert t1.threat_type == t2.threat_type
            assert t1.severity_score == t2.severity_score
            assert t1.status == t2.status

    def test_no_buyer_pii_in_response(self):
        """Ensure buyer names/PII are not exposed in API response."""
        location = create_test_location()
        evidence = OperationalEvidence(
            observation_period_days=6,
            observation_start_date="2024-01-01",
            observation_end_date="2024-06-30",
            data_classification="BUSINESS_OWNED",
            buyer_count=5,
            top_buyer_share=0.50,
        )
        response = analyze_risk(location, "CAT-001", 10.0, operational_evidence=evidence)
        
        # Serialize to dict and search for sensitive patterns
        import json
        serialized = json.dumps(response.__dict__, default=str)
        # Should not contain buyer names or company identifiers
        assert "customer_" not in serialized.lower() or "anonymized" in serialized.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
