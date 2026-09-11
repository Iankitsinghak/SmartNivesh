# Financial roadmap and curated scheme router

`POST /api/finance/roadmap` is a transparent planning service. It calculates a
project cost as `available margin capital / 10%` and an indicative financing
need as `project cost × 90%`. It is not a credit score, an application or a
sanction decision.

## Government-source registry

The rules below were reviewed on **2026-09-10**. The response repeats that date
and an official source URL on every route so an applicant can recheck terms
before applying.

| Route | Curated official rule | Calculator behavior |
| --- | --- | --- |
| [NSFDC Micro Finance / Term Loan](https://nsfdc.nic.in/faqs) | Micro Finance: project cost up to ₹1.40 lakh, up to ₹1.25 lakh, 6.5%, three years including three-month moratorium. Term Loan: project cost over ₹1.40 lakh to ₹50 lakh, up to ₹45 lakh, 8%, seven years including six-month moratorium. | Calculates the published cap and a repayment illustration. It requires applicant target-group, income, activity, channel and schedule verification. |
| [PMMY / MUDRA](https://financialservices.gov.in/pradhan-mantri-mudra-yojana-pmmy) | Shishu up to ₹50,000; Kishore over ₹50,000 to ₹5 lakh; Tarun over ₹5 lakh to ₹10 lakh; Tarun Plus over ₹10 lakh to ₹20 lakh after successful previous Tarun repayment. | Matches the published loan-size category only. It never calculates an EMI because the official page does not publish one standard borrower rate or tenure across lenders. |
| [PMEGP](https://www.kviconline.gov.in/pmegpeportal/dashboard/notification/Revised_PMEGP_Scheme_Guidelines_07122023_compressed.pdf) | Subsidy-eligible project-cost ceiling: ₹20 lakh for business/service and ₹50 lakh for manufacturing. Published new-unit margin-money rates depend on self-declared area and beneficiary group. | Calculates margin money only after the user selects activity, rural/urban area and group. It labels the result as eligibility verification, not a promised subsidy. |
| [PMFME](https://pmfme.mofpi.gov.in/pmfme/) | Individual micro food-processing units: published 35% credit-linked capital subsidy, capped at ₹10 lakh; minimum 10% beneficiary contribution. | Shows a potential subsidy only for food processing and requires current availability, ODOP/activity, food-safety and bank confirmation. It does not invent a loan rate or EMI. |
| [PM Vishwakarma](https://pmvishwakarma.gov.in/) | Eligible artisans in the published traditional trades may access ₹1 lakh / 18-month and ₹2 lakh / 30-month tranches at 5%, subject to programme conditions. | Shows a tranche illustration only after the user identifies its stage. It keeps trade, training, first-loan performance and programme verification explicit. |

## Financial controls

- No operational cost is generated from a demographic model or a generic rural
  benchmark. Rent, wages, stock, transport, utilities and sales remain blank
  until supplied by the user from their plan and quotations.
- Working-capital reserve equals `user-supplied monthly operating cost ×
  user-chosen reserve months`; the service does not prescribe a buffer period.
- The NSFDC repayment model begins after the published moratorium and does not
  capitalize moratorium interest. Micro Finance is labelled as quarterly from
  the published term; the Term Loan quarterly view is clearly an illustration
  pending channel confirmation.
- PMEGP margin money is not represented as an upfront cash payment. Bank
  disbursement, lock-in, sanctioned financing and final documents must be
  confirmed through the official channel.
- Use the [official Udyam Registration portal](https://udyamregistration.gov.in/)
  for registration. The service does not collect an Aadhaar number, caste
  certificate, income proof, bank detail or application credential.
