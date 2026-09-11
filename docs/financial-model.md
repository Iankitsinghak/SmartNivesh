# VyaparSathi Financial Model

This document describes the financial-planning functionality currently implemented in VyaparSathi. The production calculation path is the backend endpoint `POST /api/finance/roadmap`, which is exposed by `backend/app/api/finance.py` and implemented by `backend/app/services/finance/scheme_router.py`.

The result is a transparent planning illustration. It is not a credit score, loan application, sanction, subsidy guarantee, lender quotation, or legal eligibility decision.

## 1. Financial workflow

The endpoint performs these steps:

1. Validate the request with `FinancialRoadmapRequest`.
2. Build the baseline NSFDC assessment with `_nsfdc_assessment`.
3. Build five conditional government-scheme routes:
   - `_nsfdc_route`
   - `_mudra_route`
   - `_pmegp_route`
   - `_pmfme_route`
   - `_vishwakarma_route`
4. Build the user-supplied cash-flow result with `_cashflow`.
5. Return all results from `build_financial_roadmap` as `FinancialRoadmapResponse`.

The API function `financial_roadmap_endpoint` only accepts the request and delegates to `build_financial_roadmap`; it does not perform calculations itself.

## 2. Request inputs and validation

The request schema is `backend/app/schemas/finance.py:FinancialRoadmapRequest`.

| Field | Required | Accepted values / limits | Purpose |
| --- | --- | --- | --- |
| `margin_capital` | Yes | Greater than `0`, at most `5,000,000` | Available own margin capital used to derive the indicative project cost. |
| `activity_type` | No | `service_or_trading`, `manufacturing`, `food_processing`, `traditional_artisan`, `not_sure` | Controls PMEGP, PMFME and PM Vishwakarma routing. Default: `not_sure`. |
| `area_type` | No | `rural`, `urban`, `not_sure` | Controls PMEGP margin-money rates. Default: `not_sure`. |
| `pmegp_beneficiary_group` | No | `general`, `special`, `not_sure` | Controls PMEGP beneficiary contribution and subsidy rates. Default: `not_sure`. |
| `has_repaid_mudra_tarun` | No | Boolean | Required condition for the PMMY Tarun Plus route. Default: `false`. |
| `vishwakarma_loan_stage` | No | `not_confirmed`, `first`, `second` | Selects the PM Vishwakarma tranche. Default: `not_confirmed`. |
| `monthly_fixed_cost` | No | Number greater than or equal to `0` | User-entered monthly fixed operating costs. |
| `monthly_variable_cost` | No | Number greater than or equal to `0` | User-entered monthly variable operating costs. |
| `expected_monthly_revenue` | No | Number greater than or equal to `0` | User-entered expected monthly revenue. |
| `operating_reserve_months` | No | `0` through `24` | User-selected operating-cost reserve period. |

Optional cash-flow values are not inferred from demographics, rural benchmarks, market data, or scheme rules. A cash-flow metric is returned only when the inputs needed for that metric are present.

## 3. Baseline assessment

### 3.1 Project cost and requested loan

`_nsfdc_assessment(margin)` uses a planning assumption of 10% own margin and 90% indicative financing:

```text
project_cost = margin_capital / 0.10
requested_loan = project_cost * 0.90
```

With the default structure, `requested_loan` equals nine times `margin_capital`.

Example:

```text
margin_capital = INR 10,000
project_cost = 10,000 / 0.10 = INR 100,000
requested_loan = 100,000 * 0.90 = INR 90,000
```

These values are planning inputs, not a promise that a lender will finance 90% of the project.

### 3.2 NSFDC route selection

The baseline chooses the NSFDC product from `project_cost`:

| Condition | Scheme | Published loan cap in the model | Rate | Total tenure | Moratorium |
| --- | --- | ---: | ---: | ---: | ---: |
| `project_cost <= INR 140,000` | NSFDC Micro Finance Scheme | INR 125,000 | 6.5% annually | 36 months | 3 months |
| `INR 140,000 < project_cost <= INR 5,000,000` | NSFDC Term Loan | INR 4,500,000 | 8% annually | 84 months | 6 months |
| `project_cost > INR 5,000,000` | Outside baseline range | None | None | None | None |

The eligible amount is:

```text
eligible_loan = min(requested_loan, published_loan_cap)
required_own_contribution = project_cost - eligible_loan
```

When the project cost exceeds INR 5,000,000, the assessment status is `OUTSIDE_BASELINE_RANGE` and loan, repayment, rate, and tenure fields are returned as `null`.

### 3.3 Repayment periods

The model starts repayment after the published moratorium but does not capitalize moratorium interest:

