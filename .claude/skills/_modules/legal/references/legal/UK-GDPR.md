# UK Data Protection & Consumer Law

> **Scope**: Legal reference for [Your Platform], a multi-tenant SaaS platform (international scope). Covers UK-specific data protection, privacy, accessibility, food safety, and consumer law obligations.

---

## Applicability

UK law applies to [Your Platform] when:

- **Any UK-based restaurant** uses the platform (data controller = restaurant, data processor = [Your Platform])
- **Any UK-based customer** places an order through a [Your Platform]-powered tenant (even if the restaurant is outside the UK, if it targets UK consumers)
- **[Your Platform] processes personal data** of individuals located in the UK, regardless of where [Your Platform] is incorporated

The UK has its own post-Brexit data protection regime, separate from the EU. The supervisory authority is the **Information Commissioner's Office (ICO)**.

### Applicable Laws

| Law | Scope | Enacted / Amended |
|-----|-------|-------------------|
| **UK GDPR** (retained EU law) + **Data Protection Act 2018** | Personal data processing, data subject rights, lawful bases | 2018, amended by DUAA 2025 |
| **Data Use and Access Act 2025 (DUAA)** | Reforms to UK GDPR: recognised legitimate interests, transfer rules, cookie exemptions | Royal Assent 19 June 2025; phased rollout through June 2026 |
| **PECR** (Privacy and Electronic Communications Regulations 2003) | Cookies, marketing emails/SMS, electronic communications | 2003, amended by DUAA 2025 |
| **Equality Act 2010** | Disability discrimination, website/app accessibility | 2010 |
| **Natasha's Law** (Food Information (Amendment) (England) Regulations 2019) | Allergen labelling for prepacked for direct sale (PPDS) food | In force since 1 October 2021; FSA guidance updated March 2025 |
| **Consumer Rights Act 2015** | Digital content quality, unfair contract terms, refund rights | 2015 |
| **Digital Markets, Competition and Consumers Act 2024** | Enhanced consumer protections for digital services | Consumer provisions in force 6 April 2025 |

---

## Key Requirements

### UK GDPR + Data Protection Act 2018

**1. Lawful Basis for Processing**

Every processing activity must have one of six lawful bases (Article 6 UK GDPR):

- **Contract**: Processing order data to fulfil a customer's food order
- **Legitimate interests**: Fraud prevention, platform security, service improvement (but requires a balancing test)
- **Recognised legitimate interests** (NEW via DUAA 2025): A new lawful basis for specified low-risk purposes — including security, fraud detection, and safeguarding — that does NOT require the traditional three-part balancing test. Applies only to a closed list of purposes defined in the DUAA.
- **Consent**: Marketing communications, analytics cookies, loyalty programme enrolment
- **Legal obligation**: Tax records, food safety compliance records
- **Vital interests / Public task**: Rarely applicable for [Your Platform]

**2. Data Subject Rights**

[Your Platform] must enable tenants (as controllers) and itself (as processor) to honour:

| Right | Implication for [Your Platform] |
|-------|------------------------|
| Access (SAR) | Export all personal data for a given customer. DUAA adds a "stop the clock" provision — [Your Platform] can pause the 30-day SAR deadline if it needs clarification from the requester (EU GDPR does not allow this). |
| Rectification | Allow customers to correct their name, address, phone, email |
| Erasure ("right to be forgotten") | Delete customer data on request (subject to legal retention obligations) |
| Restriction | Flag data as restricted while a dispute is resolved |
| Portability | Export data in machine-readable format (JSON/CSV) |
| Object | Opt out of profiling, marketing, analytics |
| Automated decision-making | No fully automated decisions with legal effects without human review |

**3. Data Processing Agreement (DPA)**

[Your Platform] acts as a **data processor** for restaurant tenants (controllers). A DPA is mandatory (Article 28 UK GDPR) and must cover:

- Subject matter and duration of processing
- Nature and purpose of processing
- Types of personal data and categories of data subjects
- Obligations and rights of the controller
- Sub-processor list (<!-- FILL: your database/backend -->, <!-- FILL: your hosting provider -->, payment processors) with prior written consent mechanism
- Data breach notification obligations (processor to controller: without undue delay)

**4. Key Differences from EU GDPR (Post-DUAA 2025)**

