---
name: ms-forms-survey-builder
description: >-
  Grills the user one question at a time about survey goals, audience, and
  question design, then creates a configured Microsoft Form via the Forms web
  API. Use when the user asks to build a survey, create a Microsoft Form,
  design a Forms poll/questionnaire, or mentions Forms DesignPage / survey
  builder.
---

# Microsoft Forms Survey Builder

Grill → design → approve → create. Turns a vague survey ask into a live
Microsoft Form opened in the Forms designer.

There is **no official Graph create-Forms API**. Creation uses the same
undocumented `forms.office.com/formapi` the Forms web UI uses. Treat it as
best-effort automation; if it breaks, fall back to the drafted spec for manual
paste in the designer.

## When to use

- "Build me a survey" / "create a Microsoft Form"
- "Grill me on a survey then put it in Forms"
- Links to `forms.cloud.microsoft` / `DesignPageV2`
- Polls, NPS, feedback forms, event RSVPs, internal questionnaires

**Not for:** PM field survey PDF review (`pm-survey-review`), or generic plan
grilling without Forms creation (`grill-me`).

## Task progress

```
Task progress (MS Forms Survey Builder):
- [ ] 1. Scope intake (one sentence + any constraints)
- [ ] 2. Grill (one question at a time)
- [ ] 3. Draft survey spec + show for approval
- [ ] 4. Create Form via scripts/ms_forms_client.py
- [ ] 5. Hand back designer + respond URLs
```

## Step 1 — Scope intake

If the user already stated the purpose, skip re-asking it. Capture anything
offered: deadline, audience, anonymity, must-include questions, max length.

## Step 2 — Grill (mandatory)

Read [`references/interview-tree.md`](references/interview-tree.md).

Rules (same discipline as `grill-me`):

1. Ask **one question at a time**.
2. For each question, give your **recommended answer** in one short line.
3. Walk the decision tree in order; skip branches already answered.
4. Prefer repo/context facts over re-asking (Vixxo audience, known campaigns).
5. Do **not** create the Form until the user approves the drafted spec.

Stop grilling when purpose, audience, access, length, and question set are
resolved enough to write a complete spec.

## Step 3 — Draft the survey spec

Emit a JSON survey spec matching
[`references/survey-spec.md`](references/survey-spec.md). Also show a
human-readable outline (title, description, numbered questions with types).

Ask: **"Approve this and create it in Microsoft Forms?"**

Do not call the create script until explicit approval (`yes`, `create it`,
`go`, `approved`, or equivalent).

## Step 4 — Create in Microsoft Forms

Write the approved spec to
`_tmp/ms-forms-survey-builder/<slug>-spec.json`.

```powershell
py -3 .agents/skills/ms-forms-survey-builder/scripts/ms_forms_client.py auth
py -3 .agents/skills/ms-forms-survey-builder/scripts/ms_forms_client.py create --spec "_tmp/ms-forms-survey-builder/<slug>-spec.json"
```

- First run: `auth` opens device-code / browser login for
  `https://forms.office.com/.default`. Token cache lives under the user
  profile (not the repo).
- Needs `msal` and `requests` (`py -3 -m pip install msal requests`).
- On success, print **designer URL** and **respond URL**. Prefer designer:
  `https://forms.cloud.microsoft/Pages/DesignPageV2.aspx?origin=shell&subpage=design&id=<formId>`

If auth fails (conditional access / blocked device code), show the approved
spec and tell {{employee_name}} to create manually in Forms, question by
question from the outline. Do not invent a successful create.

## Step 5 — Handoff

Return:

1. Form title
2. Designer URL (primary)
3. Respond / share URL if returned
4. Question count + any settings notes
5. Reminder: review branching, theme, and collectors in the designer before
   distributing

## Guardrails

- Draft-then-approve before create (same spirit as outbound messaging).
- Do not email or Teams-blast the form link unless explicitly asked (and then
  draft-first per outbound rules).
- Do not claim Graph officially supports Forms create — it does not.
- Keep surveys short by default (≤12 questions unless the user overrides).
- Prefer measurable questions tied to a decision over vanity questions.
- Supported auto-create types: choice, text, rating, date, nps, file.
  Likert/ranking: include in the spec as `manual` and instruct the user to
  add them in the designer after create.

## References

- [`references/interview-tree.md`](references/interview-tree.md) — grill order
- [`references/survey-spec.md`](references/survey-spec.md) — JSON schema
- [`references/question-types.md`](references/question-types.md) — Forms API payloads
