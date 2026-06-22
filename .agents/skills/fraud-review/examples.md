# Fraud Review — Examples

## Example 1 — HIGH-RISK-BEC (domain + ACH fail)

**From:** `billing@acme-hvac-payments.net` | **Gateway domain:** `acme-hvac.com`

**Gateway ACH:** routing `122000661` / account •••4521 on file  
**Requested:** routing `122000661` / account •••9901 (DIFFER)

**Website:** `acme-hvac-payments.net` — login page, not on Gateway website field  
**Official site:** `acme-hvac.com` — no mention of payments.net

**Domain result:** DOMAIN-LOOKALIKE | **Classification:** HIGH-RISK-BEC

---

## Example 2 — SUSPICIOUS (ACH change, domain OK, thin artifacts)

**From:** `ap@acme-hvac.com` | **Gateway domain:** `acme-hvac.com`  
**ACH:** DIFFER (new bank) | **Website:** PASS — sender domain in footer  
**Artifacts:** none

**Classification:** SUSPICIOUS → callback + voided check required

---

## Example 3 — LOW-RISK-LEGITIMATE

**From:** `ap@acme-hvac.com` | Domain: MATCH | Website: PASS  
**ACH:** DIFFER | Voided check + W-9 attached, names match Gateway

**Classification:** LOW-RISK-LEGITIMATE → VM handoff after callback

---

## Example 4 — MATCH (duplicate)

**ACH comparison:** MATCH (same routing + last 4 as Gateway)  
**Domain:** MATCH

**Classification:** Note duplicate resend; no banking update needed

---

## Example — Freshdesk internal note (excerpt)

```
FRAUD REVIEW — POTENTIAL FRAUD (HIGH RISK)
Classification: HIGH-RISK-BEC
Reviewed: 2026-06-16 | Ticket: #44821 | Mailbox: aphelp

── WHY THIS WAS FLAGGED ──
• S2: Sender domain acme-hvac-payments.net is a lookalike of Gateway domain acme-hvac.com
• S3: ACH DIFFER — on-file acct •••4521 vs requested •••9901 (same routing)
• S8: Sender domain not found on official website acme-hvac.com
• S6: Embedded URL https://acme-hvac-payments.net/login — LOOKALIKE credential page
• S5: No voided check, W-9, or bank letter attached
• S1: Unsolicited change with urgency ("before Friday payment run")

── VERIFY BEFORE ANY BANKING UPDATE ──
[ ] Callback to Gateway on-file phone ONLY
[ ] Confirm current banking last-4 with caller before accepting new details
…
```