| Area | EU GDPR | UK GDPR (post-DUAA) |
|------|---------|---------------------|
| Legitimate interests | Three-part test always required | "Recognised legitimate interests" bypass balancing test for specified purposes |
| Data subject access requests | 30 days, extendable only for complex/numerous requests | 30 days + "stop the clock" while awaiting clarification from requester |
| International transfers | "Essentially equivalent" protection standard | "Not materially lower" protection standard (lower bar) |
| DPO requirement | Mandatory for large-scale processing | Replaced by "Senior Responsible Individual" (SRI) for certain organisations |
| Cookie consent | Strict consent for all non-essential cookies | New exemptions for analytics, security, UX improvement (see PECR section) |
| Impact assessments | DPIA required for high-risk processing | Assessment of "high risk processing" — similar but terminology may diverge |

**5. ICO Registration (Mandatory)**

Any organisation processing personal data must pay the ICO data protection fee unless exempt:

| Tier | Criteria | Annual Fee |
|------|----------|------------|
| Tier 1 (Micro) | Turnover <= GBP 632,000 AND <= 10 employees | GBP 52 |
| Tier 2 (SME) | Turnover <= GBP 36M AND <= 249 employees | GBP 66 |
| Tier 3 (Large) | Turnover > GBP 36M OR > 250 employees | GBP 3,763 |

[Your Platform] must register with the ICO if it processes UK personal data. Each restaurant tenant is separately responsible for their own ICO registration as a data controller.

**6. International Data Transfers**

Transferring personal data out of the UK requires one of:

- **UK Adequacy Regulations**: The UK has granted adequacy to the EEA/EU (and vice versa — EU renewed UK adequacy on 19 December 2025, valid until 27 December 2031). Also covers transfers via the UK-US Data Bridge (extension of EU-US Data Privacy Framework).
- **UK International Data Transfer Agreement (UK IDTA)**: The UK's equivalent of EU Standard Contractual Clauses.
- **UK Addendum to EU SCCs**: Can be used alongside EU SCCs for dual-regime compliance.
- **Article 49 derogations**: Explicit consent, contract necessity, etc. (same as EU GDPR).

**[Your Platform] implication**: <!-- FILL: your database/backend --> (hosted in cloud regions) and <!-- FILL: your hosting provider --> (CDN) require transfer mechanisms. If your database is in an EU region and data flows to US sub-processors, the UK-US Data Bridge or UK IDTA may be needed. Document the transfer mechanism in the DPA.

---

### PECR (Privacy and Electronic Communications Regulations)

**7. Cookie and Storage Consent**

PECR governs cookies, localStorage, IndexedDB, and similar "storage and access technologies" (SATs). The general rule: **informed consent before storing or accessing information on a user's device**, unless an exemption applies.

**Strictly necessary exemption** (no consent required):

| Category | Examples in [Your Platform] | Consent Needed? |
|----------|--------------------|-----------------|
| Authentication cookies/tokens | Auth session, JWT | No |
| Shopping cart state | Cart items in localStorage | No |
| Security & fraud detection | CSRF tokens | No |
| Load balancing / routing | CDN cookies | No |
| User preference cookies | Language, theme, dark mode | No |

**New DUAA exemptions** (from August 2025, pending final ICO guidance expected Spring 2026):

| Category | Examples | Consent Needed? |
|----------|----------|-----------------|
| Analytics for service improvement | Page views, error tracking (first-party only) | No (new exemption) |
| System security | Rate limiting, abuse detection | No (new exemption) |
| Software updates / UX enhancement | Service worker versioning, A/B testing | No (new exemption) |
| Fault/error detection | Client-side error logging | No (new exemption) |

**Still requires consent**:

- Third-party analytics (e.g., Google Analytics, <!-- FILL: your analytics tool --> if not self-hosted)
- Advertising / remarketing cookies
- Cross-site tracking technologies

**8. Marketing Communications**

PECR requires **prior opt-in consent** for:

- Marketing emails to individuals (B2C)
- Marketing SMS messages
- Push notifications with marketing content

**Soft opt-in exception**: If a customer gave their email during a purchase (ordering food), you may send marketing about **similar products/services** without explicit consent, provided:

- They were told at the point of collection that their details would be used for marketing
- They were given a simple way to opt out (and are reminded in every message)
- The marketing relates to similar products (e.g., other menu items, loyalty rewards)

