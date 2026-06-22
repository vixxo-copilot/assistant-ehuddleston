# Sally Beauty — survey → artwork scaling logic

Lessons from SharePoint `Sally Beauty` project folders, Pre-Production
Review workbook, and studied survey + artwork pairs (2024–2026).

Parent workflow: [`survey-first-intake.md`](./survey-first-intake.md) (Mode S).
Use with [`dual-color-wordmark.md`](./dual-color-wordmark.md) and
[`smartsheet-standards-intake.md`](./smartsheet-standards-intake.md).
**Survey and approved shop drawing beat photo estimates.**

---

## Where files live

```
Sally Beauty / Sally{storeId} /
  {year} Signage /          ← current job trunk (e.g. 2026 Signage)
    Survey/                 ← field survey PDF + photos
    Art & EPS/              ← VX###### [R#] Sally {id} {city}.pdf
    Purchase Orders/
    ...
```

- **Latest artwork** = highest revision in the **current year** `Art & EPS`
  folder (`R4` > `R3` > `R2` > `R1`; base release before `R1`).
- **Pre-Production Review.xlsx** columns:
  `Date | Client | PM | Location / Project I.D. | Design #`
  — cross-check `Design #` against the newest PDF in `Art & EPS`.
- Brand template at client root:
  `VX Sally starting Template 5-2026.cdr` (and `.24` variant).

---

## Typical workflow

```
1. R1 (or base VX) — starting template dimensions on shop drawing page 2
2. Survey PO issued → Survey/ populated (McCorkle, Coast2Coast, SCA, etc.)
3. R2+ — art revises per survey: elevation page 1, then fab block if needed
4. Pre-Prod Review row added when design is locked for manufacture
```

**Two outcomes after survey:**

| Outcome | When | Example |
|---------|------|---------|
| **Confirm template** | Existing fascia fits standard 30" set; survey mainly documents existing sign + placement | Sally10063: R1→R3, page-2 fab unchanged |
| **Rescale template** | Fascia width, existing sign, or lease constraint forces smaller letter tier | Sally3622: R1→R4, 30" set → 24" set |

---

## What to extract from a Sally survey

### A. Fascia / sign-band envelope (drives rescale yes/no)

