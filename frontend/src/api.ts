import type { AdministrativeLocation, AssessmentAssistantResponse, CompetitorMapping, FinancialIntelligence, FinancialRoadmap, FinancialRoadmapRequest, HealthState, IndiaAdministrativeOptions, LocalDemographics, MapplsAutosuggestResponse, MarketAnalysis, ProductMarketValue } from './types'
import { INDIA_STATES_RESPONSE } from './indiaStates'

const ADMINISTRATIVE_CACHE_VERSION = 'v3-census-2011'
const administrativeCacheTtlMs = {
  state: 7 * 24 * 60 * 60 * 1000,
  district: 24 * 60 * 60 * 1000,
  block: 6 * 60 * 60 * 1000,
} as const

function administrativeCacheKey(level: 'state' | 'district' | 'block', parentId?: string) {
  return `vyaparsathi:administrative:${ADMINISTRATIVE_CACHE_VERSION}:${level}:${parentId || ''}`
}

function readAdministrativeCache(level: 'state' | 'district' | 'block', parentId?: string): IndiaAdministrativeOptions | null {
  try {
    const raw = window.localStorage.getItem(administrativeCacheKey(level, parentId))
    if (!raw) return null
    const cached = JSON.parse(raw) as { expiresAt?: number; response?: IndiaAdministrativeOptions }
    if (!cached.response || !cached.expiresAt || cached.expiresAt <= Date.now()) {
      window.localStorage.removeItem(administrativeCacheKey(level, parentId))
      return null
    }
    return cached.response
  } catch {
    return null
  }
}

function writeAdministrativeCache(level: 'state' | 'district' | 'block', response: IndiaAdministrativeOptions, parentId?: string) {
  if (response.status !== 'AVAILABLE') return
  try {
    window.localStorage.setItem(administrativeCacheKey(level, parentId), JSON.stringify({
      expiresAt: Date.now() + administrativeCacheTtlMs[level],
      response,
    }))
  } catch {
    // Storage is an optional performance enhancement; live results remain usable.
  }
}

async function fetchWithTimeout(input: RequestInfo | URL, init: RequestInit = {}, timeoutMs = 30_000) {
  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs)
  try {
    return await fetch(input, { ...init, signal: controller.signal })
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new Error('The public-data service timed out. Please try again.')
    }
    throw error
  } finally {
    window.clearTimeout(timeout)
  }
}

export async function checkHealth(): Promise<HealthState> {
  try {
    const response = await fetchWithTimeout('/health', {}, 5_000)
    return response.ok ? 'online' : 'offline'
  } catch {
    return 'offline'
  }
}

export async function analyzeMarket(payload: { location_id: string; category_id: string; radius_km: number }): Promise<MarketAnalysis> {
  const response = await fetchWithTimeout('/api/market/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail || `Analysis failed (${response.status})`)
  }
  return response.json()
}

export async function mapLiveCompetitors(payload: { latitude: number; longitude: number; state_name: string; district_name: string; district_osm_id?: string; block_name?: string; village_name?: string; analysis_scope: 'DISTRICT' | 'SUBDISTRICT' | 'VILLAGE'; category_id: string; radius_km: number }): Promise<CompetitorMapping> {
  return pollLookup<CompetitorMapping>('/api/market/competitor-lookup', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
}

export async function resolveAdministrativeLocation(payload: { state_name: string; district_name: string; block_name: string }): Promise<AdministrativeLocation> {
  const response = await fetchWithTimeout('/api/market/resolve-administrative-location', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
  }, 30_000)
  if (!response.ok) throw new Error('The live map boundary service is temporarily unavailable.')
  return response.json()
}

export async function getLocalDemographics(payload: { state_name: string; district_name: string; subdistrict_name: string }): Promise<LocalDemographics> {
  const response = await fetchWithTimeout('/api/market/local-demographics', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
  }, 5_000)
  if (!response.ok) throw new Error('The local Census demographic service could not be reached.')
  return response.json()
}

