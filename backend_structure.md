# VyaparSathi --- GOLD STATE Backend Structure

## Final Implementation Contract --- Do Not Change Architecture

**Status:** GOLD STATE / FROZEN\
**Rule:** All backend work must follow this structure. Do not introduce
new architectural layers, rename core modules, or move responsibilities
unless a deliberate v2 architecture decision is made.

------------------------------------------------------------------------

# 1. Golden Principle

VyaparSathi is a **data-driven rural enterprise decision-support
platform**, not a generic AI chatbot.

The backend follows:

``` text
PUBLICLY ACCESSIBLE DATA
        ↓
DATA INGESTION
        ↓
VALIDATION + NORMALIZATION
        ↓
POSTGRESQL
        ↓
DETERMINISTIC INTELLIGENCE
        ↓
FINANCIAL / SCHEME CALCULATIONS
        ↓
DECISION ENGINE
        ↓
AI EXPLANATION
        ↓
REPORT
```

Core rule:

> If a feature requires a dataset that cannot be obtained from a
> reliable, publicly accessible or legitimately accessible source, it
> does not belong in the MVP intelligence engine.

Do not invent data to make a feature appear intelligent.

------------------------------------------------------------------------

# 2. GOLD STATE Repository

``` text
VyaparSathi/
│
├── backend/
│   │
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   │
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   ├── constants.py
│   │   │   ├── enums.py
│   │   │   ├── logging.py
│   │   │   └── exceptions.py
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── assessment.py
│   │   │   ├── location.py
│   │   │   ├── demographic.py
│   │   │   ├── business.py
│   │   │   ├── place.py
│   │   │   ├── market.py
│   │   │   ├── scheme.py
│   │   │   ├── finance.py
│   │   │   ├── risk.py
│   │   │   ├── readiness.py
│   │   │   ├── report.py
│   │   │   └── source.py
│   │   │
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── common.py
│   │   │   ├── assessment.py
│   │   │   ├── location.py
│   │   │   ├── demographic.py
│   │   │   ├── business.py
│   │   │   ├── place.py
│   │   │   ├── market.py
│   │   │   ├── finance.py
│   │   │   ├── scheme.py
│   │   │   ├── risk.py
│   │   │   ├── readiness.py
│   │   │   ├── report.py
│   │   │   └── ai.py
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   │
│   │   │   ├── assessment/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── service.py
│   │   │   │   └── validation.py
│   │   │   │
│   │   │   ├── location/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── resolver.py
│   │   │   │   ├── hierarchy.py
│   │   │   │   └── radius.py
│   │   │   │
│   │   │   ├── opportunity/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── opportunity_engine.py
│   │   │   │   ├── scoring.py
│   │   │   │   └── ranking.py
│   │   │   │
│   │   │   ├── market/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── market_engine.py
│   │   │   │   ├── demographic_engine.py
│   │   │   │   ├── poi_engine.py
│   │   │   │   ├── business_activity_engine.py
│   │   │   │   ├── demand_engine.py
│   │   │   │   ├── competition_engine.py
│   │   │   │   ├── distribution_engine.py
│   │   │   │   ├── seasonality_engine.py
│   │   │   │   └── purchasing_power_engine.py
│   │   │   │
│   │   │   ├── finance/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── finance_engine.py
│   │   │   │   ├── loan_engine.py
│   │   │   │   ├── emi.py
│   │   │   │   ├── repayment.py
│   │   │   │   ├── scenarios.py
│   │   │   │   └── recommended_financing.py
│   │   │   │
│   │   │   ├── schemes/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── scheme_router.py
│   │   │   │   ├── eligibility.py
│   │   │   │   └── rules.py
│   │   │   │
│   │   │   ├── risk/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── risk_engine.py
│   │   │   │   └── mitigation.py
│   │   │   │
│   │   │   ├── readiness/
│   │   │   │   ├── __init__.py
│   │   │   │   └── readiness_engine.py
│   │   │   │
│   │   │   ├── decision/
│   │   │   │   ├── __init__.py
│   │   │   │   └── decision_engine.py
│   │   │   │
│   │   │   ├── ai/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── client.py
│   │   │   │   ├── prompt_builder.py
│   │   │   │   ├── explanation_service.py
│   │   │   │   ├── validator.py
│   │   │   │   └── fallback.py
│   │   │   │
│   │   │   └── reports/
│   │   │       ├── __init__.py
│   │   │       ├── report_service.py
│   │   │       ├── pdf_generator.py
│   │   │       └── templates.py
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── assessment.py
│   │   │   ├── locations.py
│   │   │   ├── opportunities.py
│   │   │   ├── businesses.py
│   │   │   ├── market.py
│   │   │   ├── finance.py
│   │   │   ├── schemes.py
│   │   │   ├── scenarios.py
│   │   │   ├── risks.py
│   │   │   ├── readiness.py
│   │   │   └── reports.py
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── geo.py
│   │       ├── math.py
│   │       ├── normalization.py
│   │       └── provenance.py
│   │
│   ├── data/
│   │   ├── businesses.json
│   │   ├── business_categories.json
│   │   ├── locations.json
│   │   ├── demographics.json
│   │   ├── places.json
│   │   ├── markets.json
│   │   └── schemes.json
│   │
│   ├── scripts/
│   │   ├── seed_database.py
│   │   ├── import_locations.py
│   │   ├── import_demographics.py
│   │   ├── import_places.py
│   │   ├── import_businesses.py
│   │   └── verify_data.py
│   │
│   ├── tests/
│   │   ├── test_finance.py
│   │   ├── test_schemes.py
│   │   ├── test_market.py
│   │   ├── test_competition.py
│   │   ├── test_opportunity.py
│   │   ├── test_decision.py
│   │   └── test_api.py
│   │
│   ├── alembic/
│   │   └── versions/
│   │
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── .env.example
│   └── pytest.ini
│
├── frontend/
│
├── docs/
│   ├── architecture.md
│   ├── hyper-local-intelligence.md
│   ├── scoring.md
│   ├── data-sources.md
│   └── api.md
│
├── docker-compose.yml
├── README.md
└── .gitignore
```

