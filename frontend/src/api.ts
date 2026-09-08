import type { HealthState, MarketAnalysis } from './types'

export async function checkHealth(): Promise<HealthState> {
  try {
    const response = await fetch('/health')
    return response.ok ? 'online' : 'offline'
  } catch {
    return 'offline'
  }
}

export async function analyzeMarket(payload: { location_id: string; category_id: string; radius_km: number }): Promise<MarketAnalysis> {
  const response = await fetch('/api/market/analyze', {
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
