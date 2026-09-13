import { Fragment, useEffect, useRef, useState } from 'react'
import {
  Accessibility, AlertTriangle, ArrowLeft, ArrowRight, BarChart3,
  Check, ChevronDown, ChevronLeft, ChevronRight, Database, FileDown, IndianRupee,
  ExternalLink, Info, Landmark, LoaderCircle, MapPin, Menu, Printer, RefreshCw,
  RotateCcw, Search, ShieldCheck, Store,
} from 'lucide-react'
import { askAssessmentAssistant, checkHealth, getFinancialIntelligence, getFinancialRoadmap, getIndiaAdministrativeOptions, getLocalDemographics, getMapplsAutosuggest, getProductMarketValue, mapLiveCompetitors, resolveAdministrativeLocation } from './api'
import { formatINR } from './finance'
import type { AssessmentAssistantResponse, CompetitorMapping, FinancialIntelligence, FinancialRoadmap, FinancialRoadmapRequest, GovernmentSchemeRoute, HealthState, IndiaAdministrativeOption, LocalDemographics, MapplsSuggestion, ProductMarketValue } from './types'
import { INDIA_STATES } from './indiaStates'
import bannerMarketConfidence from './assets/home-banners/market-confidence.png'
import bannerBusinessPlanning from './assets/home-banners/business-planning.png'
import bannerFinanceReadiness from './assets/home-banners/finance-readiness.png'

const categories = [
  { id: 'CAT-001', name: 'Restaurant', group: 'Food & hospitality', icon: 'FD', theme: 'food' },
  { id: 'CAT-002', name: 'Hotel', group: 'Food & hospitality', icon: 'HT', theme: 'food' },
  { id: 'CAT-003', name: 'Cosmetics', group: 'Retail', icon: 'RT', theme: 'retail' },
  { id: 'CAT-004', name: 'Kirana / General Store', group: 'Retail', icon: 'GS', theme: 'retail' },
  { id: 'CAT-005', name: 'Tea & Snack Stall', group: 'Food & hospitality', icon: 'TS', theme: 'food' },
  { id: 'CAT-006', name: 'Bakery', group: 'Food & hospitality', icon: 'BK', theme: 'food' },
  { id: 'CAT-007', name: 'Tailoring & Boutique', group: 'Personal services', icon: 'TB', theme: 'personal' },
  { id: 'CAT-008', name: 'Beauty Salon', group: 'Personal services', icon: 'BS', theme: 'personal' },
  { id: 'CAT-009', name: 'Mobile Phone Shop & Repair', group: 'Repair & retail', icon: 'MR', theme: 'repair' },
  { id: 'CAT-010', name: 'Pharmacy / Medical Store', group: 'Retail', icon: 'PH', theme: 'retail' },
  { id: 'CAT-011', name: 'Fruit & Vegetable Shop', group: 'Retail', icon: 'FV', theme: 'agriculture' },
  { id: 'CAT-012', name: 'Dairy / Milk Shop', group: 'Retail', icon: 'DM', theme: 'agriculture' },
  { id: 'CAT-013', name: 'Stationery & Photocopy', group: 'Services', icon: 'SP', theme: 'service' },
  { id: 'CAT-014', name: 'Hardware & Electrical Store', group: 'Retail', icon: 'HE', theme: 'repair' },
  { id: 'CAT-015', name: 'Furniture & Carpentry', group: 'Manufacturing & services', icon: 'FC', theme: 'manufacturing' },
  { id: 'CAT-016', name: 'Welding & Fabrication', group: 'Manufacturing & services', icon: 'WF', theme: 'manufacturing' },
  { id: 'CAT-017', name: 'Laundry & Ironing', group: 'Personal services', icon: 'LI', theme: 'personal' },
  { id: 'CAT-018', name: 'Bicycle Sales & Repair', group: 'Repair & retail', icon: 'BR', theme: 'repair' },
  { id: 'CAT-019', name: 'Agricultural Input Store', group: 'Agriculture support', icon: 'AI', theme: 'agriculture' },
  { id: 'CAT-020', name: 'Textiles & Garment Store', group: 'Retail', icon: 'TG', theme: 'personal' },
  { id: 'CAT-021', name: 'Footwear Store & Repair', group: 'Retail & repair', icon: 'FS', theme: 'repair' },
  { id: 'CAT-022', name: 'Computer & Digital Service Centre', group: 'Services', icon: 'CD', theme: 'service' },
] as const

type Screen = 'start' | 'assessment' | 'report'
type Locale = 'en' | 'hi' | 'bn' | 'mr' | 'ta'
type BadgeKind = 'PUBLIC DATA' | 'CALCULATED' | 'ESTIMATE' | 'ASSUMPTION' | 'USER INPUT' | 'VERIFICATION REQUIRED' | 'VERIFIED GOVT RULE' | 'LENDER TERMS REQUIRED' | 'AVAILABILITY CHECK'
type FinanceProfile = Omit<FinancialRoadmapRequest, 'margin_capital'>
type AccessibilitySettings = {
  highContrast: boolean
  darkContrast: boolean
  highlightLinks: boolean
  invert: boolean
  saturation: boolean
  lineHeight: boolean
  textSpacing: boolean
  bigCursor: boolean
  hideImages: boolean
  reduceMotion: boolean
  keyboardFocus: boolean
}

const defaultAccessibility: AccessibilitySettings = {
  highContrast: false,
  darkContrast: false,
  highlightLinks: false,
  invert: false,
  saturation: false,
  lineHeight: false,
  textSpacing: false,
  bigCursor: false,
  hideImages: false,
  reduceMotion: false,
  keyboardFocus: false,
}

function loadAccessibilityPreferences() {
  try {
    const saved = JSON.parse(localStorage.getItem('vyaparsathi-accessibility') || '{}')
    return {
      settings: { ...defaultAccessibility, ...(saved.settings || {}) } as AccessibilitySettings,
      largeText: Boolean(saved.largeText),
      smallText: Boolean(saved.smallText),
    }
  } catch {
    return { settings: defaultAccessibility, largeText: false, smallText: false }
  }
}

const emptyFinanceProfile: FinanceProfile = {
  activity_type: 'not_sure',
  area_type: 'not_sure',
  pmegp_beneficiary_group: 'not_sure',
  has_repaid_mudra_tarun: false,
  vishwakarma_loan_stage: 'not_confirmed',
}

