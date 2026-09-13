export type HealthState = 'checking' | 'online' | 'offline'

export interface MarketAnalysis {
  location: {
    location_id: string
    latitude: number
    longitude: number
    hierarchy: { country: string; state: string; district: string; village_town: string }
  }
  business_category: { category_id: string; name: string; capital_min: number; capital_max: number }
  overall_score: number
  market_opportunity_level: string
  customer_potential: string
  confidence: string
  demand: { demand_score: number; demand_level: string; confidence: string }
  competition: { competition_score: number; competition_level: string; mapped_competitors: number; near_competitors: number }
  market_gap: { gap_score: number; demand_contribution: number; growth_contribution: number; distribution_contribution: number; competition_deduction: number }
  swot: { strengths: string[]; weaknesses: string[]; opportunities: string[]; threats: string[] }
  business_activity: { commercial_activity_score: number; business_density: number; relevant_business_count: number; complementary_business_count: number; market_activity_level: string }
  distribution: { distribution_score: number; distribution_level: string; nearest_relevant_hubs: string[]; supplier_signals: string[] }
  seasonality: { seasonality_score: number; seasonality_level: string; peak_periods: string[]; low_periods: string[]; risk_note?: string }
  purchasing_power: { purchasing_power_score: number; purchasing_power_level: string; confidence: string }
  data_provenance: Array<{ source_id: string; source_name: string; source_url?: string; data_type: string; confidence: string; notes?: string }>
}

export interface CompetitorMapping {
  status: 'AVAILABLE' | 'INSUFFICIENT'
  block_id?: string
  block_name: string
  analysis_scope?: 'DISTRICT' | 'SUBDISTRICT' | 'VILLAGE'
  block_admin_level?: string
  category_id: string
  mapped_competitor_count?: number
  analysis_point?: { latitude: number; longitude: number; source: string }
  mapped_competitors: Array<{ osm_id: string; osm_type: string; provider?: 'OPENSTREETMAP' | 'GOOGLE_PLACES' | 'GEOAPIFY'; source_feature_id?: string; name?: string; latitude?: number; longitude?: number; distance_km?: number; tags: Record<string, string> }>
  competitors_per_1000_residents?: number
  competitors_per_1000_target_customers?: number
  demographics?: { total_population?: number; households?: number; working_population?: number; weighted_target_population_proxy?: number }
  economic_context?: { mapped_commercial_features?: number; commercial_features_per_1000_residents?: number; competitors_per_100_commercial_features?: number }
  radius_supply?: { within_2km: number; within_5km: number; within_10km: number }
  accessibility?: { status: 'AVAILABLE' | 'INSUFFICIENT'; nearest_competitor_distance_km?: number; nearest_competitor_drive_distance_km?: number; nearest_competitor_drive_time_minutes?: number; provider?: string; limitations: string[] }
  confidence: string
  methodology: string[]
  limitations: string[]
  data_provenance: Array<{ source_id: string; source_name: string; source_url?: string; data_type: string; confidence: string; notes?: string }>
}

export interface IndiaAdministrativeOption {
  id: string
  name: string
  admin_level: string
  latitude?: number
  longitude?: number
}

export interface IndiaAdministrativeOptions {
  status: 'AVAILABLE' | 'INSUFFICIENT'
  level: 'state' | 'district' | 'block'
  parent_id?: string
  options: IndiaAdministrativeOption[]
  confidence: string
  limitations: string[]
  data_provenance: Array<{ source_id: string; source_name: string; source_url?: string; data_type: string; confidence: string }>
}

export interface AdministrativeLocation {
  status: 'AVAILABLE' | 'INSUFFICIENT'
  latitude?: number
  longitude?: number
  district_osm_id?: string
  block_osm_id?: string
  limitations: string[]
  data_provenance: Array<{ source_id: string; source_name: string; source_url?: string; data_type: string; confidence: string }>
}

export interface LocalDemographics {
  status: 'AVAILABLE' | 'INSUFFICIENT'
  geographic_scope: string
  total_population?: number
  households?: number
  working_population?: number
  population_0_6?: number
  census_year: string
  limitations: string[]
  data_provenance: Array<{ source_id: string; source_name: string; source_url?: string; notes?: string }>
}

export interface MapplsSuggestion {
  type: 'STATE' | 'DISTRICT' | 'SUB_DISTRICT' | 'VILLAGE'
  place_name: string
  place_address?: string
  alternate_name?: string
  mappls_eloc: string
}

export interface MapplsAutosuggestResponse {
  status: 'AVAILABLE' | 'INSUFFICIENT'
  suggestions: MapplsSuggestion[]
  limitations: string[]
}

