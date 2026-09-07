from app.schemas.market import OpportunityAnalysis
from app.services.reports.templates import opportunity_report


def build_report(analysis: OpportunityAnalysis) -> str:
    if analysis.opportunity is None:
        return analysis.message or "Insufficient evidence"
    return opportunity_report(analysis.opportunity)