function App() {
  const [screen, setScreen] = useState<Screen>(() => localStorage.getItem('vyaparsathi-assessment') ? 'assessment' : 'start')
  const [locale, setLocale] = useState<Locale>(() => (localStorage.getItem('vyaparsathi-locale') as Locale) || 'en')
  const [step, setStep] = useState(0)
  const [health, setHealth] = useState<HealthState>('checking')
  const [largeText, setLargeText] = useState(() => loadAccessibilityPreferences().largeText)
  const [smallText, setSmallText] = useState(() => loadAccessibilityPreferences().smallText)
  const [accessibilityOpen, setAccessibilityOpen] = useState(false)
  const [tourOpen, setTourOpen] = useState(false)
  const [accessibility, setAccessibility] = useState<AccessibilitySettings>(() => loadAccessibilityPreferences().settings)
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
    if (competitorResult.status === 'fulfilled') setCompetitors({ ...competitorResult.value, analysis_point: { latitude, longitude, source: selectedDistrict.latitude != null ? 'Administrative hierarchy coordinate' : 'Verified geocoding provider' } })
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
  function navigate(target: { screen: Screen; step?: number }) {
    setScreen(target.screen)
    if (target.step != null) setStep(target.step)
    setMobileNav(false)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
  useEffect(() => { document.documentElement.lang = locale; localStorage.setItem('vyaparsathi-locale', locale) }, [locale])
  useEffect(() => {
    localStorage.setItem('vyaparsathi-accessibility', JSON.stringify({ settings: accessibility, largeText, smallText }))
  }, [accessibility, largeText, smallText])
  const accessibilityClasses = [
    'app', largeText && 'large-text', smallText && 'small-text', accessibility.highContrast && 'a11y-high-contrast',
    accessibility.darkContrast && 'a11y-dark-contrast', accessibility.highlightLinks && 'a11y-highlight-links',
    accessibility.invert && 'a11y-invert', accessibility.saturation && 'a11y-saturation',
    accessibility.lineHeight && 'a11y-line-height', accessibility.textSpacing && 'a11y-text-spacing',
    accessibility.bigCursor && 'a11y-big-cursor', accessibility.hideImages && 'a11y-hide-images',
    accessibility.reduceMotion && 'a11y-reduce-motion', accessibility.keyboardFocus && 'a11y-keyboard-focus',
  ].filter(Boolean).join(' ')
  function updateAccessibility(change: Partial<AccessibilitySettings>) {
    setAccessibility((current) => ({ ...current, ...change }))
  }
  return <div className={accessibilityClasses}>
    <a className="skip-link" href="#main-content">Skip to main content</a>
    <ServiceHeader screen={screen} step={step} locale={locale} setLocale={setLocale} onNavigate={navigate} accessibilityOpen={accessibilityOpen} setAccessibilityOpen={setAccessibilityOpen} tourOpen={tourOpen} setTourOpen={setTourOpen} mobileNav={mobileNav} setMobileNav={setMobileNav} />
    {accessibilityOpen && <AccessibilityPanel largeText={largeText} setLargeText={setLargeText} smallText={smallText} setSmallText={setSmallText} settings={accessibility} updateSettings={updateAccessibility} onClose={() => setAccessibilityOpen(false)} />}
    {tourOpen && <GuidedTour onClose={() => setTourOpen(false)} />}
    <ServiceStrip locale={locale} health={health} />
    {screen === 'start' && <StartScreen locale={locale} onStart={() => { setScreen('assessment'); setStep(0) }} />}
    {screen === 'assessment' && <main id="main-content" className="page-wrap assessment-page">
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
    {screen === 'report' && <ReportPage locale={locale} location={[village, selectedBlock?.name, selectedDistrict?.name, selectedState?.name].filter(Boolean).join(', ')} category={selectedCategory.name} financial={financial} financialIntelligence={financialIntelligence} competitors={competitors} demographics={demographics} marketValue={marketValue} onRecalculate={() => { setScreen('assessment'); setStep(1) }} />}
    <Footer locale={locale} />
  </div>
}

function ServiceStrip({ locale, health }: { locale: Locale; health: HealthState }) {
  const copy = {
    en: { label: 'Independent decision-support service', online: 'Analysis service connected', checking: 'Checking analysis service', offline: 'Analysis service unavailable' },
    hi: { label: 'स्वतंत्र निर्णय-सहायता सेवा', online: 'विश्लेषण सेवा जुड़ी है', checking: 'विश्लेषण सेवा जांची जा रही है', offline: 'विश्लेषण सेवा उपलब्ध नहीं है' },
    bn: { label: 'স্বাধীন সিদ্ধান্ত-সহায়তা পরিষেবা', online: 'বিশ্লেষণ পরিষেবা সংযুক্ত', checking: 'বিশ্লেষণ পরিষেবা পরীক্ষা হচ্ছে', offline: 'বিশ্লেষণ পরিষেবা পাওয়া যাচ্ছে না' },
    mr: { label: 'स्वतंत्र निर्णय-सहाय्य सेवा', online: 'विश्लेषण सेवा जोडली आहे', checking: 'विश्लेषण सेवा तपासत आहे', offline: 'विश्लेषण सेवा उपलब्ध नाही' },
    ta: { label: 'சுயாதீன முடிவு-ஆதரவு சேவை', online: 'பகுப்பாய்வு சேவை இணைக்கப்பட்டுள்ளது', checking: 'பகுப்பாய்வு சேவை சரிபார்க்கப்படுகிறது', offline: 'பகுப்பாய்வு சேவை கிடைக்கவில்லை' },
  }[locale]
  return <div className="service-strip"><span><ShieldCheck size={15} /> {copy.label}</span><span className={`api-state ${health}`}>{health === 'online' ? copy.online : health === 'checking' ? copy.checking : copy.offline}</span></div>
}

function ServiceHeader({ screen, step, locale, setLocale, onNavigate, accessibilityOpen, setAccessibilityOpen, tourOpen, setTourOpen, mobileNav, setMobileNav }: { screen: Screen; step: number; locale: Locale; setLocale: (locale: Locale) => void; onNavigate: (target: { screen: Screen; step?: number }) => void; accessibilityOpen: boolean; setAccessibilityOpen: (v: boolean) => void; tourOpen: boolean; setTourOpen: (v: boolean) => void; mobileNav: boolean; setMobileNav: (v: boolean) => void }) {
  const copy = uiCopy[locale].header
  const items = [
    [copy.nav.overview, { screen: 'start' as Screen }],
    [copy.nav.location, { screen: 'assessment' as Screen, step: 0 }],
    [copy.nav.capital, { screen: 'assessment' as Screen, step: 1 }],
    [copy.nav.business, { screen: 'assessment' as Screen, step: 2 }],
    [copy.nav.market, { screen: 'assessment' as Screen, step: 3 }],
    [copy.nav.finance, { screen: 'assessment' as Screen, step: 4 }],
    [copy.nav.report, { screen: 'report' as Screen }],
  ] as const
  const active = (target: { screen: Screen; step?: number }) => screen === target.screen && (target.step == null || step === target.step)
  return <header className="service-header">
    <div className="header-primary">
      <button className="brand" onClick={() => onNavigate({ screen: 'start' })} aria-label={copy.brandAria}><span className="emblem">SN</span><span><strong>SmartNivesh</strong><small>{copy.tagline}</small></span></button>
      <div className="header-tools"><label className="language-control"><span className="sr-only">{copy.language}</span><select value={locale} onChange={(event) => setLocale(event.target.value as Locale)} aria-label={copy.language}><option value="en">English</option><option value="hi">हिंदी</option><option value="bn">বাংলা</option><option value="mr">मराठी</option><option value="ta">தமிழ்</option></select><ChevronDown size={14} /></label><button className="header-button tour-trigger" aria-expanded={tourOpen} aria-controls="guided-tour" onClick={() => setTourOpen(!tourOpen)}><Info size={16} /> <span>{copy.how}</span></button><button className="header-button" aria-expanded={accessibilityOpen} aria-controls="accessibility-tools" onClick={() => setAccessibilityOpen(!accessibilityOpen)}><Accessibility size={17} /> <span>{copy.accessibility}</span></button></div>
      <button className="menu-button" onClick={() => setMobileNav(!mobileNav)} aria-expanded={mobileNav} aria-controls="primary-navigation" aria-label={mobileNav ? copy.closeMenu : copy.openMenu}><Menu /></button>
    </div>
    <nav id="primary-navigation" className={mobileNav ? 'top-navigation open' : 'top-navigation'} aria-label="Primary service navigation">{items.map(([label, target]) => <button key={label} className={active(target) ? 'active' : ''} aria-current={active(target) ? 'page' : undefined} onClick={() => onNavigate(target)}>{label}</button>)}</nav>
  </header>
}

function GuidedTour({ onClose }: { onClose: () => void }) {
  const [current, setCurrent] = useState(0)
  const steps = [
    { title: 'Select your location', text: 'Choose the verified State, District and Sub-district where the enterprise will operate.' },
    { title: 'Set your capital and business', text: 'Add your available margin, then choose the closest supported business category.' },
    { title: 'Review local evidence', text: 'Explore mapped competitors, Census baselines and the catchment map before investing.' },
    { title: 'Check finance and next actions', text: 'Use your own revenue and cost inputs to see repayment readiness and a practical action plan.' },
  ]
  const step = steps[current]
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => { if (event.key === 'Escape') onClose() }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [onClose])
  return <aside id="guided-tour" className="guided-tour" aria-label="How SmartNivesh works"><div className="tour-progress" aria-label={'Tour step ' + (current + 1) + ' of ' + steps.length}>{steps.map((item, index) => <i className={index === current ? 'current' : index < current ? 'complete' : ''} key={item.title} />)}</div><div className="tour-heading"><span className="section-label">QUICK TOUR</span><button type="button" onClick={onClose} aria-label="Close quick tour">×</button></div><strong>{step.title}</strong><p>{step.text}</p><div className="tour-actions"><button type="button" className="secondary-button" disabled={current === 0} onClick={() => setCurrent((value) => value - 1)}>Back</button>{current < steps.length - 1 ? <button type="button" className="primary-button" onClick={() => setCurrent((value) => value + 1)}>Next</button> : <button type="button" className="primary-button" onClick={onClose}>Start assessment</button>}</div></aside>
}

function AccessibilityPanel({ largeText, setLargeText, smallText, setSmallText, settings, updateSettings, onClose }: { largeText: boolean; setLargeText: (v: boolean) => void; smallText: boolean; setSmallText: (v: boolean) => void; settings: AccessibilitySettings; updateSettings: (change: Partial<AccessibilitySettings>) => void; onClose: () => void }) {
  const controls: Array<[keyof AccessibilitySettings, string, string]> = [
    ['highContrast', 'High contrast', 'Increase contrast between text and surfaces'],
    ['darkContrast', 'Dark contrast', 'Use a dark, high-contrast reading surface'],
    ['highlightLinks', 'Highlight links', 'Underline and emphasize links'],
    ['invert', 'Invert colors', 'Invert page colors for visual comfort'],
    ['saturation', 'Saturation', 'Increase color separation'],
  ]
  function readPage() {
    if (!('speechSynthesis' in window)) return
    window.speechSynthesis.cancel()
    const content = document.querySelector('main')?.textContent?.replace(/\s+/g, ' ').trim()
    if (content) window.speechSynthesis.speak(new SpeechSynthesisUtterance(content.slice(0, 5000)))
  }
  useEffect(() => {
    const closeOnEscape = (event: KeyboardEvent) => { if (event.key === 'Escape') onClose() }
    document.addEventListener('keydown', closeOnEscape)
    return () => document.removeEventListener('keydown', closeOnEscape)
  }, [onClose])
  return <aside id="accessibility-tools" className="accessibility-panel" aria-label="Accessibility tools">
    <div className="accessibility-panel-header"><div><span className="section-label">READING SUPPORT</span><h2>Accessibility tools</h2></div><button className="panel-close" type="button" onClick={onClose} aria-label="Close accessibility tools">×</button></div>
    <section><div className="accessibility-section-heading"><h3>Color adjustment</h3><span aria-hidden="true">−</span></div><div className="accessibility-grid">{controls.map(([key, label, description]) => <ToggleControl key={key} label={label} description={description} checked={settings[key]} onChange={() => updateSettings({ [key]: !settings[key] })} />)}</div></section>
    <section><div className="accessibility-section-heading"><h3>Text size & reading</h3><span aria-hidden="true">−</span></div><div className="accessibility-grid accessibility-grid-three"><ToggleControl label="Increase text" description="Make service text larger" checked={largeText} onChange={() => { setLargeText(!largeText); setSmallText(false) }} /><ToggleControl label="Decrease text" description="Make service text more compact" checked={smallText} onChange={() => { setSmallText(!smallText); setLargeText(false) }} /><button type="button" className="accessibility-tile" onClick={() => { setLargeText(false); setSmallText(false) }}><span aria-hidden="true">A</span><b>Reset text</b><small>Restore the default text size</small></button><ToggleControl label="Line height" description="Add more space between lines" checked={settings.lineHeight} onChange={() => updateSettings({ lineHeight: !settings.lineHeight })} /><ToggleControl label="Text spacing" description="Add more space between words" checked={settings.textSpacing} onChange={() => updateSettings({ textSpacing: !settings.textSpacing })} /></div></section>
    <section><div className="accessibility-section-heading"><h3>Navigation adjustment</h3><span aria-hidden="true">−</span></div><div className="accessibility-grid accessibility-grid-three"><ToggleControl label="Big cursor" description="Increase pointer size" checked={settings.bigCursor} onChange={() => updateSettings({ bigCursor: !settings.bigCursor })} /><ToggleControl label="Hide images" description="Hide decorative images" checked={settings.hideImages} onChange={() => updateSettings({ hideImages: !settings.hideImages })} /><ToggleControl label="Reduce motion" description="Stop non-essential animation" checked={settings.reduceMotion} onChange={() => updateSettings({ reduceMotion: !settings.reduceMotion })} /><ToggleControl label="Keyboard focus" description="Show a stronger focus indicator" checked={settings.keyboardFocus} onChange={() => updateSettings({ keyboardFocus: !settings.keyboardFocus })} /><button type="button" className="accessibility-tile" onClick={readPage}><span aria-hidden="true">◌</span><b>Read aloud</b><small>Use browser speech support</small></button></div></section>
    <button className="accessibility-reset" type="button" onClick={() => { setLargeText(false); setSmallText(false); updateSettings(defaultAccessibility) }}>Reset accessibility settings</button>
  </aside>
}

function ToggleControl({ label, description, checked, onChange }: { label: string; description: string; checked: boolean; onChange: () => void }) {
  return <button type="button" className={`accessibility-tile${checked ? ' selected' : ''}`} aria-pressed={checked} onClick={onChange}><span aria-hidden="true">{checked ? '✓' : '◐'}</span><b>{label}</b><small>{description}</small></button>
}

const uiCopy: Record<Locale, {
  header: {
    tagline: string
    brandAria: string
    language: string
    how: string
    accessibility: string
    openMenu: string
    closeMenu: string
    nav: Record<'overview' | 'location' | 'capital' | 'business' | 'market' | 'finance' | 'report', string>
  }
  landing: {
    label: string
    title: string
    text: string
    start: string
    proof: string[]
    aboutTitle: string
    aboutText: string
    cards: Array<{ title: string; text: string }>
  }
  banner: Array<{ eyebrow: string; title: string; text: string }>
  trust: Array<{ title: string; text: string }>
  footer: { advisory: string; sources: string; note: string }
}> = {
  en: {
    header: { tagline: 'Independent enterprise decision support', brandAria: 'Go to SmartNivesh overview', language: 'Choose language', how: 'How it works', accessibility: 'Accessibility', openMenu: 'Open navigation menu', closeMenu: 'Close navigation menu', nav: { overview: 'Overview', location: 'Location', capital: 'Capital', business: 'Business', market: 'Market analysis', finance: 'Finance', report: 'Full report' } },
    landing: { label: 'RURAL ENTERPRISE DECISION SUPPORT', title: 'Understand your local market. Plan your finances. Start with confidence.', text: 'Assess your local market, understand project finance, and review indicative public schemes through one guided service.', start: 'Start business assessment', proof: ['Location', 'Business', 'Capital', 'Feasibility and finance'], aboutTitle: 'What is this?', aboutText: 'SmartNivesh is a guided decision-support service for rural entrepreneurs. It combines location context, category evidence, finance planning, repayment readiness, and AI explanations into one practical assessment you can review before investing or applying.', cards: [{ title: 'Local market', text: 'Understand nearby demand and mapped supply signals.' }, { title: 'Business feasibility', text: 'Review evidence, limitations, risks, and opportunities.' }, { title: 'Finance planning', text: 'Estimate margin, project cost, repayment comfort, and scheme routes.' }, { title: 'AI insights', text: 'Ask questions about the report in your selected language.' }] },
    banner: [{ eyebrow: 'LOCAL MARKET', title: 'See the opportunity around you', text: 'Use mapped and verified Census context to make a grounded start.' }, { eyebrow: 'COMPETITOR MAPPING', title: 'Watch your local competition', text: 'Compare location, business category, and mapped evidence before you decide.' }, { eyebrow: 'SMART FEASIBILITY', title: 'Smart business feasibility report', text: 'Review risk calculation, loan planning, government schemes, and AI-powered analysis.' }],
    trust: [{ title: 'Local market assessment', text: 'Based on the area you select' }, { title: 'Business feasibility', text: 'Evidence and limitations shown' }, { title: 'Finance planning', text: 'Caps and contribution included' }],
    footer: { advisory: 'Rural Enterprise Advisory', sources: 'Official sources', note: 'This is an independent decision-support tool and does not represent a government authority. Final scheme eligibility and sanction are determined by the implementing authority.' },
  },
  hi: {
    header: { tagline: 'स्वतंत्र उद्यम निर्णय सहायता', brandAria: 'SmartNivesh ओवरव्यू पर जाएं', language: 'भाषा चुनें', how: 'कैसे काम करता है', accessibility: 'सुगम्यता', openMenu: 'नेविगेशन मेनू खोलें', closeMenu: 'नेविगेशन मेनू बंद करें', nav: { overview: 'ओवरव्यू', location: 'स्थान', capital: 'पूंजी', business: 'व्यवसाय', market: 'बाज़ार विश्लेषण', finance: 'वित्त', report: 'पूरी रिपोर्ट' } },
    landing: { label: 'ग्रामीण उद्यम निर्णय सहायता', title: 'अपने स्थानीय बाज़ार को समझें। अपने वित्त की योजना बनाएं। विश्वास के साथ शुरू करें।', text: 'एक निर्देशित सेवा में स्थानीय बाज़ार, परियोजना वित्त और सार्वजनिक योजनाओं की जानकारी पाएं।', start: 'व्यवसाय आकलन शुरू करें', proof: ['स्थान', 'व्यवसाय', 'पूंजी', 'व्यवहार्यता और वित्त'], aboutTitle: 'यह क्या है?', aboutText: 'SmartNivesh ग्रामीण उद्यमियों के लिए एक निर्देशित निर्णय-सहायता सेवा है। यह स्थान, व्यवसाय श्रेणी, वित्त योजना, पुनर्भुगतान तैयारी और एआई स्पष्टीकरण को एक व्यावहारिक आकलन में जोड़ती है।', cards: [{ title: 'स्थानीय बाज़ार', text: 'पास की मांग और मैप किए गए आपूर्ति संकेत समझें।' }, { title: 'व्यवसाय व्यवहार्यता', text: 'साक्ष्य, सीमाएं, जोखिम और अवसर देखें।' }, { title: 'वित्तीय योजना', text: 'मार्जिन, परियोजना लागत, पुनर्भुगतान सुविधा और योजना मार्ग समझें।' }, { title: 'एआई जानकारी', text: 'चुनी गई भाषा में रिपोर्ट से जुड़े प्रश्न पूछें।' }] },
    banner: [{ eyebrow: 'स्थानीय बाज़ार', title: 'अपने आसपास का अवसर देखें', text: 'सत्यापित जनगणना संदर्भ और मैप किए गए संकेतों से मजबूत शुरुआत करें।' }, { eyebrow: 'प्रतिस्पर्धी मैपिंग', title: 'स्थानीय प्रतिस्पर्धा पर नज़र रखें', text: 'निर्णय से पहले स्थान, श्रेणी और मैप किए गए साक्ष्य की तुलना करें।' }, { eyebrow: 'स्मार्ट व्यवहार्यता', title: 'स्मार्ट व्यवसाय व्यवहार्यता रिपोर्ट', text: 'जोखिम, ऋण योजना, सरकारी योजनाएं और एआई विश्लेषण देखें।' }],
    trust: [{ title: 'स्थानीय बाज़ार आकलन', text: 'आपके चुने हुए क्षेत्र पर आधारित' }, { title: 'व्यवसाय व्यवहार्यता', text: 'साक्ष्य और सीमाएं स्पष्ट' }, { title: 'वित्तीय योजना', text: 'सीमा और योगदान शामिल' }],
    footer: { advisory: 'ग्रामीण उद्यम सलाह', sources: 'आधिकारिक स्रोत', note: 'यह एक स्वतंत्र निर्णय-सहायता उपकरण है और सरकारी प्राधिकरण का प्रतिनिधित्व नहीं करता। अंतिम योजना पात्रता और स्वीकृति संबंधित कार्यान्वयन प्राधिकरण तय करता है।' },
  },
  bn: {
    header: { tagline: 'স্বাধীন উদ্যোগ সিদ্ধান্ত সহায়তা', brandAria: 'SmartNivesh ওভারভিউতে যান', language: 'ভাষা নির্বাচন করুন', how: 'কীভাবে কাজ করে', accessibility: 'অ্যাক্সেসিবিলিটি', openMenu: 'নেভিগেশন মেনু খুলুন', closeMenu: 'নেভিগেশন মেনু বন্ধ করুন', nav: { overview: 'ওভারভিউ', location: 'অবস্থান', capital: 'মূলধন', business: 'ব্যবসা', market: 'বাজার বিশ্লেষণ', finance: 'অর্থায়ন', report: 'পূর্ণ রিপোর্ট' } },
    landing: { label: 'গ্রামীণ উদ্যোগ সিদ্ধান্ত সহায়তা', title: 'স্থানীয় বাজার বুঝুন। অর্থ পরিকল্পনা করুন। আত্মবিশ্বাসের সঙ্গে শুরু করুন।', text: 'একটি নির্দেশিত পরিষেবায় স্থানীয় বাজার, প্রকল্প অর্থায়ন এবং সরকারি প্রকল্প দেখুন।', start: 'ব্যবসা মূল্যায়ন শুরু করুন', proof: ['অবস্থান', 'ব্যবসা', 'মূলধন', 'সম্ভাব্যতা ও অর্থায়ন'], aboutTitle: 'এটি কী?', aboutText: 'SmartNivesh গ্রামীণ উদ্যোক্তাদের জন্য একটি নির্দেশিত সিদ্ধান্ত-সহায়তা পরিষেবা। এটি অবস্থান, ব্যবসা বিভাগ, অর্থ পরিকল্পনা, পরিশোধ প্রস্তুতি এবং AI ব্যাখ্যাকে এক মূল্যায়নে আনে।', cards: [{ title: 'স্থানীয় বাজার', text: 'কাছাকাছি চাহিদা ও সরবরাহের সংকেত বুঝুন।' }, { title: 'ব্যবসার সম্ভাব্যতা', text: 'প্রমাণ, সীমাবদ্ধতা, ঝুঁকি ও সুযোগ দেখুন।' }, { title: 'অর্থ পরিকল্পনা', text: 'মার্জিন, প্রকল্প খরচ ও পরিশোধ স্বাচ্ছন্দ্য বুঝুন।' }, { title: 'AI অন্তর্দৃষ্টি', text: 'নির্বাচিত ভাষায় রিপোর্ট সম্পর্কে প্রশ্ন করুন।' }] },
    banner: [{ eyebrow: 'স্থানীয় বাজার', title: 'আপনার চারপাশের সুযোগ দেখুন', text: 'যাচাইকৃত Census প্রসঙ্গ ও ম্যাপ করা সংকেত ব্যবহার করুন।' }, { eyebrow: 'প্রতিযোগী ম্যাপিং', title: 'স্থানীয় প্রতিযোগিতা দেখুন', text: 'সিদ্ধান্তের আগে অবস্থান, বিভাগ ও ম্যাপ করা প্রমাণ তুলনা করুন।' }, { eyebrow: 'স্মার্ট সম্ভাব্যতা', title: 'স্মার্ট ব্যবসা সম্ভাব্যতা রিপোর্ট', text: 'ঝুঁকি, ঋণ পরিকল্পনা, সরকারি প্রকল্প ও AI বিশ্লেষণ দেখুন।' }],
    trust: [{ title: 'স্থানীয় বাজার মূল্যায়ন', text: 'আপনার নির্বাচিত এলাকার ভিত্তিতে' }, { title: 'ব্যবসার সম্ভাব্যতা', text: 'প্রমাণ ও সীমাবদ্ধতা দেখানো হয়' }, { title: 'অর্থ পরিকল্পনা', text: 'সীমা ও অবদান অন্তর্ভুক্ত' }],
    footer: { advisory: 'গ্রামীণ উদ্যোগ পরামর্শ', sources: 'সরকারি সূত্র', note: 'এটি একটি স্বাধীন সিদ্ধান্ত-সহায়তা টুল এবং সরকারি কর্তৃপক্ষের প্রতিনিধিত্ব করে না। চূড়ান্ত যোগ্যতা ও অনুমোদন সংশ্লিষ্ট কর্তৃপক্ষ নির্ধারণ করে।' },
  },
  mr: {
    header: { tagline: 'स्वतंत्र उद्यम निर्णय सहाय्य', brandAria: 'SmartNivesh ओव्हरव्ह्यूवर जा', language: 'भाषा निवडा', how: 'कसे काम करते', accessibility: 'सुलभता', openMenu: 'नेव्हिगेशन मेनू उघडा', closeMenu: 'नेव्हिगेशन मेनू बंद करा', nav: { overview: 'आढावा', location: 'स्थान', capital: 'भांडवल', business: 'व्यवसाय', market: 'बाजार विश्लेषण', finance: 'वित्त', report: 'पूर्ण अहवाल' } },
    landing: { label: 'ग्रामीण उद्यम निर्णय सहाय्य', title: 'स्थानिक बाजार समजा. वित्ताचे नियोजन करा. आत्मविश्वासाने सुरुवात करा.', text: 'एका मार्गदर्शित सेवेत स्थानिक बाजार, प्रकल्प वित्त आणि सार्वजनिक योजना समजा.', start: 'व्यवसाय मूल्यांकन सुरू करा', proof: ['स्थान', 'व्यवसाय', 'भांडवल', 'व्यवहार्यता आणि वित्त'], aboutTitle: 'हे काय आहे?', aboutText: 'SmartNivesh ही ग्रामीण उद्योजकांसाठी मार्गदर्शित निर्णय-सहाय्य सेवा आहे. ती स्थान, व्यवसाय श्रेणी, वित्त नियोजन, परतफेड तयारी आणि AI स्पष्टीकरण एका मूल्यांकनात आणते.', cards: [{ title: 'स्थानिक बाजार', text: 'जवळची मागणी आणि पुरवठा संकेत समजा.' }, { title: 'व्यवसाय व्यवहार्यता', text: 'पुरावे, मर्यादा, धोके आणि संधी पहा.' }, { title: 'वित्त नियोजन', text: 'मार्जिन, प्रकल्प खर्च आणि परतफेड क्षमता समजा.' }, { title: 'AI अंतर्दृष्टी', text: 'निवडलेल्या भाषेत अहवालाविषयी प्रश्न विचारा.' }] },
    banner: [{ eyebrow: 'स्थानिक बाजार', title: 'आपल्या आसपासची संधी पहा', text: 'सत्यापित Census संदर्भ आणि मॅप केलेले संकेत वापरा.' }, { eyebrow: 'स्पर्धक मॅपिंग', title: 'स्थानिक स्पर्धा पहा', text: 'निर्णयापूर्वी स्थान, श्रेणी आणि पुरावे तुलना करा.' }, { eyebrow: 'स्मार्ट व्यवहार्यता', title: 'स्मार्ट व्यवसाय व्यवहार्यता अहवाल', text: 'जोखीम, कर्ज नियोजन, सरकारी योजना आणि AI विश्लेषण पहा.' }],
    trust: [{ title: 'स्थानिक बाजार मूल्यांकन', text: 'निवडलेल्या क्षेत्रावर आधारित' }, { title: 'व्यवसाय व्यवहार्यता', text: 'पुरावे आणि मर्यादा दाखवल्या जातात' }, { title: 'वित्त नियोजन', text: 'मर्यादा आणि योगदान समाविष्ट' }],
    footer: { advisory: 'ग्रामीण उद्यम सल्ला', sources: 'अधिकृत स्रोत', note: 'हे स्वतंत्र निर्णय-सहाय्य साधन आहे आणि सरकारी प्राधिकरणाचे प्रतिनिधित्व करत नाही. अंतिम पात्रता आणि मंजुरी संबंधित प्राधिकरण ठरवते.' },
  },
  ta: {
    header: { tagline: 'சுயாதீன தொழில் முடிவு ஆதரவு', brandAria: 'SmartNivesh மேலோட்டத்திற்கு செல்லவும்', language: 'மொழியைத் தேர்ந்தெடுக்கவும்', how: 'இது எப்படி வேலை செய்கிறது', accessibility: 'அணுகல்தன்மை', openMenu: 'வழிசெலுத்தல் மெனுவைத் திறக்கவும்', closeMenu: 'வழிசெலுத்தல் மெனுவை மூடவும்', nav: { overview: 'மேலோட்டம்', location: 'இடம்', capital: 'மூலதனம்', business: 'வணிகம்', market: 'சந்தை பகுப்பாய்வு', finance: 'நிதி', report: 'முழு அறிக்கை' } },
    landing: { label: 'கிராமப்புற தொழில் முடிவு ஆதரவு', title: 'உங்கள் உள்ளூர் சந்தையைப் புரிந்து கொள்ளுங்கள். நிதியைத் திட்டமிடுங்கள். நம்பிக்கையுடன் தொடங்குங்கள்.', text: 'ஒரே வழிகாட்டும் சேவையில் சந்தை, திட்ட நிதி மற்றும் பொதுத் திட்டங்களைப் பாருங்கள்.', start: 'வணிக மதிப்பீட்டைத் தொடங்குங்கள்', proof: ['இடம்', 'வணிகம்', 'மூலதனம்', 'சாத்தியம் மற்றும் நிதி'], aboutTitle: 'இது என்ன?', aboutText: 'SmartNivesh கிராமப்புற தொழில்முனைவோருக்கான வழிகாட்டும் முடிவு-ஆதரவு சேவை. இது இடம், வணிக வகை, நிதி திட்டம், திருப்பிச் செலுத்தும் தயார் நிலை மற்றும் AI விளக்கங்களை ஒரே மதிப்பீட்டில் சேர்க்கிறது.', cards: [{ title: 'உள்ளூர் சந்தை', text: 'அருகிலுள்ள தேவை மற்றும் வழங்கல் சைகைகளைப் புரிந்துகொள்ளுங்கள்.' }, { title: 'வணிக சாத்தியம்', text: 'ஆதாரம், வரம்புகள், அபாயங்கள் மற்றும் வாய்ப்புகள் பார்க்கவும்.' }, { title: 'நிதி திட்டம்', text: 'மார்ஜின், திட்ட செலவு மற்றும் திருப்பிச் செலுத்தும் வசதி புரிந்துகொள்ளுங்கள்.' }, { title: 'AI விளக்கங்கள்', text: 'தேர்ந்தெடுத்த மொழியில் அறிக்கை பற்றி கேளுங்கள்.' }] },
    banner: [{ eyebrow: 'உள்ளூர் சந்தை', title: 'உங்களைச் சுற்றியுள்ள வாய்ப்பைப் பாருங்கள்', text: 'சரிபார்க்கப்பட்ட Census சூழல் மற்றும் வரைபட சைகைகளைப் பயன்படுத்துங்கள்.' }, { eyebrow: 'போட்டி வரைபடம்', title: 'உள்ளூர் போட்டியைப் பாருங்கள்', text: 'முடிவிற்கு முன் இடம், வகை மற்றும் ஆதாரங்களை ஒப்பிடுங்கள்.' }, { eyebrow: 'ஸ்மார்ட் சாத்தியம்', title: 'ஸ்மார்ட் வணிக சாத்திய அறிக்கை', text: 'அபாயம், கடன் திட்டம், அரசு திட்டங்கள் மற்றும் AI பகுப்பாய்வைப் பாருங்கள்.' }],
    trust: [{ title: 'உள்ளூர் சந்தை மதிப்பீடு', text: 'நீங்கள் தேர்ந்தெடுத்த பகுதியின் அடிப்படையில்' }, { title: 'வணிக சாத்தியம்', text: 'ஆதாரம் மற்றும் வரம்புகள் காட்டப்படும்' }, { title: 'நிதி திட்டம்', text: 'வரம்புகள் மற்றும் பங்களிப்பு சேர்க்கப்பட்டது' }],
    footer: { advisory: 'கிராமப்புற தொழில் ஆலோசனை', sources: 'அதிகாரப்பூர்வ ஆதாரங்கள்', note: 'இது சுயாதீன முடிவு-ஆதரவு கருவி; அரசு அதிகாரத்தை பிரதிநிதித்துவப்படுத்தாது. இறுதி தகுதி மற்றும் அனுமதி சம்பந்தப்பட்ட அதிகாரத்தால் தீர்மானிக்கப்படும்.' },
  },
}

function FeatureBanner({ locale }: { locale: Locale }) {
  const copy = uiCopy[locale].banner
  const slides = [
    { image: bannerFinanceReadiness, ...copy[2] },
    { image: bannerBusinessPlanning, ...copy[1] },
    { image: bannerMarketConfidence, ...copy[0] },
  ]
  const [current, setCurrent] = useState(0)
  useEffect(() => {
    if (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) return
    const timer = window.setInterval(() => setCurrent((value) => (value + 1) % slides.length), 5500)
    return () => window.clearInterval(timer)
  }, [slides.length])
  const slide = slides[current]
  return <section className="feature-banner" aria-roledescription="carousel" aria-label="SmartNivesh service features"><div className="feature-banner-image" key={slide.image} style={{ backgroundImage: `url(${slide.image})` }} aria-hidden="true" /><div className="feature-banner-copy"><span>{slide.eyebrow}</span><h2>{slide.title}</h2><p>{slide.text}</p><div className="feature-banner-controls"><button type="button" onClick={() => setCurrent((current + slides.length - 1) % slides.length)} aria-label="Previous feature"><ChevronLeft size={18} /></button><div role="tablist" aria-label="Feature slides">{slides.map((item, index) => <button key={item.title} role="tab" aria-selected={current === index} aria-label={`Show feature ${index + 1}`} onClick={() => setCurrent(index)} />)}</div><button type="button" onClick={() => setCurrent((current + 1) % slides.length)} aria-label="Next feature"><ChevronRight size={18} /></button></div></div></section>
}

function StartScreen({ onStart, locale }: { onStart: () => void; locale: Locale }) {
  const copy = uiCopy[locale].landing
  return <main id="main-content"><FeatureBanner locale={locale} /><section className="start-hero overview-intro"><div className="hero-copy"><span className="section-label">{copy.label}</span><h1>{copy.title}</h1><p>{copy.text}</p><div className="hero-actions"><button className="primary-button" onClick={onStart}>{copy.start} <ArrowRight size={18} /></button></div><div className="hero-proof">{copy.proof.map((label, index) => <Fragment key={label}><span>{label}</span><b>{index + 1}</b></Fragment>)}</div></div></section><section className="about-platform" aria-labelledby="about-platform-title"><div><span className="section-label">{copy.aboutTitle}</span><h2 id="about-platform-title">{copy.aboutTitle}</h2><p>{copy.aboutText}</p></div><div className="about-grid">{copy.cards.map((card, index) => <article key={card.title}><span>{index === 0 ? <MapPin size={18} /> : index === 1 ? <BarChart3 size={18} /> : index === 2 ? <IndianRupee size={18} /> : <Info size={18} />}</span><strong>{card.title}</strong><p>{card.text}</p></article>)}</div></section><section className="trust-row">{uiCopy[locale].trust.map((item, index) => <article key={item.title}>{index === 0 ? <MapPin /> : index === 1 ? <BarChart3 /> : <IndianRupee />}<div><strong>{item.title}</strong><span>{item.text}</span></div></article>)}</section><Disclaimer locale={locale} /></main>
}

function Footer({ locale }: { locale: Locale }) {
  const copy = uiCopy[locale].footer
  return <footer className="site-footer"><div><strong>SmartNivesh</strong><span>{copy.advisory}</span></div><nav className="footer-sources" aria-label="Official data and scheme sources"><strong>{copy.sources}</strong><div><a href="https://udyamregistration.gov.in/" target="_blank" rel="noreferrer">MSME Udyam Registration</a><a href="https://msme.gov.in/" target="_blank" rel="noreferrer">Ministry of MSME</a><a href="https://www.data.gov.in/" target="_blank" rel="noreferrer">Open Government Data</a><a href="https://censusindia.gov.in/" target="_blank" rel="noreferrer">Census of India</a><a href="https://kviconline.gov.in/pmegpeportal/" target="_blank" rel="noreferrer">PMEGP portal</a><a href="https://www.mudra.org.in/" target="_blank" rel="noreferrer">Pradhan Mantri MUDRA Yojana</a></div></nav><p>{copy.note}</p></footer>
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
  return <div className="step-content"><StepIntro number="03" title="Choose your business category" text="Select the closest supported category. Every category has a configured OpenStreetMap mapping rule for live competitor evidence." /><div className="category-grid" role="radiogroup" aria-label="Business category">{categories.map((category) => <label key={category.id} data-theme={category.theme} className={categoryId === category.id ? 'category-card selected' : 'category-card'}><input type="radio" name="category" value={category.id} checked={categoryId === category.id} onChange={() => setCategoryId(category.id)} /><span className="category-icon" aria-hidden="true">{category.icon}</span><strong>{category.name}</strong><small>{category.group}</small><span className="radio-mark">{categoryId === category.id && <Check size={14} />}</span></label>)}</div><section className="reference-price-panel"><div><Badge kind="USER INPUT" /><h3>Optional comparable reference price</h3><p>Enter your current menu/list price, a supplier quotation, or another comparable price per sale or unit. The calculator applies the verified rural-MPCE multiplier; it does not call a market-price API or invent a category price.</p></div><label className="form-field" htmlFor="reference-price"><span>Reference price <small>Optional · ₹ per sale / unit</small></span><div className="compact-currency"><b>₹</b><input id="reference-price" type="number" min="1" step="0.01" inputMode="decimal" value={referencePrice || ''} onChange={(event) => setReferencePrice(Math.max(0, Number(event.target.value) || 0))} placeholder="e.g. 100" /></div></label></section><div className="info-callout"><Info size={17} /><p>These micro-enterprise categories use documented OpenStreetMap tags for competitor mapping. Results show observed mapped features, never an assumed competitor count.</p></div></div>
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
  return <><GeospatialEvidenceMap competitors={competitors} demographics={demographics} radius={radius} /><section className="visual-data-panel" aria-label="Visual evidence overview"><div className="visual-data-heading"><div><span className="section-label">EVIDENCE AT A GLANCE</span><h3>What the available data is saying</h3><p>Supply is shown as mapped businesses. Population stays at its verified Census scope; it is not a radius estimate.</p></div><Badge kind={competitors?.status === 'AVAILABLE' ? 'PUBLIC DATA' : 'VERIFICATION REQUIRED'} /></div><div className="visual-data-grid"><div className="supply-chart"><div className="chart-title"><span>Mapped similar businesses</span><strong>{competitors?.mapped_competitor_count ?? '—'}</strong></div>{bars.map((bar) => <div className="data-bar-row" key={bar.label}><span>{bar.label}</span><div className="data-bar-track"><i style={{ width: `${Math.max(bar.width, supply && bar.value ? 8 : 0)}%` }} /></div><b>{bar.value ?? '—'}</b></div>)}<small>Search radius selected: {radius} km</small></div><div className="signal-stack"><article><span>Rural affordability position</span><strong>{affordability != null ? `${affordability}%` : 'Unavailable'}</strong><div className="signal-meter"><i style={{ width: `${Math.min(100, Math.max(0, affordability ?? 0))}%` }} /></div><small>State rural MPCE compared with the all-India rural baseline</small></article><article><span>Verified population baseline</span><strong>{populationLabel}</strong><small>{demographics?.status === 'AVAILABLE' || competitors?.demographics?.total_population ? 'Census 2011 sub-district residents' : 'No verified demographic record yet'}</small></article></div></div></section></>
}

function GeospatialEvidenceMap({ competitors, demographics, radius }: { competitors: CompetitorMapping | null; demographics: LocalDemographics | null; radius: number }) {
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [mapRadius, setMapRadius] = useState(radius)
  const point = competitors?.analysis_point
  if (!point) return <section className="geo-map-empty" data-pdf-exclude="true"><MapPin size={28} /><div><strong>Geographic view unavailable</strong><p>A verified analysis coordinate is required before map tiles and business markers can be shown.</p></div></section>
  const zoom = mapRadius <= 2 ? 14 : mapRadius <= 5 ? 13 : 12
  const world = (latitude: number, longitude: number) => {
    const scale = 256 * 2 ** zoom
    const sin = Math.sin(latitude * Math.PI / 180)
    return { x: (longitude + 180) / 360 * scale, y: (0.5 - Math.log((1 + sin) / (1 - sin)) / (4 * Math.PI)) * scale }
  }
  const center = world(point.latitude, point.longitude)
  const centerTileX = Math.floor(center.x / 256)
  const centerTileY = Math.floor(center.y / 256)
  const tiles = [] as Array<{ x: number; y: number; left: number; top: number }>
  for (let dy = -2; dy <= 2; dy += 1) for (let dx = -3; dx <= 3; dx += 1) {
    const x = centerTileX + dx; const y = centerTileY + dy
    tiles.push({ x, y, left: 50 + ((x * 256 - center.x) / 1024) * 100, top: 50 + ((y * 256 - center.y) / 512) * 100 })
  }
  const visible = (competitors?.mapped_competitors ?? [])
    .filter((item) => item.latitude != null && item.longitude != null && (item.distance_km == null || item.distance_km <= mapRadius))
    .map((item, index) => ({
      ...item,
      osm_id: item.osm_id || item.source_feature_id || `${item.provider || 'mapped'}-${item.latitude}-${item.longitude}-${index}`,
    }))
  const markerPosition = (latitude: number, longitude: number) => { const p = world(latitude, longitude); return { left: `${50 + ((p.x - center.x) / 1024) * 100}%`, top: `${50 + ((p.y - center.y) / 512) * 100}%` } }
  const metresPerPixel = 156543.03392 * Math.cos(point.latitude * Math.PI / 180) / 2 ** zoom
  const radiusPixels = Math.min(430, mapRadius * 1000 / metresPerPixel)
  const selected = visible.find((item) => item.osm_id === selectedId)
  const population = competitors?.demographics?.total_population ?? demographics?.total_population
  return <section className="geo-evidence" data-pdf-exclude="true" aria-labelledby="geo-evidence-title"><div className="geo-map-heading"><div><span className="section-label">GEOGRAPHIC EVIDENCE</span><h3 id="geo-evidence-title"><MapPin size={21} /> Active Business Intelligence Map</h3><p>{competitors.block_name} · Actual mapped coordinates from the completed lookup</p></div><div className="catchment-tabs" aria-label={`Current catchment ${mapRadius} kilometres`}><span>Catchment</span>{[2, 5, 10].map((value) => <button type="button" key={value} className={mapRadius === value ? 'active' : ''} aria-pressed={mapRadius === value} onClick={() => { setMapRadius(value); setSelectedId(null) }}>{value} km</button>)}</div></div><div className="geo-map" role="region" aria-label={`Map centred on the proposed business point with ${visible.length} mapped competitor markers inside ${mapRadius} kilometres`}><div className="map-tiles" aria-hidden="true">{tiles.map((tile) => <img key={`${tile.x}-${tile.y}`} src={`https://tile.openstreetmap.org/${zoom}/${tile.x}/${tile.y}.png`} alt="" draggable={false} style={{ left: `${tile.left}%`, top: `${tile.top}%` }} />)}</div><div className="catchment-ring" aria-hidden="true" style={{ width: `${radiusPixels / 512 * 100}%`, height: `${radiusPixels / 256 * 100}%` }} /><div className="map-legend"><strong>GIS MAP LAYERS</strong><span><i className="proposed" /> Proposed business point</span><span><i className="competitor" /> Mapped competitors</span><span><i className="catchment" /> {mapRadius} km catchment</span></div><button className="proposed-marker" type="button" style={{ left: '50%', top: '50%' }} aria-label="Proposed business analysis point"><Store size={21} /><b>Proposed business</b></button>{visible.map((item, index) => <button key={`${item.provider}-${item.osm_id}`} type="button" className={`competitor-marker${selectedId === item.osm_id ? ' selected' : ''}`} style={markerPosition(item.latitude!, item.longitude!)} onClick={() => setSelectedId(item.osm_id)} aria-label={`${item.name || `Mapped competitor ${index + 1}`}${item.distance_km != null ? `, ${item.distance_km.toFixed(1)} kilometres away` : ''}`}><span>{index + 1}</span></button>)}{selected && <article className="map-popover"><strong>{selected.name || 'Unnamed mapped business'}</strong><span>{selected.provider?.replace('_', ' ') || 'Mapped source'}{selected.distance_km != null ? ` · ${selected.distance_km.toFixed(1)} km` : ''}</span>{selected.latitude != null && selected.longitude != null && <a href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(`${selected.latitude},${selected.longitude}`)}`} target="_blank" rel="noreferrer">Open map <ExternalLink size={13} /></a>}</article>}<a className="osm-attribution" href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">© OpenStreetMap contributors</a></div><div className="catchment-summary"><div><span>Catchment</span><strong>{mapRadius} km radius</strong></div><div><span>Mapped competitors</span><strong>{visible.length}</strong></div>{population != null && <div><span>Census population scope</span><strong>{population.toLocaleString('en-IN')}</strong></div>}<div><span>Data confidence</span><strong>{competitors?.confidence || 'Unknown'}</strong></div></div><p className="map-integrity-note"><Info size={14} /> Mapped records are observed provider data, not a complete register of formal or informal businesses. Map centre: {point.source}.</p></section>
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
  return <section className="finance-input-panel"><div className="panel-heading"><div><Badge kind={complete ? 'CALCULATED' : 'VERIFICATION REQUIRED'} /><h3>Financial feasibility and scenarios</h3><p>Repayment Coverage, downside scenarios and financing recommendations use only the figures you enter.</p></div></div>{complete ? <><div className="financial-grid"><Metric label="Operating profit" value={formatINR(result.costs?.operating_profit ?? 0)} /><Metric label="Repayment Coverage" value={`${result.repayment_metrics?.repayment_coverage ?? 0}×`} note="Operating profit ÷ EMI; not formal DSCR" /><Metric label="Monthly cash after EMI" value={formatINR(result.repayment_metrics?.monthly_cash_surplus ?? 0)} /><Metric label="Working-capital requirement" value={result.working_capital?.requirement != null ? formatINR(result.working_capital.requirement) : 'Unknown'} /><Metric label="Financial feasibility" value={result.feasibility?.status ?? 'UNKNOWN'} /><Metric label="Recommended loan" value={result.recommendation?.recommended_loan != null ? formatINR(result.recommendation.recommended_loan) : 'Not recommended'} /></div><FinancialRiskDashboard result={result} /><div className="scenario-grid">{result.scenario_results.map((scenario) => <article className="report-metric" key={scenario.name}><span>{scenario.name}</span><strong>{scenario.repayment_coverage != null ? `${scenario.repayment_coverage}× coverage` : 'Unknown'}</strong><small>{scenario.monthly_cash_after_emi != null ? `${formatINR(scenario.monthly_cash_after_emi)} after EMI` : 'Needs complete inputs'}</small></article>)}</div></> : <div className="info-callout"><Info size={17} /><p>Enter monthly revenue plus both fixed and variable costs to calculate repayment coverage, scenarios and recommended financing. Missing figures remain UNKNOWN.</p></div>}<details className="plain-details"><summary>Financial methodology and limitations</summary><ul>{[...result.assumptions, ...result.limitations].map((item) => <li key={item}>{item}</li>)}</ul></details></section>
}

function FinancialRiskDashboard({ result }: { result: FinancialIntelligence }) {
  const feasibility = result.feasibility
  const level = feasibility?.status ?? 'UNKNOWN'
  const downside = feasibility?.downside_status === 'POSITIVE' ? 'Cash remains positive' : feasibility?.downside_status === 'NEGATIVE' ? 'Cash turns negative' : 'Needs complete inputs'
  const riskText = level === 'COMFORTABLE'
    ? 'The current figures cover the illustrated repayment amount. Keep validating revenue, costs and local demand.'
    : level === 'TIGHT'
      ? 'The current plan has limited room for shocks. Reduce fixed costs, improve margin or lower the funding need before proceeding.'
      : level === 'UNAFFORDABLE'
        ? 'The entered cash flow does not comfortably support the illustrated repayment. Rework the operating plan before applying.'
        : 'Add revenue plus fixed and variable costs to calculate this risk signal.'
  return <section className="financial-risk-dashboard" aria-label="Financial risk readiness"><div className="risk-dashboard-gauge"><span className="section-label">RISK READINESS</span><h4>Repayment risk</h4><RiskGauge level={level} expanded /></div><div className="risk-dashboard-detail"><strong>{riskText}</strong><div className="risk-thread-list"><article><span>Base repayment coverage</span><b>{feasibility?.repayment_coverage != null ? `${feasibility.repayment_coverage}×` : 'Unknown'}</b><small>Operating profit ÷ illustrated EMI</small></article><article><span>Downside case</span><b>{downside}</b><small>{feasibility?.conservative_repayment_coverage != null ? `${feasibility.conservative_repayment_coverage}× conservative coverage` : 'Conservative scenario is not available'}</small></article><article><span>Cash after EMI</span><b>{feasibility?.monthly_cash_surplus != null ? formatINR(feasibility.monthly_cash_surplus) : 'Unknown'}</b><small>Based only on your entered revenue and costs</small></article></div></div></section>
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

function ReportPage({ locale, location, category, financial, financialIntelligence, competitors, demographics, marketValue, onRecalculate }: { locale: Locale; location: string; category: string; financial: FinancialRoadmap | null; financialIntelligence: FinancialIntelligence | null; competitors: CompetitorMapping | null; demographics: LocalDemographics | null; marketValue: ProductMarketValue | null; onRecalculate: () => void }) {
  const assessment = financial?.assessment
  const cashflow = financial?.cashflow
  const financialFit = assessment?.status === 'VALID'
  return <main className="report-page page-wrap"><div className="report-toolbar"><button className="quiet-button" onClick={onRecalculate}><ArrowLeft size={16} /> Recalculate</button><div><button className="secondary-button" onClick={() => window.print()}><Printer size={16} /> Print / Save PDF</button><button className="primary-button" onClick={() => window.print()}><FileDown size={16} /> Download report</button></div></div><header className="report-header"><div><span className="section-label">LOCAL FEASIBILITY REPORT</span><h1>{category} enterprise assessment</h1><p><MapPin size={16} /> {location || 'Location not specified'}</p></div><dl><div><dt>Assessment date</dt><dd>{new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium' }).format(new Date())}</dd></div><div><dt>Data status</dt><dd><Badge kind={financial ? 'VERIFIED GOVT RULE' : 'VERIFICATION REQUIRED'} /></dd></div></dl></header><Disclaimer />
    <ReportSection title="Executive summary" eyebrow="01 · DECISION SNAPSHOT"><div className="executive-grid"><article className="executive-primary"><span>FINANCIAL FIT</span><strong>{financialFit ? 'Government-rule roadmap ready' : 'Action required'}</strong><p>{financialFit ? `${assessment?.scheme_name} provides the baseline. All programme routes require eligibility and sanction verification.` : assessment?.message || 'The financial service did not return a roadmap.'}</p></article><Metric label="Local Census baseline" value={demographics?.total_population?.toLocaleString('en-IN') ?? 'Unavailable'} note={demographics?.status === 'AVAILABLE' ? 'Census 2011 sub-district residents' : 'No verified local demographic record'} /><Metric label="Competition signal" value={competitors?.mapped_competitor_count == null ? 'Unavailable' : `${competitors.mapped_competitor_count} mapped`} note="OpenStreetMap coverage varies" /><Metric label="Next action" value="Verify locally" note="Demand, quotations and eligibility" /></div><VisualDataPanel competitors={competitors} demographics={demographics} marketValue={marketValue} radius={competitors?.analysis_scope === 'VILLAGE' ? 5 : 10} /></ReportSection>
    <ReportSection title="Market reach and opportunity" eyebrow="02 · LOCAL EVIDENCE"><FeasibilityEvidence competitors={competitors} demographics={demographics} marketValue={marketValue} /></ReportSection>
    <ReportSection title="Competitor mapping" eyebrow="03 · EXISTING SUPPLY"><div className="competitor-report"><div className="big-stat"><strong>{competitors?.mapped_competitor_count ?? '—'}</strong><span>mapped similar businesses in the selected search radius</span><Badge kind={competitors?.status === 'AVAILABLE' ? 'PUBLIC DATA' : 'VERIFICATION REQUIRED'} /></div><div><h3>Competition evidence</h3><div className="financial-grid"><Metric label="Competitors per 1,000 residents" value={competitors?.competitors_per_1000_residents?.toLocaleString('en-IN') ?? 'Unavailable'} note="Mapped businesses ÷ Census 2011 block population × 1,000" /><Metric label="Census 2011 sub-district residents" value={(competitors?.demographics?.total_population ?? demographics?.total_population)?.toLocaleString('en-IN') ?? 'Unavailable'} note="Local Census demographic baseline" /><Metric label="Census 2011 households" value={demographics?.households?.toLocaleString('en-IN') ?? 'Unavailable'} note="Local Census household baseline" /></div><h3>Mapped businesses</h3><p>Select any business row to open its mapped location in Google Maps.</p>{competitors?.mapped_competitors?.length ? <ul className="competitor-list">{competitors.mapped_competitors.slice(0, 12).map((item) => { const query = item.latitude != null && item.longitude != null ? `${item.latitude},${item.longitude}` : item.name || ''; const mapsUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(query)}`; return <li key={`${item.provider}-${item.osm_id}`}><a className="competitor-map-link" href={mapsUrl} target="_blank" rel="noreferrer" aria-label={`Open ${item.name || 'mapped business'} in Google Maps`}><Store size={16} /><span><b>{item.name || 'Unnamed mapped business'}</b><small>{item.provider === 'GOOGLE_PLACES' ? 'Google Places' : item.provider === 'GEOAPIFY' ? 'Geoapify / OpenStreetMap' : 'OpenStreetMap'} · {item.distance_km != null ? `${item.distance_km.toFixed(1)} km away` : 'distance unavailable'}</small></span><ExternalLink size={17} aria-hidden="true" /></a></li> })}</ul> : null}<h3>Important limitation</h3><p>{competitors?.limitations?.[0] || 'No completed competitor result is available. Mapped records may be incomplete.'}</p></div></div><SourceList sources={[...(competitors?.data_provenance ?? []), ...(demographics?.data_provenance ?? [])]} /></ReportSection>
    <ReportSection title="Product market value" eyebrow="04 · REGIONAL PRICE REFERENCE"><ProductMarketValuePanel result={marketValue} /></ReportSection>
    <ReportSection title="SWOT and risk watch" eyebrow="05 · EVIDENCE-LED DECISION SUPPORT"><SwotAndThreats competitors={competitors} marketValue={marketValue} /><RiskAndOpportunityGuide competitors={competitors} demographics={demographics} /></ReportSection>
    <ReportSection title="Financial structure" eyebrow="06 · GOVERNMENT-RULE BASELINE">{financialFit ? <><div className="finance-summary"><div className="finance-lead"><span>PUBLISHED BASELINE</span><h3>{assessment?.scheme_name}</h3><p>Calculated with the verified registry; eligibility and channel terms are not presumed.</p></div><div className="financial-grid"><Metric label="Available margin" value={formatINR(assessment?.margin_capital ?? 0)} /><Metric label="Project cost" value={formatINR(assessment?.project_cost ?? 0)} /><Metric label="Published-cap financing" value={formatINR(assessment?.eligible_loan ?? 0)} /><Metric label="Required contribution" value={formatINR(assessment?.required_own_contribution ?? 0)} /></div></div>{financial && <FinancialCompositionChart financial={financial} />}</> : <UnavailablePanel title="No financial baseline" text={assessment?.message || 'Recalculate after the financial service is available.'} />}<>{financial && <GovernmentSchemeRouter routes={financial.routes} />}</></ReportSection>
    {financialFit && <ReportSection title="Quarterly repayment planner" eyebrow="07 · ILLUSTRATIVE REPAYMENT"><div className="repayment-layout"><div className="emi-card"><span>Monthly planning equivalent</span><strong>{formatINR(assessment?.estimated_monthly_instalment ?? 0)}</strong><small>for {assessment?.repayment_months} repayment months</small></div><div className="financial-grid"><Metric label="Quarterly instalment illustration" value={formatINR(assessment?.estimated_quarterly_instalment ?? 0)} /><Metric label="Repayment quarters" value={`${assessment?.repayment_quarters ?? 0}`} /><Metric label="Total repayment illustration" value={formatINR(assessment?.estimated_total_repayment ?? 0)} /><Metric label="Total interest illustration" value={formatINR(assessment?.estimated_total_interest ?? 0)} /></div></div><div className="timeline"><div style={{ flex: assessment?.moratorium_months ?? 1 }}><span>Published moratorium</span><strong>{assessment?.moratorium_months} months</strong></div><div className="repay" style={{ flex: assessment?.repayment_months ?? 1 }}><span>Illustrative repayment</span><strong>{assessment?.repayment_quarters} quarters</strong></div></div><p className="method-note"><Badge kind="ASSUMPTION" /> {assessment?.repayment_frequency_note}</p></ReportSection>}
    <ReportSection title="Cash-flow and working-capital check" eyebrow="08 · USER-SUPPLIED BUSINESS PLAN">{cashflow?.status === 'AVAILABLE' ? <div className="financial-grid"><Metric label="Monthly operating cost" value={formatINR(cashflow.monthly_operating_cost ?? 0)} /><Metric label="Cash before debt" value={formatINR(cashflow.monthly_cash_before_debt ?? 0)} /><Metric label="Cash after baseline EMI" value={formatINR(cashflow.monthly_cash_after_baseline_instalment ?? 0)} /><Metric label="User-chosen cash reserve" value={formatINR(cashflow.operating_reserve_requirement ?? 0)} /></div> : <UnavailablePanel title="Operating affordability requires your actual figures" text={cashflow?.limitations.slice(1).join(' ') || 'Return to Finance and provide your own costs, expected revenue and reserve months. No default business cost is applied.'} />}</ReportSection>
    <ReportSection title="Financial feasibility scenarios" eyebrow="09 · DETERMINISTIC FINANCIAL INTELLIGENCE"><ScenarioComparisonChart result={financialIntelligence} /><FinancialIntelligencePanel result={financialIntelligence} /></ReportSection>
    <ReportSection title="Action plan" eyebrow="10 · APPLICATION READINESS"><ol className="action-list">{(financial?.readiness_actions ?? ['Collect current equipment, fit-out and supplier quotations.', 'Separate working capital from capital expenditure in a project report.', 'Verify scheme eligibility and apply only through the official government channel.']).map((item, i) => <li key={item}><span>{i + 1}</span>{item}</li>)}</ol></ReportSection>
    <ReportSection title="Ask about this assessment" eyebrow="11 · EXPLANATIONS" pdfExclude><AssessmentAssistant locale={locale} context={{ location, business: category, demographics: demographics?.total_population ? { population_2011: demographics.total_population, households_2011: demographics.households } : 'UNKNOWN', competition: competitors ? { status: competitors.status, mapped_similar_businesses: competitors.mapped_competitor_count ?? 'UNKNOWN', radius_supply: competitors.radius_supply ?? 'UNKNOWN', limitations: competitors.limitations } : 'UNKNOWN', financial: financialIntelligence ? { feasibility: financialIntelligence.feasibility?.status, repayment_coverage: financialIntelligence.repayment_metrics?.repayment_coverage, recommended_loan: financialIntelligence.recommendation?.recommended_loan } : 'UNKNOWN', limitations: [...(competitors?.limitations ?? []), ...(demographics?.limitations ?? [])], next_actions: financial?.readiness_actions ?? [] }} /></ReportSection>
    <MethodologyPanel competitors={competitors} marketValue={marketValue} financial={financial} />
  </main>
}

