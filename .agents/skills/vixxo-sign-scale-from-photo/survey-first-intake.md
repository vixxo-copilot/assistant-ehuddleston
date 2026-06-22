# Survey-first intake (default path)

**Start here.** Dimensions come from the **field survey** and the **latest
approved shop drawing** — not from photo pixel estimation.

Photo is used **only after** fab is locked: to place red-line ticks on an
elevation or storefront image using survey anchors (door, existing sign).

Use with [`vixxo-project-history-research`](../vixxo-project-history-research/SKILL.md)
for SharePoint discovery and
[`sally-survey-artwork-scaling.md`](./sally-survey-artwork-scaling.md) for Sally
Beauty brand rules.

---

## When this path applies

- User names a **store / design # / client** and wants dimensions or overlays
- Pre-Production Review row exists or job folder is on New L Drive
- User says "scale from survey", "read the survey", "match the artwork"
- **Before** any photo iteration on channel-letter or dual-wordmark jobs

**Photo-only fallback:** No survey in folder and user only supplies a photo →
see Mode B photo-only section in `SKILL.md`. State clearly that output is an
**estimate** until survey + shop drawing exist.

---

## Mandatory workflow (survey-first)

```
Task progress:
- [ ] 0. Resolve project — client + store id → SharePoint folder
- [ ] 1. Load Survey/ — PDF sketch + photos; extract envelope + anchors
- [ ] 2. Load Art & EPS/ — latest VX###### R# PDF; extract page-2 fab block
- [ ] 3. Reconcile — survey constraints vs template; confirm or rescale fab
- [ ] 4. Smartsheet — brand workbook + design log when client known
- [ ] 5. Sanity checks — sanity-checks.md on fab table (not photo guesses)
- [ ] 6. Optional photo overlay — ticks only; labels from step 3
- [ ] 7. Emit packet + PNG/PDF if user asked for red-line deliverable
```

Steps **0–5** are required before publishing fab numbers. Step **6** is
optional unless the user wants a photo elevation overlay.

---

## Step 0 — Resolve project folder

**Microsoft 365 MCP** (`list-folder-files`, `search-onedrive-files`,
`download-bytes`). Org mode required — see project-history-research setup.

| Resource | Location |
|----------|----------|
| New L Drive | SharePoint `VixxoSignLighting` → `New L Drive` |
| Drive ID | `b!mH_hJO5alE-AvutIOImhpkdHB25X00xHirWbk4ejWSAkn2z2REgVTbm6ZMFdID_h` |
| Client IDs | [`vixxo-project-history-research/data/clients.md`](../vixxo-project-history-research/data/clients.md) |

**Resolve order:**

1. User store id (e.g. `3622`, `Sally3622`, `Sally Beauty #3622`)
2. Optional **Design #** from Pre-Production Review or user (`VX1108945 R4`)
3. `{year} Signage` trunk under `Sally{id}` (or client equivalent)

**Pre-Production Review.xlsx** (when user provides path): columns
`Location / Project I.D.` and `Design #` — match to `Art & EPS` filename.

---

## Step 1 — Read the survey

**Folder:** `{year} Signage/Survey/`

**Typical contents:**

- `Survey.pdf` or vendor-named PDF (McCorkle Survey Order, C2C sketch, etc.)
- `IMG_####.jpg` straight-on photos
- Placement markups (pylon, blade sign notes)

**Download** survey PDF via `download-bytes`. Render pages if text extract is
thin; read **handwritten dimensions** on sketches.

### Extract (minimum)

| Category | Examples | Drives |
|----------|----------|--------|
| **Sign-band envelope** | Total fascia width, sign-area height, raceway length | Rescale yes/no |
| **Existing sign** | OAL × OAH, prior tenant letter sizes | Elevation page 1 |
| **Wall anchors** | Door H×L, window grid, lease/frontage width | Photo homography |
| **Placement** | Offset to seam, canopy, raceway position | Elevation overlay |
| **Site spec** | Paint code (SW 7100, PMS 482C), wall type, pylon notes | Spec block only |