------------------------------------------------------------------------

# 3. Responsibility of Every Layer

## `models/`

Database representation only.

Do not put business calculations here.

## `schemas/`

API input/output validation.

Do not put database queries here.

## `services/`

All business intelligence and calculations.

This is the core application layer.

## `api/`

HTTP endpoints only.

Routes should call services, not implement business logic.

## `data/`

Seed/demo/configuration data.

## `scripts/`

Data ingestion and verification.

## `utils/`

Small reusable technical helpers.

## `core/`

Application configuration, database, constants, logging and global
exceptions.

------------------------------------------------------------------------

# 4. Final Hyper-Local Intelligence Architecture

``` text
                         USER
                           │
                           ▼
                    LOCATION INPUT
                           │
                           ▼
                 LOCATION RESOLVER
                           │
                           ▼
              LOCATION + GEO CONTEXT
                           │
           ┌───────────────┼────────────────┐
           │               │                │
           ▼               ▼                ▼
      DEMOGRAPHICS        POIs         BUSINESSES
           │               │                │
           │               │                │
           │          Schools              Hotels
           │          Colleges             Restaurants
           │          Hospitals            Pharmacies
           │          Monuments            Salons
           │          Railway              Grocery
           │          Bus                  etc.
           │               │                │
           └───────────────┼────────────────┘
                           ▼
                 SELECTED BUSINESS
                           │
                           ▼
              CUSTOMER PROFILE MATCH
                           │
                           ▼
                  RELEVANCE ENGINE
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
           DEMAND      COMPETITION   DISTRIBUTION
           SIGNALS       SIGNALS       SIGNALS
              │            │            │
              └────────────┼────────────┘
                           ▼
                   MARKET OPPORTUNITY
                           │
                           ▼
                    FEASIBILITY
```

------------------------------------------------------------------------

# 5. Location Radius Model

Use:

``` text
0–2 km     Immediate Local Market
2–5 km     Primary Market
5–10 km    Extended Market
```

Distance must influence relevance.

Do not simply count everything inside 10 km equally.

Example:

``` text
Competitor A → 700 m
Competitor B → 8.5 km
```

