import unittest

from tests.test_opportunity import evidence
from app.schemas.common import Location
from app.services.ai.explanation_service import explain
from app.services.opportunity.opportunity_engine import analyze_geographic_service_gap


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