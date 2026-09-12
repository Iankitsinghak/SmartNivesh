import { useEffect, useRef, useState } from 'react'
import {
  Accessibility, AlertTriangle, ArrowLeft, ArrowRight, BarChart3, Building2,
  Calculator, Check, ChevronDown, Database, FileDown, IndianRupee,
  Eye, ExternalLink, Info, Landmark, LoaderCircle, MapPin, Menu, Printer, RefreshCw,
  RotateCcw, Search, ShieldCheck, Store,
} from 'lucide-react'
import { askAssessmentAssistant, checkHealth, getFinancialIntelligence, getFinancialRoadmap, getIndiaAdministrativeOptions, getLocalDemographics, getMapplsAutosuggest, getProductMarketValue, mapLiveCompetitors, resolveAdministrativeLocation } from './api'
import { formatINR } from './finance'
import type { AssessmentAssistantResponse, CompetitorMapping, FinancialIntelligence, FinancialRoadmap, FinancialRoadmapRequest, GovernmentSchemeRoute, HealthState, IndiaAdministrativeOption, LocalDemographics, MapplsSuggestion, ProductMarketValue } from './types'
import { INDIA_STATES } from './indiaStates'

const categories = [
  { id: 'CAT-001', name: 'Restaurant', group: 'Food & hospitality', icon: 'FD' },
  { id: 'CAT-002', name: 'Hotel', group: 'Food & hospitality', icon: 'HT' },
  { id: 'CAT-003', name: 'Cosmetics', group: 'Retail', icon: 'RT' },
  { id: 'CAT-004', name: 'Kirana / General Store', group: 'Retail', icon: 'GS' },
  { id: 'CAT-005', name: 'Tea & Snack Stall', group: 'Food & hospitality', icon: 'TS' },
  { id: 'CAT-006', name: 'Bakery', group: 'Food & hospitality', icon: 'BK' },
  { id: 'CAT-007', name: 'Tailoring & Boutique', group: 'Personal services', icon: 'TB' },
  { id: 'CAT-008', name: 'Beauty Salon', group: 'Personal services', icon: 'BS' },
  { id: 'CAT-009', name: 'Mobile Phone Shop & Repair', group: 'Repair & retail', icon: 'MR' },
  { id: 'CAT-010', name: 'Pharmacy / Medical Store', group: 'Retail', icon: 'PH' },
  { id: 'CAT-011', name: 'Fruit & Vegetable Shop', group: 'Retail', icon: 'FV' },
  { id: 'CAT-012', name: 'Dairy / Milk Shop', group: 'Retail', icon: 'DM' },
  { id: 'CAT-013', name: 'Stationery & Photocopy', group: 'Services', icon: 'SP' },
  { id: 'CAT-014', name: 'Hardware & Electrical Store', group: 'Retail', icon: 'HE' },
  { id: 'CAT-015', name: 'Furniture & Carpentry', group: 'Manufacturing & services', icon: 'FC' },
  { id: 'CAT-016', name: 'Welding & Fabrication', group: 'Manufacturing & services', icon: 'WF' },
  { id: 'CAT-017', name: 'Laundry & Ironing', group: 'Personal services', icon: 'LI' },
  { id: 'CAT-018', name: 'Bicycle Sales & Repair', group: 'Repair & retail', icon: 'BR' },
  { id: 'CAT-019', name: 'Agricultural Input Store', group: 'Agriculture support', icon: 'AI' },
  { id: 'CAT-020', name: 'Textiles & Garment Store', group: 'Retail', icon: 'TG' },
  { id: 'CAT-021', name: 'Footwear Store & Repair', group: 'Retail & repair', icon: 'FS' },
  { id: 'CAT-022', name: 'Computer & Digital Service Centre', group: 'Services', icon: 'CD' },
] as const

type Screen = 'start' | 'assessment' | 'report'
type BadgeKind = 'PUBLIC DATA' | 'CALCULATED' | 'ESTIMATE' | 'ASSUMPTION' | 'USER INPUT' | 'VERIFICATION REQUIRED' | 'VERIFIED GOVT RULE' | 'LENDER TERMS REQUIRED' | 'AVAILABILITY CHECK'
type FinanceProfile = Omit<FinancialRoadmapRequest, 'margin_capital'>

const emptyFinanceProfile: FinanceProfile = {
  activity_type: 'not_sure',
  area_type: 'not_sure',
  pmegp_beneficiary_group: 'not_sure',
  has_repaid_mudra_tarun: false,
  vishwakarma_loan_stage: 'not_confirmed',
}

