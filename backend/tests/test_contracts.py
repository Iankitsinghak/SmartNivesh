import unittest
from datetime import date
from pathlib import Path

from app.core.enums import OpportunityType, Provenance
from app.schemas.common import DataSource, Evidence, Location
from app.services.opportunity.opportunity_engine import analyze_opportunity
from app.services.reports.report_service import build_report
from scripts.verify_data import load_source_registry
from scripts.import_public_data import normalize_public_record


class ContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = DataSource(
            source_id="gov-demo",
            provider_name="Public government dataset",
            dataset_name="Verified local indicators",
            source_url="https://data.gov.in/",
            access_method="Public download",
            publication_date=date(2025, 1, 1),
            geographic_coverage="Target district",
            limitations=("Coverage varies by dataset.",),
        )
        self.location = Location("Rampur", "Example", "State", 20, 78)

    def item(self, indicator: str, value: object, unit: str = "records") -> Evidence:
        return Evidence(
            indicator=indicator,
            value=value,
            unit=unit,
            geographic_scope="target catchment",
            source=self.source,
            dataset_date=date(2025, 1, 1),
            provenance=Provenance.VERIFIED,
        )

    def test_each_opportunity_type_requires_explicit_indicators(self) -> None:
        required = {
            OpportunityType.LOCAL_SUPPLY_GAP: [self.item("identified_providers", 1), self.item("local_activity", 200, "units")],
            OpportunityType.INFRASTRUCTURE_GAP: [self.item("identified_facilities", 1), self.item("population_or_coverage", 500, "people")],
            OpportunityType.AGRICULTURE_LINKED: [self.item("agricultural_activity", 100, "hectares"), self.item("identified_providers", 0)],
            OpportunityType.LIVESTOCK_LINKED: [self.item("livestock_activity", 80, "animals"), self.item("identified_providers", 0)],
            OpportunityType.RESOURCE_LINKED: [self.item("local_resource", 1, "identified resources"), self.item("identified_providers", 0)],
        }
        for opportunity_type, evidence in required.items():
            with self.subTest(opportunity_type=opportunity_type):
                result = analyze_opportunity(
                    location=self.location,
                    title=opportunity_type.value,
                    opportunity_type=opportunity_type,
                    evidence=evidence,
                )
                self.assertIsNotNone(result.opportunity)

    def test_report_is_evidence_transparent(self) -> None:
        result = analyze_opportunity(
            location=self.location,
            title="Linked service",
            opportunity_type=OpportunityType.RESOURCE_LINKED,
            evidence=[self.item("local_resource", 1), self.item("identified_providers", 0)],
        )
        report = build_report(result)
        self.assertIn("dataset date", report)
        self.assertIn("Limitations", report)
        self.assertIn("not inferred", report)

    def test_registry_loads_typed_sources(self) -> None:
        sources = load_source_registry(Path(__file__).parents[1] / "data" / "data_sources.json")
        self.assertEqual(sources[0].source_id, "osm")
        self.assertIsInstance(sources[0].publication_date, date)

    def test_public_import_normalizes_and_requires_scope(self) -> None:
        record = normalize_public_record(
            {"indicator": " Agricultural Activity ", "value": 12, "unit": "hectares", "geographic_scope": "village"},
            source_id="gov-demo",
            dataset_date="2025-01-01",
        )
        self.assertEqual(record["indicator"], "agricultural_activity")
        self.assertEqual(record["provenance"], Provenance.VERIFIED)
        with self.assertRaises(ValueError):
            normalize_public_record(
                {"indicator": "activity", "value": 12},
                source_id="gov-demo",
                dataset_date="2025-01-01",
            )


if __name__ == "__main__":
    unittest.main()