function FinancialCompositionChart({ financial }: { financial: FinancialRoadmap }) {
  const assessment = financial.assessment
  const projectCost = Math.max(assessment.project_cost, 1)
  const own = Math.min(projectCost, Math.max(0, assessment.margin_capital))
  const financed = Math.min(Math.max(projectCost - own, 0), Math.max(0, assessment.eligible_loan ?? assessment.requested_loan))
  const gap = Math.max(0, projectCost - own - financed)
  const parts = [
    { label: 'Own margin', value: own, className: 'own' },
    { label: 'Published-cap financing', value: financed, className: 'financed' },
    { label: 'Uncovered amount', value: gap, className: 'gap' },
  ].filter((item) => item.value > 0)
  const ownPct = own / projectCost * 100
  const financedPct = financed / projectCost * 100
  return <section className="composition-chart" aria-labelledby="composition-title"><div className="chart-heading"><div><span className="section-label">CAPITAL COMPOSITION</span><h3 id="composition-title">How the indicative project cost is funded</h3></div><Badge kind="CALCULATED" /></div><div className="composition-visual"><div className="funding-donut" role="img" aria-label={parts.map((item) => `${item.label}: ${formatINR(item.value)}`).join('; ')} style={{ background: `conic-gradient(var(--navy) 0 ${ownPct}%, var(--green) ${ownPct}% ${ownPct + financedPct}%, var(--amber) ${ownPct + financedPct}% 100%)` }}><span><strong>{formatINR(projectCost)}</strong><small>Total project cost</small></span></div><div className="composition-detail"><div className="composition-track" aria-hidden="true">{parts.map((item) => <i key={item.label} className={item.className} style={{ width: `${(item.value / projectCost) * 100}%` }} />)}</div><div className="composition-legend">{parts.map((item) => <div key={item.label}><i className={item.className} /><span>{item.label}</span><strong>{formatINR(item.value)}</strong><small>{Math.round((item.value / projectCost) * 100)}%</small></div>)}</div></div></div></section>
}