function App() {
  const [screen, setScreen] = useState<Screen>(() => localStorage.getItem('vyaparsathi-assessment') ? 'assessment' : 'start')
  const [step, setStep] = useState(0)
  const [health, setHealth] = useState<HealthState>('checking')
  const [largeText, setLargeText] = useState(false)
  const [mobileNav, setMobileNav] = useState(false)
  const [states, setStates] = useState<IndiaAdministrativeOption[]>(INDIA_STATES)
  const [districts, setDistricts] = useState<IndiaAdministrativeOption[]>([])
  const [blocks, setBlocks] = useState<IndiaAdministrativeOption[]>([])
  const [stateId, setStateId] = useState('')
  const [districtId, setDistrictId] = useState('')
  const [blockId, setBlockId] = useState('')
  const [village, setVillage] = useState('')
  const [margin, setMargin] = useState(100_000)
  const [categoryId, setCategoryId] = useState('CAT-001')
  const [competitorRadius, setCompetitorRadius] = useState(10)
  const [referencePrice, setReferencePrice] = useState(0)
  const [hierarchyLoading, setHierarchyLoading] = useState(false)
  const [hierarchyError, setHierarchyError] = useState('')
  const [competitors, setCompetitors] = useState<CompetitorMapping | null>(null)
  const [demographics, setDemographics] = useState<LocalDemographics | null>(null)
  const [marketValue, setMarketValue] = useState<ProductMarketValue | null>(null)
  const [analysisLoading, setAnalysisLoading] = useState(false)
  const [analysisError, setAnalysisError] = useState('')
  const [financeProfile, setFinanceProfile] = useState<FinanceProfile>(emptyFinanceProfile)
  const [financial, setFinancial] = useState<FinancialRoadmap | null>(null)
  const [financialIntelligence, setFinancialIntelligence] = useState<FinancialIntelligence | null>(null)
  const [financeLoading, setFinanceLoading] = useState(true)
  const [financeError, setFinanceError] = useState('')
  const hierarchyVersions = useRef({ state: 0, district: 0, block: 0 })
  const locationSelection = useRef({ stateId, districtId })
  locationSelection.current = { stateId, districtId }
  const analysisVersion = useRef(0)

  const selectedState = states.find((item) => item.id === stateId)
  const selectedDistrict = districts.find((item) => item.id === districtId)
  const selectedBlock = blocks.find((item) => item.id === blockId)
  const selectedCategory = categories.find((item) => item.id === categoryId) ?? categories[0]

  async function applyLocationSuggestion(suggestion: MapplsSuggestion): Promise<string> {
    const normalized = (value: string) => value.normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('en-IN').replace(/[^a-z0-9]+/g, ' ').trim()
    const source = normalized([suggestion.place_name, suggestion.place_address, suggestion.alternate_name].filter(Boolean).join(' '))
    const includesName = (name: string) => {
      const candidate = normalized(name)
      return candidate.length > 2 && (` ${source} `).includes(` ${candidate} `)
    }
    const state = [...states].sort((a, b) => b.name.length - a.name.length).find((item) => includesName(item.name))
    if (!state) {
      if (suggestion.type === 'VILLAGE') setVillage(suggestion.place_name)
      return 'We found the place, but could not safely match its State to the Census hierarchy. Select the State below to continue.'
    }
    hierarchyVersions.current.district += 1; hierarchyVersions.current.block += 1
    setStateId(state.id); setDistrictId(''); setBlockId(''); setDistricts([]); setBlocks([]); setVillage(suggestion.type === 'VILLAGE' ? suggestion.place_name : '')
    if (suggestion.type === 'STATE') return `${state.name} selected. Choose a District to continue.`
    const districtResponse = await getIndiaAdministrativeOptions('district', state.id, state.name)
    if (districtResponse.status !== 'AVAILABLE') return `${state.name} selected, but its Census districts could not be loaded. Use Retry lookup below.`
    setDistricts(districtResponse.options)
    const district = [...districtResponse.options].sort((a, b) => b.name.length - a.name.length).find((item) => {
      const candidate = normalized(item.name)
      return normalized(suggestion.place_name) === candidate || includesName(item.name)
    })
    if (!district) return `${state.name} selected. We could not safely identify the matching Census District from this map result; choose it below.`
    setDistrictId(district.id)
    if (suggestion.type === 'DISTRICT') return `${state.name} → ${district.name} selected. Choose a Sub-district to continue.`
    const blockResponse = await getIndiaAdministrativeOptions('block', district.id, state.name, district.name)
    if (blockResponse.status !== 'AVAILABLE') return `${state.name} → ${district.name} selected, but Sub-district choices could not be loaded. Use Retry lookup below.`
    setBlocks(blockResponse.options)
    const block = [...blockResponse.options].sort((a, b) => b.name.length - a.name.length).find((item) => normalized(suggestion.place_name) === normalized(item.name) || includesName(item.name))
    if (!block) return `${state.name} → ${district.name} selected. Choose the matching Sub-district below to continue.`
    setBlockId(block.id)
    return `${state.name} → ${district.name} → ${block.name} selected. You can now continue.`
  }

  useEffect(() => { checkHealth().then(setHealth) }, [])
  useEffect(() => {
    const saved = localStorage.getItem('vyaparsathi-assessment')
    if (!saved) return
    try {
      const value = JSON.parse(saved)
      setStateId(value.stateId ?? ''); setDistrictId(value.districtId ?? ''); setBlockId(value.blockId ?? '')
      setVillage(value.village ?? ''); setMargin(value.margin ?? 100_000); setCategoryId(value.categoryId ?? 'CAT-001'); setCompetitorRadius(value.competitorRadius ?? 10); setReferencePrice(value.referencePrice ?? 0); setStep(value.step ?? 0)
      setFinanceProfile({ ...emptyFinanceProfile, ...(value.financeProfile ?? {}) })
    } catch { localStorage.removeItem('vyaparsathi-assessment') }
  }, [])
  useEffect(() => {
    if (screen !== 'start') localStorage.setItem('vyaparsathi-assessment', JSON.stringify({ stateId, districtId, blockId, village, margin, categoryId, competitorRadius, referencePrice, step, financeProfile }))
  }, [screen, stateId, districtId, blockId, village, margin, categoryId, competitorRadius, referencePrice, step, financeProfile])
  useEffect(() => { if (stateId && selectedState?.name) loadHierarchy('district', stateId, selectedState.name) }, [stateId, selectedState?.name])
  useEffect(() => { if (districtId && selectedState?.name && selectedDistrict?.name) loadHierarchy('block', districtId, selectedState.name, selectedDistrict.name) }, [districtId, selectedState?.name, selectedDistrict?.name])
  useEffect(() => {
    let active = true
    setFinanceLoading(true); setFinanceError('')
    getFinancialRoadmap({ margin_capital: Math.max(1, margin), ...financeProfile })
      .then((response) => { if (active) setFinancial(response) })
      .catch((error) => { if (active) { setFinancial(null); setFinanceError(error instanceof Error ? error.message : 'Financial roadmap could not be calculated.') } })
      .finally(() => { if (active) setFinanceLoading(false) })
    return () => { active = false }
  }, [margin, financeProfile])
  useEffect(() => {
    let active = true
    const payload: Parameters<typeof getFinancialIntelligence>[0] = { available_margin_capital: Math.max(1, margin) }
    if (financeProfile.expected_monthly_revenue != null) payload.revenue = { monthly_revenue: financeProfile.expected_monthly_revenue }
    if (financeProfile.monthly_fixed_cost != null && financeProfile.monthly_variable_cost != null) {
      payload.costs = { monthly_fixed_cost: financeProfile.monthly_fixed_cost, monthly_variable_cost: financeProfile.monthly_variable_cost }
      if (financeProfile.operating_reserve_months != null) payload.working_capital = { operating_buffer_months: financeProfile.operating_reserve_months }
    }
    getFinancialIntelligence(payload)
      .then((response) => { if (active) setFinancialIntelligence(response) })
      .catch(() => { if (active) setFinancialIntelligence(null) })
    return () => { active = false }
  }, [margin, financeProfile.expected_monthly_revenue, financeProfile.monthly_fixed_cost, financeProfile.monthly_variable_cost, financeProfile.operating_reserve_months])

  async function loadHierarchy(level: 'state' | 'district' | 'block', parentId?: string, stateName?: string, districtName?: string) {
    const version = ++hierarchyVersions.current[level]
    const active = () => version === hierarchyVersions.current[level] && (level === 'state' || parentId === (level === 'district' ? locationSelection.current.stateId : locationSelection.current.districtId))
    setHierarchyLoading(true); setHierarchyError('')
    try {
      const response = await getIndiaAdministrativeOptions(level, parentId, stateName, districtName)
      if (!active()) return
      if (response.status !== 'AVAILABLE') throw new Error(response.limitations[0] || `No ${level} data is available.`)
      if (level === 'state') setStates(response.options)
      if (level === 'district') setDistricts(response.options)
      if (level === 'block') setBlocks(response.options)
    } catch (error) { if (active()) setHierarchyError(error instanceof Error ? error.message : 'Administrative data could not be loaded.') }
    finally { if (active()) setHierarchyLoading(false) }
  }

  async function runLiveAnalysis(radiusOverride = competitorRadius) {
    if (!selectedState || !selectedDistrict) {
      setAnalysisError('Select at least a State and District before analysing public data.')
      return
    }
    setAnalysisLoading(true); setAnalysisError(''); setStep(3)
    const version = ++analysisVersion.current
    setCompetitors(null); setDemographics(null); setMarketValue(null)
    const localResults = await Promise.allSettled([
      selectedBlock ? getLocalDemographics({ state_name: selectedState.name, district_name: selectedDistrict.name, subdistrict_name: selectedBlock.name }) : Promise.resolve(null),
      getProductMarketValue({ state_name: selectedState.name, district_name: selectedDistrict.name, block_name: selectedBlock?.name, category_id: categoryId, reference_price: referencePrice > 0 ? referencePrice : undefined }),
    ])
    if (version !== analysisVersion.current) return
    const [demographicsResult, marketValueResult] = localResults
    if (demographicsResult.status === 'fulfilled' && demographicsResult.value) setDemographics(demographicsResult.value)
    if (marketValueResult.status === 'fulfilled') setMarketValue(marketValueResult.value)
    if (marketValueResult.status !== 'fulfilled') {
      setAnalysisError('The local analysis service could not complete. Please restart the application and try again.')
      setAnalysisLoading(false)
      return
    }
    let latitude = selectedDistrict.latitude
    let longitude = selectedDistrict.longitude
    let districtOsmId = selectedDistrict.id.startsWith('relation:') ? selectedDistrict.id : undefined
    if (latitude == null || longitude == null) {
      try {
        const location = await resolveAdministrativeLocation({ state_name: selectedState.name, district_name: selectedDistrict.name, block_name: village || selectedBlock?.name || selectedDistrict.name })
        if (location.status !== 'AVAILABLE' || location.latitude == null || location.longitude == null) throw new Error(location.limitations[0] || 'The selected area has no verified live map geometry.')
        latitude = location.latitude; longitude = location.longitude; districtOsmId = location.district_osm_id
      } catch (error) {
        if (version === analysisVersion.current) {
          setAnalysisError('Affordability analysis completed. Live competitor mapping is unavailable because this selection has no verified map point yet.')
          setAnalysisLoading(false)
        }
        return
      }
    }
    const [competitorResult] = await Promise.allSettled([
      mapLiveCompetitors({ latitude, longitude, state_name: selectedState.name, district_name: selectedDistrict.name, district_osm_id: districtOsmId, block_name: selectedBlock?.name, village_name: village || undefined, analysis_scope: village ? 'VILLAGE' : selectedBlock ? 'SUBDISTRICT' : 'DISTRICT', category_id: categoryId, radius_km: radiusOverride }),
    ])
    if (version !== analysisVersion.current) return
    if (competitorResult.status === 'fulfilled') setCompetitors(competitorResult.value)
    if (competitorResult.status === 'rejected') setAnalysisError('Local Census and affordability analysis completed. Live competitor mapping is temporarily unavailable.')
    setAnalysisLoading(false)
  }

  function retryHierarchy() {
    if (districtId) return loadHierarchy('block', districtId, selectedState?.name, selectedDistrict?.name)
    if (stateId) return loadHierarchy('district', stateId, selectedState?.name)
    // State/UT choices are bundled and do not require a network retry.
  }

  function resetAssessment() {
    if (!window.confirm('Clear this assessment and start again?')) return
    localStorage.removeItem('vyaparsathi-assessment')
    setStateId(''); setDistrictId(''); setBlockId(''); setVillage(''); setMargin(100_000); setCategoryId('CAT-001'); setCompetitorRadius(10); setReferencePrice(0); setFinanceProfile(emptyFinanceProfile); setCompetitors(null); setDemographics(null); setMarketValue(null); setStep(0); setScreen('start')
  }

  const canContinue = step === 0 ? Boolean(stateId && districtId) : step === 1 ? financial?.assessment.status === 'VALID' && !financeLoading : true
  useEffect(() => { document.documentElement.lang = 'en' }, [])
  return <div className={largeText ? 'app large-text' : 'app'}>
    <ServiceHeader largeText={largeText} setLargeText={setLargeText} mobileNav={mobileNav} setMobileNav={setMobileNav} />
    <div className="service-strip"><span><ShieldCheck size={15} /> Independent decision-support service</span><span className={`api-state ${health}`}>{health === 'online' ? 'Analysis service connected' : health === 'checking' ? 'Checking analysis service' : 'Analysis service unavailable'}</span></div>
    {screen === 'start' && <StartScreen onStart={() => { setScreen('assessment'); setStep(0) }} onLoan={() => { setScreen('assessment'); setStep(1) }} />}
    {screen === 'assessment' && <main className="page-wrap assessment-page">
      <div className="assessment-heading"><div><span className="section-label">BUSINESS ASSESSMENT</span><h1>Plan a viable rural enterprise</h1><p>Complete one short step at a time. Your progress is saved on this device.</p></div><button className="quiet-button" onClick={resetAssessment}><RotateCcw size={16} /> Reset</button></div>
      <JourneyMap current={step} />
      <section className="wizard-card" aria-live="polite">
        {step === 0 && <LocationStep states={states} districts={districts} blocks={blocks} stateId={stateId} districtId={districtId} blockId={blockId} village={village} loading={hierarchyLoading} error={hierarchyError} onRetry={retryHierarchy} onSuggestion={applyLocationSuggestion} onState={(value) => { hierarchyVersions.current.district += 1; hierarchyVersions.current.block += 1; setHierarchyError(''); setStateId(value); setDistrictId(''); setBlockId(''); setDistricts([]); setBlocks([]) }} onDistrict={(value) => { hierarchyVersions.current.block += 1; setHierarchyError(''); setDistrictId(value); setBlockId(''); setBlocks([]) }} onBlock={setBlockId} onVillage={setVillage} />}
        {step === 1 && <CapitalStep margin={margin} setMargin={setMargin} financial={financial} loading={financeLoading} error={financeError} />}
        {step === 2 && <BusinessStep categoryId={categoryId} setCategoryId={setCategoryId} referencePrice={referencePrice} setReferencePrice={setReferencePrice} />}
        {step === 3 && <AnalysisStep loading={analysisLoading} error={analysisError} result={competitors} demographics={demographics} marketValue={marketValue} blockName={selectedBlock?.name} radius={competitorRadius} onRadiusChange={(value) => { setCompetitorRadius(value); if (competitors) runLiveAnalysis(value) }} onRetry={() => runLiveAnalysis()} />}
        {step === 4 && <FinanceStep financial={financial} intelligence={financialIntelligence} profile={financeProfile} loading={financeLoading} error={financeError} onProfileChange={(change) => setFinanceProfile((current) => ({ ...current, ...change }))} />}
        <div className="wizard-actions"><button className="secondary-button" disabled={step === 0} onClick={() => setStep((value) => Math.max(0, value - 1))}><ArrowLeft size={17} /> Back</button>
          {step < 2 && <button className="primary-button" disabled={!canContinue} onClick={() => setStep(step + 1)}>Continue <ArrowRight size={17} /></button>}
          {step === 2 && <button className="primary-button" onClick={() => runLiveAnalysis()}>Analyse public data <ArrowRight size={17} /></button>}
          {step === 3 && <button className="primary-button" onClick={() => setStep(4)}>Review finance <ArrowRight size={17} /></button>}
          {step === 4 && <button className="primary-button" onClick={() => setScreen('report')}>View full report <ArrowRight size={17} /></button>}
        </div>
      </section>
    </main>}
    {screen === 'report' && <ReportPage locale="en" location={[village, selectedBlock?.name, selectedDistrict?.name, selectedState?.name].filter(Boolean).join(', ')} category={selectedCategory.name} financial={financial} financialIntelligence={financialIntelligence} competitors={competitors} demographics={demographics} marketValue={marketValue} onRecalculate={() => { setScreen('assessment'); setStep(1) }} />}
    <footer className="site-footer"><div><strong>VyaparSathi</strong><span>Rural Enterprise Advisory</span></div><p>This is an independent decision-support tool and does not represent a government authority. Final scheme eligibility and sanction are determined by the implementing authority.</p></footer>
  </div>
}

