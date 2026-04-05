# EU General Data Protection Regulation (GDPR)

## Applicability

GDPR applies to [Your Platform] when **any EU/EEA resident** uses the platform — regardless of where [Your Platform] is incorporated. This is extraterritorial reach (Art. 3). The Lebanese diaspora in EU countries triggers GDPR compliance. If even one EU-based customer orders through a [Your Platform]-powered tenant, GDPR applies.

**[Your Platform]'s roles**:
- **Processor** when handling tenant customer data (orders, profiles, rewards)
- **Controller** when processing data for its own purposes (platform analytics, billing, waitlist, marketing to tenants)

## Key Requirements

### 1. Lawful Basis for Processing (Art. 6)

| Processing Activity | Lawful Basis | Notes |
|---|---|---|
| Order fulfillment (name, phone, address) | Contract | Necessary to perform the service |
| Account creation | Contract | Necessary for platform access |
| Analytics (<!-- FILL: your analytics tool -->) | Consent | Must be opt-in via cookie banner |
| Marketing emails | Consent | Explicit opt-in required |
| Fraud prevention, security | Legitimate interest | Requires balancing test |
| Tax/legal records | Legal obligation | Retention required by law |
| Loyalty/rewards program | Consent or Contract | Depends on how it's structured |

### 2. Data Minimization (Art. 5(1)(c))

Only collect data adequate, relevant, and limited to what is necessary. Audit each table for fields collected but never used.

### 3. Purpose Limitation (Art. 5(1)(b))

Data collected for ordering must NOT be used for marketing without separate consent. Customer profiles for one restaurant must NOT be shared across tenants without knowledge/consent.

### 4. Storage Limitation (Art. 5(1)(e))

| Data Type | Current Retention | GDPR Assessment |
|---|---|---|
| IndexedDB (offline orders) | 30-day auto-cleanup | COMPLIANT |
| Completed orders (<!-- FILL: your database/backend -->) | Indefinite | REQUIRES POLICY (e.g., 2 years then anonymize) |
| Customer profiles | Indefinite | REQUIRES POLICY (e.g., 24 months inactivity purge) |
| Device sessions | Indefinite | REQUIRES CLEANUP (e.g., 90 days inactivity) |
| Analytics (<!-- FILL: your analytics tool -->) | Per <!-- FILL: your analytics tool --> settings | VERIFY retention period |

### 5. Right of Access — DSAR (Art. 15)

Data subjects can request ALL personal data. **30-day deadline** (extendable 60 days for complex requests). DSAR scope: <!-- FILL: your key tables (e.g., users, customer_profiles, orders, rewards, addresses, push_subscriptions, device_sessions, email_queue) -->, <!-- FILL: your analytics tool --> data, <!-- FILL: your payment provider --> customer data.

### 6. Right to Erasure (Art. 17)

Delete or anonymize on request. Multi-tenant complication: erasure must cover ALL tenants. Recommended approach: anonymize (replace PII with "DELETED_USER_12345") to preserve referential integrity for accounting.

### 7. Right to Data Portability (Art. 20)

Export data in JSON/CSV. In scope: profile, order history, addresses, rewards. Out of scope: derived analytics, audit logs.

### 8. Data Protection Officer (Art. 37)

At current scale (~10 tenants, ~3,300 orders): **NOT required**. Reassess at 100+ tenants / 50,000+ users.

### 9. Data Processing Agreement (Art. 28) — CRITICAL

Multi-tenant model creates a three-layer chain:

```
Tenant (Controller) → [Your Platform] (Processor) → Sub-processors
                                                  ├── <!-- FILL: your database/backend --> (DB)
                                                  ├── <!-- FILL: your hosting provider --> (hosting)
                                                  ├── <!-- FILL: your payment provider --> (payments)
                                                  └── <!-- FILL: your analytics tool --> (analytics)
```

