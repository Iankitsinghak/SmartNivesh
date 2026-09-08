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
  business_activity: { commercial_activity_score: number; business_density: number; relevant_business_count: number; complementary_business_count: number; market_activity_level: string }
  distribution: { distribution_score: number; distribution_level: string; nearest_relevant_hubs: string[]; supplier_signals: string[] }
  seasonality: { seasonality_score: number; seasonality_level: string; peak_periods: string[]; low_periods: string[]; risk_note?: string }
  purchasing_power: { purchasing_power_score: number; purchasing_power_level: string; confidence: string }
  data_provenance: Array<{ source_id: string; source_name: string; data_type: string; confidence: string }>
}