Record values in a **fab intake table** before opening artwork.

---

## Step 2 — Read latest shop drawing (Art & EPS)

**Folder:** `{year} Signage/Art & EPS/`

Pick **highest revision** for the current job (`R4` > `R3` > `R2` > `R1`).

**Page 2** (channel-letter fab elevation) — authoritative fab labels:

- Per-word width × height (or single cap height tier label, e.g. `30" LINEAR`)
- Gap, BEAUTY drop, overall / raceway width
- Square footage, raceway size, materials

**Page 1** (if present) — elevation photo + existing sign caption + placement
dims — use for overlay context, not for overriding page 2 unless revision
notes say otherwise.

**Extract text** from PDF (PyMuPDF / `get_text`) or read rendered pages.
Never invent dimensions missing from survey + art.

---

## Step 3 — Reconcile survey vs artwork

Compare survey **envelope** to artwork **page-2 fab**:

| Signal | Action |
|--------|--------|
| Fab fits band + existing context | **Confirm** — use art page 2 as-is |
| Band too narrow / existing scale smaller | **Rescale** — use latest R# after survey (not R1 template) |
| Survey notes only (paint, wall) | **Confirm fab** — update spec / elevation only |
| Art is R1, survey arrived, no R2+ yet | **Do not publish R1 fab as final** — note survey pending art revision |

**Priority stack:**

1. Latest **R#** shop drawing page 2 (after survey revision)
2. Survey measurements (constraints + anchors)
3. Smartsheet brand template / dimension workbook
4. Photo pixels (**tick placement only**)

Sally Beauty detail: [`sally-survey-artwork-scaling.md`](./sally-survey-artwork-scaling.md).

---

## Step 4 — Smartsheet (when brand known)

[`smartsheet-standards-intake.md`](./smartsheet-standards-intake.md) — Design
Standards Collection + New Design Log for rescale comments and tier tables.

---

## Step 5 — Sanity checks

Run [`sanity-checks.md`](./sanity-checks.md) on the **fab table from steps 2–3**,
not on photo-derived estimates.

Dual-color wordmarks: [`dual-color-wordmark.md`](./dual-color-wordmark.md) —
gate N (overall ≠ sum), gate L (secondary height), baseline gap.

---

## Step 6 — Photo overlay (optional)

**Only when** user supplies or survey includes a straight-on storefront photo.

| Source | Role |
|--------|------|
| Fab labels | Shop drawing page 2 (step 2) |
| `px_per_in` / homography | Survey door size or existing sign OAL×OAH |
| Tick positions | Letter faces on photo — **not** new inch values |

If user corrects a tick, adjust **pixels only**; do not change fab labels
unless they provide new shop drawing or survey revision.

Scripts: `measure_facade.py`, `detect_channel_letters.py` — see Mode B in
`SKILL.md`.

---

## Step 7 — Deliverables

- **Packet:** [`output-template.md`](./output-template.md) or
  [`dimension-overlay-template.md`](./dimension-overlay-template.md)
- **Red-line PNG/PDF** when requested — [`overlay-conventions.md`](./overlay-conventions.md)
- Cite sources: survey filename, art `VX###### R#`, revision date

---

## Fab intake table (emit in chat)

```markdown
## Fab intake — {client} {storeId} — {VX###### R#}

| Label | Inches | Source |
|-------|--------|--------|
| Primary W × H | | Art p2 |
| Secondary W × H | | Art p2 |
| Gap | | Art p2 |
| Overall / raceway | | Art p2 |
| Door reference | | Survey |
| Existing sign | | Survey / Art p1 |
| Rescale note | confirm \| down-tier \| pending art | Survey vs R1 |

Survey: [filename](webUrl)
Artwork: [filename](webUrl)
```

---

## MCP tool pattern

```
verify-login
search-onedrive-files(driveId, q="Sally3622")  → project folder
list-folder-files → {year} Signage → Survey, Art & EPS
download-bytes → /drives/{driveId}/items/{itemId}/content
```

Cache folder IDs for the session. Prefer `list-folder-files` over tenant-wide
search when parent folder is known.
