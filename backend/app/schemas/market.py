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
from typing import List, Dict, Literal, Optional
from app.schemas.common import DataProvenance
from app.schemas.location import Location
from app.schemas.business import BusinessCategory
from app.core.enums import ConfidenceLevel

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

class SWOTAnalysis(BaseModel):
    strengths: List[str]
    weaknesses: List[str]
    opportunities: List[str]
    threats: List[str]

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
    swot: SWOTAnalysis
    customer_potential: str
    market_opportunity_level: str
    overall_score: float = Field(ge=0, le=100)
    confidence: ConfidenceLevel
    data_provenance: List[DataProvenance] = []
    threat_summary: Optional[dict] = None  # Compact structured threat summary for market context


class CompetitorMappingRequest(BaseModel):
    """Input for a live, block-scoped competitor lookup."""

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    state_name: str = Field(min_length=2, max_length=160)
    district_name: str = Field(min_length=2, max_length=160)
    district_osm_id: Optional[str] = Field(default=None, max_length=80)
    block_name: str = Field(min_length=2, max_length=160)
    category_id: str


class AdministrativeLocationRequest(BaseModel):
    state_name: str = Field(min_length=2, max_length=160)
    district_name: str = Field(min_length=2, max_length=160)
    block_name: str = Field(min_length=2, max_length=160)


class AdministrativeLocationResponse(BaseModel):
    status: Literal["AVAILABLE", "INSUFFICIENT"]
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    district_osm_id: Optional[str] = None
    block_osm_id: Optional[str] = None
    limitations: List[str] = []
    data_provenance: List[DataProvenance] = []


class MappedCompetitor(BaseModel):
    osm_id: str
    osm_type: str
    name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    tags: Dict[str, str] = {}


class DemographicMappingContext(BaseModel):
    total_population: Optional[int] = None
    households: Optional[int] = None
    working_population: Optional[int] = None
    weighted_target_population_proxy: Optional[float] = None


class EconomicMappingContext(BaseModel):
    mapped_commercial_features: Optional[int] = None
    commercial_features_per_1000_residents: Optional[float] = None
    competitors_per_100_commercial_features: Optional[float] = None


class CompetitorMappingResponse(BaseModel):
    """A live-data result. No demo records or synthetic counts are used."""

    status: Literal["AVAILABLE", "INSUFFICIENT"]
    block_id: Optional[str] = None
    block_name: str
    block_admin_level: Optional[str] = None
    category_id: str
    mapped_competitor_count: Optional[int] = None
    mapped_competitors: List[MappedCompetitor] = []
    competitors_per_1000_residents: Optional[float] = None
    competitors_per_1000_target_customers: Optional[float] = None
    demographics: Optional[DemographicMappingContext] = None
    economic_context: Optional[EconomicMappingContext] = None
    confidence: ConfidenceLevel
    methodology: List[str] = []
    limitations: List[str] = []
    data_provenance: List[DataProvenance] = []


class IndiaAdministrativeOption(BaseModel):
    id: str
    name: str
    admin_level: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class IndiaAdministrativeOptionsResponse(BaseModel):
    status: Literal["AVAILABLE", "INSUFFICIENT"]
    level: Literal["state", "district", "block"]
    parent_id: Optional[str] = None
    options: List[IndiaAdministrativeOption] = []
    confidence: ConfidenceLevel
    limitations: List[str] = []
    data_provenance: List[DataProvenance] = []


class ProductMarketValueRequest(BaseModel):
    """Input for an MPCE-based local price-positioning calculation."""

    state_name: str = Field(min_length=2, max_length=160)
    district_name: Optional[str] = Field(default=None, min_length=2, max_length=160)
    block_name: Optional[str] = Field(default=None, min_length=2, max_length=160)
    category_id: str
    reference_price: Optional[float] = Field(default=None, gt=0, le=10_000_000)


class PurchasingPowerContext(BaseModel):
    index: float
    baseline: float
    geographic_scope: str
    observed_at: Optional[str] = None
    basis: Optional[str] = None


class PricingRecommendation(BaseModel):
    adjustment_factor: float
    relative_position_percent: float
    reference_price: Optional[float] = None
    adjusted_reference_price: Optional[float] = None
    strategy: str


class ProductMarketValueResponse(BaseModel):
    """Evidence-gated price positioning. It does not claim an observed or optimal price."""

    status: Literal["AVAILABLE", "INSUFFICIENT"]
    category_id: str
    state_name: str
    district_name: Optional[str] = None
    block_name: Optional[str] = None
    purchasing_power: Optional[PurchasingPowerContext] = None
    recommendation: Optional[PricingRecommendation] = None
    confidence: ConfidenceLevel
    methodology: List[str] = []
    limitations: List[str] = []
    data_provenance: List[DataProvenance] = []