**Required**: DPA with each tenant (part of onboarding). DPAs with <!-- FILL: your database/backend -->, <!-- FILL: your payment provider -->, <!-- FILL: your analytics tool -->, <!-- FILL: your hosting provider -->. Sub-processor list published and maintained.

### 10. Privacy by Design (Art. 25)

| Principle | Status |
|---|---|
| RLS (tenant isolation) | COMPLIANT |
| Encryption in transit (HTTPS) | COMPLIANT |
| Encryption at rest (<!-- FILL: your database/backend -->) | COMPLIANT |
| Cookie consent gating <!-- FILL: your analytics tool --> | COMPLIANT |
| Data minimization | GAP — needs audit |
| Server-side retention policies | GAP |

### 11. Data Breach Notification (Art. 33-34)

- Notify supervisory authority within **72 hours**
- Notify affected data subjects "without undue delay" if high risk
- Notify restaurant tenants (controllers) — [Your Platform] as processor must inform its controllers

### 12. Consent Requirements (Art. 7)

| Criterion | CookieConsent.tsx | Assessment |
|---|---|---|
| Freely given | Two buttons, no pre-selection | COMPLIANT |
| Specific | Mentions "analytics" generically | NEEDS IMPROVEMENT — name specific analytics provider |
| Informed | "Learn more" links to /cookies | VERIFY page exists |
| Unambiguous | Active click required | COMPLIANT |
| Easy to withdraw | No mechanism to change after initial choice | GAP — need footer/settings toggle |
| Record of consent | localStorage only | GAP — server-side logging needed |

### 13. Children's Data (Art. 8)

Ordering food not primarily directed at children. ToS should state minimum age (e.g., 16). Tenant tenants bear primary responsibility for age-appropriate handling.

### 14. Cross-Border Transfers (Art. 44-49)

| Sub-processor | Transfer Mechanism | Status |
|---|---|---|
| <!-- FILL: your database/backend --> | EU-US DPF or EU hosting | VERIFY project region |
| <!-- FILL: your hosting provider --> | EU-US DPF | VERIFY certification |
| <!-- FILL: your payment provider --> | EU-US DPF + SCCs | COMPLIANT |
| <!-- FILL: your analytics tool --> | EU Cloud available | VERIFY hosting region |

### 15. Records of Processing — ROPA (Art. 30)

[Your Platform]'s processing is continuous (not occasional) — ROPA is **REQUIRED** regardless of employee count.

## [Your Platform]-Specific Implications

- Each restaurant = controller, [Your Platform] = processor. DPA required for each.
- Customer identity across tenants: treat each tenant-customer relationship as independent for GDPR. Erasure per-controller unless platform-wide requested.
- Waitlist, billing, platform analytics = [Your Platform]-as-controller processing (needs own privacy notice + lawful basis).
- <!-- FILL: your analytics tool --> consent-gated via CookieConsent component (good). But no consent withdrawal mechanism (gap).
- 30-day IndexedDB cleanup aligns with storage limitation (good). Server-side retention undefined (gap).

## Penalties

| Tier | Maximum | Applies To |
|---|---|---|
| Lower | EUR 10M or 2% global turnover | Processor obligations, records, security, breach notification |
| Upper | EUR 20M or 4% global turnover | Lawful basis, consent, data subject rights, transfers |

**Enforcement trends (2025-2026)**: EUR 7.1B+ total fines since 2018. Processor liability increasing. Consent dark patterns actively enforced. Small SaaS platforms increasingly audited (EUR 10K-500K range for missing DPA, privacy policy, or DSAR capability).

## Sources

- [GDPR Full Text](https://gdpr-info.eu/)
- [ICO Guide to GDPR](https://ico.org.uk/for-organisations/guide-to-data-protection/guide-to-the-general-data-protection-regulation-gdpr/)
- [EDPB Guidelines](https://edpb.europa.eu/our-work-tools/general-guidance/guidelines-recommendations-best-practices_en)
- <!-- FILL: your database/backend DPA link -->
- <!-- FILL: your payment provider GDPR guide link -->

## Last Verified

2026-03-25