function ScenarioComparisonChart({ result }: { result: FinancialIntelligence | null }) {
  const scenarios = (result?.scenario_results ?? []).filter((item) => item.monthly_revenue != null || item.monthly_operating_cost != null || item.monthly_cash_after_emi != null)
  if (!scenarios.length) return <UnavailablePanel title="Scenario chart needs your business figures" text="Add expected revenue and monthly costs in Finance to compare conservative, base and optimistic cases." />
  const max = Math.max(1, ...scenarios.flatMap((item) => [item.monthly_revenue ?? 0, item.monthly_operating_cost ?? 0, Math.max(0, item.monthly_cash_after_emi ?? 0)]))
  return <section className="scenario-chart" aria-labelledby="scenario-chart-title"><div className="chart-heading"><div><span className="section-label">MONTHLY COMPARISON</span><h3 id="scenario-chart-title">Revenue, operating cost and cash after EMI</h3><p>Each bar uses the same rupee scale across all three planning cases.</p></div><Badge kind="CALCULATED" /></div><div className="scenario-legend" aria-hidden="true"><span><i className="revenue" /> Revenue</span><span><i className="cost" /> Operating cost</span><span><i className="surplus" /> Cash after EMI</span></div><div className="scenario-plot">{scenarios.map((item) => <article key={item.name}><strong>{item.name.charAt(0) + item.name.slice(1).toLowerCase()}</strong><div className="scenario-bars"><ChartBar label="Revenue" value={item.monthly_revenue} max={max} className="revenue" /><ChartBar label="Operating cost" value={item.monthly_operating_cost} max={max} className="cost" /><ChartBar label="Cash after EMI" value={item.monthly_cash_after_emi} max={max} className="surplus" /></div></article>)}</div><p className="chart-footnote">Negative post-EMI cash is shown as ₹0 in bar length and remains visible in the value label.</p></section>
}