| Field | Used for |
|-------|----------|
| **Total sign-band width** | Max raceway + letter span (e.g. **19'-11"** Cary sketch) |
| **Sign-area height** | Vertical clearance for returns + raceway (e.g. **84 1/2"**) |
| **Raceway length** | Often noted separately (e.g. **5'-10"** top raceway) |
| **Lease space width** | Frontage cap (e.g. **28'** Houston graph-paper survey) |

If template overall (**13'-4"**) fits inside measured band with margin,
keep standard fab. If not, rescale proportionally to the measured band
and existing sign.

### B. Existing sign (elevation page 1)

| Field | Used for |
|-------|----------|
| **OAL × OAH** | Caption on existing photo (`37" OAH × 16' OAL`) |
| **Per-letter sizes** | Prior tenant letters on sketch (helps sanity-check) |
| **Photo straight-on** | Scale for proposed overlay on elevation |

### C. Reference anchors (photo overlay / permitting)

| Field | Used for |
|-------|----------|
| **Door H × L** | Primary scale reference (**72 1/4" × 30 3/4"** typical) |
| **Window grid H × L** | Secondary checks on elevation |
| **Offset to seam / canopy** | Placement callouts (e.g. **1'-5"** to horizontal seam) |

### D. Site notes (spec block updates, not always dimension changes)

- Raceway / trim paint (**PMS 482 C** at Cary; **SW 7100** arcade white)
- Wall type (Dryvit + plywood vs tilt-wall concrete) — mounting detail only
- Pylon / monument dimensions when scope includes pylons
- Blade / hanging sign sizes when noted on survey photos

---

## Standard template fab (R1 / starting template)

**30" linear channel letter set** — white fascia rebrand, or red SALLY +
black BEAUTY on split-color jobs.

| Label | Inches |
|-------|--------|
| SALLY height (outline) | **2'-6"** (30") |
| SALLY width | **9'-10 1/4"** |
| BEAUTY height (outline) | **10 1/2"** |
| BEAUTY width | **4'-1"** |
| Gap (Y → B) | **3 3/4"** |
| BEAUTY vertical drop from SALLY cap | **1 5/8"** |
| Overall / raceway width | **13'-4"** |
| Square feet | **33.3 SF** |
| Shop scale (fab page) | **3/8" = 1'-0"** |
| Elevation scale (photo page) | **3/16" = 1'-0"** or **1/8" = 1'-0"** |

Raceway: **5" × 7"** extruded aluminum, painted to fascia (SW 7100 or
survey-specified match).

---

## Rescaled fab (when survey forces down-tier)

**Sally3622 Cary** — survey band **19'-11"**; existing elevation updated to
**19'-11" × 7'-0 1/2"**; fab rescaled to **24" linear** set:

| Label | Template (R1) | After survey (R4) |
|-------|---------------|-------------------|
| Cap tier label | 30" linear | **24" linear** |
| SALLY height | 2'-6" | **2'-0"** |
| SALLY width | 9'-10 1/4" | **7'-10 3/4"** |
| BEAUTY height | 10 1/2" | **8 3/8"** |
| BEAUTY width | 4'-1" | **3'-3 1/4"** |
| Gap | 3 3/4" | **3"** |
| BEAUTY drop | 1 5/8" | **1 3/8"** |
| Overall / raceway | 13'-4" | **10'-8"** |
| Square feet | 33.3 | **21.3** |

**Scaling rule observed:** height tier ratio ≈ **24/30 = 0.8** applied across
word widths, gap, and drop while preserving dual-wordmark proportions.
Raceway paint updated from generic fascia match to survey note
(**PMS 482 C**).

---

## Confirm-template case (fab unchanged)

**Sally10063 Houston** — Coast2Coast graph-paper survey documented
**16' SALLY width**, **37" letter height**, **28' lease space**, stucco
**SW 7100**. R1 and R3 **page-2 fab identical** (standard 30" set above).

Survey drove **elevation / scope**, not fab rescale:

- Existing photo captioned **37" OAH × 16' OAL**
- Proposed overlay placement (**1'-5"** to seam)
- Split-color spec on R3: SALLY **#2793 red** plex, BEAUTY **#2447 white**
  acrylic + **70/30 black perforated vinyl**
- Page 1 elevation dims adjusted; page 2 letter fab held at template

---

## Reading survey PDFs (formats seen)

### McCorkle Survey Order (typed + sketch)

- Job #, site address, PM / surveyor contacts
- Checklist: photos, measure existing signage, doors/windows, color match
- Hand-drawn elevation with pink dimensions on sign band, doors, windows
- Follow-on pages: annotated site photos (blade signs, pylons, etc.)

### Coast2Coast / field graph-paper sketch

- Wall type + paint code header
- Lease width, existing letter sizes, fascia height
- Window/door module grid with H × L per opening

### Survey deliverable package

Often `Survey.pdf` plus numbered `IMG_####.jpg` photos and occasional
placement markup (`pylon panel placement.jpg`).

---

## Agent checklist (survey + latest art)

```
- [ ] Resolve store id → Sally{id} folder on New L Drive
- [ ] Open current year Signage/Survey — read sketch + photos
- [ ] Open Art & EPS — latest VX###### R# PDF
- [ ] Compare page 2 fab block: template vs rescaled?
- [ ] Pull elevation page 1: existing OAL/OAH, placement offsets
- [ ] Cross-check Pre-Production Review Design # if row exists
- [ ] For photo overlays: use survey door or existing-sign dims as
      reference; label from fab page 2, not from photo pixels
- [ ] Dual-color: separate SALLY / BEAUTY masks; gap at baseline
- [ ] Overall width may ≠ SALLY + gap + BEAUTY (gate N) — use
      raceway/overall callout from shop drawing
```

---

## Studied exemplars (2026-06)

| Store | Survey | Art rev | Lesson |
|-------|--------|---------|--------|
| **Sally3622** Cary NC | McCorkle 03/2026, band **19'-11"** | VX1108945 **R1→R4** | Full rescale 30"→24" tier |
| **Sally10063** Houston TX | C2C graph paper 03/2024 | VX1105604 **R1→R3** | Template confirmed; color + elevation |
| **Sally10063** 2026 | SCA pylon survey 04/2026 | VX1109111 | Pylon/vinyl scope — not channel-letter rescale |

Local study artifacts: `tmp/sally-study/` (PDFs + page renders).
