export type SchemeId = 'micro-finance' | 'term-loan'

export interface SchemeRule {
  id: SchemeId
  name: string
  projectCostMinExclusive: number
  projectCostMax: number
  financeShare: number
  loanCap: number
  annualInterestRate: number
  tenureMonths: number
  moratoriumMonths: number
}

export interface FinancialAssessment {
  status: 'valid' | 'invalid' | 'unsupported'
  message?: string
  marginCapital: number
  projectCost: number
  requestedLoan: number
  eligibleLoan: number
  beneficiaryContribution: number
  scheme?: SchemeRule
  repaymentMonths: number
  estimatedMonthlyInstalment: number
  estimatedQuarterlyRepayment: number
  estimatedTotalRepayment: number
  estimatedTotalInterest: number
}

export const SCHEME_RULES: SchemeRule[] = [
  { id: 'micro-finance', name: 'NSFDC Micro Finance Scheme', projectCostMinExclusive: 0, projectCostMax: 140_000, financeShare: 0.9, loanCap: 125_000, annualInterestRate: 0.065, tenureMonths: 36, moratoriumMonths: 3 },
  { id: 'term-loan', name: 'NSFDC Term Loan', projectCostMinExclusive: 140_000, projectCostMax: 5_000_000, financeShare: 0.9, loanCap: 4_500_000, annualInterestRate: 0.08, tenureMonths: 84, moratoriumMonths: 6 },
]

function amortizedPayment(principal: number, annualRate: number, months: number) {
  if (principal <= 0 || months <= 0) return 0
  const monthlyRate = annualRate / 12
  return principal * monthlyRate * (1 + monthlyRate) ** months / ((1 + monthlyRate) ** months - 1)
}

export function calculateFinancialAssessment(marginCapital: number): FinancialAssessment {
  const margin = Number.isFinite(marginCapital) ? Math.max(0, marginCapital) : 0
  const projectCost = margin / 0.1
  const requestedLoan = projectCost * 0.9
  const base = { marginCapital: margin, projectCost, requestedLoan, eligibleLoan: 0, beneficiaryContribution: margin, repaymentMonths: 0, estimatedMonthlyInstalment: 0, estimatedQuarterlyRepayment: 0, estimatedTotalRepayment: 0, estimatedTotalInterest: 0 }
  if (margin <= 0) return { ...base, status: 'invalid', message: 'Enter margin capital greater than ₹0.' }
  const scheme = SCHEME_RULES.find((rule) => projectCost > rule.projectCostMinExclusive && projectCost <= rule.projectCostMax)
  if (!scheme) return { ...base, status: 'unsupported', message: 'The calculated project cost exceeds the ₹50 lakh limit covered by this calculator.' }
  const eligibleLoan = Math.min(requestedLoan, scheme.loanCap)
  const beneficiaryContribution = projectCost - eligibleLoan
  const repaymentMonths = scheme.tenureMonths - scheme.moratoriumMonths
  const estimatedMonthlyInstalment = amortizedPayment(eligibleLoan, scheme.annualInterestRate, repaymentMonths)
  const estimatedTotalRepayment = estimatedMonthlyInstalment * repaymentMonths
  return { ...base, status: 'valid', scheme, eligibleLoan, beneficiaryContribution, repaymentMonths, estimatedMonthlyInstalment, estimatedQuarterlyRepayment: estimatedMonthlyInstalment * 3, estimatedTotalRepayment, estimatedTotalInterest: estimatedTotalRepayment - eligibleLoan }
}

export function formatINR(value: number) {
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(Math.round(value))
}