**[Your Platform] implication**: Order confirmation emails are transactional (no consent needed). Promotional emails about new menu items can use soft opt-in. Unsubscribe must be one-click.

---

### Equality Act 2010 (Accessibility)

**9. Website and App Accessibility**

The Equality Act 2010 requires service providers to make "reasonable adjustments" so that disabled people are not placed at a substantial disadvantage. This applies to websites and mobile apps as digital services.

While the Equality Act does not prescribe specific technical standards, **WCAG 2.2 Level AA** is the accepted benchmark for demonstrating compliance. Courts and the Equality and Human Rights Commission (EHRC) use WCAG as the reference standard.

**10. "Reasonable Adjustments" Duty**

Service providers must:

- Anticipate the needs of disabled users (not wait for complaints)
- Provide alternative means of access where digital barriers exist (e.g., phone ordering)
- Ensure key user journeys are accessible: browsing menu, placing order, making payment

Failure is a civil claim with **no statutory cap on damages** — awards are based on injury to feelings and financial loss.

---

### Natasha's Law (Food Allergen Labelling)

**11. Allergen Labelling for PPDS Food**

Natasha's Law (in force since 1 October 2021) requires all **prepacked for direct sale (PPDS)** food to display a full ingredients list with the 14 major allergens emphasised (e.g., bold, highlighted).

PPDS means food that is:

- Packaged at the same place it is offered or sold to consumers
- In packaging before it is ordered or selected

**12. The 14 Major Allergens**

1. Celery
2. Cereals containing gluten (wheat, rye, barley, oats)
3. Crustaceans (prawns, crab, lobster)
4. Eggs
5. Fish
6. Lupin
7. Milk
8. Molluscs (mussels, oysters, squid)
9. Mustard
10. Tree nuts (almonds, hazelnuts, walnuts, cashews, pecans, brazils, pistachios, macadamia)
11. Peanuts
12. Sesame
13. Soya
14. Sulphur dioxide and sulphites (> 10mg/kg or 10mg/litre)

**13. March 2025 FSA Guidance Update**

The Food Standards Agency updated guidance in March 2025, encouraging (not yet mandating) the out-of-home sector to provide **written allergen information** for non-PPDS foods (loose items, made-to-order meals). This means:

- Allergen data on menus, food labels, or allergen charts
- Customers should be able to access allergen info **without having to ask staff**

**[Your Platform] implication**: Menu items SHOULD support structured allergen data fields for each of the 14 allergens. This enables tenants to display allergen icons/badges on digital menus, filter menu items by allergen, and satisfy the FSA's direction toward written allergen disclosure. This is a **competitive advantage** and a compliance enabler for UK restaurant tenants.

---

### Consumer Rights Act 2015 (CRA)

**14. Digital Content Quality Rights**

The CRA Part 1 Chapter 3 applies to digital content supplied to consumers. Key quality standards:

| Standard | Meaning for [Your Platform] |
|----------|---------------------|
| **Satisfactory quality** | The platform should work reliably, be free from significant bugs |
| **Fit for a particular purpose** | If a restaurant signs up for order management, it must actually work |
| **As described** | Features described in marketing/onboarding must be delivered |

**15. Unfair Contract Terms**

Terms in [Your Platform]'s ToS may be unenforceable if they:

- Exclude or limit liability for death or personal injury caused by negligence
- Exclude statutory rights (quality, fitness, description)
- Create a significant imbalance in the parties' rights to the detriment of the consumer
- Are not transparent and prominent

**16. Right to Refund**

Consumers have the right to a repair, replacement, or price reduction if digital content is faulty. A "no refunds" policy is not enforceable under UK consumer law if the service was defective.

---

### Digital Markets, Competition and Consumers Act 2024 (DMCCA)

**17. Enhanced Consumer Protections (from 6 April 2025)**

- Direct enforcement powers for the CMA (no need for court orders)
- Fines of up to **10% of global turnover** for consumer law breaches
- New rules on subscription contracts: pre-contract information, cooling-off periods, reminder notices before renewal
- "Dark patterns" restrictions: fake urgency, hidden charges, making cancellation harder than sign-up

**[Your Platform] implication**: Tenant subscription plans must include clear pre-contract information, easy cancellation paths, and renewal reminders. No dark patterns in onboarding flows.

