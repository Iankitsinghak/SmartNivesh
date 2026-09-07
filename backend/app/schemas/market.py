from dataclasses import dataclass, field
from typing import Optional

from app.core.enums import Confidence, EvidenceSufficiency, OpportunityType
from app.schemas.common import Evidence, Location, SufficiencyResult


@dataclass
class Opportunity:
    opportunity_id: str
    title: str
    opportunity_type: OpportunityType
    location: Location
    evidence: list[Evidence]
    data_confidence: Confidence
    limitations: list[str]
    methodology: list[str]
    unsupported_assumptions: list[str] = field(default_factory=list)
    supply_gap: Optional[str] = None
    accessibility_gap: Optional[str] = None
    local_need_evidence: Optional[str] = None
    data_coverage: Optional[str] = None


@dataclass
class OpportunityAnalysis:
    sufficiency: SufficiencyResult
    opportunity: Optional[Opportunity] = None
    message: Optional[str] = None
    status: EvidenceSufficiency = EvidenceSufficiency.INSUFFICIENT
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from app.schemas.common import DataProvenance
from app.schemas.location import Location
from app.schemas.business import BusinessCategory
from app.utils.provenance import ConfidenceLevel

class MarketAnalysisRequest(BaseModel):
    location_id: str
    category_id: str
    radius_km: float = 10.0

class RadiusAnalysis(BaseModel):
    radius_0_2_km: dict = {}
    radius_2_5_km: dict = {}
    radius_5_10_km: dict = {}

class DemandResult(BaseModel):
    demand_score: float = Field(ge=0, le=100)
    demand_level: str
    signals: dict = {}
    confidence: ConfidenceLevel

class CompetitionResult(BaseModel):
    mapped_competitors: int
    near_competitors: int
    competition_score: float = Field(ge=0, le=100)
    competition_level: str
    confidence: ConfidenceLevel

class BusinessActivityResult(BaseModel):
    commercial_activity_score: float = Field(ge=0, le=100)
    business_density: float
    relevant_business_count: int
    complementary_business_count: int
    supplier_presence: int
    market_activity_level: str

class POIResult(BaseModel):
    within_2km: dict = {}
    within_5km: dict = {}
    within_10km: dict = {}
    relevant_signals: List[dict] = []

class DistributionResult(BaseModel):
    distribution_score: float = Field(ge=0, le=100)
    distribution_level: str
    nearest_relevant_hubs: List[str] = []
    supplier_signals: List[str] = []
    confidence: ConfidenceLevel

class SeasonalityResult(BaseModel):
    seasonality_score: float = Field(ge=0, le=100)
    seasonality_level: str
    peak_periods: List[str] = []
    low_periods: List[str] = []
    risk_note: Optional[str] = None

class PurchasingPowerResult(BaseModel):
    purchasing_power_score: float = Field(ge=0, le=100)
    purchasing_power_level: str
    confidence: ConfidenceLevel

class MarketOpportunityGap(BaseModel):
    gap_score: float = Field(ge=0, le=100)
    demand_contribution: float
    growth_contribution: float
    distribution_contribution: float
    competition_deduction: float

class MarketAnalysisResponse(BaseModel):
    location: Location
    business_category: BusinessCategory
    radius_analysis: RadiusAnalysis
    poi_analysis: POIResult
    business_activity: BusinessActivityResult
    competition: CompetitionResult
    demand: DemandResult
    distribution: DistributionResult
    seasonality: SeasonalityResult
    purchasing_power: PurchasingPowerResult
    market_gap: MarketOpportunityGap
    customer_potential: str
    market_opportunity_level: str
    overall_score: float = Field(ge=0, le=100)
    confidence: ConfidenceLevel
    data_provenance: List[DataProvenance] = []
