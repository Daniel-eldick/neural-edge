# Legal Compliance Knowledge Base — Index

> Master index mapping jurisdictions to applicable regulations and reference files. Used by the `/legal-compliance` skill at runtime.

## Jurisdiction → Regulation Map

| Jurisdiction | Applicable References | Key Regulations |
|-------------|----------------------|-----------------|
| **EU** | GDPR, WCAG, PCI-DSS, FOOD-SAFETY, MARKETING, CONSUMER-PROTECTION | GDPR, EAA (accessibility), FIR 1169/2011 (allergens), UCPD (marketing), CRD (consumer rights), DSA (platform liability) |
| **US** | CCPA, WCAG, PCI-DSS, FOOD-SAFETY, MARKETING, CONSUMER-PROTECTION | CCPA/CPRA, CalOPPA, ADA Title III, FALCPA/FASTER Act, FTC Act §5, CAN-SPAM, Lanham Act |
| **UK** | UK-GDPR, WCAG, PCI-DSS, FOOD-SAFETY, MARKETING, CONSUMER-PROTECTION | UK GDPR + DUAA 2025, PECR, Equality Act 2010, Natasha's Law, CRA 2015, DMCCA 2024 |
| **Canada** | GDPR (as baseline), WCAG, PCI-DSS, FOOD-SAFETY, MARKETING, CONSUMER-PROTECTION | PIPEDA, CASL ($10M fines), Accessible Canada Act, AODA (Ontario), Safe Food for Canadians Regulations |
| **Australia** | GDPR (as baseline), WCAG, PCI-DSS, FOOD-SAFETY, MARKETING, CONSUMER-PROTECTION | Privacy Act 1988, APPs, DDA 1992, ACL, Spam Act 2003, FSANZ Code |
| **Lebanon** | PCI-DSS, CONSUMER-PROTECTION | Law No. 81/2018 (e-transactions), BDL Decision 13790 (payments), Law No. 220/2000 (disability rights) |
| **Global** | All files | GDPR as baseline satisfies most jurisdictions |

## Reference Files

| File | Domain | Regulations Covered | Last Verified |
|------|--------|-------------------|---------------|
| [GDPR.md](GDPR.md) | Data Privacy (EU) | GDPR (Art. 5-49), lawful basis, DSAR, DPA, consent, breach notification, cross-border transfers | 2026-03-25 |
| [CCPA.md](CCPA.md) | Data Privacy (US) | CCPA, CPRA, CalOPPA, financial incentive programs (rewards/loyalty) | 2026-03-25 |
| [UK-GDPR.md](UK-GDPR.md) | Data Privacy + Consumer (UK) | UK GDPR, DUAA 2025, PECR, Equality Act 2010, Natasha's Law, CRA 2015, DMCCA 2024 | 2026-03-25 |
| [WCAG.md](WCAG.md) | Accessibility | WCAG 2.2 AA, EAA (EU), ADA Title III (US), Equality Act (UK), DDA (AU), AODA (CA) | 2026-03-25 |
| [PCI-DSS.md](PCI-DSS.md) | Payment Security | PCI DSS 4.0, SAQ A (Stripe Elements), Stripe Connect shared responsibility | 2026-03-25 |
| [FOOD-SAFETY.md](FOOD-SAFETY.md) | Food & Allergens | EU FIR 1169/2011, Natasha's Law, FALCPA, FASTER Act, Codex Alimentarius, FSANZ | 2026-03-25 |
| [MARKETING.md](MARKETING.md) | Advertising & Anti-Spam | FTC Act §5, Lanham Act, CAN-SPAM, CASL, UCPD, PECR, competitor comparison rules | 2026-03-25 |
| [CONSUMER-PROTECTION.md](CONSUMER-PROTECTION.md) | Consumer Rights | CRD (EU), CRA 2015 (UK), DMCCA 2024, FTC Act, ACL (AU), right of withdrawal, pricing transparency | 2026-03-25 |

## How to Use This Index

1. **Monthly audit** (`/legal-compliance`): Read all files, run all checks
2. **Market gate** (`/legal-compliance gate <jurisdiction>`): Read INDEX.md → identify applicable files → read only those → run filtered checks
3. **Ad-hoc counsel** (`/legal-compliance "question"`): Identify relevant domains → read applicable files → reason from regulations

## Maintenance

- **Staleness rule**: Each file has a `Last Verified` date. If > 6 months old, flag as YELLOW and recommend `/research` to refresh.
- **Adding regulations**: Create a new `.md` file, follow the template (Applicability → Key Requirements → [Your Platform]-Specific → Penalties → Sources → Last Verified), add to this index.
- **Updating laws**: Edit the relevant `.md` file, update `Last Verified` date, update this index if the regulation mapping changed.

## Template for New Reference Files

```markdown
# [Regulation Name]

## Applicability
[When does this apply to [Your Platform]? Jurisdictional triggers.]

## Key Requirements
[Numbered list of requirements with practical implications.]

## [Your Platform]-Specific Implications
[How each requirement maps to [Your Platform]'s architecture, features, and operations.]

## Penalties
[Fines, enforcement actions, private right of action.]

## Sources
[Primary legislation links, regulatory guidance links.]

## Last Verified
YYYY-MM-DD
```