function ServiceHeader({ largeText, setLargeText, mobileNav, setMobileNav }: { largeText: boolean; setLargeText: (v: boolean) => void; mobileNav: boolean; setMobileNav: (v: boolean) => void }) {
  return <header className="service-header"><button className="brand" onClick={() => window.location.reload()} aria-label="VyaparSathi home"><span className="emblem">VS</span><span><strong>VyaparSathi</strong><small>Rural Enterprise Advisory</small></span></button><nav className="service-nav" aria-label="Assessment sections"><span>Location</span><span>Capital</span><span>Business</span><span>Feasibility</span><span>Finance</span></nav><div className={mobileNav ? 'header-tools open' : 'header-tools'}><button className="header-button" aria-pressed={largeText} onClick={() => setLargeText(!largeText)}><Accessibility size={17} /> <span>Text size</span></button></div><button className="menu-button" onClick={() => setMobileNav(!mobileNav)} aria-expanded={mobileNav} aria-label="Open menu"><Menu /></button></header>
}

function StartScreen({ onStart, onLoan }: { onStart: () => void; onLoan: () => void }) {
  return <main><section className="start-hero"><div className="hero-copy"><span className="section-label">RURAL ENTERPRISE DECISION SUPPORT</span><h1>Understand your local market. Plan your finances. Start with confidence.</h1><p>Assess your local market, understand project finance, and review indicative public schemes through one guided service.</p><div className="hero-actions"><button className="primary-button" onClick={onStart}>Start business assessment <ArrowRight size={18} /></button><button className="secondary-button" onClick={onLoan}>Check loan estimate <Calculator size={18} /></button></div><div className="hero-proof"><span>Location</span><b>1</b><span>Business</span><b>2</b><span>Capital</span><b>3</b><span>Feasibility and finance</span></div></div><aside className="service-summary" aria-label="What this service provides"><div className="summary-icon"><Building2 size={28} /></div><span className="summary-kicker">ASSESSMENT OVERVIEW</span><h2>One guided view of your business idea</h2><ul><li><Check /> Local market evidence</li><li><Check /> Business feasibility signals</li><li><Check /> Scheme and repayment estimate</li></ul><p><Info size={15} /> Takes about 5 minutes. No sign-in required.</p></aside></section><section className="trust-row"><article><MapPin /><div><strong>Local market assessment</strong><span>Based on the area you select</span></div></article><article><BarChart3 /><div><strong>Business feasibility</strong><span>Evidence and limitations shown</span></div></article><article><IndianRupee /><div><strong>Finance planning</strong><span>Caps and contribution included</span></div></article></section><Disclaimer /></main>
}

function JourneyMap({ current }: { current: number }) {
  const journey = [
    ['Location', 'Confirm your Census area'], ['Capital', 'Calculate project scale'],
    ['Business', 'Select the closest category'], ['Feasibility', 'Review supply and affordability'],
    ['Finance', 'Test repayment comfort'],
  ]
  const active = Math.min(current, journey.length - 1)
  return <section className="journey-map" aria-label="Your enterprise journey"><div className="journey-heading"><div><span className="section-label">YOUR BUSINESS PATH</span><strong>{journey[active][0]}</strong></div><p>Next: {journey[Math.min(active + 1, journey.length - 1)][1]}</p></div><ol>{journey.map(([title, subtitle], index) => <li key={title} className={index < active ? 'done' : index === active ? 'current' : ''}><span>{index < active ? <Check size={13} /> : index + 1}</span><div><b>{title}</b><small>{subtitle}</small></div></li>)}</ol></section>
}

function LocationStep(props: { states: IndiaAdministrativeOption[]; districts: IndiaAdministrativeOption[]; blocks: IndiaAdministrativeOption[]; stateId: string; districtId: string; blockId: string; village: string; loading: boolean; error: string; onRetry: () => void; onSuggestion: (suggestion: MapplsSuggestion) => Promise<string>; onState: (v: string) => void; onDistrict: (v: string) => void; onBlock: (v: string) => void; onVillage: (v: string) => void }) {
  return <div className="step-content"><StepIntro number="01" title="Where will the enterprise operate?" text="Search for a place and select it. We fill the matching local Census hierarchy automatically whenever it can be verified." /><LocationAssistant onChoose={props.onSuggestion} /><div className="form-grid"><FormSelect id="state" label="State" value={props.stateId} onChange={props.onState} options={props.states} placeholder="Select state" /><FormSelect id="district" label="District" value={props.districtId} onChange={props.onDistrict} options={props.districts} placeholder={props.stateId ? props.loading && !props.districts.length ? 'Loading districts…' : 'Select district' : 'Select state first'} disabled={!props.stateId || (props.loading && !props.districts.length)} /><FormSelect id="block" label="Sub-district / Tehsil" required={false} value={props.blockId} onChange={props.onBlock} options={props.blocks} placeholder={props.districtId ? props.loading && !props.blocks.length ? 'Loading sub-districts…' : 'Select sub-district' : 'Select district first'} disabled={!props.districtId || (props.loading && !props.blocks.length)} /><label className="form-field"><span>Village <small>Optional</small></span><div className="input-with-icon"><Search size={17} /><input value={props.village} onChange={(e) => props.onVillage(e.target.value)} placeholder="Enter village name" /></div></label></div>{props.error && props.stateId && <><ErrorState message={props.error} /><button className="secondary-button retry-button" onClick={props.onRetry}><RefreshCw size={16} /> Retry lookup</button></>}<div className="source-note"><Database size={16} /><div><strong>Administrative hierarchy: local Census of India 2011 PCA</strong><span>State, district, sub-district, village and demographic records are loaded locally for fast lookup. Location search fills only verified matches and never replaces the Census hierarchy.</span></div><Badge kind="PUBLIC DATA" /></div></div>
}

