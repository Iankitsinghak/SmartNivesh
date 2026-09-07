import unittest
from datetime import date

from app.core.enums import Provenance
from app.schemas.common import DataSource, Evidence, Location
from app.services.opportunity.opportunity_engine import analyze_geographic_service_gap


def source() -> DataSource:
    return DataSource(
        source_id="osm",
        provider_name="OpenStreetMap contributors",
        dataset_name="Mapped businesses and services",
        source_url="https://www.openstreetmap.org/",
        access_method="Public Overpass API extract",
        publication_date=date(2026, 1, 1),
        geographic_coverage="Target catchment",
        limitations=("Rural business listings may be incomplete.",),
    )


def evidence(indicator: str, value: object, unit: str = "providers") -> Evidence:
    return Evidence(
        indicator=indicator,
        value=value,
        unit=unit,
        geographic_scope="within 5 km",
        source=source(),
        dataset_date=date(2026, 1, 1),
        provenance=Provenance.VERIFIED,
        method="dataset query",
        limitations=("Absence from the dataset does not prove real-world absence.",),
    )


class OpportunityEngineTests(unittest.TestCase):
    location = Location("Rampur", "Example", "State", 20.0, 78.0)

    def test_complete_evidence_produces_transparent_opportunity(self) -> None:
        result = analyze_geographic_service_gap(
            location=self.location,
            title="Agricultural Equipment Repair Service",
            evidence=[
                evidence("identified_providers", 0),
                evidence("nearest_identified_provider", 8.4, "km"),
            ],
        )

        self.assertIsNotNone(result.opportunity)
        self.assertEqual(result.opportunity.supply_gap, "high")
        self.assertIn("does not prove", result.opportunity.limitations[0])
        self.assertEqual(result.opportunity.data_confidence.value, "high")

    def test_missing_required_evidence_blocks_display(self) -> None:
        result = analyze_geographic_service_gap(
            location=self.location,
            title="Agricultural Equipment Repair Service",
            evidence=[evidence("identified_providers", 0)],
        )

        self.assertIsNone(result.opportunity)
        self.assertIn("nearest_identified_provider", result.sufficiency.missing_data)
        self.assertIn("Insufficient evidence", result.message)

    def test_invalid_source_metadata_blocks_display(self) -> None:
        invalid = evidence("nearest_identified_provider", 8.4, "km")
        invalid = Evidence(
            indicator=invalid.indicator,
            value=invalid.value,
            unit=invalid.unit,
            geographic_scope=invalid.geographic_scope,
            source=DataSource(
                source_id="",
                provider_name=invalid.source.provider_name,
                dataset_name=invalid.source.dataset_name,
                source_url=invalid.source.source_url,
                access_method=invalid.source.access_method,
                publication_date=invalid.source.publication_date,
                geographic_coverage=invalid.source.geographic_coverage,
            ),
            dataset_date=invalid.dataset_date,
            provenance=invalid.provenance,
        )
        result = analyze_geographic_service_gap(
            location=self.location,
            title="Agricultural Equipment Repair Service",
            evidence=[evidence("identified_providers", 0), invalid],
        )

        self.assertIsNone(result.opportunity)
        self.assertIn("nearest_identified_provider.source_id", result.sufficiency.missing_data)


if __name__ == "__main__":
    unittest.main()