Competitor A should have substantially higher local relevance.

Use a bounded distance-decay function in production rather than a raw
inverse-distance formula.

------------------------------------------------------------------------

# 6. Places vs Businesses

## Places

Contextual demand/location signals:

``` text
SCHOOL
COLLEGE
HOSPITAL
CLINIC
TEMPLE
MOSQUE
CHURCH
MONUMENT
TOURIST_SITE
RAILWAY_STATION
BUS_STOP
BUS_STAND
MARKET
GOVERNMENT_OFFICE
BANK
INDUSTRIAL_AREA
RESIDENTIAL_AREA
```

## Businesses

Commercial entities:

``` text
HOTEL
RESTAURANT
CAFE
GROCERY
PHARMACY
COSMETICS
SALON
TAILOR
BAKERY
GARAGE
ELECTRONICS
STATIONERY
```

A business is stored as a business.

Its analytical relationship changes according to the selected business.

Example:

``` text
User wants Hotel:
Nearby Hotels → competitors

User wants Restaurant:
Nearby Hotels → potential demand generators

User wants Laundry:
Nearby Hotels → potential demand generators
```

Do not duplicate the same hotel into multiple database entities.

------------------------------------------------------------------------

# 7. Public Data Availability Gate

Before implementing any intelligence feature, ask:

``` text
1. What exact data does this feature require?
2. Is the data publicly/legitimately accessible?
3. Is the source reliable enough?
4. Can we legally/technically retrieve it?
5. Is geographic coverage sufficient?
6. What is the update frequency?
7. Can we store/cache it?
8. Can we expose its uncertainty?
```

Only if the answer is sufficiently positive should the feature enter the
production intelligence pipeline.

## Do not build features around unavailable data.

Examples of unsafe design:

``` text
Exact daily customer count
Exact village purchasing power without source
Exact local sales volume
Exact competitor count when coverage is incomplete
Exact footfall without a credible dataset
```

Instead use:

``` text
Estimated Customer Potential
Mapped Business Activity
Market Activity Indicator
Purchasing Power Indicator
Mapped Competition Density
Footfall Potential
```

with confidence and source metadata.

------------------------------------------------------------------------

# 8. Data Source Architecture

``` text
              PUBLIC DATA SOURCES
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   Government       Geospatial      Open Data
      Data             Data
        │              │              │
        └──────────────┼──────────────┘
                       ▼
                 INGESTION SCRIPTS
                       │
                       ▼
                  VALIDATION
                       │
                       ▼
                 NORMALIZATION
                       │
                       ▼
                  DEDUPLICATION
                       │
                       ▼
                  POSTGRESQL
                       │
                       ▼
             INTELLIGENCE ENGINES
```

Do not make every user request call external APIs.

Use ingestion/cache/storage wherever licensing and source terms permit.

------------------------------------------------------------------------

# 9. Data Provenance

Every externally derived dataset must carry:

``` text
source_id
source_name
source_url
data_type
last_verified
confidence
notes
```

Allowed data classifications:

``` text
VERIFIED
CALCULATED
ESTIMATED
SEEDED_DEMO
ASSUMPTION
AI_INTERPRETATION
```

Example:

``` text
Population
→ VERIFIED

EMI
→ CALCULATED

Mapped competitor count
→ ESTIMATED

Demo business
→ SEEDED_DEMO

Customer fingerprint
→ ASSUMPTION / DOMAIN_RULE

Natural-language explanation
→ AI_INTERPRETATION
```

------------------------------------------------------------------------

# 10. Business Category as Configuration

Every supported business must have a configuration record.

``` text
BusinessCategory
├── name
├── capital range
├── target customer profile
├── relevant demographic groups
├── relevant POI types
├── competitor categories
├── complementary categories
├── supplier categories
├── seasonality
└── distribution requirements
```

This allows new business categories to be added without rewriting the
intelligence engine.

------------------------------------------------------------------------

# 11. Core Market Signals

For every selected business calculate only signals that can be supported
by available data:

``` text
Demographic Fit
POI Relevance
Business Activity
Competition Density
Market Activity
Distribution Accessibility
Seasonality
Purchasing Power Indicator
```

