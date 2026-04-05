# Food Safety & Allergen Disclosure

<!-- NOTE: This reference file is for FOOD SERVICE businesses (restaurants, cafes, etc.).
     If your platform is in a different industry, replace this file with your industry's
     equivalent regulations (e.g., HIPAA for healthcare, FERPA for education). -->

## Applicability

Food safety regulations apply to **all businesses involved in the food supply chain**, including online ordering platforms. While [Your Platform] does not prepare food, it facilitates food ordering — creating obligations around allergen information display, nutritional data, and food safety compliance enablement for restaurant tenants.

**Key question**: Is [Your Platform] a "food business operator" (FBO)? In most jurisdictions, no — tenants are the FBOs. But [Your Platform] has a **platform facilitation obligation**: failing to provide allergen capability could expose restaurant tenants to non-compliance, creating churn risk and potential negligence claims.

### Applicable Regulations

| Regulation | Jurisdiction | Scope |
|-----------|-------------|-------|
| **EU FIR 1169/2011** (Food Information to Consumers Regulation) | EU | Mandatory allergen disclosure for all food sold to consumers, including distance selling (online ordering) |
| **Natasha's Law** (Food Information (Amendment) (England) Regulations 2019) | UK (England) | PPDS food must list all ingredients with 14 allergens emphasised |
| **FDA FALCPA** (Food Allergen Labeling and Consumer Protection Act 2004) | US | 8 major allergens must be declared on packaged food labels |
| **FDA FASTER Act** (Food Allergy Safety, Treatment, Education, and Research Act 2021) | US | Added sesame as the 9th major allergen (effective January 2023) |
| **Codex Alimentarius** (FAO/WHO) | International | Global food standards framework, basis for national regulations |
| **FSANZ Food Standards Code** | Australia/NZ | Allergen declaration requirements for packaged and unpackaged food |
| **Safe Food for Canadians Regulations** | Canada | Allergen declaration on pre-packaged food, priority allergens list |

## Key Requirements

### Allergen Lists by Jurisdiction

**EU 14 Allergens** (FIR 1169/2011 Annex II) — the global superset:

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

**US 9 Major Allergens** (FALCPA + FASTER Act):
Milk, Eggs, Fish, Crustacean shellfish, Tree nuts, Peanuts, Wheat, Soybeans, Sesame

**Australia/NZ**: Similar to EU list, with some differences in groupings.

**Engineering decision**: Use the **EU 14 allergens as the data model** — it's the superset. Other jurisdictions' requirements are subsets.

### Distance Selling (Online Ordering) Requirements

1. **EU FIR Art. 14 — Distance Selling**: Allergen information must be available to the consumer **before the purchase is concluded** (i.e., before checkout). It must be provided through the distance selling medium (the app/website) or by other appropriate means clearly identified by the FBO.

2. **UK FIR 2014 Regulation 5**: For distance selling, mandatory food information (including allergens) must be available before the purchase and at the time of delivery. The name of the food and any allergen-containing ingredients must be available before purchase.

3. **US**: No federal distance-selling-specific allergen rule for restaurant food. However, state and local regulations may apply. FDA's Model Food Code encourages allergen awareness for food service.

4. **Practical implication**: Menu items displayed in the [Your Platform] ordering app MUST show allergen information before the customer adds them to cart. "Ask staff" is not sufficient for distance/online selling in EU/UK.

### Allergen Display Requirements

5. **Emphasis requirement** (EU/UK): Allergens must be **emphasised** in the ingredients list — typically bold, italic, underline, or different colour. The method must be clearly distinguishable from the rest of the text.

6. **"Contains" statement** (US): The 9 major allergens must be declared either in the ingredient list (with the common name) or in a separate "Contains" statement immediately after the ingredient list.

7. **"May contain" / cross-contamination**: Precautionary allergen labelling ("may contain traces of...") is NOT regulated in most jurisdictions but is industry best practice. It should be a separate field from "Contains" to avoid confusion.

### Nutritional Information

8. **EU FIR 1169/2011**: Mandatory nutritional declaration (energy, fat, saturates, carbohydrate, sugars, protein, salt) for pre-packaged food. Exempt for food supplied by mass caterers (tenants), but encouraged.

9. **US FDA**: Tenants and food establishments with 20+ locations must display calorie counts on menus (ACA Section 4205). Does not apply to small tenants, but many voluntarily comply.

10. **Platform responsibility**: Even where not legally required for tenants, providing the **capability** for nutritional data is a competitive advantage and future-proofs against expanding regulations.

