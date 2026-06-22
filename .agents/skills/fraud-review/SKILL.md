---
name: fraud-review
description: >-
  Fraud Review — triages service-provider ACH and banking change requests from
  Freshdesk (aphelp@vixxo.com, service.providermanagement@vixxo.com,
  ksonboarding@vixxo.com). Compares requested banking to Gateway on-file ACH,
  verifies sender email domain against the SP's registered domain and website,
  fetches and reviews linked websites, and scores BEC risk. Use when the user
  asks for fraud review, ACH fraud check, banking change verification, BEC
  triage, or to work the ACH mailbox queue. Internal only — auto-posts private
  Freshdesk notes; never contacts service providers.
---

# Fraud Review

**Internal review only.** Fraud Review analyzes ACH/banking change requests,
scores fraud risk, and auto-posts a **private Freshdesk internal note** on each
ticket. It does **not** contact service providers — no public replies, no
emails, no forwards, no ack drafts, ever. Follow-up with the SP is handled
outside this skill (Vendor Maintenance, Account Update, etc.).

For each ticket or email it:

1. Reads the full thread and extracts the **requested** banking change.
2. Pulls **on-file ACH** from Gateway and compares field-by-field.
3. Verifies the **sender email domain** matches the SP's registered domain.
4. **Fetches and reviews websites** (SP corporate site + suspicious links).
5. Scores BEC indicators and classifies risk.

**Never updates banking data.**

**Only write surface:** private Freshdesk `create_note` (auto-posted).

**Never use:** `create_reply`, `forward`, public conversation, email/Teams to
the service provider, or BCC to `invoices@vixxo.com`.

Tag and status changes are out of scope unless the operator invokes a
different skill or workflow.

## ACH mailboxes (Freshdesk intake)

| Mailbox | Role |
|---------|------|
| `aphelp@vixxo.com` | AP Help — ACH / banking change |
| `service.providermanagement@vixxo.com` | SPM — ACH / banking change |
| `ksonboarding@vixxo.com` | KS Onboarding — ACH / banking setup |

`vixxo-freshdesk-invoice-review` excludes the SPM and KS Onboarding mailboxes;
**Fraud Review owns them.**

## Modes

| Mode | Trigger | Source |
|------|---------|--------|
| **B — Queue** | "Run fraud review", "work the ACH queue" | Freshdesk (default) |
| **C — Single** | Ticket #, pasted email | User input + MCP |
| **A — Mailbox** | M365 scan of ACH folders | Microsoft 365 |

Default to **Mode B** when the user says "fraud review" without scoping a
single item.

## Workflow checklist

```
Fraud Review progress (every item):
- [ ] 1. Intake + mailbox scope
- [ ] 2. Read full thread
- [ ] 3. Extract requested banking + sender identity
- [ ] 4. Gateway — SP record + on-file ACH comparison
- [ ] 5. Domain verification (email vs SP registered domain)
- [ ] 6. Website review (SP site + embedded links)
- [ ] 7. Fraud score + classification
- [ ] 8. Fraud review packet
- [ ] 9. Freshdesk internal note (auto-post private note)
```

---

### 1. Intake

- **Batch size:** 10 Open tickets per page, oldest-first (Mode B).
- Ticket must be addressed to an ACH mailbox (see table above) unless the
  operator names a specific ticket.
- **Skip** with reason: `invoice-only` → invoice triage skill;
  `no-banking-content` → no ACH/banking keywords and no account details.

### 2. Read full thread

Read subject, body, quoted history, and attachment **metadata** together.
Do not open attachments when strong fraud indicators are already present.

### 3. Extract requested change

Build the **requested** side of the comparison table:

| Field | Requested value |
|-------|-----------------|
| SP legal name / DBA | |
| SP number | |
| From address + domain | |
| Reply-To address + domain (if different) | |
| Bank name | |
| Routing / ABA | |
| Account number (internal: full; output: last 4 only) | |
| Account type | |
| Beneficiary name on account | |
| Wire vs ACH | |
| URLs in body (list each) | |
| Artifacts | voided check / W-9 / bank letter / none |

---

### 4. Gateway — on-file ACH comparison (required)

**Before scoring**, pull the service provider from Gateway and compare banking.

#### Gateway tool discovery

List Gateway MCP tools at session start. Prefer tools named like:

- `gateway_get_service_provider` / `gateway_search_service_providers`
- `gateway_get_provider` / provider search by SP number or legal name

If tool names differ, use the closest provider-detail tool and read
[reference/gateway-ach-comparison.md](reference/gateway-ach-comparison.md).