Then generate:

``` text
Demand Score
Competition Score
Opportunity Gap
Customer Potential
Market Opportunity
Confidence
```

------------------------------------------------------------------------

# 12. Opportunity Score

Initial deterministic formula:

``` text
Opportunity Score =
25% Market Demand
15% Opportunity Gap
20% Capital Fit
15% Skill Fit
10% Asset Fit
10% Distribution Fit
5% Risk Adjustment
```

Normalize:

``` text
0–39     Weak
40–59    Moderate
60–74    Good
75–89    Strong
90–100   Very Strong
```

Weights must be configurable.

AI cannot modify them.

------------------------------------------------------------------------

# 13. Market Gap

Initial formula:

``` text
Market Opportunity Gap =
0.45 × Demand
+ 0.25 × Demand Growth
+ 0.20 × Distribution Availability
− 0.10 × Competition
```

Clamp:

``` text
0–100
```

If a required input is unavailable, the engine must not silently invent
a number.

Use a documented fallback/availability state.

------------------------------------------------------------------------

# 14. Finance Architecture

``` text
Financial Assessment
        │
        ├── Project Cost
        ├── Margin
        ├── Loan
        ├── Revenue
        ├── Variable Cost
        ├── Fixed Cost
        ├── EMI
        ├── Repayment
        └── Scenarios
```

Rules:

``` text
Project Cost = Available Margin / 0.10
Loan = Project Cost × 0.90
```

Revenue:

``` text
Revenue = Units × Selling Price
```

Operating profit:

``` text
Revenue − Variable Cost − Fixed Cost
```

Standard EMI:

``` text
EMI =
P × r × (1+r)^n
----------------
(1+r)^n − 1
```

Finance calculations are 100% deterministic.

------------------------------------------------------------------------

# 15. Recommended Financing

Never equate:

``` text
Maximum Eligibility
=
Recommended Borrowing
```

Recommended financing must test:

``` text
Market potential
Project scale
Loan requirement
Expected repayment
Conservative scenario
Working capital
Risk
```

Then output:

``` text
Recommended Project Cost
Recommended Loan
Maximum Eligible Loan
Reason
```

------------------------------------------------------------------------

# 16. Scheme Engine

Scheme rules are deterministic and configuration-driven.

Initial scheme rules:

``` text
≤ ₹1.40 lakh
→ Micro Finance
→ 6.5%
→ 3 years
→ 3-month moratorium
→ maximum agency loan ₹1.25 lakh
```

``` text
> ₹1.40 lakh and ≤ ₹50 lakh
→ Term Loan
→ 8%
→ 7 years
→ 6-month moratorium
→ maximum agency loan ₹45 lakh
```

Do not ask an LLM to determine scheme eligibility.

------------------------------------------------------------------------

# 17. Scenario Engine

``` text
CONSERVATIVE
EXPECTED
OPTIMISTIC
```

Inputs:

``` text
Price
Units / Customers
Variable Cost
Fixed Cost
Loan
Interest
Tenure
```

Outputs:

``` text
Revenue
Operating Profit
EMI
Cash After EMI
Repayment Coverage
Risk
```

------------------------------------------------------------------------

# 18. Risk Engine

Dimensions:

``` text
Market
Finance
Competition
Supply
Seasonality
Execution
```

Return:

``` text
Overall Risk
Risk Score
Top 3 Risks
Evidence
Mitigation
Confidence
```

------------------------------------------------------------------------

# 19. Readiness Engine

Dimensions:

``` text
Capital
Market Understanding
Business Planning
Financial Readiness
Risk Preparedness
```

Weights:

``` text
20% each
```

Output:

``` text
Readiness Score
Readiness Level
Improvement Actions
```

------------------------------------------------------------------------

# 20. Decision Engine

Inputs:

``` text
Market
Capital
Financial Fit
Downside
Eligibility
Risk
Readiness
```

Output:

``` text
GO
MODIFY
STOP
```

### GO

Reasonably viable.

### MODIFY

Potential exists but business needs changes.

### STOP

Unsafe even after reasonable modifications.

Decision must include evidence.

------------------------------------------------------------------------

