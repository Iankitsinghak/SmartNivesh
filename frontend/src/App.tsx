import { useEffect, useState } from 'react'
import { Activity, ArrowUpRight, Database, Gauge, LoaderCircle, MapPin, Play, RefreshCw, ShieldCheck, Sparkles, Users } from 'lucide-react'
import { analyzeMarket, checkHealth } from './api'
import type { HealthState, MarketAnalysis } from './types'

const presets = [
  { value: 'CAT-001', label: 'Restaurant', note: 'High-footfall food service' },
  { value: 'CAT-002', label: 'Hotel', note: 'Hospitality and lodging' },
  { value: 'CAT-003', label: 'Cosmetics', note: 'Personal care retail' }
]

function scoreTone(score: number) {
  if (score >= 70) return 'good'
  if (score >= 45) return 'watch'
  return 'low'
}

function formatCurrency(value: number) {
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(value)
}

function App() {
  const [health, setHealth] = useState<HealthState>('checking')
  const [category, setCategory] = useState('CAT-001')
  const [radius, setRadius] = useState(10)
  const [result, setResult] = useState<MarketAnalysis | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function refreshHealth() {
    setHealth('checking')
    setHealth(await checkHealth())
  }

  async function runAnalysis() {
    setLoading(true)
    setError('')
    try {
      setResult(await analyzeMarket({ location_id: 'LOC-001', category_id: category, radius_km: radius }))
    } catch (analysisError) {
      setError(analysisError instanceof Error ? analysisError.message : 'Unable to reach the analysis endpoint.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    refreshHealth()
    runAnalysis()
  }, [])

  const selectedPreset = presets.find((preset) => preset.value === category) ?? presets[0]

  return (
    <main className="shell">
      <aside className="sidebar">
        <div className="brand"><span className="brand-mark">V</span><span>Vyapar<span className="brand-accent">Sathi</span></span></div>
        <div className="sidebar-label">Workspace</div>
        <nav><button className="nav-item active"><Gauge size={17} /> Market console</button><button className="nav-item"><Database size={17} /> Data coverage <span className="nav-count">3</span></button></nav>
        <div className="sidebar-spacer" />
        <div className="connection-card">
          <div className="connection-title"><span className={`status-dot ${health}`} /> API connection</div>
          <strong>{health === 'online' ? 'Backend online' : health === 'checking' ? 'Checking service' : 'Backend offline'}</strong>
          <span>127.0.0.1:8000</span>
          <button className="text-button" onClick={refreshHealth}><RefreshCw size={13} /> Refresh status</button>
        </div>
        <div className="sidebar-footer">v0.1 · deterministic preview</div>
      </aside>

      <section className="content">
        <header className="topbar"><div className="crumb"><span>Workspace</span><span className="slash">/</span><strong>Market console</strong></div><div className="topbar-right"><span className="live-indicator"><span /> Live workspace</span><button className="icon-button" title="Refresh API status" onClick={refreshHealth}><RefreshCw size={17} /></button></div></header>
        <div className="page-heading"><div><p className="eyebrow">Local area intelligence</p><h1>Find the signal in your market.</h1><p className="lede">Run a deterministic feasibility scan against the seeded data layer.</p></div><div className="heading-meta"><span className="meta-label">Last scan</span><strong>{result ? 'Just now' : 'Waiting'}</strong></div></div>

        <div className="workspace-grid">
          <section className="panel setup-panel"><div className="panel-kicker"><span className="step-number">01</span><span>Scan setup</span></div><h2>Define your market</h2><p className="panel-subtitle">Choose a business category and search radius to start the local analysis.</p>
            <div className="field-group"><label htmlFor="location">Location</label><div className="input-shell disabled"><MapPin size={16} /><input id="location" value="Model Town · North West Delhi" readOnly /><span className="seed-tag">LOC-001</span></div></div>
            <div className="field-group"><label htmlFor="category">Business category</label><select id="category" value={category} onChange={(event) => setCategory(event.target.value)}>{presets.map((preset) => <option key={preset.value} value={preset.value}>{preset.label} · {preset.note}</option>)}</select></div>
            <div className="field-group"><div className="label-row"><label htmlFor="radius">Analysis radius</label><strong>{radius} km</strong></div><input className="range" id="radius" type="range" min="2" max="10" step="1" value={radius} onChange={(event) => setRadius(Number(event.target.value))} /><div className="range-labels"><span>2 km</span><span>10 km</span></div></div>
            <button className="primary-button" onClick={runAnalysis} disabled={loading}>{loading ? <LoaderCircle className="spin" size={17} /> : <Play size={17} fill="currentColor" />}{loading ? 'Running scan...' : 'Run market scan'}<ArrowUpRight size={17} /></button>
            {error && <div className="error-box"><Activity size={16} /><span>{error}</span></div>}
          </section>

          <section className="results-area"><div className="results-header"><div><div className="panel-kicker"><span className="step-number">02</span><span>Decision snapshot</span></div><h2>What the data says</h2></div>{result && <span className={`confidence-pill ${result.confidence}`}><ShieldCheck size={14} /> {result.confidence} confidence</span>}</div>
            {result ? <><div className="score-layout"><div className={`score-card ${scoreTone(result.overall_score)}`}><div className="score-orbit"><span>{Math.round(result.overall_score)}</span><small>/100</small></div><div><span className="score-label">Market opportunity</span><strong>{result.market_opportunity_level}</strong><span className="score-location"><MapPin size={13} /> {result.location.hierarchy.village_town}, {result.location.hierarchy.state}</span></div></div><div className="signal-card"><span className="signal-icon"><Sparkles size={16} /></span><div><span className="score-label">Customer potential</span><strong>{result.customer_potential}</strong><p>Based on local demand, POIs and demographic fit.</p></div></div></div><div className="metric-grid"><MetricCard label="Demand" value={result.demand.demand_score} caption={result.demand.demand_level} icon={<Users size={17} />} /><MetricCard label="Competition" value={result.competition.competition_score} caption={`${result.competition.mapped_competitors} mapped businesses`} icon={<Activity size={17} />} inverted /><MetricCard label="Market gap" value={result.market_gap.gap_score} caption="Opportunity headroom" icon={<Gauge size={17} />} /><MetricCard label="Purchasing power" value={result.purchasing_power.purchasing_power_score} caption={result.purchasing_power.purchasing_power_level} icon={<ArrowUpRight size={17} />} /></div><div className="detail-grid"><DetailPanel title="Operating context"><DetailRow label="Selected category" value={result.business_category.name} /><DetailRow label="Capital range" value={`${formatCurrency(result.business_category.capital_min)} – ${formatCurrency(result.business_category.capital_max)}`} /><DetailRow label="Commercial activity" value={`${result.business_activity.commercial_activity_score}/100`} /><DetailRow label="Seasonality" value={result.seasonality.seasonality_level} /></DetailPanel><DetailPanel title="Data coverage"><div className="coverage-bar"><span style={{ width: `${Math.min(100, result.data_provenance.length * 38)}%` }} /></div><p className="coverage-copy"><strong>{result.data_provenance.length} verified sources</strong> are informing this scan.</p>{result.data_provenance.map((source) => <div className="source-row" key={source.source_id}><span className="source-dot" /><span>{source.source_name}</span><small>{source.confidence}</small></div>)}</DetailPanel></div></> : <div className="empty-state"><LoaderCircle className="spin" size={23} /><p>Preparing your market snapshot...</p></div>}
          </section>
        </div>
        <footer className="page-footer"><span><ShieldCheck size={14} /> Calculated from deterministic backend engines</span><span>Location seed: LOC-001 · Category: {selectedPreset.label}</span></footer>
      </section>
    </main>
  )
}

function MetricCard({ label, value, caption, icon, inverted = false }: { label: string; value: number; caption: string; icon: React.ReactNode; inverted?: boolean }) {
  return <div className="metric-card"><div className="metric-head"><span>{label}</span><span className={`metric-icon ${inverted ? 'inverted' : ''}`}>{icon}</span></div><strong>{Math.round(value)}<small>/100</small></strong><div className="metric-foot"><span className={`mini-bar ${inverted ? 'bar-red' : ''}`}><span style={{ width: `${value}%` }} /></span><span>{caption}</span></div></div>
}

function DetailPanel({ title, children }: { title: string; children: React.ReactNode }) { return <div className="detail-panel"><h3>{title}</h3>{children}</div> }
function DetailRow({ label, value }: { label: string; value: string }) { return <div className="detail-row"><span>{label}</span><strong>{value}</strong></div> }

export default App