export async function getMapplsAutosuggest(query: string, pod?: 'STATE' | 'DIST' | 'SDIST' | 'VLG'): Promise<MapplsAutosuggestResponse> {
  const response = await fetchWithTimeout('/api/location/autosuggest', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ query, pod }),
  }, 10_000)
  if (!response.ok) throw new Error('Location assistance is temporarily unavailable.')
  return response.json()
}

export async function askAssessmentAssistant(payload: { question: string; language: 'en' | 'hi'; assessment_context: Record<string, unknown> }): Promise<AssessmentAssistantResponse> {
  const response = await fetchWithTimeout('/api/assistant/ask', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
  }, 30_000)
  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail || 'The explanation service is temporarily unavailable.')
  }
  return response.json()
}

const pendingLookups = new Map<string, Promise<unknown>>()
function pollLookup<T>(url: string, init: RequestInit = {}): Promise<T> {
  const key = url + (init.body || '')
  const existing = pendingLookups.get(key)
  if (existing) return existing as Promise<T>
  const operation = (async () => {
    let failures = 0
    const deadline = Date.now() + 240_000
    while (Date.now() < deadline) {
      try {
        const response = await fetchWithTimeout(url, init, 10_000)
        if (!response.ok) throw new Error('Lookup service is temporarily unavailable.')
        const job = await response.json()
        failures = 0
        if (job.status === 'COMPLETE') {
          const result = job.result
          if (job.refreshing && result.limitations) result.limitations = [...result.limitations, `Showing saved evidence from ${new Date(job.cached_at * 1000).toLocaleString()}; refreshing in the background.`]
          return result as T
        }
      } catch (error) {
        if (++failures >= 3) throw error
      }
      await new Promise(resolve => window.setTimeout(resolve, failures ? 3000 : 1000))
    }
    throw new Error('The source is still processing this lookup. Retry to reconnect; completed results are saved automatically.')
  })().finally(() => pendingLookups.delete(key))
  pendingLookups.set(key, operation)
  return operation
}

export async function getProductMarketValue(payload: { state_name: string; district_name?: string; block_name?: string; category_id: string; reference_price?: number }): Promise<ProductMarketValue> {
  const response = await fetchWithTimeout('/api/market/product-market-value', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  }, 45_000)
  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail || `Product market value failed (${response.status})`)
  }
  return response.json()
}

export async function getFinancialRoadmap(payload: FinancialRoadmapRequest): Promise<FinancialRoadmap> {
  const response = await fetchWithTimeout('/api/finance/roadmap', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail || `Financial roadmap failed (${response.status})`)
  }
  return response.json()
}

export async function getFinancialIntelligence(payload: {
  available_margin_capital: number
  revenue?: { monthly_revenue: number }
  costs?: { monthly_fixed_cost: number; monthly_variable_cost: number }
  working_capital?: { operating_buffer_months: number }
}): Promise<FinancialIntelligence> {
  const response = await fetchWithTimeout('/api/finance/analyze', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail || `Financial intelligence failed (${response.status})`)
  }
  return response.json()
}

export async function getIndiaAdministrativeOptions(level: 'state' | 'district' | 'block', parentId?: string, stateName?: string, districtName?: string): Promise<IndiaAdministrativeOptions> {
  // This is intentionally local: a user should never see a loading state just
  // to choose an Indian State/UT. Dependent records remain evidence-backed.
  if (level === 'state') return INDIA_STATES_RESPONSE
  const cached = readAdministrativeCache(level, parentId)
  if (cached) return cached
  const params = new URLSearchParams()
  if (parentId) params.set('parent_id', parentId)
  if (stateName) params.set('state_name', stateName)
  if (districtName) params.set('district_name', districtName)
  const query = params.size ? '?' + params.toString() : ''
  const data = await pollLookup<IndiaAdministrativeOptions>('/api/market/administrative-lookup/' + level + query)
  writeAdministrativeCache(level, data, parentId)
  return data
}
