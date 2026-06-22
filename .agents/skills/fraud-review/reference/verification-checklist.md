# Legitimate ACH Change — Verification Checklist

Use when classification is `SUSPICIOUS` or `LOW-RISK-LEGITIMATE`.

**Golden rule:** verify through channels that existed **before** the email.

## Pre-requisites from Fraud Review

Before callback, confirm automated checks:

- [ ] Gateway ACH comparison completed (`DIFFER` or `NEW-SETUP`)
- [ ] Domain result is `DOMAIN-MATCH` or `DOMAIN-HISTORY-MATCH`
- [ ] Corporate website review PASS
- [ ] No `LOOKALIKE` embedded URLs

## Required artifacts

- [ ] W-9 — legal name matches Gateway
- [ ] Voided check or bank letter — routing/account; payee matches SP legal name
- [ ] SP number and legal name on request

## Out-of-band verification (mandatory for SUSPICIOUS)

- [ ] Call **Gateway on-file phone** only
- [ ] Ask caller to confirm **old** banking last-4 before accepting new
- [ ] Document verifier, date, number dialed

## After verification succeeds

Operator path only: route to Vendor Maintenance; tags `ach-change-verified`.

## After verification fails

`HIGH-RISK-BEC`; tags `bec-risk`, `banking-change-unverified`, `security-review`.

## Never (this skill)

- Contact the service provider (no public reply, email, or forward)
- Update Gateway banking from this skill
- Forward to `invoices@vixxo.com`
