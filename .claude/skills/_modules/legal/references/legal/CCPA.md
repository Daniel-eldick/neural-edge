# California Consumer Privacy Act (CCPA) + CPRA

## Applicability

### CCPA Thresholds (must meet ONE)

| Threshold | Criteria | [Your Platform] Today |
|---|---|---|
| Revenue | > $25M annual gross | Likely below |
| Data volume | 100K+ CA consumers/households | Likely below |
| Revenue source | 50%+ from selling/sharing PI | No |

**Even below thresholds**: **CalOPPA** requires a privacy policy for ANY website collecting CA resident data. No revenue threshold. This is a Day 1 requirement.

**CPRA amendments** (effective Jan 2023): Created California Privacy Protection Agency (CPPA), added right to correct, right to limit sensitive PI use, expanded "sharing" definition for cross-context behavioral advertising. Tripled penalties for violations involving minors.

## Key Requirements

### 1. Right to Know
Consumers can request: categories of PI collected, specific pieces, sources, purposes, third parties shared with.

### 2. Right to Delete
Must cascade across all systems: <!-- FILL: your database/backend --> tables, <!-- FILL: your payment provider -->, <!-- FILL: your analytics tool -->, and restaurant tenant copies.

### 3. Right to Opt-Out of Sale/Sharing
"Do Not Sell or Share My Personal Information" link required. CPRA expanded to cover "sharing" for behavioral advertising.

### 4. Right to Non-Discrimination
Cannot degrade service because a consumer exercised CCPA rights. Opt-out users must still order food normally.

### 5. Right to Correct (CPRA)
Allow consumers to correct inaccurate PI. In-app profile editing + correction request flow for data they can't self-edit.

### 6. Right to Limit Sensitive PI (CPRA)
[Your Platform] collects sensitive PI: precise geolocation (delivery addresses), financial account info (via <!-- FILL: your payment provider -->). Use must be limited to order fulfillment.

### 7. Privacy Policy Requirements (CalOPPA + CCPA)

Must disclose: categories of PI, sources, purposes, third parties, consumer rights, "Do Not Sell" link, financial incentive programs (rewards/loyalty), retention periods, how to submit requests, last update date.

### 8. "Sale" Definition
Does sharing customer data with restaurant tenants = "sale"? **Likely no if** tenants are service providers under contract that prohibits independent use of customer data.

**Risk**: If tenants use [Your Platform] customer data for own marketing (email blasts outside platform), could be reclassified as "sale." ToS must explicitly prohibit this.

### 9. Service Provider Contracts
Written contracts must: specify business purpose, prohibit selling/sharing, prohibit use outside direct relationship, require notification if can't meet obligations.

### 10. Financial Incentive Programs (Rewards)
Loyalty/rewards programs require disclosure of: material terms, opt-in/opt-out, how data value is calculated, how incentive relates to data value.

## [Your Platform]-Specific Implications

- CalOPPA privacy policy required before any CA user accesses the platform (Day 1)
- "Do Not Sell" link recommended even if no technical "sale" occurs (preempts enforcement risk)
- Tenant tenant contracts must prohibit independent use of customer data
- <!-- FILL: your analytics tool -->: verify DPA classifies them as service provider, not third party
- <!-- FILL: your payment provider -->: service provider exemption applies (compliant DPA in place)
- Multi-tenant data flow documentation required (customer → [Your Platform] → restaurant → ?)

## Penalties

| Type | Amount | Enforced By |
|---|---|---|
| Unintentional | $2,500/violation | CPPA / CA AG |
| Intentional | $7,500/violation | CPPA / CA AG |
| Minor (under 16) | $7,500/violation | CPPA / CA AG |
| Data breach | $100-$750/consumer/incident (private action) | Class action lawsuits |

"Per violation" = per affected consumer. 10K affected consumers = $25M-$75M potential exposure.

## Sources

- [CCPA Full Text](https://leginfo.legislature.ca.gov/faces/codes_displayText.xhtml?division=3.&part=4.&lawCode=CIV&title=1.81.5)
- [CPRA Full Text (Proposition 24)](https://vig.cdn.sos.ca.gov/2020/general/pdf/topl-prop24.pdf)
- [CalOPPA](https://leginfo.legislature.ca.gov/faces/codes_displayText.xhtml?lawCode=BPC&division=8.&title=&part=&chapter=22.&article=)
- [CPPA Official Site](https://cppa.ca.gov/)
- [CA AG CCPA Guidance](https://oag.ca.gov/privacy/ccpa)

## Last Verified

2026-03-25