---

## [Your Platform]-Specific Implications

### Data Protection Architecture

| Obligation | Implementation |
|------------|---------------|
| ICO registration | Register [Your Platform] as a data processor; remind restaurant tenants to register as controllers |
| DPA with each tenant | Contractual requirement during onboarding — cover sub-processors (<!-- FILL: your database/backend -->, <!-- FILL: your hosting provider -->, <!-- FILL: your payment provider -->) |
| Privacy policy | Platform-level privacy policy + per-tenant customisable privacy notice |
| Data subject rights portal | Build mechanism for SARs, erasure requests, data export (JSON/CSV) |
| Breach notification | Processor-to-controller notification process (without undue delay); controller notifies ICO within 72 hours |
| Records of processing | Maintain Article 30 records for [Your Platform]'s processing activities |

### Cookie / Storage Compliance

| Technology | Purpose | Legal Basis |
|------------|---------|-------------|
| Auth tokens (localStorage) | Authentication | Strictly necessary (no consent) |
| IndexedDB (offline orders) | Offline-first order storage | Strictly necessary (no consent) |
| Cart state (localStorage) | Shopping cart persistence | Strictly necessary (no consent) |
| Service worker cache | PWA offline support | Strictly necessary (no consent) |
| Theme preferences (CSS vars) | UI customisation | Strictly necessary / UX enhancement (no consent under DUAA) |
| <!-- FILL: your analytics tool --> / analytics | Usage analytics | Consent required (unless self-hosted + first-party under DUAA exemption) |

### Allergen Data Model

[Your Platform]'s menu item schema SHOULD include:

- Boolean flags or tags for each of the 14 allergens
- Free-text ingredients field for PPDS label generation
- Allergen filter capability on customer-facing menu
- This satisfies Natasha's Law (for PPDS tenants) and the FSA's March 2025 written allergen guidance

### Accessibility

- Target WCAG 2.2 Level AA across all customer-facing pages
- Publish an accessibility statement
- Ensure themed components maintain sufficient colour contrast (relevant to dynamic theme system)
- Test with screen readers for key flows: menu browsing, cart management, order placement

## Penalties

| Law | Maximum Penalty | Enforcer |
|-----|----------------|----------|
| **UK GDPR** | Up to GBP 17.5M or 4% of global annual turnover | ICO |
| **PECR** | Up to GBP 500,000 (serious contraventions) | ICO |
| **Equality Act 2010** | Civil claims — no statutory cap; injury to feelings GBP 1,000-45,000+ | County Court / EHRC |
| **Natasha's Law** | Criminal prosecution; unlimited fines; imprisonment | Local authorities / FSA |
| **Consumer Rights Act 2015** | Civil claims; Trading Standards enforcement | Courts / Trading Standards |
| **DMCCA 2024** | Up to 10% of global turnover; CMA direct enforcement | CMA |

---

## Sources

### Primary Legislation
- [UK GDPR (retained EU law)](https://www.legislation.gov.uk/eur/2016/679/contents)
- [Data Protection Act 2018](https://www.legislation.gov.uk/ukpga/2018/12/contents/enacted)
- [Data (Use and Access) Act 2025](https://www.legislation.gov.uk/ukpga/2025/25/contents/enacted)
- [Privacy and Electronic Communications Regulations 2003](https://www.legislation.gov.uk/uksi/2003/2426/contents)
- [Equality Act 2010](https://www.legislation.gov.uk/ukpga/2010/15/contents)
- [Natasha's Law](https://www.legislation.gov.uk/uksi/2019/1218/contents/made)
- [Consumer Rights Act 2015](https://www.legislation.gov.uk/ukpga/2015/15/contents/enacted)
- [DMCCA 2024](https://www.legislation.gov.uk/ukpga/2024/13/contents/enacted)

### ICO Guidance
- [ICO UK GDPR Guidance Hub](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/)
- [ICO Data Protection Fee Registration](https://ico.org.uk/for-organisations/data-protection-fee/)
- [ICO International Transfers Guidance](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/international-transfers/)

### Food Standards Agency
- [FSA Allergen Guidance for Food Businesses](https://www.food.gov.uk/business-guidance/allergen-guidance-for-food-businesses)

## Last Verified

2026-03-25
