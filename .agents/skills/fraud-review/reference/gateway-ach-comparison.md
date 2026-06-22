# Gateway ACH Comparison

Fraud Review **must** compare requested banking against Gateway on-file data
before final classification.

## Tool discovery

At the start of a session, list Gateway MCP tools and select the provider
lookup that returns payment / remittance fields. Common patterns on this
tenant:

| Intent | Likely tool name pattern |
|--------|--------------------------|
| Provider by SP # | `gateway_get_service_provider`, `gateway_get_provider` |
| Provider search | `gateway_search_service_providers`, `gateway_search_providers` |
| SR context (secondary) | `gateway_get_service_request` — use only for SP # extraction, not as primary banking source |

Read the tool schema before calling. If banking fields are nested (e.g.
`paymentProfile`, `remittance`, `bankDetails`), drill into the response.

## Fields to pull (on-file)

Record every field Gateway returns for payment setup, including:

- `bankName` / `financialInstitution`
- `routingNumber` / `aba` / `routing`
- `accountNumber` / `account` (store full internally; display last 4 only)
- `accountType` (checking / savings)
- `paymentMethod` (ACH / wire / check)
- `beneficiaryName` / `accountHolderName`
- `remitToAddress` (if wire)

Also pull identity fields used for cross-check:

- Legal name, DBA, SP number, status
- Primary email, website URL, phone

## Normalization before compare

- Strip spaces and dashes from routing numbers.
- Compare account numbers on last 4 when full number unavailable in email.
- Treat leading-zero routing differences as significant — do not auto-trim.
- Bank name: case-insensitive; accept common abbreviations (e.g. "BofA" vs
  "Bank of America") only when routing also matches.

## Comparison results

| Result | Condition |
|--------|-----------|
| `MATCH` | Routing and account (last 4) both match on-file |
| `DIFFER` | At least one of routing, account, bank name, or beneficiary differs |
| `MISSING-ON-FILE` | Gateway has no banking record (onboarding / new SP) |
| `MISSING-IN-REQUEST` | Email asks for update but omits routing or account |
| `PARTIAL` | Only one of routing/account provided |

## How comparison affects classification

| ACH result | Domain | Website | Typical classification |
|------------|--------|---------|------------------------|
| `MATCH` | match | pass | Low priority — duplicate request |
| `DIFFER` | match | pass | `SUSPICIOUS` → `LOW-RISK` after artifacts + callback |
| `DIFFER` | mismatch | fail | `HIGH-RISK-BEC` |
| `MISSING-ON-FILE` | match | pass | `SUSPICIOUS` or `LOW-RISK` (onboarding path) |
| `MISSING-IN-REQUEST` | any | any | `INSUFFICIENT-DATA` |

## When Gateway lookup fails

- SP number in email not found → try legal name search; if still missing,
  `INSUFFICIENT-DATA` and do not trust banking in email.
- Gateway timeout → retry once; if still failing, complete domain and website
  checks and note `gateway-unavailable` in packet.

## Output table (mandatory)

Every Fraud Review packet includes:

```
| Field | On file (Gateway) | Requested (email) | Result |
| Routing | ••• | ••• | DIFFER |
| Account (last 4) | ••• | ••• | DIFFER |
| Bank name | ••• | ••• | MATCH |
| Beneficiary | ••• | ••• | MATCH |
```