export interface AssessmentAssistantResponse {
  answer: string
  language: 'en' | 'hi'
  generated_by: 'gemini' | 'safe_fallback'
  limitations: string[]
}

export interface ProductMarketValue {
  status: 'AVAILABLE' | 'INSUFFICIENT'
  category_id: string
  state_name: string
  district_name?: string
  block_name?: string
  purchasing_power?: {
    index: number
    baseline: number
    geographic_scope: string
    observed_at?: string
    basis?: string
  }
  recommendation?: {
    adjustment_factor: number
    relative_position_percent: number
    reference_price?: number
    adjusted_reference_price?: number
    strategy: string
  }
  confidence: string
  methodology: string[]
  limitations: string[]
  data_provenance: Array<{ source_id: string; source_name: string; source_url?: string; data_type: string; confidence: string; notes?: string }>
}

export type ActivityType = 'service_or_trading' | 'manufacturing' | 'food_processing' | 'traditional_artisan' | 'not_sure'
export type AreaType = 'rural' | 'urban' | 'not_sure'
export type PMEGPBeneficiaryGroup = 'general' | 'special' | 'not_sure'

export interface FinancialRoadmapRequest {
  margin_capital: number
  activity_type: ActivityType
  area_type: AreaType
  pmegp_beneficiary_group: PMEGPBeneficiaryGroup
  has_repaid_mudra_tarun: boolean
  vishwakarma_loan_stage: 'not_confirmed' | 'first' | 'second'
  monthly_fixed_cost?: number
  monthly_variable_cost?: number
  expected_monthly_revenue?: number
  operating_reserve_months?: number
}

export interface FinancialIntelligence {
  calculated_project_cost: number
  calculated_loan_requirement: number
  monthly_emi: number
  total_repayment: number
  total_interest: number
  revenue?: { status: string; monthly_revenue?: number; methodology: string }
  costs?: { status: string; variable_cost?: number; fixed_cost?: number; total_operating_cost?: number; operating_profit?: number; methodology: string[] }
  working_capital?: { status: string; requirement?: number; methodology: string }
  repayment_metrics?: { status: string; available_monthly_cash?: number; repayment_coverage?: number; monthly_cash_surplus?: number; methodology: string }
  scenario_results: Array<{ name: 'CONSERVATIVE' | 'BASE' | 'OPTIMISTIC'; status: string; monthly_revenue?: number; monthly_operating_cost?: number; operating_profit?: number; repayment_coverage?: number; monthly_cash_after_emi?: number }>
  recommendation?: { status: string; recommended_project_cost?: number; recommended_loan?: number; monthly_emi?: number; base_repayment_coverage?: number; conservative_repayment_coverage?: number; financial_feasibility: string; methodology: string[] }
  feasibility?: { status: string; repayment_coverage?: number; conservative_repayment_coverage?: number; monthly_cash_surplus?: number; downside_status: string; methodology: string }
  assumptions: string[]
  limitations: string[]
}

export interface FinancialRoadmap {
  assessment: {
    status: 'VALID' | 'OUTSIDE_BASELINE_RANGE'
    message?: string
    margin_capital: number
    project_cost: number
    requested_loan: number
    eligible_loan?: number
    required_own_contribution?: number
    scheme_name?: string
    annual_interest_rate?: number
    tenure_months?: number
    moratorium_months?: number
    repayment_months?: number
    repayment_quarters?: number
    estimated_monthly_instalment?: number
    estimated_quarterly_instalment?: number
    estimated_total_repayment?: number
    estimated_total_interest?: number
    repayment_frequency_note: string
    calculation_limitations: string[]
  }
  cashflow: {
    status: 'INCOMPLETE' | 'AVAILABLE'
    monthly_operating_cost?: number
    monthly_cash_before_debt?: number
    monthly_cash_after_baseline_instalment?: number
    operating_reserve_requirement?: number
    limitations: string[]
  }
  routes: GovernmentSchemeRoute[]
  readiness_actions: string[]
  data_status: 'VERIFIED_GOVERNMENT_RULES'
  data_limitations: string[]
}

export interface GovernmentSchemeRoute {
  code: string
  name: string
  administering_body: string
  status: 'PUBLISHED_TERMS' | 'PROFILE_NEEDED' | 'ELIGIBILITY_CHECK' | 'LENDER_TERMS_REQUIRED' | 'AVAILABILITY_CHECK' | 'NOT_APPLICABLE'
  summary: string
  official_url: string
  source_verified_on: string
  funding_limit?: number
  beneficiary_interest_rate?: number
  tenure_months?: number
  moratorium_months?: number
  estimated_monthly_instalment?: number
  estimated_quarterly_instalment?: number
  potential_subsidy?: number
  minimum_beneficiary_contribution?: number
  conditions: string[]
  limitations: string[]
}