#### Pull on-file fields

From the Gateway provider record, extract every banking/payment field available,
for example:

- Legal name, DBA, SP number, status (active / on hold)
- Primary email, website URL, phone
- Registered / corporate email domain (from email or website)
- On-file bank name, routing number, account number (mask in output)
- Payment method (ACH / wire / check)

#### Comparison matrix (required in every packet)

| Field | On file (Gateway) | Requested (email) | Result |
|-------|-------------------|-------------------|--------|
| Routing | | | `MATCH` / `DIFFER` / `MISSING-ON-FILE` / `MISSING-IN-REQUEST` |
| Account (last 4) | | | same |
| Bank name | | | same |
| Beneficiary name | | | same |

**ACH comparison outcomes:**

| Outcome | Meaning |
|---------|---------|
| `MATCH` | Requested banking identical to Gateway — likely duplicate or resend |
| `CHANGE` | Requested banking differs from Gateway — expected for a real update; still requires domain + fraud checks |
| `NEW-SETUP` | No banking on file — common for onboarding mailbox |
| `PARTIAL` | Only some fields present — flag `INSUFFICIENT-DATA` |

**High-risk rule:** If comparison is `CHANGE` **and** domain verification fails
(step 5), classify at least `SUSPICIOUS`; often `HIGH-RISK-BEC`.

**Gateway caution:** When strong BEC indicators fire first, treat SP numbers in
the email as unverified until out-of-band confirmation.

---

### 5. Domain verification (required)

Verify the **requesting email domain** belongs to the service provider.

Read [reference/domain-and-website-verification.md](reference/domain-and-website-verification.md)
for full rules.

#### Extract domains

| Source | Domain |
|--------|--------|
| `From` | |
| `Reply-To` (if present) | |
| Gateway primary email | |
| Gateway website URL | registrable domain |
| Prior Freshdesk tickets (same SP) | historical sender domains |

Normalize to **registrable domain** (e.g. `mail.acme-hvac.com` → `acme-hvac.com`).

#### Domain match result (required in every packet)

| Result | Rule |
|--------|------|
| `DOMAIN-MATCH` | Sender domain equals Gateway email domain or website domain, or is a documented subdomain of the same org |
| `DOMAIN-HISTORY-MATCH` | Sender domain matches ≥3 prior Freshdesk tickets for this SP |
| `DOMAIN-MISMATCH` | Sender domain unrelated to Gateway email, website, or history |
| `DOMAIN-LOOKALIKE` | Typosquat / homoglyph of SP domain (e.g. `acme-hvac.co` vs `acme-hvac.com`) |
| `FREE-WEBMAIL` | Gmail, Yahoo, Outlook.com, iCloud, Proton, etc. |

**Strong fraud indicator:** `DOMAIN-MISMATCH`, `DOMAIN-LOOKALIKE`, or
`FREE-WEBMAIL` for an established SP with corporate domain on file.

**Reply-To rule:** If `From` is corporate but `Reply-To` is free webmail or
unrelated domain → strong indicator (S4).

---

### 6. Website review (required)

**Pull and look at websites** for every fraud review. Use `WebFetch` (or
equivalent) — never enter credentials or submit forms.

#### 6a. Service provider corporate website

1. Take website URL from Gateway (preferred) or infer `https://<sender-domain>`.
2. Fetch the homepage and, if needed, `/contact` or footer.
3. Record:
   - Does the site load and match the SP legal name / brand?
   - Contact email domains listed on the site
   - Phone numbers (compare to Gateway on-file phone — do not treat as verified
     from email alone)
   - Whether the **sender email domain** appears on the official site

| Website check | Pass | Fail |
|---------------|------|------|
| Site resolves | HTTP 200, legitimate business content | NXDOMAIN, parking page, unrelated content |
| Brand match | Name/logo matches Gateway legal name | Different company or generic template |
| Email on site | Sender domain listed or same org | Sender domain absent; only different domain listed |
| Sender vs site | Request came from domain on website | Request domain not on official site |

#### 6b. URLs embedded in the email

For each link in the request body:

1. Fetch the URL (follow redirects up to 3 hops).
2. Classify: legitimate SP/bank domain, free file host, lookalike login, or
   unknown.
3. **Never** click "confirm banking" flows or download from suspicious hosts.

**Strong fraud indicator:** payment-portal or login page on a domain that is
not the SP's registered domain or known financial institution.

---

### 7. Fraud score + classification

Apply [reference/fraud-indicators.md](reference/fraud-indicators.md). **Upgrade**
risk when any of these fail:

- Gateway ACH comparison `CHANGE` + `DOMAIN-MISMATCH`
- Website check fails brand or email-domain alignment
- Embedded URL is lookalike or credential harvest

| Classification | When |
|----------------|------|
| `HIGH-RISK-BEC` | Any strong indicator, or `CHANGE` + domain/website fail |
| `SUSPICIOUS` | Two+ soft indicators, or partial verification pass |
| `LOW-RISK-LEGITIMATE` | `CHANGE` or `NEW-SETUP`, domain match, website pass, artifacts present |
| `INSUFFICIENT-DATA` | Cannot resolve SP or parse banking fields |

---

### 8. Fraud review packet (required output)

Every reviewed item gets the chat summary below **and** a Freshdesk internal
note (step 9).

```markdown
## Fraud Review — [SP name] — [ticket # / message id]

**Classification:** …
**Mailbox:** aphelp | spm | ksonboarding

### Why flagged
- [every reason — same bullets that go in the internal note]

### Sender & domain
…

### Gateway ACH comparison
…

### Websites reviewed
…

### Recommended action
…
```

### 9. Freshdesk internal note (required for Mode B and C)

**Every Freshdesk ticket** reviewed by this skill gets a **private internal
note**. Read the full template at
[reference/freshdesk-internal-note.md](reference/freshdesk-internal-note.md).

The note **must** include:

1. **Potential fraud banner** — classification-specific header (internal note
   for agents; not sent to the SP).
2. **Why this was flagged** — numbered/bulleted list of **every** reason:
   fraud indicators (S/W IDs + plain English), ACH comparison failures,
   domain mismatch, website failures, lookalike URLs, missing artifacts,
   urgency language, Reply-To mismatch.
3. **Automated check summary** — SP #, domains, ACH table, websites reviewed.
4. **Recommended next step** and **DO NOT** block.

**Do not** paste the human verification checklist into the note. That SOP lives
in [reference/verification-checklist.md](reference/verification-checklist.md).

**Workflow (auto-post — no approval for internal notes):**

1. Build the note from the template (no checklist).
2. **Immediately** post with `conversations_manage create_note` — **private
   only**, never `create_reply`.
3. If classification is **`HIGH-RISK-BEC`**: close the ticket (`status: 5`)
   with merged tags `fraud-review`, `bec-risk`, `banking-change-unverified`,
   `high-risk-closed`. The note must state why it was closed and that banking
   was **not** processed from this channel.
4. Confirm write via direct `GET /api/v2/tickets/{id}` — not search alone.
5. Include note text (or excerpt) in the chat fraud review packet.

**Do not** auto-apply tags or change status for non-HIGH-RISK tickets unless
the operator requests it later.

**Batch (Mode B):** post the internal note for **every** ticket on the page as
each review completes; end-of-page summary includes
`ticket | classification | note OK/FAIL | closed OK/FAIL (HIGH-RISK only)`.

This skill **never** drafts or posts service-provider-facing communication.

---

## Mode B — Freshdesk queue

1. Resolve `email_config_id` for all three ACH mailboxes (`GET /api/v2/email_configs`).
   Candidate: `aphelp@vixxo.com` → `159000195932` (verify on first run).
2. Filter:

```
(email_config_id:<aphelp_id> OR email_config_id:<spm_id> OR email_config_id:<ks_id>) AND status:2
```

3. Process 10 tickets per page — full review + **auto-post internal note** per
   ticket.
4. Pause: show summary table (`ticket | classification | # flags | note posted`).
5. Ask before continuing to the next page.

---

## Mode C — Single item

Paste email, `.eml`, or ticket #. Run the full checklist (steps 3–8).

---

## Mode A — Microsoft 365

Prefer Mode B for canonical queue. When used, scope to the three ACH shared
mailboxes and run the same Gateway / domain / website checks.

---

## Safety

- **Internal only** — no `create_reply`, forward, or outbound email/Teams to SPs.
- Mask account numbers in output (last 4).
- Do not echo full routing+account for `HIGH-RISK-BEC` items.
- Callback only to **Gateway on-file phone**, never numbers from the email.
- WebFetch only — no form submission, no credential entry.
- Never forward BEC content to `invoices@vixxo.com`.

---

## Additional resources

- [Gateway ACH comparison](reference/gateway-ach-comparison.md)
- [Domain and website verification](reference/domain-and-website-verification.md)
- [Fraud indicator rubric](reference/fraud-indicators.md)
- [Verification checklist](reference/verification-checklist.md)
- [Freshdesk internal note template](reference/freshdesk-internal-note.md)
- [Examples](examples.md)
