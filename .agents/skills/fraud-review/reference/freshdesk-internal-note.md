# Freshdesk Internal Note — Fraud Review

Every Fraud Review on a Freshdesk ticket **must** produce and **auto-post**
this internal note via `conversations_manage create_note` (private). No
operator approval step for internal notes.

Do **not** post a public reply, forward, or BCC `invoices@vixxo.com`. This
skill uses **`create_note` only** — never `create_reply`.

## Note template

Copy and fill every section. Use plain text in the note body (Freshdesk private
notes accept plain text; avoid HTML).

```
FRAUD REVIEW — POTENTIAL FRAUD
Classification: [HIGH-RISK-BEC | SUSPICIOUS | LOW-RISK-LEGITIMATE | INSUFFICIENT-DATA]
Reviewed: [YYYY-MM-DD] | Ticket: [#id] | Mailbox: [aphelp | spm | ksonboarding]

── WHY THIS WAS FLAGGED ──
[List every reason — be specific; one bullet per finding]

• [Indicator ID + plain-language reason, e.g. "S2: Sender domain gmail.com does not match Gateway domain acme-hvac.com"]
• [ACH: "Gateway on-file routing •••661 / acct •••4521 DIFFERS from requested •••661 / acct •••9901"]
• [Domain: "DOMAIN-MISMATCH — request from outlook.com, Gateway email domain acme-hvac.com"]
• [Website: "acme-hvac-payments.net failed — login page, not listed on official site acme-hvac.com"]
• [Reply-To: "Reply-To yahoo.com differs from From corporate domain"]
• [Artifacts: "No voided check, W-9, or bank letter attached"]
• [Urgency: "Body requests update before Friday payment run"]

── AUTOMATED CHECK SUMMARY ──
SP: [legal name] | SP #: [number or unknown]
From: [email] | Reply-To: [email or —]
Gateway domain: [domain] | Domain result: [DOMAIN-MATCH | MISMATCH | etc.]

ACH comparison:
  Routing on file: [masked] → requested: [masked] → [MATCH|DIFFER|…]
  Account on file: ••••[last4] → requested: ••••[last4] → [result]
  Bank on file: [name] → requested: [name] → [result]

Websites reviewed:
  • [url] — [PASS|FAIL — one line]

── RECOMMENDED NEXT STEP ──
[One line for internal staff — tier-specific; see below]

── DO NOT (this skill) ──
• Contact the service provider from this ticket (no public reply)
• Forward banking details to AP intake
• Update Gateway / Siebel banking from unverified email
```

**Do not** include the human verification checklist in the note body.
Operators use [verification-checklist.md](verification-checklist.md) as SOP
outside the ticket note.

## Classification-specific headers

Use the top banner that matches risk:

| Classification | Banner line |
|----------------|-------------|
| `HIGH-RISK-BEC` | `FRAUD REVIEW — POTENTIAL FRAUD (HIGH RISK)` |
| `SUSPICIOUS` | `FRAUD REVIEW — POTENTIAL FRAUD (SUSPICIOUS — VERIFY BEFORE ACTION)` |
| `LOW-RISK-LEGITIMATE` | `FRAUD REVIEW — LOW RISK (VERIFY CHECKLIST BEFORE UPDATE)` |
| `INSUFFICIENT-DATA` | `FRAUD REVIEW — INSUFFICIENT DATA (DO NOT UPDATE)` |

## "Why flagged" rules

Always list **every** fired indicator with evidence:

1. Each strong indicator (S1–S10) from [fraud-indicators.md](fraud-indicators.md)
2. Each soft indicator (W1–W7) when classification is SUSPICIOUS or higher
3. ACH comparison failures (`DIFFER`, `MISSING-IN-REQUEST`, `PARTIAL`)
4. Domain result when not `DOMAIN-MATCH` / `SUBDOMAIN-MATCH` / `DOMAIN-HISTORY-MATCH`
5. Each website FAIL or `LOOKALIKE` URL
6. Missing artifacts when banking change was requested

If nothing fired but classification is SUSPICIOUS (default posture), state:
`Default safe posture — banking change requires manual verification.`

## Optional tags (operator approval only — not auto-applied)

| Classification | Suggested tags |
|----------------|----------------|
| `HIGH-RISK-BEC` | `fraud-review`, `bec-risk`, `banking-change-unverified`, `security-review`, `vendor-maintenance-audit` |
| `SUSPICIOUS` | `fraud-review`, `banking-change-unverified`, `pending-verification` |
| `LOW-RISK-LEGITIMATE` | `fraud-review`, `pending-verification` |
| `INSUFFICIENT-DATA` | `fraud-review`, `insufficient-data` |

Freshdesk `tags` on update **replace** the full set — merge existing tags.

## HIGH-RISK-BEC — close the ticket

When classification is `HIGH-RISK-BEC`:

1. **Auto-post** private note (no checklist) with full **why flagged** reasons.
2. Add a **closure line** in the note, e.g. `TICKET CLOSED — HIGH-RISK BEC. Banking change not processed from this channel.`
3. **Immediately** `tickets_manage update` → `status: 5` (Closed). Merge tags:
   `fraud-review`, `bec-risk`, `banking-change-unverified`, `high-risk-closed`
   (preserve existing tags).
4. **Never** post a public reply or forward.

Do not leave HIGH-RISK tickets Open in the ACH queue.

## Write order (Mode B)

1. Complete fraud review (steps 1–7).
2. **Auto-post** `create_note` immediately (no checklist).
3. If `HIGH-RISK-BEC` → close ticket (above).
4. Confirm note visible on ticket; direct-fetch ticket if search lags.
5. Echo note excerpt in chat packet.

For non-HIGH-RISK tickets, tags and status changes stay out of scope unless
the operator requests them later.

## Batch mode

After each page of 10 reviews:

- Summary table: `ticket_id | classification | flag count | note posted OK/FAIL`
- Internal notes already posted during the run — no batch approval step.
