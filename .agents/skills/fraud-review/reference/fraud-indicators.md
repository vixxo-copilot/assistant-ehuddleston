# Fraud Indicator Rubric

Use after Gateway ACH comparison, domain verification, and website review.
See [domain-and-website-verification.md](domain-and-website-verification.md)
and [gateway-ach-comparison.md](gateway-ach-comparison.md).

## Strong indicators (any one → HIGH-RISK-BEC)

| ID | Indicator |
|----|-----------|
| S1 | Unsolicited banking change with urgency |
| S2 | `DOMAIN-MISMATCH`, `DOMAIN-LOOKALIKE`, or `FREE-WEBMAIL` for established corporate SP |
| S3 | `DIFFER` ACH comparison + domain or website fail |
| S4 | Reply-To domain ≠ From org domain (webmail / unrelated) |
| S5 | No verification artifacts (voided check, W-9, bank letter) |
| S6 | Embedded URL class `LOOKALIKE` or credential-harvest page |
| S7 | Website brand fail — site does not match Gateway legal name |
| S8 | Sender domain not listed on SP official website |
| S9 | Dangerous attachment type from unknown sender |
| S10 | Vixxo or SP domain typosquat |

## Soft indicators (two or more → SUSPICIOUS)

| ID | Indicator |
|----|-----------|
| W1 | Generic salutation + urgent payment language |
| W2 | SP name in body ≠ Gateway legal name |
| W3 | No prior Freshdesk history from this domain |
| W4 | Bank institution change vs on-file |
| W5 | `PARTIAL` or `MISSING-IN-REQUEST` banking fields |
| W6 | Embedded URL class `UNKNOWN` |
| W7 | `MATCH` ACH — possible duplicate resend |

## Legitimacy signals (never sufficient alone)

| ID | Signal |
|----|--------|
| L1 | `DOMAIN-MATCH` + website PASS |
| L2 | `DIFFER` ACH with voided check + W-9 matching legal name |
| L3 | `DOMAIN-HISTORY-MATCH` (≥3 prior tickets) |
| L4 | Operator callback to Gateway on-file phone confirmed |
| L5 | Continuation of verified Vixxo-initiated ticket |

## Scoring

```
IF any strong (S1–S10): HIGH-RISK-BEC
ELSE IF soft count >= 2: SUSPICIOUS
ELSE IF L1+L2 and no strong/soft: LOW-RISK-LEGITIMATE
ELSE IF cannot resolve SP: INSUFFICIENT-DATA
ELSE: SUSPICIOUS
```

## Cluster alert

3+ requests, same vendor or bank last-4, within 7 days → stop batch; escalate.
