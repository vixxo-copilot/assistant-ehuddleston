# Domain and Website Verification

Fraud Review requires **both** domain alignment and live website checks.

## Part 1 — Email domain verification

### Domains to collect

1. **Request domains:** `From`, `Reply-To`, any `Cc` from external senders.
2. **On-file domains:**
   - Registrable domain from Gateway primary email
   - Registrable domain from Gateway website URL
   - Domains from prior Freshdesk tickets for the same SP (last 12 months)

### Normalization

- Lowercase; strip display names.
- Extract registrable domain (eTLD+1). Examples:
  - `billing@acme-hvac.com` → `acme-hvac.com`
  - `user@mail.acme-hvac.com` → `acme-hvac.com`
- Ignore `vixxo.com` internal forwarders when determining the **external**
  requester domain.

### Match rules

| Result | Criteria |
|--------|----------|
| `DOMAIN-MATCH` | Request domain equals on-file email or website domain |
| `SUBDOMAIN-MATCH` | Request is subdomain of on-file org domain (e.g. `ap.sp.com` vs `sp.com`) |
| `DOMAIN-HISTORY-MATCH` | Matches dominant domain in ≥3 prior tickets for SP |
| `DOMAIN-MISMATCH` | No relationship to on-file or historical domains |
| `DOMAIN-LOOKALIKE` | Levenshtein / homoglyph close to SP domain but not equal |
| `FREE-WEBMAIL` | gmail.com, yahoo.com, outlook.com, hotmail.com, icloud.com, proton.me, aol.com, live.com |

### Lookalike examples

- `vixx0.com`, `vixxo-payments.com` (Vixxo spoof — always strong)
- `acme-hvac.co` vs `acme-hvac.com`
- `acmehvac.com` vs `acme-hvac.com`

### Required packet lines

```
Sender domain: acme-hvac.com
Gateway domain: acme-hvac.com
Domain result: DOMAIN-MATCH
Reply-To domain: gmail.com → S4 flag if From is corporate
```

---

## Part 2 — Website review

Use `WebFetch` on every review. **Read only** — no logins, no form posts.

### 2a. Corporate website (always)

**URL priority:**

1. Gateway `website` / `websiteUrl` field
2. `https://<sender-registrable-domain>`
3. `https://www.<sender-registrable-domain>`

**Fetch:** homepage; if thin, also `/contact`, `/about`, or footer links.

**Record:**

| Check | Pass | Fail |
|-------|------|------|
| Resolves | Real business site | Parked, for-sale, unrelated |
| Brand | Name matches Gateway legal name | Wrong company |
| Email on site | Sender domain or same-org email listed | Only unrelated domains |
| Phone | Optional note vs Gateway phone | — |

### 2b. Embedded email URLs (each link)

For every `http(s)://` in the body:

1. Fetch URL; note final domain after redirects (max 3 hops).
2. Classify:

| Class | Examples |
|-------|----------|
| `SP-OK` | Same org as Gateway website |
| `BANK-OK` | Known FI domain matching stated bank |
| `FILE-HOST` | Dropbox, Google Drive — neutral; verify artifact separately |
| `LOOKALIKE` | Login/payment page on wrong domain |
| `UNKNOWN` | Cannot classify — treat as soft risk |

**Never** follow links that download executables or prompt for credentials.

### Website section in packet (mandatory)

```markdown
### Websites reviewed
- https://acme-hvac.com — loads; brand matches; billing@acme-hvac.com in footer — PASS
- https://acme-hvac-payments.net — login form, not SP domain — FAIL (LOOKALIKE)
```

---

## Combined failure = high risk

Escalate to `HIGH-RISK-BEC` when **any**:

- `DOMAIN-MISMATCH` or `DOMAIN-LOOKALIKE` on a `DIFFER` ACH comparison
- Corporate website fails brand match
- Sender domain not found anywhere on official website
- Embedded URL is `LOOKALIKE`

Legitimate path requires `DOMAIN-MATCH` (or history match) **and** website PASS
**and** successful out-of-band callback per verification checklist.