function ChartBar({ label, value, max, className }: { label: string; value?: number; max: number; className: string }) {
  const width = value == null ? 0 : Math.max(0, (value / max) * 100)
  return <div className="chart-bar"><span>{label}</span><div><i className={className} style={{ width: `${width}%` }} /></div><b>{value == null ? 'Unavailable' : formatINR(value)}</b></div>
}

function AssessmentAssistant({ locale, context }: { locale: Locale; context: Record<string, unknown> }) {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState<AssessmentAssistantResponse | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const assistantCopy = {
    en: { intro: 'Ask in English about the evidence already shown in this report. The assistant cannot create new local facts or change financial calculations.', placeholder: 'Ask a question about this assessment', loading: 'Answering...', ask: 'Ask SmartNivesh', presets: ['What is the most important risk for me?', 'What should I verify before investing?', 'What is my best next step?'] },
    hi: { intro: 'इस रिपोर्ट में दिखाए गए साक्ष्य के बारे में हिंदी में पूछें। सहायक नए स्थानीय तथ्य नहीं बना सकता और वित्तीय गणना नहीं बदल सकता।', placeholder: 'अपना प्रश्न लिखें', loading: 'उत्तर दे रहा है...', ask: 'SmartNivesh से पूछें', presets: ['मेरे लिए सबसे महत्वपूर्ण जोखिम क्या है?', 'निवेश से पहले मुझे क्या जांचना चाहिए?', 'अगला सही कदम क्या है?'] },
    bn: { intro: 'এই রিপোর্টে দেখানো প্রমাণ সম্পর্কে বাংলায় প্রশ্ন করুন। সহায়ক নতুন স্থানীয় তথ্য তৈরি করতে বা আর্থিক হিসাব বদলাতে পারে না।', placeholder: 'এই মূল্যায়ন সম্পর্কে প্রশ্ন করুন', loading: 'উত্তর তৈরি হচ্ছে...', ask: 'SmartNivesh-কে জিজ্ঞাসা করুন', presets: ['আমার জন্য সবচেয়ে গুরুত্বপূর্ণ ঝুঁকি কী?', 'বিনিয়োগের আগে কী যাচাই করব?', 'আমার পরবর্তী সেরা পদক্ষেপ কী?'] },
    mr: { intro: 'या अहवालात दाखवलेल्या पुराव्यांबद्दल मराठीत विचारा. सहाय्यक नवीन स्थानिक तथ्य तयार करू शकत नाही किंवा आर्थिक गणना बदलू शकत नाही.', placeholder: 'या मूल्यांकनाबद्दल प्रश्न विचारा', loading: 'उत्तर देत आहे...', ask: 'SmartNivesh ला विचारा', presets: ['माझ्यासाठी सर्वात महत्त्वाचा धोका कोणता?', 'गुंतवणुकीपूर्वी मी काय पडताळावे?', 'माझे पुढचे सर्वोत्तम पाऊल कोणते?'] },
    ta: { intro: 'இந்த அறிக்கையில் காட்டப்பட்ட ஆதாரங்கள் பற்றி தமிழில் கேளுங்கள். உதவியாளர் புதிய உள்ளூர் தகவல் உருவாக்கவோ நிதி கணக்குகளை மாற்றவோ முடியாது.', placeholder: 'இந்த மதிப்பீடு பற்றி கேள்வி கேளுங்கள்', loading: 'பதில் வருகிறது...', ask: 'SmartNivesh-யிடம் கேளுங்கள்', presets: ['எனக்கு மிக முக்கியமான அபாயம் என்ன?', 'முதலீட்டுக்கு முன் என்ன சரிபார்க்க வேண்டும்?', 'எனது அடுத்த சிறந்த படி என்ன?'] },
  }[locale]
  async function ask() {
    if (question.trim().length < 2) return
    setLoading(true); setError(''); setAnswer(null)
    try { setAnswer(await askAssessmentAssistant({ question: question.trim(), language: locale, assessment_context: context })) }
    catch (err) { setError(err instanceof Error ? err.message : 'The explanation service is unavailable.') }
    finally { setLoading(false) }
  }
  return <section className="assessment-assistant"><p>{assistantCopy.intro}</p><div className="assistant-presets">{assistantCopy.presets.map((item) => <button type="button" className="secondary-button" key={item} onClick={() => setQuestion(item)}>{item}</button>)}</div><div className="assistant-compose"><textarea value={question} onChange={(event) => setQuestion(event.target.value)} placeholder={assistantCopy.placeholder} maxLength={1000} /><button className="primary-button" type="button" onClick={() => void ask()} disabled={loading || question.trim().length < 2}>{loading ? assistantCopy.loading : assistantCopy.ask}</button></div>{error && <ErrorState message={error} />}{answer && <article className="assistant-answer"><Badge kind={answer.generated_by === 'gemini' ? 'CALCULATED' : 'VERIFICATION REQUIRED'} /><p>{answer.answer}</p><small>{answer.limitations.join(' ')}</small></article>}</section>
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

function ReportSection({ title, eyebrow, children, pdfExclude = false }: { title: string; eyebrow: string; children: React.ReactNode; pdfExclude?: boolean }) { return <section className="report-section" data-pdf-exclude={pdfExclude || undefined}><div className="report-section-heading"><span>{eyebrow}</span><h2>{title}</h2></div>{children}</section> }
function StepIntro({ number, title, text }: { number: string; title: string; text: string }) { return <header className="step-intro"><span>{number} / 05</span><h2>{title}</h2><p>{text}</p></header> }
function CalculationCard({ label, value, badge, formula }: { label: string; value: string; badge: BadgeKind; formula?: string }) { return <article className="calculation-card"><Badge kind={badge} /><span>{label}</span><strong>{value}</strong>{formula && <small>{formula}</small>}</article> }
function Metric({ label, value, note }: { label: string; value: string; note?: string }) {
  if (label === 'Financial feasibility') return <article className="report-metric risk-metric"><div className="metric-label"><span>{label}</span></div><RiskGauge level={value} />{note && <small>{note}</small>}</article>
  return <article className="report-metric"><div className="metric-label"><span>{label}</span></div><strong>{value}</strong>{note && <small>{note}</small>}</article>
}
function RiskGauge({ level, expanded = false }: { level: string; expanded?: boolean }) {
  const normalized = level.toUpperCase()
  const angle = normalized === 'COMFORTABLE' ? -58 : normalized === 'TIGHT' ? 0 : normalized === 'UNAFFORDABLE' ? 58 : null
  const label = normalized === 'COMFORTABLE' ? 'Lower financial risk' : normalized === 'TIGHT' ? 'Moderate financial risk' : normalized === 'UNAFFORDABLE' ? 'Higher financial risk' : 'Risk not scored'
  return <div className={expanded ? 'risk-gauge expanded' : 'risk-gauge'} role="img" aria-label={`${label}; backend feasibility status ${normalized}`}><svg viewBox="0 0 180 105" aria-hidden="true"><path d="M22 88 A68 68 0 0 1 55 30" className="gauge-low" /><path d="M55 30 A68 68 0 0 1 125 30" className="gauge-mid" /><path d="M125 30 A68 68 0 0 1 158 88" className="gauge-high" />{angle != null && <g transform={`rotate(${angle} 90 88)`}><line x1="90" y1="88" x2="90" y2="36" /><circle cx="90" cy="88" r="7" /></g>}</svg><div className="gauge-scale" aria-hidden="true"><span>Lower</span><span>Watch</span><span>Higher</span></div><b>{label}</b><small>{normalized === 'UNKNOWN' ? 'Add revenue and costs to calculate' : `Backend status: ${normalized}`}</small></div>
}
function Badge({ kind }: { kind: BadgeKind }) {
  const labels: Partial<Record<BadgeKind, string>> = { 'PUBLIC DATA': 'Verified source', 'VERIFIED GOVT RULE': 'Verified source', 'CALCULATED': 'Calculated', 'ESTIMATE': 'Illustrative', 'ASSUMPTION': 'Illustrative', 'VERIFICATION REQUIRED': 'Needs verification', 'LENDER TERMS REQUIRED': 'Needs verification', 'AVAILABILITY CHECK': 'Needs verification', 'USER INPUT': 'User input' }
  return <span className={`evidence-badge ${kind.toLowerCase().replace(/ /g, '-')}`}>{labels[kind] ?? kind}</span>
}
function Disclaimer({ locale = 'en' }: { locale?: Locale }) {
  const copy = {
    en: { title: 'Decision-support estimate', text: 'Results are indicative. Public-data coverage may be incomplete. Final loan eligibility and sanction are determined by the relevant authority.' },
    hi: { title: 'निर्णय-सहायता अनुमान', text: 'परिणाम संकेतात्मक हैं। सार्वजनिक डेटा कवरेज अधूरा हो सकता है। अंतिम ऋण पात्रता और स्वीकृति संबंधित प्राधिकरण द्वारा तय की जाती है।' },
    bn: { title: 'সিদ্ধান্ত-সহায়তা অনুমান', text: 'ফলাফল নির্দেশক। সরকারি ডেটা অসম্পূর্ণ হতে পারে। চূড়ান্ত ঋণ যোগ্যতা ও অনুমোদন সংশ্লিষ্ট কর্তৃপক্ষ নির্ধারণ করে।' },
    mr: { title: 'निर्णय-सहाय्य अंदाज', text: 'परिणाम सूचक आहेत. सार्वजनिक डेटा अपूर्ण असू शकतो. अंतिम कर्ज पात्रता आणि मंजुरी संबंधित प्राधिकरण ठरवते.' },
    ta: { title: 'முடிவு-ஆதரவு மதிப்பீடு', text: 'முடிவுகள் வழிகாட்டுதலுக்கானவை. பொது தரவு முழுமையற்றதாக இருக்கலாம். இறுதி கடன் தகுதி மற்றும் அனுமதி சம்பந்தப்பட்ட அதிகாரத்தால் தீர்மானிக்கப்படும்.' },
  }[locale]
  return <aside className="disclaimer"><ShieldCheck size={20} /><div><strong>{copy.title}</strong><p>{copy.text}</p></div></aside>
}
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