function LocationAssistant({ onChoose }: { onChoose: (suggestion: MapplsSuggestion) => Promise<string> }) {
  const [query, setQuery] = useState('')
  const [suggestions, setSuggestions] = useState<MapplsSuggestion[]>([])
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)
  async function search() {
    if (query.trim().length < 2) return
    setLoading(true); setMessage(''); setSuggestions([])
    try {
      const response = await getMapplsAutosuggest(query.trim())
      setSuggestions(response.suggestions)
      const normalize = (value: string) => value.normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('en-IN').replace(/[^a-z0-9]+/g, ' ').trim()
      const exact = response.suggestions.find((suggestion) => normalize(suggestion.place_name) === normalize(query))
      if (exact) {
        setLoading(false)
        await choose(exact)
        return
      }
      if (!response.suggestions.length) setMessage(response.limitations[0] || 'No location suggestion matched that search.')
      else setMessage('Choose the matching place below to fill the Census selections automatically.')
    } catch (error) { setMessage(error instanceof Error ? error.message : 'Location assistance is unavailable.') }
    finally { setLoading(false) }
  }
  async function choose(suggestion: MapplsSuggestion) {
    setLoading(true); setMessage('Applying the verified Census hierarchy…')
    try { setMessage(await onChoose(suggestion)); setQuery(suggestion.place_name); setSuggestions([]) }
    catch { setMessage('The location was found, but the Census hierarchy could not be applied. Choose the dropdowns below.') }
    finally { setLoading(false) }
  }
  return <section className="location-assistant"><div><Badge kind="PUBLIC DATA" /><h3>Find an area quickly</h3><p>Search, choose the correct result, and the verified Census hierarchy fills automatically.</p></div><div className="location-search"><input value={query} onChange={(event) => setQuery(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter') { event.preventDefault(); void search() } }} placeholder="e.g. Kanksa or Paschim Bardhaman" aria-label="Search for a location" /><button className="secondary-button" type="button" onClick={() => void search()} disabled={loading || query.trim().length < 2}>{loading ? 'Finding…' : 'Find location'}</button></div>{message && <p className="search-message">{message}</p>}{suggestions.length > 0 && <ul className="location-suggestions">{suggestions.map((suggestion) => <li key={suggestion.mappls_eloc}><button type="button" onClick={() => void choose(suggestion)} disabled={loading}><MapPin size={16} /><span><b>{suggestion.place_name}</b><small>{suggestion.type.replace('_', ' ')} · {suggestion.place_address || 'India'}</small></span><ArrowRight size={16} /></button></li>)}</ul>}</section>
}

function FormSelect({ id, label, value, onChange, options, placeholder, disabled, required = true }: { id: string; label: string; value: string; onChange: (v: string) => void; options: IndiaAdministrativeOption[]; placeholder: string; disabled?: boolean; required?: boolean }) { return <label className="form-field" htmlFor={id}><span>{label} {required ? <b>*</b> : <small>Optional</small>}</span><select id={id} value={value} onChange={(e) => onChange(e.target.value)} disabled={disabled}><option value="">{placeholder}</option>{options.map((option) => <option key={option.id} value={option.id}>{option.name}</option>)}</select></label> }

function CapitalStep({ margin, setMargin, financial, loading, error }: { margin: number; setMargin: (v: number) => void; financial: FinancialRoadmap | null; loading: boolean; error: string }) {
  const assessment = financial?.assessment
  return <div className="step-content"><StepIntro number="02" title="How much can you contribute?" text="Enter the amount available from your own funds. The government-rule roadmap uses a 10% planning model, then tests published scheme conditions separately." /><label className="currency-field"><span>Available margin capital</span><div><b>₹</b><input type="number" inputMode="numeric" min="1" max="5000000" value={margin || ''} onChange={(e) => setMargin(Number(e.target.value))} aria-describedby="margin-help" /></div><small id="margin-help">Enter whole rupees. Your official contribution may differ after appraisal.</small></label>{loading && <div className="inline-loading"><LoaderCircle className="spin" size={16} /> Updating the government-rule roadmap…</div>}{error && <ErrorState message={error} />}{assessment?.status === 'OUTSIDE_BASELINE_RANGE' && <ErrorState message={assessment.message || 'Enter a supported amount.'} />}<CapitalStructurePanel assessment={assessment} /><div className="calculation-flow"><CalculationCard label="Your available margin" value={assessment ? formatINR(assessment.margin_capital) : '—'} badge="USER INPUT" /><ArrowRight /><CalculationCard label="Indicative project cost" value={assessment ? formatINR(assessment.project_cost) : 'Checking'} badge="CALCULATED" formula="Margin ÷ 10%" /><ArrowRight /><CalculationCard label="Indicative loan need" value={assessment ? formatINR(assessment.requested_loan) : 'Checking'} badge="CALCULATED" formula="Project cost × 90%" /></div><details className="plain-details"><summary>What this calculation does and does not decide</summary><p>It translates a 10% margin into an indicative project cost and 90% financing need. The published NSFDC cap, personal eligibility, activity viability, bank appraisal and final repayment schedule are checked separately. It is not a sanction or an entitlement.</p></details></div>
}

function CapitalStructurePanel({ assessment }: { assessment?: FinancialRoadmap['assessment'] }) {
  if (!assessment || assessment.status !== 'VALID' || assessment.project_cost <= 0) return null
  const ownShare = Math.min(100, Math.max(0, Math.round((assessment.margin_capital / assessment.project_cost) * 100)))
  const financeShare = Math.max(0, 100 - ownShare)
  return <section className="capital-structure" aria-label="Indicative capital structure"><div className="capital-structure-heading"><div><Badge kind="CALCULATED" /><h3>Indicative capital structure</h3><p>This visual uses your entered margin and the current government-rule planning model.</p></div><strong>{formatINR(assessment.project_cost)}</strong></div><div className="capital-split" role="img" aria-label={`${ownShare}% own margin and ${financeShare}% indicative financing need`}><i className="own-capital" style={{ width: `${ownShare}%` }} /><i className="finance-gap" style={{ width: `${financeShare}%` }} /></div><div className="capital-legend"><span><i className="own-capital" /> Your margin: {formatINR(assessment.margin_capital)} ({ownShare}%)</span><span><i className="finance-gap" /> Indicative financing: {formatINR(assessment.requested_loan)} ({financeShare}%)</span></div></section>
}

function BusinessStep({ categoryId, setCategoryId, referencePrice, setReferencePrice }: { categoryId: string; setCategoryId: (v: string) => void; referencePrice: number; setReferencePrice: (v: number) => void }) {
  return <div className="step-content"><StepIntro number="03" title="Choose your business category" text="Select the closest supported category. Every category has a configured OpenStreetMap mapping rule for live competitor evidence." /><div className="category-grid" role="radiogroup" aria-label="Business category">{categories.map((category) => <label key={category.id} className={categoryId === category.id ? 'category-card selected' : 'category-card'}><input type="radio" name="category" value={category.id} checked={categoryId === category.id} onChange={() => setCategoryId(category.id)} /><span className="category-icon" aria-hidden="true">{category.icon}</span><strong>{category.name}</strong><small>{category.group}</small><span className="radio-mark">{categoryId === category.id && <Check size={14} />}</span></label>)}</div><section className="reference-price-panel"><div><Badge kind="USER INPUT" /><h3>Optional comparable reference price</h3><p>Enter your current menu/list price, a supplier quotation, or another comparable price per sale or unit. The calculator applies the verified rural-MPCE multiplier; it does not call a market-price API or invent a category price.</p></div><label className="form-field" htmlFor="reference-price"><span>Reference price <small>Optional · ₹ per sale / unit</small></span><div className="compact-currency"><b>₹</b><input id="reference-price" type="number" min="1" step="0.01" inputMode="decimal" value={referencePrice || ''} onChange={(event) => setReferencePrice(Math.max(0, Number(event.target.value) || 0))} placeholder="e.g. 100" /></div></label></section><div className="info-callout"><Info size={17} /><p>These micro-enterprise categories use documented OpenStreetMap tags for competitor mapping. Results show observed mapped features, never an assumed competitor count.</p></div></div>
}

function AnalysisStep({ loading, error, result, demographics, marketValue, blockName, radius, onRadiusChange, onRetry }: { loading: boolean; error: string; result: CompetitorMapping | null; demographics: LocalDemographics | null; marketValue: ProductMarketValue | null; blockName?: string; radius: number; onRadiusChange: (value: number) => void; onRetry: () => void }) {
  if (loading) return <div><LoadingState title="Checking public records" text={`Retrieving evidence for ${blockName ?? 'the selected block'}. This continues in the background; completed results are saved for reuse.`} />{marketValue && <ProductMarketValuePanel result={marketValue} />}</div>
  if (error && !result && !demographics && !marketValue) return <div className="step-content"><ErrorState message={error} /><button className="secondary-button inline" onClick={onRetry}><RefreshCw size={16} /> Try again</button></div>
  if (!result && !demographics && !marketValue) return <EmptyState title="Analysis has not started" text="Return to Business and select Analyse public data." />
  const sources = [...(result?.data_provenance ?? []), ...(demographics?.data_provenance ?? []), ...(marketValue?.data_provenance ?? [])]
  return <div className="step-content"><StepIntro number="04" title="Local analysis complete" text="Choose the search radius for similar businesses. Census demographics and affordability remain local and fast." />{error && <div className="warning-callout"><AlertTriangle /><div><strong>Optional live map evidence unavailable</strong><p>{error}</p></div></div>}<section className="radius-control"><div><Badge kind="PUBLIC DATA" /><h3>Similar businesses search radius</h3><p>Google Places, Geoapify and OpenStreetMap results are searched around the selected location.</p></div><label htmlFor="competitor-radius"><strong>{radius} km</strong><input id="competitor-radius" type="range" min="2" max="10" step="1" value={radius} onChange={(event) => onRadiusChange(Number(event.target.value))} /><span className="radius-scale"><span>2 km</span><span>10 km</span></span></label>{result?.radius_supply && <div className="radius-bands"><span><strong>{result.radius_supply.within_2km}</strong> within 2 km</span><span><strong>{result.radius_supply.within_5km}</strong> within 5 km</span><span><strong>{result.radius_supply.within_10km}</strong> within 10 km</span></div>}</section><div className="analysis-summary"><div><Badge kind={result?.status === 'AVAILABLE' ? 'PUBLIC DATA' : 'VERIFICATION REQUIRED'} /><strong>{result?.mapped_competitor_count ?? '—'}</strong><span>mapped similar businesses within {radius} km</span></div><div><strong>{result?.competitors_per_1000_residents?.toLocaleString('en-IN') ?? 'Unavailable'}</strong><span>competitors per 1,000 residents</span></div><div><Badge kind={demographics?.status === 'AVAILABLE' ? 'PUBLIC DATA' : 'VERIFICATION REQUIRED'} /><strong>{demographics?.total_population?.toLocaleString('en-IN') ?? 'Unavailable'}</strong><span>Census 2011 sub-district residents</span></div><div><strong>{demographics?.households?.toLocaleString('en-IN') ?? 'Unavailable'}</strong><span>Census 2011 households</span></div><div><strong>{marketValue?.recommendation ? `${marketValue.recommendation.relative_position_percent}%` : 'Unavailable'}</strong><span>rural affordability position / India</span></div></div><VisualDataPanel competitors={result} demographics={demographics} marketValue={marketValue} radius={radius} />{result?.status === 'INSUFFICIENT' && <div className="warning-callout"><AlertTriangle /><div><strong>Partial map evidence only</strong><p>{result.limitations[0] || 'Mapped-business evidence could not be verified for this sub-district.'}</p></div></div>}<RiskAndOpportunityGuide competitors={result} demographics={demographics} /><ProductMarketValuePanel result={marketValue} compact /><SourceList sources={sources} /><details className="plain-details" open><summary>Data limitations</summary><ul>{[...(result?.limitations ?? []), ...(result?.accessibility?.limitations ?? []), ...(demographics?.limitations ?? []), ...(marketValue?.limitations ?? [])].map((item) => <li key={item}>{item}</li>)}</ul></details></div>
}

function VisualDataPanel({ competitors, demographics, marketValue, radius }: { competitors: CompetitorMapping | null; demographics: LocalDemographics | null; marketValue: ProductMarketValue | null; radius: number }) {
  const supply = competitors?.radius_supply
  const maxSupply = Math.max(supply?.within_10km ?? 0, 1)
  const affordability = marketValue?.recommendation?.relative_position_percent
  const population = competitors?.demographics?.total_population ?? demographics?.total_population
  const populationLabel = population != null ? population.toLocaleString('en-IN') : 'Unavailable'
  const bars = [
    { label: 'Within 2 km', value: supply?.within_2km, width: supply ? (supply.within_2km / maxSupply) * 100 : 0 },
    { label: 'Within 5 km', value: supply?.within_5km, width: supply ? (supply.within_5km / maxSupply) * 100 : 0 },
    { label: 'Within 10 km', value: supply?.within_10km, width: supply ? (supply.within_10km / maxSupply) * 100 : 0 },
  ]
  return <section className="visual-data-panel" aria-label="Visual evidence overview"><div className="visual-data-heading"><div><span className="section-label">EVIDENCE AT A GLANCE</span><h3>What the available data is saying</h3><p>Supply is shown as mapped businesses. Population stays at its verified Census scope; it is not a radius estimate.</p></div><Badge kind={competitors?.status === 'AVAILABLE' ? 'PUBLIC DATA' : 'VERIFICATION REQUIRED'} /></div><div className="visual-data-grid"><div className="supply-chart"><div className="chart-title"><span>Mapped similar businesses</span><strong>{competitors?.mapped_competitor_count ?? '—'}</strong></div>{bars.map((bar) => <div className="data-bar-row" key={bar.label}><span>{bar.label}</span><div className="data-bar-track"><i style={{ width: `${Math.max(bar.width, supply && bar.value ? 8 : 0)}%` }} /></div><b>{bar.value ?? '—'}</b></div>)}<small>Search radius selected: {radius} km</small></div><div className="signal-stack"><article><span>Rural affordability position</span><strong>{affordability != null ? `${affordability}%` : 'Unavailable'}</strong><div className="signal-meter"><i style={{ width: `${Math.min(100, Math.max(0, affordability ?? 0))}%` }} /></div><small>State rural MPCE compared with the all-India rural baseline</small></article><article><span>Verified population baseline</span><strong>{populationLabel}</strong><small>{demographics?.status === 'AVAILABLE' || competitors?.demographics?.total_population ? 'Census 2011 sub-district residents' : 'No verified demographic record yet'}</small></article></div></div></section>
}

function RiskAndOpportunityGuide({ competitors, demographics }: { competitors: CompetitorMapping | null; demographics: LocalDemographics | null }) {
  const mapped = competitors?.mapped_competitor_count
  const mapReady = competitors?.status === 'AVAILABLE'
  const nextAction = !demographics?.total_population
    ? 'Confirm the selected Census sub-district before using local evidence.'
    : !mapReady
      ? 'Complete a local walk-through of similar businesses, prices, footfall and suppliers; the live map source is incomplete for this area.'
      : mapped === 0
        ? 'Validate the apparent supply gap with a local walk-through before investing; no mapped business does not prove no business exists.'
        : 'Compare the mapped businesses locally on price, service, quality, opening hours and customer footfall before finalising your offer.'
  const risk = !mapReady ? 'Evidence gap' : mapped && mapped >= 10 ? 'Competition watch' : 'Local validation required'
  return <section className="risk-guide"><div className="panel-heading"><div><Badge kind="VERIFICATION REQUIRED" /><h3>Risk and opportunity guide</h3><p>These actions respond to the evidence currently available. They do not claim demand, profit or a guaranteed business outcome.</p></div></div><div className="risk-guide-grid"><article><span>Current watch</span><strong>{risk}</strong><p>{nextAction}</p></article><article><span>Protect your downside</span><ul><li>Collect at least three current supplier quotations.</li><li>Test your offer with real local customers before investing.</li><li>Keep working-capital reserve separate from equipment cost.</li></ul></article><article><span>Potential opportunity</span><p>{mapReady ? 'Differentiate by a verified local need such as service quality, delivery, product range or timing. Validate it through interviews and a field visit.' : 'Opportunity cannot be classified from incomplete mapped-business evidence. Complete local verification first.'}</p></article></div></section>
}

function FinanceStep({ financial, intelligence, profile, loading, error, onProfileChange }: { financial: FinancialRoadmap | null; intelligence: FinancialIntelligence | null; profile: FinanceProfile; loading: boolean; error: string; onProfileChange: (change: Partial<FinanceProfile>) => void }) {
  if (loading && !financial) return <LoadingState title="Building your financial roadmap" text="Applying the current curated government-rule registry." />
  if (!financial) return <ErrorState message={error || 'The financial roadmap is unavailable.'} />
  const assessment = financial.assessment
  if (assessment.status !== 'VALID') return <ErrorState message={assessment.message || 'No supported baseline was found.'} />
  return <div className="step-content"><StepIntro number="05" title="Build a fundable enterprise roadmap" text="Compare curated government routes, then add only the business costs you know. Missing or lender-controlled values remain clearly unverified." />
    <div className="scheme-recommendation"><div><Badge kind="VERIFIED GOVT RULE" /><span>BASELINE FINANCIAL STRUCTURE</span><h2>{assessment.scheme_name}</h2><p>Published terms are calculated below. Applicant eligibility and the final repayment schedule still require the authorized agency.</p></div><Landmark size={36} /></div>
    <div className="financial-grid"><Metric label="Indicative project cost" value={formatINR(assessment.project_cost)} /><Metric label="Published-cap financing" value={formatINR(assessment.eligible_loan ?? 0)} /><Metric label="Required own contribution" value={formatINR(assessment.required_own_contribution ?? 0)} /><Metric label="Published beneficiary rate" value={`${(assessment.annual_interest_rate ?? 0) * 100}% p.a.`} /><Metric label="Published tenure" value={`${assessment.tenure_months ?? 0} months`} /><Metric label="Published moratorium" value={`${assessment.moratorium_months ?? 0} months`} /></div>
    <div className="warning-callout"><Info /><div><strong>Repayment treatment requires confirmation</strong><p>{assessment.repayment_frequency_note} The illustration does not capitalize moratorium interest.</p></div></div>
    <EnterpriseProfile profile={profile} onChange={onProfileChange} />
    <CashflowPlanner profile={profile} cashflow={financial.cashflow} onChange={onProfileChange} />
    <FinancialIntelligencePanel result={intelligence} />
    <GovernmentSchemeRouter routes={financial.routes} />
    <details className="plain-details"><summary>Financial-data limitations</summary><ul>{financial.data_limitations.map((item) => <li key={item}>{item}</li>)}</ul></details>
  </div>
}

function FinancialIntelligencePanel({ result }: { result: FinancialIntelligence | null }) {
  if (!result) return <div className="info-callout"><Info size={17} /><p>The deterministic financial analysis is updating.</p></div>
  const complete = result.repayment_metrics?.status === 'CALCULATED'
  return <section className="finance-input-panel"><div className="panel-heading"><div><Badge kind={complete ? 'CALCULATED' : 'VERIFICATION REQUIRED'} /><h3>Financial feasibility and scenarios</h3><p>Repayment Coverage, downside scenarios and financing recommendations use only the figures you enter.</p></div></div>{complete ? <><div className="financial-grid"><Metric label="Operating profit" value={formatINR(result.costs?.operating_profit ?? 0)} /><Metric label="Repayment Coverage" value={`${result.repayment_metrics?.repayment_coverage ?? 0}×`} note="Operating profit ÷ EMI; not formal DSCR" /><Metric label="Monthly cash after EMI" value={formatINR(result.repayment_metrics?.monthly_cash_surplus ?? 0)} /><Metric label="Working-capital requirement" value={result.working_capital?.requirement != null ? formatINR(result.working_capital.requirement) : 'Unknown'} /><Metric label="Financial feasibility" value={result.feasibility?.status ?? 'UNKNOWN'} /><Metric label="Recommended loan" value={result.recommendation?.recommended_loan != null ? formatINR(result.recommendation.recommended_loan) : 'Not recommended'} /></div><div className="scenario-grid">{result.scenario_results.map((scenario) => <article className="report-metric" key={scenario.name}><span>{scenario.name}</span><strong>{scenario.repayment_coverage != null ? `${scenario.repayment_coverage}× coverage` : 'Unknown'}</strong><small>{scenario.monthly_cash_after_emi != null ? `${formatINR(scenario.monthly_cash_after_emi)} after EMI` : 'Needs complete inputs'}</small></article>)}</div></> : <div className="info-callout"><Info size={17} /><p>Enter monthly revenue plus both fixed and variable costs to calculate repayment coverage, scenarios and recommended financing. Missing figures remain UNKNOWN.</p></div>}<details className="plain-details"><summary>Financial methodology and limitations</summary><ul>{[...result.assumptions, ...result.limitations].map((item) => <li key={item}>{item}</li>)}</ul></details></section>
}

function EnterpriseProfile({ profile, onChange }: { profile: FinanceProfile; onChange: (change: Partial<FinanceProfile>) => void }) {
  return <section className="finance-input-panel"><div className="panel-heading"><div><Badge kind="USER INPUT" /><h3>Scheme-fit profile</h3><p>These selections only screen published route conditions. Your location is not assumed to be rural, and no social category is inferred.</p></div></div><div className="finance-input-grid"><label className="form-field"><span>Enterprise activity</span><select value={profile.activity_type} onChange={(e) => onChange({ activity_type: e.target.value as FinanceProfile['activity_type'] })}><option value="not_sure">I will confirm later</option><option value="service_or_trading">Business / service / trading</option><option value="manufacturing">Manufacturing</option><option value="food_processing">Food processing</option><option value="traditional_artisan">Eligible traditional artisan / craftsperson</option></select></label><label className="form-field"><span>Operating area for PMEGP</span><select value={profile.area_type} onChange={(e) => onChange({ area_type: e.target.value as FinanceProfile['area_type'] })}><option value="not_sure">I will confirm later</option><option value="rural">Rural</option><option value="urban">Urban</option></select></label><label className="form-field"><span>PMEGP calculation group <small>Self-declared</small></span><select value={profile.pmegp_beneficiary_group} onChange={(e) => onChange({ pmegp_beneficiary_group: e.target.value as FinanceProfile['pmegp_beneficiary_group'] })}><option value="not_sure">Do not calculate subsidy yet</option><option value="general">General category</option><option value="special">Special category under PMEGP</option></select></label><label className="form-field"><span>PM Vishwakarma stage</span><select value={profile.vishwakarma_loan_stage} onChange={(e) => onChange({ vishwakarma_loan_stage: e.target.value as FinanceProfile['vishwakarma_loan_stage'] })}><option value="not_confirmed">Not confirmed</option><option value="first">First loan after basic training</option><option value="second">Second loan stage</option></select></label></div><label className="check-field"><input type="checkbox" checked={profile.has_repaid_mudra_tarun} onChange={(e) => onChange({ has_repaid_mudra_tarun: e.target.checked })} /><span>I have successfully repaid a previous MUDRA Tarun loan <small>Required before Tarun Plus can be considered.</small></span></label></section>
}

function CashflowPlanner({ profile, cashflow, onChange }: { profile: FinanceProfile; cashflow: FinancialRoadmap['cashflow']; onChange: (change: Partial<FinanceProfile>) => void }) {
  return <section className="finance-input-panel"><div className="panel-heading"><div><Badge kind="USER INPUT" /><h3>Cash-flow and working-capital planner</h3><p>Use quotations and your operating plan. The service never inserts assumed rent, stock, wages, transport, utility or sales figures.</p></div><Badge kind={cashflow.status === 'AVAILABLE' ? 'CALCULATED' : 'VERIFICATION REQUIRED'} /></div><div className="finance-input-grid"><CurrencyInput label="Monthly fixed costs" value={profile.monthly_fixed_cost} onChange={(value) => onChange({ monthly_fixed_cost: value })} help="Rent, salaries, utilities and other fixed costs" /><CurrencyInput label="Monthly variable costs" value={profile.monthly_variable_cost} onChange={(value) => onChange({ monthly_variable_cost: value })} help="Stock, materials, delivery and variable costs" /><CurrencyInput label="Expected monthly revenue" value={profile.expected_monthly_revenue} onChange={(value) => onChange({ expected_monthly_revenue: value })} help="Use a conservative, evidenced sales estimate" /><label className="form-field"><span>Operating reserve months</span><input type="number" min="0" max="24" step="0.5" value={profile.operating_reserve_months ?? ''} onChange={(e) => onChange({ operating_reserve_months: optionalNumber(e.target.value) })} placeholder="e.g. 3" /><small>You choose the buffer; no default is assumed.</small></label></div>{cashflow.status === 'AVAILABLE' ? <div className="financial-grid cashflow-results"><Metric label="Monthly operating cost" value={formatINR(cashflow.monthly_operating_cost ?? 0)} /><Metric label="Cash before debt" value={formatINR(cashflow.monthly_cash_before_debt ?? 0)} /><Metric label="Cash after baseline EMI" value={formatINR(cashflow.monthly_cash_after_baseline_instalment ?? 0)} /><Metric label="User-chosen operating reserve" value={formatINR(cashflow.operating_reserve_requirement ?? 0)} /></div> : <div className="info-callout"><Info size={17} /><p>{cashflow.limitations.slice(1).join(' ')}</p></div>}</section>
}

function CurrencyInput({ label, value, onChange, help }: { label: string; value?: number; onChange: (value?: number) => void; help: string }) {
  return <label className="form-field"><span>{label}</span><div className="compact-currency"><b>₹</b><input type="number" min="0" inputMode="numeric" value={value ?? ''} onChange={(e) => onChange(optionalNumber(e.target.value))} placeholder="Enter amount" /></div><small>{help}</small></label>
}

function optionalNumber(value: string) {
  if (value.trim() === '') return undefined
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : undefined
}

function GovernmentSchemeRouter({ routes }: { routes: GovernmentSchemeRoute[] }) {
  return <section className="scheme-router"><div className="panel-heading"><div><Badge kind="VERIFIED GOVT RULE" /><h3>Curated government scheme routes</h3><p>Every route links to its official source and identifies whether the figure is published, profile-dependent, lender-controlled or needs availability confirmation.</p></div></div><div className="scheme-route-grid">{routes.map((route) => <article className={`scheme-route ${route.status.toLowerCase()}`} key={route.code}><div className="scheme-route-top"><div><SchemeRouteBadge status={route.status} /><h4>{route.name}</h4><p>{route.administering_body}</p></div><a href={route.official_url} target="_blank" rel="noreferrer">Official source <ArrowRight size={14} /></a></div><p className="route-summary">{route.summary}</p><div className="route-metrics">{route.funding_limit != null && <Metric label="Published limit / route amount" value={formatINR(route.funding_limit)} />}{route.potential_subsidy != null && <Metric label="Potential subsidy" value={formatINR(route.potential_subsidy)} />}{route.minimum_beneficiary_contribution != null && <Metric label="Minimum contribution" value={formatINR(route.minimum_beneficiary_contribution)} />}{route.beneficiary_interest_rate != null && <Metric label="Published beneficiary rate" value={`${route.beneficiary_interest_rate * 100}% p.a.`} />}{route.tenure_months != null && <Metric label="Published tenure" value={`${route.tenure_months} months`} />}{route.estimated_monthly_instalment != null && <Metric label="Illustrative monthly instalment" value={formatINR(route.estimated_monthly_instalment)} />}</div>{route.conditions.length > 0 && <details><summary>Published conditions to verify</summary><ul>{route.conditions.map((condition) => <li key={condition}>{condition}</li>)}</ul></details>}{route.limitations.length > 0 && <div className="route-limitations"><Badge kind="VERIFICATION REQUIRED" /><span>{route.limitations.join(' ')}</span></div>}<small className="source-date">Government source reviewed: {route.source_verified_on}</small></article>)}</div></section>
}

function SchemeRouteBadge({ status }: { status: GovernmentSchemeRoute['status'] }) {
  const mapping: Record<GovernmentSchemeRoute['status'], BadgeKind> = { PUBLISHED_TERMS: 'VERIFIED GOVT RULE', PROFILE_NEEDED: 'USER INPUT', ELIGIBILITY_CHECK: 'VERIFICATION REQUIRED', LENDER_TERMS_REQUIRED: 'LENDER TERMS REQUIRED', AVAILABILITY_CHECK: 'AVAILABILITY CHECK', NOT_APPLICABLE: 'VERIFICATION REQUIRED' }
  const labels: Record<GovernmentSchemeRoute['status'], string> = { PUBLISHED_TERMS: 'VERIFIED GOVT RULE', PROFILE_NEEDED: 'PROFILE NEEDED', ELIGIBILITY_CHECK: 'ELIGIBILITY CHECK', LENDER_TERMS_REQUIRED: 'LENDER TERMS REQUIRED', AVAILABILITY_CHECK: 'AVAILABILITY CHECK', NOT_APPLICABLE: 'NOT APPLICABLE' }
  return <span title={labels[status]}><Badge kind={mapping[status]} /></span>
}

function ReportPage({ locale, location, category, financial, financialIntelligence, competitors, demographics, marketValue, onRecalculate }: { locale: 'en' | 'hi'; location: string; category: string; financial: FinancialRoadmap | null; financialIntelligence: FinancialIntelligence | null; competitors: CompetitorMapping | null; demographics: LocalDemographics | null; marketValue: ProductMarketValue | null; onRecalculate: () => void }) {
  const assessment = financial?.assessment
  const cashflow = financial?.cashflow
  const financialFit = assessment?.status === 'VALID'
  return <main className="report-page page-wrap"><div className="report-toolbar"><button className="quiet-button" onClick={onRecalculate}><ArrowLeft size={16} /> Recalculate</button><div><button className="secondary-button" onClick={() => window.print()}><Printer size={16} /> Print / Save PDF</button><button className="primary-button" onClick={() => window.print()}><FileDown size={16} /> Download report</button></div></div><header className="report-header"><div><span className="section-label">LOCAL FEASIBILITY REPORT</span><h1>{category} enterprise assessment</h1><p><MapPin size={16} /> {location || 'Location not specified'}</p></div><dl><div><dt>Assessment date</dt><dd>{new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium' }).format(new Date())}</dd></div><div><dt>Data status</dt><dd><Badge kind={financial ? 'VERIFIED GOVT RULE' : 'VERIFICATION REQUIRED'} /></dd></div></dl></header><Disclaimer />
    <ReportSection title="Executive summary" eyebrow="01 · DECISION SNAPSHOT"><div className="executive-grid"><article className="executive-primary"><span>FINANCIAL FIT</span><strong>{financialFit ? 'Government-rule roadmap ready' : 'Action required'}</strong><p>{financialFit ? `${assessment?.scheme_name} provides the baseline. All programme routes require eligibility and sanction verification.` : assessment?.message || 'The financial service did not return a roadmap.'}</p></article><Metric label="Local Census baseline" value={demographics?.total_population?.toLocaleString('en-IN') ?? 'Unavailable'} note={demographics?.status === 'AVAILABLE' ? 'Census 2011 sub-district residents' : 'No verified local demographic record'} /><Metric label="Competition signal" value={competitors?.mapped_competitor_count == null ? 'Unavailable' : `${competitors.mapped_competitor_count} mapped`} note="OpenStreetMap coverage varies" /><Metric label="Next action" value="Verify locally" note="Demand, quotations and eligibility" /></div><VisualDataPanel competitors={competitors} demographics={demographics} marketValue={marketValue} radius={competitors?.analysis_scope === 'VILLAGE' ? 5 : 10} /></ReportSection>
    <ReportSection title="Market reach and opportunity" eyebrow="02 · LOCAL EVIDENCE"><FeasibilityEvidence competitors={competitors} demographics={demographics} marketValue={marketValue} /></ReportSection>
    <ReportSection title="Competitor mapping" eyebrow="03 · EXISTING SUPPLY"><div className="competitor-report"><div className="big-stat"><strong>{competitors?.mapped_competitor_count ?? '—'}</strong><span>mapped similar businesses in the selected search radius</span><Badge kind={competitors?.status === 'AVAILABLE' ? 'PUBLIC DATA' : 'VERIFICATION REQUIRED'} /></div><div><h3>Competition evidence</h3><div className="financial-grid"><Metric label="Competitors per 1,000 residents" value={competitors?.competitors_per_1000_residents?.toLocaleString('en-IN') ?? 'Unavailable'} note="Mapped businesses ÷ Census 2011 block population × 1,000" /><Metric label="Census 2011 sub-district residents" value={(competitors?.demographics?.total_population ?? demographics?.total_population)?.toLocaleString('en-IN') ?? 'Unavailable'} note="Local Census demographic baseline" /><Metric label="Census 2011 households" value={demographics?.households?.toLocaleString('en-IN') ?? 'Unavailable'} note="Local Census household baseline" /></div><h3>Mapped businesses</h3><p>Select any business row to open its mapped location in Google Maps.</p>{competitors?.mapped_competitors?.length ? <ul className="competitor-list">{competitors.mapped_competitors.slice(0, 12).map((item) => { const query = item.latitude != null && item.longitude != null ? `${item.latitude},${item.longitude}` : item.name || ''; const mapsUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(query)}`; return <li key={`${item.provider}-${item.osm_id}`}><a className="competitor-map-link" href={mapsUrl} target="_blank" rel="noreferrer" aria-label={`Open ${item.name || 'mapped business'} in Google Maps`}><Store size={16} /><span><b>{item.name || 'Unnamed mapped business'}</b><small>{item.provider === 'GOOGLE_PLACES' ? 'Google Places' : item.provider === 'GEOAPIFY' ? 'Geoapify / OpenStreetMap' : 'OpenStreetMap'} · {item.distance_km != null ? `${item.distance_km.toFixed(1)} km away` : 'distance unavailable'}</small></span><ExternalLink size={17} aria-hidden="true" /></a></li> })}</ul> : null}<h3>Important limitation</h3><p>{competitors?.limitations?.[0] || 'No completed competitor result is available. Mapped records may be incomplete.'}</p></div></div><SourceList sources={[...(competitors?.data_provenance ?? []), ...(demographics?.data_provenance ?? [])]} /></ReportSection>
    <ReportSection title="Product market value" eyebrow="04 · REGIONAL PRICE REFERENCE"><ProductMarketValuePanel result={marketValue} /></ReportSection>
    <ReportSection title="SWOT and risk watch" eyebrow="05 · EVIDENCE-LED DECISION SUPPORT"><SwotAndThreats competitors={competitors} marketValue={marketValue} /><RiskAndOpportunityGuide competitors={competitors} demographics={demographics} /></ReportSection>
    <ReportSection title="Financial structure" eyebrow="06 · GOVERNMENT-RULE BASELINE">{financialFit ? <div className="finance-summary"><div className="finance-lead"><span>PUBLISHED BASELINE</span><h3>{assessment?.scheme_name}</h3><p>Calculated with the verified registry; eligibility and channel terms are not presumed.</p></div><div className="financial-grid"><Metric label="Available margin" value={formatINR(assessment?.margin_capital ?? 0)} /><Metric label="Project cost" value={formatINR(assessment?.project_cost ?? 0)} /><Metric label="Published-cap financing" value={formatINR(assessment?.eligible_loan ?? 0)} /><Metric label="Required contribution" value={formatINR(assessment?.required_own_contribution ?? 0)} /></div></div> : <UnavailablePanel title="No financial baseline" text={assessment?.message || 'Recalculate after the financial service is available.'} />}<>{financial && <GovernmentSchemeRouter routes={financial.routes} />}</></ReportSection>
    {financialFit && <ReportSection title="Quarterly repayment planner" eyebrow="07 · ILLUSTRATIVE REPAYMENT"><div className="repayment-layout"><div className="emi-card"><span>Monthly planning equivalent</span><strong>{formatINR(assessment?.estimated_monthly_instalment ?? 0)}</strong><small>for {assessment?.repayment_months} repayment months</small></div><div className="financial-grid"><Metric label="Quarterly instalment illustration" value={formatINR(assessment?.estimated_quarterly_instalment ?? 0)} /><Metric label="Repayment quarters" value={`${assessment?.repayment_quarters ?? 0}`} /><Metric label="Total repayment illustration" value={formatINR(assessment?.estimated_total_repayment ?? 0)} /><Metric label="Total interest illustration" value={formatINR(assessment?.estimated_total_interest ?? 0)} /></div></div><div className="timeline"><div style={{ flex: assessment?.moratorium_months ?? 1 }}><span>Published moratorium</span><strong>{assessment?.moratorium_months} months</strong></div><div className="repay" style={{ flex: assessment?.repayment_months ?? 1 }}><span>Illustrative repayment</span><strong>{assessment?.repayment_quarters} quarters</strong></div></div><p className="method-note"><Badge kind="ASSUMPTION" /> {assessment?.repayment_frequency_note}</p></ReportSection>}
    <ReportSection title="Cash-flow and working-capital check" eyebrow="08 · USER-SUPPLIED BUSINESS PLAN">{cashflow?.status === 'AVAILABLE' ? <div className="financial-grid"><Metric label="Monthly operating cost" value={formatINR(cashflow.monthly_operating_cost ?? 0)} /><Metric label="Cash before debt" value={formatINR(cashflow.monthly_cash_before_debt ?? 0)} /><Metric label="Cash after baseline EMI" value={formatINR(cashflow.monthly_cash_after_baseline_instalment ?? 0)} /><Metric label="User-chosen cash reserve" value={formatINR(cashflow.operating_reserve_requirement ?? 0)} /></div> : <UnavailablePanel title="Operating affordability requires your actual figures" text={cashflow?.limitations.slice(1).join(' ') || 'Return to Finance and provide your own costs, expected revenue and reserve months. No default business cost is applied.'} />}</ReportSection>
    <ReportSection title="Financial feasibility scenarios" eyebrow="09 · DETERMINISTIC FINANCIAL INTELLIGENCE"><FinancialIntelligencePanel result={financialIntelligence} /></ReportSection>
    <ReportSection title="Action plan" eyebrow="10 · APPLICATION READINESS"><ol className="action-list">{(financial?.readiness_actions ?? ['Collect current equipment, fit-out and supplier quotations.', 'Separate working capital from capital expenditure in a project report.', 'Verify scheme eligibility and apply only through the official government channel.']).map((item, i) => <li key={item}><span>{i + 1}</span>{item}</li>)}</ol></ReportSection>
    <ReportSection title="Ask about this assessment" eyebrow="11 · EXPLANATIONS"><AssessmentAssistant locale={locale} context={{ location, business: category, demographics: demographics?.total_population ? { population_2011: demographics.total_population, households_2011: demographics.households } : 'UNKNOWN', competition: competitors ? { status: competitors.status, mapped_similar_businesses: competitors.mapped_competitor_count ?? 'UNKNOWN', radius_supply: competitors.radius_supply ?? 'UNKNOWN', limitations: competitors.limitations } : 'UNKNOWN', financial: financialIntelligence ? { feasibility: financialIntelligence.feasibility?.status, repayment_coverage: financialIntelligence.repayment_metrics?.repayment_coverage, recommended_loan: financialIntelligence.recommendation?.recommended_loan } : 'UNKNOWN', limitations: [...(competitors?.limitations ?? []), ...(demographics?.limitations ?? [])], next_actions: financial?.readiness_actions ?? [] }} /></ReportSection>
    <MethodologyPanel competitors={competitors} marketValue={marketValue} financial={financial} />
  </main>
}

function AssessmentAssistant({ locale, context }: { locale: 'en' | 'hi'; context: Record<string, unknown> }) {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState<AssessmentAssistantResponse | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const presets = locale === 'hi'
    ? ['मेरे लिए सबसे महत्वपूर्ण जोखिम क्या है?', 'निवेश से पहले मुझे क्या जांचना चाहिए?', 'अगला सही कदम क्या है?']
    : ['What is the most important risk for me?', 'What should I verify before investing?', 'What is my best next step?']
  async function ask() {
    if (question.trim().length < 2) return
    setLoading(true); setError(''); setAnswer(null)
    try { setAnswer(await askAssessmentAssistant({ question: question.trim(), language: locale, assessment_context: context })) }
    catch (err) { setError(err instanceof Error ? err.message : 'The explanation service is unavailable.') }
    finally { setLoading(false) }
  }
  return <section className="assessment-assistant"><p>Ask in {locale === 'hi' ? 'Hindi or English' : 'English or Hindi'} about the evidence already shown in this report. The assistant cannot create new local facts or change financial calculations.</p><div className="assistant-presets">{presets.map((item) => <button type="button" className="secondary-button" key={item} onClick={() => setQuestion(item)}>{item}</button>)}</div><div className="assistant-compose"><textarea value={question} onChange={(event) => setQuestion(event.target.value)} placeholder={locale === 'hi' ? 'अपना प्रश्न लिखें' : 'Ask a question about this assessment'} maxLength={1000} /><button className="primary-button" type="button" onClick={() => void ask()} disabled={loading || question.trim().length < 2}>{loading ? 'Answering…' : 'Ask VyaparSathi'}</button></div>{error && <ErrorState message={error} />}{answer && <article className="assistant-answer"><Badge kind={answer.generated_by === 'gemini' ? 'CALCULATED' : 'VERIFICATION REQUIRED'} /><p>{answer.answer}</p><small>{answer.limitations.join(' ')}</small></article>}</section>
}

function FeasibilityEvidence({ competitors, demographics, marketValue }: { competitors: CompetitorMapping | null; demographics: LocalDemographics | null; marketValue: ProductMarketValue | null }) {
  const radius = competitors?.radius_supply
  const population = competitors?.demographics?.total_population ?? demographics?.total_population
  const density = competitors?.competitors_per_1000_residents
  const opportunity = density == null ? 'Supply opportunity cannot be classified until the mapped-business and population sources complete.' : density === 0 ? 'No similar business is currently mapped in this block. Verify this through a local walk-through before treating it as an unmet-demand opportunity.' : `${density.toLocaleString('en-IN')} mapped similar businesses per 1,000 Census 2011 rural residents is an observed supply signal; validate demand with customer interviews before investing.`
  return <><div className="financial-grid"><Metric label="Mapped competitors within 2 km" value={radius ? String(radius.within_2km) : 'Unavailable'} note="Observed OSM supply" /><Metric label="Mapped competitors within 5 km" value={radius ? String(radius.within_5km) : 'Unavailable'} note="Cumulative observed supply" /><Metric label="Mapped competitors within 10 km" value={radius ? String(radius.within_10km) : 'Unavailable'} note="Cumulative observed supply" /><Metric label="Block rural population baseline" value={population?.toLocaleString('en-IN') ?? 'Unavailable'} note="Census 2011; not a radius estimate" /></div><div className="info-callout"><Info size={17} /><p><strong>Opportunity interpretation:</strong> {opportunity}</p></div><div className="info-callout"><AlertTriangle size={17} /><p><strong>Consumer-base boundary:</strong> A 5 km/10 km population estimate requires a verified village/grid demographic dataset and cannot be derived from a block total. The report now presents the completed radius-level supply evidence and clearly keeps population at its verified block scope.</p></div>{marketValue?.recommendation && <p className="method-note"><Badge kind="CALCULATED" /> State rural affordability position: {marketValue.recommendation.relative_position_percent}% of the all-India rural baseline. This informs price positioning, not local demand.</p>}</>
}

function SwotAndThreats({ competitors, marketValue }: { competitors: CompetitorMapping | null; marketValue: ProductMarketValue | null }) {
  const count = competitors?.mapped_competitor_count
  const density = competitors?.competitors_per_1000_residents
  const commercial = competitors?.economic_context?.mapped_commercial_features
  const affordability = marketValue?.recommendation?.relative_position_percent
  const strengths = [commercial == null ? 'No verified commercial-feature count is available yet.' : `${commercial} mapped commercial features provide an observed local activity signal.`, count == null ? 'Competitor evidence is pending.' : `${count} similar businesses were mapped in the selected block.`]
  const weaknesses = ['Block-level Census population is not a 5 km or 10 km consumer-base estimate.', 'OpenStreetMap coverage can omit informal and unmapped enterprises.']
  const opportunities = [density == null ? 'Classify supply only after the demographic and OSM lookup completes.' : density === 0 ? 'Conduct a field survey to test whether the absence of mapped supply reflects a genuine service gap.' : 'Use the observed competitor density to differentiate product mix, service, or location after field validation.', affordability == null ? 'Add a comparable local price to create an affordability-positioning reference.' : `Use the ${affordability}% rural affordability position as a conservative price-planning input.`]
  const threats = [count == null ? 'Competition cannot yet be assessed because the live mapping lookup is incomplete.' : `${count} mapped similar businesses may compete for the same customers; validate their prices and footfall locally.`, 'Demand, supplier prices, and informal competitors require local verification before a go/no-go decision.']
  return <div className="two-column">{([['Strengths', strengths], ['Weaknesses', weaknesses], ['Opportunities', opportunities], ['Threats / risks', threats]] as const).map(([title, items]) => <article className="unavailable-panel" key={title}><Badge kind={title === 'Threats / risks' ? 'VERIFICATION REQUIRED' : 'PUBLIC DATA'} /><h3>{title}</h3><ul>{items.map(item => <li key={item}>{item}</li>)}</ul></article>)}</div>
}

function ReportSection({ title, eyebrow, children }: { title: string; eyebrow: string; children: React.ReactNode }) { return <section className="report-section"><div className="report-section-heading"><span>{eyebrow}</span><h2>{title}</h2></div>{children}</section> }
function StepIntro({ number, title, text }: { number: string; title: string; text: string }) { return <header className="step-intro"><span>{number} / 05</span><h2>{title}</h2><p>{text}</p></header> }
function CalculationCard({ label, value, badge, formula }: { label: string; value: string; badge: BadgeKind; formula?: string }) { return <article className="calculation-card"><Badge kind={badge} /><span>{label}</span><strong>{value}</strong>{formula && <small>{formula}</small>}</article> }
function Metric({ label, value, note }: { label: string; value: string; note?: string }) {
  const [open, setOpen] = useState(false)
  const explanation = note || 'This figure is based on the current assessment inputs and the source shown in this section. It is decision support, not a guarantee or official approval.'
  return <article className="report-metric"><div className="metric-label"><span>{label}</span><button className="metric-eye" type="button" onClick={() => setOpen(!open)} aria-label={`Explain ${label}`} aria-expanded={open}><Eye size={14} /></button></div><strong>{value}</strong>{note && <small>{note}</small>}{open && <p className="metric-help">{explanation}</p>}</article>
}
function Badge({ kind }: { kind: BadgeKind }) { return <span className={`evidence-badge ${kind.toLowerCase().replace(/ /g, '-')}`}>{kind}</span> }
function Disclaimer() { return <aside className="disclaimer"><ShieldCheck size={20} /><div><strong>Decision-support estimate</strong><p>Results are indicative. Public-data coverage may be incomplete. Final loan eligibility and sanction are determined by the relevant authority.</p></div></aside> }
function ErrorState({ message }: { message: string }) { return <div className="state-box error" role="alert"><AlertTriangle size={20} /><div><strong>We could not complete this step</strong><p>{message}</p></div></div> }
function LoadingState({ title, text }: { title: string; text: string }) { return <div className="state-box loading"><LoaderCircle className="spin" size={25} /><div><strong>{title}</strong><p>{text}</p><small>No result is shown until the source responds.</small></div></div> }
function EmptyState({ title, text }: { title: string; text: string }) { return <div className="state-box"><Database size={24} /><div><strong>{title}</strong><p>{text}</p></div></div> }
function UnavailablePanel({ title, text }: { title: string; text: string }) { return <article className="unavailable-panel"><Badge kind="VERIFICATION REQUIRED" /><h3>{title}</h3><p>{text}</p></article> }
function ProductMarketValuePanel({ result, compact = false }: { result: ProductMarketValue | null; compact?: boolean }) {
  if (result?.status !== 'AVAILABLE' || !result.purchasing_power || !result.recommendation) return <UnavailablePanel title="No verified affordability position" text={result?.limitations[0] || 'The official purchasing-capacity source could not be matched for this state.'} />
  const { purchasing_power: power, recommendation } = result
  const hasReferencePrice = recommendation.reference_price != null && recommendation.adjusted_reference_price != null
  const formula = hasReferencePrice
    ? `${formatINR(recommendation.reference_price!)} × ${recommendation.adjustment_factor.toFixed(4)} = ${formatINR(recommendation.adjusted_reference_price!)}`
    : `${formatINR(power.index)} ÷ ${formatINR(power.baseline)} = ${recommendation.adjustment_factor.toFixed(4)} (${recommendation.relative_position_percent}%)`
  return <div className={compact ? 'product-value-panel compact' : 'product-value-panel'}><div className="pricing-range"><Badge kind="CALCULATED" /><span>VERIFIED AFFORDABILITY POSITIONING</span><strong>{hasReferencePrice ? formatINR(recommendation.adjusted_reference_price!) : `${recommendation.relative_position_percent}%`}</strong><small>{hasReferencePrice ? 'MPCE-adjusted reference price' : 'state rural affordability position / India'}</small></div><div className="pricing-evidence"><div className="financial-grid"><Metric label="State rural MPCE / India" value={`${formatINR(power.index)} / ${formatINR(power.baseline)}`} note={power.basis || `${power.geographic_scope} scope`} /><Metric label="Affordability multiplier" value={`${recommendation.adjustment_factor.toFixed(4)}×`} note="State rural MPCE ÷ All-India rural MPCE" /><Metric label="Comparable reference price" value={hasReferencePrice ? formatINR(recommendation.reference_price!) : 'Not entered'} note={hasReferencePrice ? 'Entrepreneur input' : 'Enter one in Business to calculate ₹'} /></div><div className="info-callout"><Info size={17} /><p><strong>Formula:</strong> {formula}. {recommendation.strategy}</p></div><p className="source-date">HCES reference period: {power.observed_at || 'not supplied'} · This is a calculated planning reference, not an observed market price.</p>{!compact && <SourceList sources={result.data_provenance} />}</div></div>
}
function SourceList({ sources }: { sources: Array<{ source_id: string; source_name: string; source_url?: string; notes?: string }> }) { const unique = Array.from(new Map(sources.map((source) => [source.source_id, source])).values()); if (!unique.length) return null; return <section className="source-list"><strong>Sources used</strong>{unique.map((source) => <article key={source.source_id}><div><b>{source.source_name}</b><small>{source.notes || source.source_id}</small></div>{source.source_url && <a href={source.source_url} target="_blank" rel="noreferrer">Open source</a>}</article>)}</section> }
function MethodologyPanel({ competitors, marketValue, financial }: { competitors: CompetitorMapping | null; marketValue: ProductMarketValue | null; financial: FinancialRoadmap | null }) { return <details className="methodology-panel"><summary><span><Database size={19} /><b>Data & methodology</b></span><ChevronDown size={18} /></summary><div><article><Badge kind="USER INPUT" /><h3>Location, capital and cash flow</h3><p>Geography, margin capital, activity profile, operating costs, revenue and reserve months are supplied by the user. No business-cost default is inserted.</p></article><article><Badge kind="VERIFIED GOVT RULE" /><h3>Financial roadmap</h3><p>Project cost = margin ÷ 10%; financing need = project cost × 90%. The calculator applies only curated government terms whose linked official sources were reviewed on the stated date.</p></article><article><Badge kind="PUBLIC DATA" /><h3>Competitors</h3><p>{competitors?.methodology?.join(' ') || 'No competitor methodology is available until a live analysis completes.'}</p></article><article><Badge kind={marketValue?.status === 'AVAILABLE' ? 'CALCULATED' : 'VERIFICATION REQUIRED'} /><h3>Local price positioning</h3><p>{marketValue?.methodology?.join(' ') || marketValue?.limitations[0] || 'The official state rural MPCE source is unavailable for this location.'}</p></article><article><Badge kind="VERIFICATION REQUIRED" /><h3>Scheme eligibility and lender terms</h3><p>{financial?.data_limitations[1] || 'Final eligibility, availability, interest where not published, documents, repayment schedule and sanction must be checked through the official scheme channel.'}</p><a href="https://udyamregistration.gov.in/" target="_blank" rel="noreferrer">Official Udyam Registration portal</a></article></div></details> }

export default App