```text
repayment_months = tenure_months - moratorium_months
repayment_quarters = ceil(repayment_months / 3)
```

Therefore, the NSFDC examples use 33 repayment months for Micro Finance and 78 repayment months for Term Loan. The quarterly count is rounded up because the model uses whole quarterly periods.

### 3.4 Amortized payment formula

The private helper `_amortized_payment(principal, annual_rate, periods, periods_per_year)` calculates a fixed periodic repayment:

```text
periodic_rate = annual_rate / periods_per_year

payment = principal * periodic_rate * (1 + periodic_rate)^periods
          / ((1 + periodic_rate)^periods - 1)
```

For a zero rate, the fallback is:

```text
payment = principal / periods
```

For a non-positive principal or period count, the helper returns `0`.

The assessment calculates both views:

```text
estimated_monthly_instalment  = amortized_payment(loan, rate, repayment_months, 12)
estimated_quarterly_instalment = amortized_payment(loan, rate, repayment_quarters, 4)
estimated_total_repayment = estimated_quarterly_instalment * repayment_quarters
estimated_total_interest = estimated_total_repayment - eligible_loan
```

The quarterly figure is an illustration based on quarterly compounding periods. It is not calculated as monthly instalment multiplied by three. The Term Loan quarterly frequency must be confirmed with the channelizing agency.

## 4. Government-scheme routes

Every route includes a code, name, administering body, status, summary, official URL, source review date, optional financial values, conditions, and limitations. The registry review date currently returned by the service is `2026-09-10`.

### 4.1 NSFDC

`_nsfdc_route` exposes the baseline assessment and labels a valid route `ELIGIBILITY_CHECK`. If the baseline is outside range, the route is `NOT_APPLICABLE`.

The route states that applicant group, income, activity, viability, documents, and the authorized channelizing agency must verify final eligibility. The model does not decide these conditions.

### 4.2 PMMY / MUDRA

`_mudra_route` uses `assessment.requested_loan` to select a published category:

| Requested loan | Category | Published ceiling |
| ---: | --- | ---: |
| Up to INR 50,000 | Shishu | INR 50,000 |
| Above INR 50,000 to INR 500,000 | Kishore | INR 500,000 |
| Above INR 500,000 to INR 1,000,000 | Tarun | INR 1,000,000 |
| Above INR 1,000,000 to INR 2,000,000 | Tarun Plus | INR 2,000,000 |
| Above INR 2,000,000 | Not applicable | None |

Tarun Plus also requires `has_repaid_mudra_tarun == true`. If that condition is not confirmed, the route status is `ELIGIBILITY_CHECK`.

No PMMY EMI is calculated. The official scheme page does not provide one common borrower interest rate or tenure for all participating lenders, so lender terms remain outside this service.

### 4.3 PMEGP

`_pmegp_route` first requires a usable activity profile. `not_sure` and `traditional_artisan` return `PROFILE_NEEDED`.

Published project-cost ceilings represented by the service are:

| Activity profile | Ceiling |
| --- | ---: |
| `service_or_trading` | INR 2,000,000 |
| `manufacturing` or `food_processing` | INR 5,000,000 |

If the project cost exceeds the selected ceiling, the route is `NOT_APPLICABLE`.

Once activity, area, and beneficiary group are supplied, the model uses:

```text
beneficiary_contribution_rate = 5% if group == special else 10%

subsidy_rate =
    35% if group == special and area == rural
    25% if group == special or area == rural
    15% otherwise

potential_subsidy = project_cost * subsidy_rate
minimum_beneficiary_contribution = project_cost * beneficiary_contribution_rate
```

The route status is `ELIGIBILITY_CHECK`. Margin money is not treated as cash paid upfront; bank finance, lock-in, activity classification, new-unit status, training, and final approval remain subject to the official process.

### 4.4 PMFME

`_pmfme_route` is shown only when `activity_type == food_processing`; otherwise it is `NOT_APPLICABLE`.

For food processing:

```text
potential_subsidy = min(project_cost * 0.35, INR 1,000,000)
minimum_beneficiary_contribution = project_cost * 0.10
```

The status is `AVAILABILITY_CHECK`. The service does not calculate a PMFME loan or EMI. Current availability, ODOP priority, food-safety requirements, activity eligibility, and bank sanction must be confirmed.

### 4.5 PM Vishwakarma

`_vishwakarma_route` is shown only for `traditional_artisan`; other activities are `NOT_APPLICABLE`.

If the stage is `not_confirmed`, the route is `PROFILE_NEEDED`. For a selected stage:

