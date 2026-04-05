# Payment Card Industry Data Security Standard (PCI DSS 4.0)

## Applicability

PCI DSS applies to **all entities** that store, process, or transmit cardholder data. There are no size exemptions — even a single transaction brings you into scope.

**[Your Platform]'s position**: [Your Platform] uses Stripe Elements / Stripe Checkout. Card data never touches [Your Platform]'s servers — it flows directly from the customer's browser to Stripe's PCI-certified infrastructure via iFrame isolation. This means [Your Platform] qualifies for **SAQ A** (Self-Assessment Questionnaire A), the lightest compliance level with approximately **22 requirements**.

**SAQ A eligibility criteria** (all must be true):
- Card-not-present transactions only (e-commerce / online ordering)
- All payment processing outsourced to a PCI DSS validated third-party (Stripe)
- No electronic storage, processing, or transmission of cardholder data on [Your Platform] systems
- [Your Platform]'s website does not serve card capture pages (Stripe Elements iFrame handles this)
- [Your Platform] has confirmed PCI DSS compliance of its payment processor (Stripe is a PCI Level 1 Service Provider)

**If [Your Platform] ever handles card numbers directly** (e.g., custom card input fields, server-side card processing, logging card data), it jumps to **SAQ D** — over 300 requirements including penetration testing, network segmentation, encryption, and formal audit. This would be an order-of-magnitude increase in compliance burden. **Do not go here.**

**Stripe's PCI compliance** covers their side of the responsibility. Stripe maintains PCI DSS Level 1 certification (the highest level, validated by annual third-party audit).

## Key Requirements

### SAQ A Requirements (Stripe Elements / Stripe Checkout)

1. **Use HTTPS everywhere** (TLS 1.2 or higher) — all pages that include Stripe.js or redirect to Stripe Checkout must be served over HTTPS. Mixed content is a disqualification.

2. **No storage of cardholder data on [Your Platform] servers** — no card numbers (PAN), CVVs, expiration dates, or magnetic stripe data may exist anywhere in [Your Platform]'s infrastructure, including logs, databases, IndexedDB, localStorage, error tracking services, or analytics.

3. **Stripe.js loaded from js.stripe.com** (not self-hosted) — Stripe.js must be loaded directly from Stripe's CDN. Self-hosting or proxying Stripe.js breaks SAQ A eligibility.

4. **iFrame isolation** — Stripe Elements renders card input fields in a cross-origin iFrame controlled by Stripe. [Your Platform]'s JavaScript cannot read card data from the iFrame. Do not attempt to manipulate the iFrame contents.

5. **Quarterly vulnerability scans** — if directly internet-facing (it is, via Vercel), quarterly external vulnerability scans by an Approved Scanning Vendor (ASV) may be required depending on acquirer requirements. Many acquirers waive this for SAQ A merchants.

6. **Annual SAQ A self-assessment** — complete and sign the SAQ A questionnaire annually. Submit to acquiring bank if requested. Retain documentation for at least 3 years.

7. **Incident response plan for payment data breaches** — even under SAQ A, must have a plan for suspected security incidents that could impact payment data.

8. **Access control for Stripe Dashboard** — restrict access to authorized personnel only. Use individual accounts (no shared logins). Enable two-factor authentication. Review access quarterly.

9. **Secure Stripe API key management** — API keys stored as environment variables, never committed to source control, never exposed in client-side code, never logged. Use restricted keys with minimum necessary permissions. Publishable keys (client-side) and secret keys (server-side) serve different purposes — never use secret keys client-side.

10. **PCI DSS 4.0 compliance mandatory as of March 31, 2025** — version 3.2.1 is sunset. Key 4.0 additions for SAQ A: explicit requirement for inventory of all payment page scripts, monitoring for unauthorized changes to payment pages, and stricter control of third-party scripts.

### What Would Change Under SAQ D (AVOID)

If [Your Platform] ever directly handles card data, the compliance scope explodes:

- **300+ requirements** across 12 requirement families
- **Annual penetration testing** by qualified security assessor
- **Network segmentation** — cardholder data environment isolated
- **Full cardholder data encryption** at rest and in transit
- **Key management** — encryption key lifecycle, split knowledge, dual control
- **Intrusion detection / prevention systems** (IDS/IPS)
- **File integrity monitoring** on all system components
- **Formal security policy** reviewed annually
- **Security awareness training** for all personnel
- **Log monitoring** — daily review of all security events
- **Estimated cost**: $50,000-$500,000+ annually

**Engineering mandate**: Never implement custom card input forms. Never log, store, or process card numbers. Never proxy Stripe.js. Keep using Stripe Elements / Stripe Checkout. SAQ A is the only sustainable path.

## [Your Platform]-Specific Implications

- **Stripe Elements = SAQ A** — verify no custom card forms exist anywhere in the codebase. Search for input elements that accept card numbers, CVV, or expiry — none should exist.

- **Stripe API keys in environment variables** — STRIPE_SECRET_KEY and STRIPE_PUBLISHABLE_KEY must live in .env (gitignored). Vercel environment variables are the production equivalent.

- **HTTPS enforced by Vercel** — Vercel automatically provisions TLS certificates and enforces HTTPS. This satisfies the TLS 1.2+ requirement. No additional configuration needed.

- **No card data in IndexedDB, localStorage, or Supabase** — the offline-first architecture (IndexedDB for order sync) must never store payment card information. Orders should reference a Stripe Payment Intent ID, not card details.

- **Multi-tenant Stripe Connect** — tenants connect their own Stripe accounts. Shared responsibility model:
  - [Your Platform] (platform): Secure integration, SAQ A compliance, protecting Connect account credentials.
  - Tenant tenant: Their own Stripe account security, PCI compliance for card-present (POS) transactions.
  - Document this responsibility split in onboarding and ToS.

- **Refund processing** — refunds through Stripe's API or Dashboard, not custom logic requiring original card data. Reference Stripe Payment Intent IDs only.

- **Logging and error tracking** — ensure no payment-related PII leaks into error tracking. Stripe webhook payloads may contain customer email/name but never card numbers. Sanitize webhook logging regardless.

- **Third-party script inventory** (PCI DSS 4.0 addition) — maintain inventory of all JavaScript loaded on payment pages. Unauthorized scripts could compromise SAQ A status.

## Penalties

- **PCI non-compliance fines**: $5,000 to $100,000 per month from payment card brands, imposed on acquirer and passed to merchant.
- **Processing termination**: Card brands can revoke ability to accept card payments. For an ordering platform, this is existential.
- **Data breach liability**: Non-compliant merchant bears liability for fraudulent charges, card reissuance costs ($3-$10/card), forensic investigation ($20,000-$100,000+), and notification costs.
- **Increased transaction fees**: Non-compliant merchants may face increased per-transaction fees.
- **Legal liability**: Class action lawsuits, regulatory fines under GDPR/CCPA if personal data also compromised.

## Sources

- [PCI Security Standards Council](https://www.pcisecuritystandards.org/)
- [Stripe PCI DSS Compliance Guide](https://stripe.com/docs/security/guide)
- [SAQ A v4.0 Template](https://www.pcisecuritystandards.org/document_library/)
- [Stripe Connect Documentation](https://stripe.com/docs/connect)

## Last Verified

2026-03-25