### Platform Facilitation Obligations

The minimum viable compliance posture is: **provide the schema, provide the UI, prompt tenants to fill it in, and display it to customers**.

- Provide allergen data fields in the menu editor
- Display allergen information on customer-facing menu (before checkout)
- Support "Contains" and "May contain" as separate concepts
- Display a standard disclaimer: "Allergen information is provided by the restaurant. If you have a severe allergy, please contact the restaurant directly to confirm."
- Support allergen filtering on the customer menu (competitive advantage)
- Maintain audit trail for allergen changes (legally valuable if an incident occurs)

## [Your Platform]-Specific Implications

- **Menu item schema should support allergen fields** — the 14 EU allergens as a boolean/multi-select field on each menu item. Schema suggestion: `allergens` (array of enum values) and `may_contain_allergens` (separate array for cross-contamination) on the <!-- FILL: your menu/product table -->.

- **Allergen display on customer-facing menu** — allergen icons or labels must appear on the menu item card or detail view, before "add to cart." Small allergen icons with a legend, plus text list for screen readers (accessibility).

- **Tenant admin allergen picker** — admin menu editor needs a multi-select allergen picker. Default to "no allergens set" with a visible warning state (distinct from "allergen-free" which implies restaurant confirmed it).

- **"Contains" vs "May contain" distinction** — two separate fields. "Contains" = definitive ingredient. "May contain" = cross-contamination risk. Both displayed to customer, visually differentiated.

- **Nutritional info fields** — calories, protein, carbohydrates, fat, fiber, sodium at minimum. Optional fields in schema, displayed when populated.

- **Cross-restaurant allergen consistency** — use a standardized allergen enum (not free text) so allergen filtering works across all tenants. A "nut-free" filter should give consistent results.

- **Current state: no allergen fields in <!-- FILL: your menu/product table -->** — this is a **compliance gap** for EU/UK markets. Any restaurant in the EU/UK using [Your Platform] for online ordering would be non-compliant with FIR 1169/2011 without allergen disclosure capability.

- **Dietary preference filters** — beyond legal allergens: vegetarian, vegan, halal, kosher, gluten-free lifestyle. Not legally mandated but a significant UX expectation. Can be built on the same schema.

- **Audit trail for allergen changes** — if a restaurant changes an item's allergen status, record it. In an allergen-related incident, the ability to show historical allergen data is legally valuable.

- **Disclaimer architecture** — standard disclaimer on every menu page. Prominent, not buried in ToS. Creates a liability buffer while still providing useful information.

## Penalties

- **EU**: Member state enforcement. Administrative fines (vary by country). Criminal penalties for serious violations causing harm (e.g., France: up to 2 years imprisonment and EUR 300,000 fine). Product recalls and business closure orders.

- **UK**: Food Safety Act 1990 and Food Information Regulations 2014. Unlimited fines for food safety offenses. Criminal prosecution (up to 2 years imprisonment). Increased enforcement in the Natasha's Law era.

- **US**: FDA enforcement. Warning letters (public, reputational damage). Mandatory recalls. Injunctions. Criminal prosecution for knowing violations (up to 3 years felony, 1 year misdemeanor under FDCA).

- **Allergen-related incidents**: Beyond regulatory penalties — wrongful death lawsuits (settlements in millions), personal injury claims, class actions, reputational damage. Platform liability is an emerging area with risk direction toward greater platform responsibility.

## Sources

- [EU FIR 1169/2011](https://eur-lex.europa.eu/legal-content/EN/ALL/?uri=CELEX:32011R1169)
- [UK FSA Allergen Guidance](https://www.food.gov.uk/business-guidance/allergen-guidance-for-food-businesses)
- [FDA FALCPA](https://www.fda.gov/food/food-allergensgluten-free-guidance-documents-regulatory-information/food-allergen-labeling-and-consumer-protection-act-2004-falcpa)
- [FDA FASTER Act](https://www.fda.gov/food/food-allergensgluten-free-guidance-documents-regulatory-information/food-allergy-safety-treatment-education-and-research-faster-act)
- [Codex Alimentarius — Food Labelling](https://www.fao.org/fao-who-codexalimentarius/thematic-areas/food-labelling/en/)
- [FSANZ Food Standards Code](https://www.foodstandards.gov.au/code)
- [Natasha's Law](https://www.food.gov.uk/business-guidance/introduction-to-allergen-labelling-changes-ppds)

## Last Verified

2026-03-25