| Stage | Principal | Tenure | Beneficiary rate |
| --- | ---: | ---: | ---: |
| First | INR 100,000 | 18 months | 5% annually |
| Second | INR 200,000 | 30 months | 5% annually |

The monthly illustration is:

```text
estimated_monthly_instalment = amortized_payment(principal, 0.05, tenure_months, 12)
```

The route status is `ELIGIBILITY_CHECK`. The service does not assume a blanket moratorium for this illustration and requires trade, training, prior repayment, and programme conditions to be verified.

## 5. Cash-flow and working-capital calculations

`_cashflow` uses only explicit user-entered values.

Both `monthly_fixed_cost` and `monthly_variable_cost` are required for operating cost:

```text
monthly_operating_cost = monthly_fixed_cost + monthly_variable_cost
```

When revenue is also provided:

```text
monthly_cash_before_debt = expected_monthly_revenue - monthly_operating_cost
monthly_cash_after_baseline_instalment =
    monthly_cash_before_debt - estimated_monthly_instalment
```

When operating cost and reserve months are both provided:

```text
operating_reserve_requirement =
    monthly_operating_cost * operating_reserve_months
```

The cash-flow status is:

```text
AVAILABLE  if fixed cost, variable cost, revenue, and reserve months are supplied
INCOMPLETE otherwise
```

Missing values produce `null` for the affected output and an explanatory limitation. Negative cash is allowed as an output because it is a planning signal, not an input-validation error.

## 6. Response structure

`FinancialRoadmapResponse` contains:

| Property | Meaning |
| --- | --- |
| `assessment` | Baseline project-cost, NSFDC route, repayment, and contribution illustration. |
| `cashflow` | Operating-cost, cash-before-debt, cash-after-baseline-instalment, and reserve calculations. |
| `routes` | NSFDC, PMMY, PMEGP, PMFME, and PM Vishwakarma route results. |
| `readiness_actions` | Practical preparation and official-channel guidance. |
| `data_status` | Currently `VERIFIED_GOVERNMENT_RULES`. |
| `data_limitations` | Global limitations about curated rules, lender terms, availability, and changing government policy. |

Route statuses mean:

- `ELIGIBILITY_CHECK`: a calculation or published category is available, but final eligibility is unverified.
- `PROFILE_NEEDED`: required user profile information is missing.
- `LENDER_TERMS_REQUIRED`: the scheme category is identified, but lender-specific terms are required.
- `AVAILABILITY_CHECK`: a potential benefit is calculated, but current availability or programme conditions require confirmation.
- `NOT_APPLICABLE`: the current inputs do not match the route.
- `PUBLISHED_TERMS`: reserved for a route exposing published terms directly; the current baseline routes generally use the more cautious statuses above.

## 7. Frontend note

`frontend/src/finance.ts` contains `SCHEME_RULES`, `amortizedPayment`, and `calculateFinancialAssessment`. This is a legacy standalone calculator with only the two NSFDC products. In the current frontend, `App.tsx` imports `formatINR` from that file, while financial results are fetched from `getFinancialRoadmap` and the backend API. Therefore, the backend service and its response contract are authoritative for the current application behavior.

The legacy module differs in several details: it accepts and clamps invalid numeric input locally, returns lowercase client-side statuses, represents quarterly repayment as monthly payment multiplied by three, and does not implement PMMY, PMEGP, PMFME, PM Vishwakarma, or cash-flow planning. It should not be used as the source of financial-policy documentation.

## 8. Official sources and limitations

The service currently records these official sources in `scheme_router.py`:

- NSFDC: <https://nsfdc.nic.in/faqs>
- PMMY / MUDRA: <https://financialservices.gov.in/pradhan-mantri-mudra-yojana-pmmy>
- PMEGP: <https://www.kviconline.gov.in/pmegpeportal/dashboard/notification/Revised_PMEGP_Scheme_Guidelines_07122023_compressed.pdf>
- PMFME: <https://pmfme.mofpi.gov.in/pmfme/>
- PM Vishwakarma: <https://pmvishwakarma.gov.in/>
- Udyam Registration: <https://udyamregistration.gov.in/>

Rules can change. Applicants must confirm current terms, documents, eligibility, repayment schedules, and application availability with the relevant official agency or participating bank before making a financial decision. The service does not collect Aadhaar numbers, caste certificates, income proof, bank credentials, or application credentials.

## 9. Related files

- `backend/app/api/finance.py` - API route.
- `backend/app/schemas/finance.py` - request and response contracts.
- `backend/app/services/finance/scheme_router.py` - financial calculations and scheme routing.
- `backend/tests/test_financial_roadmap.py` - financial behavior tests.
- `docs/financial-roadmap.md` - shorter public-facing scheme summary.