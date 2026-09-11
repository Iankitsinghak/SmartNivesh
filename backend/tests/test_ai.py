import unittest
from datetime import date

from app.core.enums import Provenance
from app.schemas.common import DataSource, Evidence, Location
from app.services.ai.explanation_service import explain
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


class ExplanationTests(unittest.TestCase):
    def setUp(self) -> None:
        result = analyze_geographic_service_gap(
            location=Location("Rampur", "Example", "State", 20.0, 78.0),
            title="Agricultural Equipment Repair Service",
            evidence=[
                evidence("identified_providers", 0),
                evidence("nearest_identified_provider", 8.4, "km"),
            ],
        )
        self.opportunity = result.opportunity

    def test_invalid_generated_claim_falls_back(self) -> None:
        text = explain(self.opportunity, "Customers want this and it has guaranteed revenue.")
        self.assertIn("Potential Opportunity", text)
        self.assertIn("limitations", text.lower())
        self.assertIn("8.4", text)


if __name__ == "__main__":
    unittest.main()