# 21. AI Architecture

``` text
Deterministic Backend
        ↓
Structured JSON
        ↓
Prompt Builder
        ↓
Gemini
        ↓
Pydantic Validator
        ↓
Explanation
```

AI may:

-   explain
-   summarize
-   translate
-   generate SWOT wording
-   explain risks
-   generate action plans

AI may not:

-   calculate EMI
-   calculate loan
-   determine eligibility
-   invent market data
-   invent competitors
-   invent scheme terms
-   invent local statistics
-   guarantee revenue
-   override deterministic decisions

Fallback:

``` text
AI unavailable
      ↓
Template-based explanation
      ↓
System still works
```

------------------------------------------------------------------------

# 22. API Layer

``` text
POST /api/assessments

GET /api/assessments/{id}

PATCH /api/assessments/{id}

GET /api/locations/search

GET /api/locations/{id}

POST /api/opportunities

GET /api/businesses/{id}

GET /api/businesses/{id}/market

POST /api/market/analyze

POST /api/feasibility

POST /api/finance

POST /api/schemes/evaluate

POST /api/scenarios

GET /api/risk/{assessment_id}

GET /api/readiness/{assessment_id}

GET /api/reports/{assessment_id}

GET /api/reports/{assessment_id}/pdf
```

Routes only orchestrate services.

No calculations inside route handlers.

------------------------------------------------------------------------

# 23. Production Data Strategy

MVP must support:

``` text
Verified public data
+
Seeded demo data
+
Calculated data
+
Estimated signals
```

The system must always indicate which one is being shown.

The architecture must support future data refresh without changing the
scoring engine.

------------------------------------------------------------------------

# 24. Gold-State Development Rules

1.  Do not change the folder structure.
2.  Do not move business logic into API routes.
3.  Do not put calculations into database models.
4.  Do not let AI calculate deterministic values.
5.  Do not create features requiring unavailable data.
6.  Do not fabricate local statistics.
7.  Do not present mapped data as complete census/business inventory.
8.  Do not hardcode scheme rules throughout the codebase.
9.  Keep scoring formulas configurable.
10. Keep source metadata attached to data.
11. Keep seeded demo mode working.
12. Every deterministic engine requires tests.
13. Every public-data ingestion process requires validation.
14. Every uncertain result must carry confidence.
15. Maximum loan must never automatically become recommended loan.
16. Eligibility must remain separate from affordability and viability.

------------------------------------------------------------------------

# 25. Final Build Pipeline

``` text
DATA SOURCES
     ↓
INGEST
     ↓
VALIDATE
     ↓
NORMALIZE
     ↓
STORE
     ↓
LOCATION INTELLIGENCE
     ↓
MARKET INTELLIGENCE
     ↓
OPPORTUNITY ENGINE
     ↓
FINANCE ENGINE
     ↓
SCHEME ROUTER
     ↓
RISK ENGINE
     ↓
READINESS ENGINE
     ↓
DECISION ENGINE
     ↓
AI EXPLANATION
     ↓
REPORT ENGINE
     ↓
FASTAPI
     ↓
REACT FRONTEND
     ↓
DOCKER
     ↓
PRODUCTION
```

------------------------------------------------------------------------

# 26. Gold-State Success Condition

A complete assessment must be able to travel through:

``` text
Location
   ↓
Business Selection
   ↓
Local Market
   ↓
Demand
   ↓
Competition
   ↓
Distribution
   ↓
Feasibility
   ↓
Project Cost
   ↓
Recommended Financing
   ↓
Scheme
   ↓
Repayment
   ↓
Scenarios
   ↓
Risk
   ↓
Readiness
   ↓
GO / MODIFY / STOP
   ↓
AI Explanation
   ↓
Final Report
```

This repository structure and architecture are the **single
implementation contract** for the VyaparSathi backend.

No feature should be added merely because it sounds impressive. Every
feature must have:

``` text
A clear user/business purpose
+
Available supporting data
+
A deterministic calculation/decision method
+
Source/provenance
+
Confidence handling
+
Tests
```

If those conditions cannot be satisfied, defer the feature rather than
fabricate intelligence.
