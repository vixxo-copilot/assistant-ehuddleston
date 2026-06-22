---
name: vixxo-sign-scale-from-photo
description: >-
  Survey-first sign dimension workflow — reads field survey PDFs and latest shop
  drawing (Art & EPS) from SharePoint, reconciles fab against brand templates,
  then optionally places red-line overlays on storefront photos. Also supports
  photo-only estimation, tan/low-contrast fascias (CLAHE + leaf anchor),
  letter-face vs raceway fab width (gates J/K), dual-color wordmarks (Sally
  Beauty — gates L/M/N), logo+letter signs, and white-panel fascia mockups.
  Use when the user asks to scale from survey, read survey dimensions, match
  shop drawing fab, measure a sign from a photo, or add dimension lines.
---

# Sign scale (survey-first)

**Default path:** field **survey** + latest **shop drawing** (Art & EPS) → locked
fab table → optional **photo** red-line overlay. Full procedure:
[`survey-first-intake.md`](./survey-first-intake.md).

Three modes (labels match section headings below):

- **Mode S — Survey-first** (default) — SharePoint `Survey/` + `Art & EPS/`;
  reconcile fab; optional elevation overlay using survey anchors.
- **Mode A — Fascia panel mockup** — white rectangular panel composited on a
  building photo; dual-axis anchors for panel height **and** width; red-line
  overlay deliverables.
- **Mode B — Reference scaling** — channel letters / logos on a wall; use **after
  Mode S** when fab is locked, or photo-only when no survey exists.

Photo-only scale is an **estimate**, not fabrication proof. Survey + shop drawing
beat photo when both exist.

## When to use

- "Scale from the survey" / "read the survey" / store id or design # given
- Pre-Production Review row or New L Drive job folder exists
- "Measure this sign from the photo" (after survey+art, or photo-only estimate)
- "Add dimension lines to the sign mockup"
- "Scale the letters — door is 7 feet"
- User iterates: "make it taller", "width is good, decrease height"
- LifeCare / Select Medical / hospital fascia mockups on porte-cochère photos
- Sally Beauty–style **dual-color wordmarks** (red + black on white fascia)

## What this skill does NOT do

- Does not replace a field survey or tape measure.
- Does not send outbound messages.
- Does not modify Smartsheet, SharePoint, or SR records unless asked.

## Dependencies

- **Microsoft 365 MCP** (org mode) — SharePoint `Survey/` and `Art & EPS/` on
  New L Drive; see [`vixxo-project-history-research`](../vixxo-project-history-research/SKILL.md)
  and [`survey-first-intake.md`](./survey-first-intake.md).
- **Read** — inspect survey PDFs, shop drawings, and photos.
- **Shell** — run scripts under `scripts/` (Pillow + numpy; OpenCV for
  `detect_channel_letters.py` on tan fascias).
- **Smartsheet MCP** — `Design Standards Collection` dimension workbooks and
  recent `New Design Log 1.B` revision patterns when client/brand is known.

## Reference files

- [`survey-first-intake.md`](./survey-first-intake.md) — **default workflow**:
  survey + art → fab table → optional photo overlay.
- [`smartsheet-standards-intake.md`](./smartsheet-standards-intake.md) — brand
  workbooks, sheet IDs, photo-overlay SOP from design log.
- [`reference-dimensions.md`](./reference-dimensions.md) — default reference sizes.
- [`tan-fascia-detection.md`](./tan-fascia-detection.md) — **low-contrast CL on beige
  EIFS** (cornice trap, CLAHE, leaf anchor, letter-face vs fab width).
- [`dual-color-wordmark.md`](./dual-color-wordmark.md) — **red + black (or dual-tier)
  wordmarks** on white fascia (Sally Beauty): separate masks, gap, overall width.
- [`sally-survey-artwork-scaling.md`](./sally-survey-artwork-scaling.md) — **Sally
  Beauty survey → shop-drawing rescale logic** (template vs down-tier, what to
  read from McCorkle/C2C surveys, Pre-Prod Review + SharePoint folder pairing).
- [`sanity-checks.md`](./sanity-checks.md) — mandatory gates before final numbers.
- [`overlay-conventions.md`](./overlay-conventions.md) — **deliverable = red dimension lines, not boxes**.
- [`output-template.md`](./output-template.md) — reference-scaling packet.
- [`dimension-overlay-template.md`](./dimension-overlay-template.md) — mockup overlay packet.

---

## Mandatory workflow — Mode S (survey-first, default)

When a store id, design #, or SharePoint job folder is available, **start here**.
Do not derive primary fab from photo pixels until steps 0–5 complete.

```
Task progress:
- [ ] 0. Resolve project — SharePoint folder — survey-first-intake.md
- [ ] 1. Survey/ — PDF sketch + photos; envelope + anchors
- [ ] 2. Art & EPS/ — latest VX###### R#; page-2 fab block
- [ ] 3. Reconcile — survey vs template; confirm or rescale
- [ ] 4. Smartsheet — brand row + dimension xlsx when client known
- [ ] 5. Sanity checks — sanity-checks.md on fab table (not photo guesses)
- [ ] 6. Optional photo overlay — ticks only; labels from step 3
- [ ] 7. Emit packet (+ PDF when user asks for red-line deliverable)
```

Sally Beauty rescale rules: [`sally-survey-artwork-scaling.md`](./sally-survey-artwork-scaling.md).

---

## Mandatory workflow — Modes A / B (photo path)

Use when **no survey/art folder** exists, or after Mode S fab is locked and user
wants overlay only. Photo scale is an **estimate** until survey + shop drawing load.

```
Task progress:
- [ ] 0. Smartsheet — brand row + dimension xlsx when client known — smartsheet-standards-intake.md
- [ ] 1. Intake — fab per element (letters, logo, **each color block**, gap, overall) + door size on site;
  photo-only → state "estimate until survey"
- [ ] 2. Mark pixel edges internally (cap line, logo form, door quad) — sanity-checks.md;
  tan fascia → tan-fascia-detection.md; dual-color → dual-color-wordmark.md
- [ ] 3. Run sanity checks — fix edges or downgrade confidence if any fail
- [ ] 4. Draw deliverable overlay — red dimension lines only — overlay-conventions.md
- [ ] 5. Emit packet (+ PDF when user asks for red-line deliverable)
```

**Step 0 (when brand is named):** Read [`smartsheet-standards-intake.md`](./smartsheet-standards-intake.md).
Pull the brand's dimension workbook from **Design Standards Collection** and
note recent **New Design Log** comments (survey rescale, photo overlay, % rules).
**Survey and fab spec beat photo** — matching art-team practice on latest revs.

**User fab spec overrides photo.** If the user gives letter height, logo height,
and/or overall width (e.g. globe **4'-0"**, letters **13"**, width **9'-8"**),
stop estimating those from pixels. Use the photo only to place red-line overlays
at spec (homography from confirmed door or other reference).

**No logo height from color masks.** Dimensional logos (AT&T globe, medallions)
must not be scaled from stripe/ink detection. Withhold logo numbers until fab
spec or manually verified logo edges pass gates E/F in [`sanity-checks.md`](./sanity-checks.md).
Deliverable overlays use **dimension lines**, not yellow/red/green boxes — see
[`overlay-conventions.md`](./overlay-conventions.md).

**Label format.** Default overlay labels are feet-inches only (`4'-0"`, `22'-0"`).
Do **not** append `EVO` unless the user explicitly requests evo in that turn.

**Clarify feedback.** When the user says dimensions are "too small" or "too big",
ask whether they are **correcting the estimate** or **giving fabrication size**.
When they say "decrease by 1'" (or similar), ask **which labels** — overall width,
gap, and per-word sizes are independent on dual-color overlays ([`dual-color-wordmark.md`](./dual-color-wordmark.md)).
Do not widen the cap band without re-checking the overlay.

Full gate definitions: [`sanity-checks.md`](./sanity-checks.md).

---

## Mode S — Survey-first (default)

Full procedure: [`survey-first-intake.md`](./survey-first-intake.md).

**Quick sequence:**

1. Resolve `{client}{storeId}` on New L Drive via Microsoft 365 MCP
   (`list-folder-files`, `download-bytes`). Client folder IDs:
   [`vixxo-project-history-research/data/clients.md`](../vixxo-project-history-research/data/clients.md).
2. Read `Survey/` PDF — fascia width, sign-area height, door, existing sign,
   paint codes, placement notes.
3. Read latest `Art & EPS/` `VX###### R#` — **page 2** fab dimensions.
4. Reconcile: if survey forces down-tier, use post-survey R# (not R1 template).
5. Run sanity checks on fab table; emit **fab intake table** in chat.
6. If user wants red-line on survey photo or storefront image → Mode B overlay
   with **labels from step 3**, ticks from photo only.

**Do not** derive primary fab widths/heights from photo letter bounding boxes
when survey + art exist in the folder.

---

## Mode A — Fascia panel mockup (preferred for composited signs)

Use when a **white panel** is visible on the building fascia (mockup or installed
cabinet) and the user wants a dimension table plus red-line overlay.

### Workflow

```
Task progress:
- [ ] 1. Detect panel + graphic ink in photo
- [ ] 2. Set panel height and width anchors (dual-axis)
- [ ] 3. Run measure_panel_sign.py
- [ ] 4. Tune anchors from user feedback
- [ ] 5. Emit dimension packet + deliver PNG/PDF
```

### 1. Anchors (dual-axis)

Set **two independent anchors**:

| Anchor | Controls | Example |
|--------|----------|---------|
| `panel_height` | All vertical dimensions | `4'-3"` |
| `panel_width` | All horizontal dimensions | `10'-0"` |

**Iteration rules** (from field use):

- "Width is good" → hold `panel_width`; adjust `panel_height` only.
- "Height too small / too large" → move `panel_height`; do not change width unless asked.
- "4' is too small" → do not go below ~4'-0"; prefer `4'-3"` between `4'-0"` and `4'-6"`.
- Increase height **or** decrease height independently of width — never uniform scale when user names one axis.

### 2. Run the script

```bash
python3 .agents/skills/vixxo-sign-scale-from-photo/scripts/measure_panel_sign.py \
  --image <photo> \
  --panel-height "4'-3\"" \
  --panel-width "10'-0\"" \
  --out-png tmp/<slug>-sign-dimensions.png \
  --out-pdf ~/Desktop/<slug>-sign-dimensions.pdf
```

Add `--json` for structured output.

### 3. Overlay conventions

Follow [`overlay-conventions.md`](./overlay-conventions.md). The script emits
**dimension lines** (not filled boxes):

- Red outline + bottom horizontal: **panel width**.
- Red vertical at right: **panel height**.
- White backing behind label text only; Arial Bold 15–16 px.

### 4. Element detection notes

- **White panel:** RGB > (220, 230, 240) in upper fascia band.
- **Brand ink:** teal/green `(r<50, g>60, b>50)`.
- **Tagline ink:** neutral gray/black on panel.
- Split **two text rows** at the widest vertical gap in the middle third of panel ink.
- Split **logo / primary / tagline** by x-cluster gaps on each row.

Rename elements in the chat table to match the sign (e.g. "Select", "SPECIALTY HOSPITAL").

### 5. Emit packet

Fill [`dimension-overlay-template.md`](./dimension-overlay-template.md).

---

## Mode B — Reference scaling (channel letters, angled storefronts)

Use **after Mode S** when fab is locked and user wants a photo overlay, **or**
when scaling from a **known reference** on the wall plane with no survey/art yet
(photo-only estimate).

### Workflow

```
Task progress:
- [ ] 1. Intake — fab size known (letters **+ logo**)? door size confirmed?
- [ ] 2. Mark pixel edges internally (door quad, cap line, logo form); tan fascia →
  detect_channel_letters.py + tan-fascia-detection.md
- [ ] 3. Run measure_facade.py or scale_from_reference.py
- [ ] 4. Run sanity checks (sanity-checks.md) — withhold logo height if gate E fails
- [ ] 5. Draw deliverable — red dimension lines per overlay-conventions.md
- [ ] 6. Emit output-template.md packet (+ PDF if requested)
```

### Logo + letters (AT&T, globe + wordmark, etc.)

Treat as **two elements** for measurement — one **line set** per requested dimension
on the deliverable:

| Element | Internal edges | Deliverable (when user asks) |
|---------|----------------|------------------------------|
| Letters | Cap-line top/bottom, outermost width | Height and/or width **dimension lines** |
| Logo / globe | Full sphere top → bottom (not stripe band) | Vertical **dimension line** + label at spec |

**Do not** scale logo height from the same mask as letters. **Do not** publish
logo height when logo ÷ cap **< 1.5** but the globe is visibly taller — ask for
fab spec (e.g. **4'-0"** globe).

**AT&T (from Smartsheet standards + design log):** Letter cap height is typically
**~60% of globe height**. Use `ATT DImensions Table with layout.xlsx` cap tier
(column A) for nearest standard overall width; globe is sized separately (survey,
EagleView, or user spec). See [`smartsheet-standards-intake.md`](./smartsheet-standards-intake.md).

When user gives logo fab size, place ticks/lines at spec height beside the globe
([`overlay-conventions.md`](./overlay-conventions.md)). Do not draw yellow/red
bounding boxes on the PNG/PDF.

**Spec label ≠ tick placement.** The label (e.g. **4'-0"**) comes from fab spec;
append **`EVO` only when the user asks**. Ticks must still land on the **sphere
top/bottom** via tight ROI + largest contiguous row block — not the last blue
pixel row in a wide mask.

### Mixed-case channel letters (CosmoProf, etc.)

Measure on the **cap line only** — same horizontal band for height and width.

| Dimension | Pixel edges |
|-----------|-------------|
| **Cap height** | Top of **C/P** → bottom of **C/P** |
| **Overall width (photo)** | Outermost **letter faces** at that cap line |
| **Overall width (fab)** | Raceway / cabinet / permitting width — often **wider** than letter faces; use user spec for labels |

**Tan fascia / low contrast:** Do **not** trust a full-width blue mask — it usually
hits the **gray cornice** above the letters. Follow [`tan-fascia-detection.md`](./tan-fascia-detection.md):
CLAHE → green-leaf anchor → cap-row ink → Sobel outer faces. Run:

```bash
python3 .agents/skills/vixxo-sign-scale-from-photo/scripts/detect_channel_letters.py \
  --image <photo> --json --debug tmp/<slug>-letter-edges-debug.png
```

Map detection JSON to `measure_facade.py --sign` as four **`x,y`** corners (TL TR
BR BL): `sign_l,cap_top sign_r,cap_top sign_l,cap_bot sign_r,cap_bot`. Use
`sign_quad` from `--json` when present. `sign_overall_width_in` from
`measure_facade.py` is **letter-face width**, not raceway fab width. If photo
letter-face width is **> 20% below** user fab width, report both and label overlay
from **fab spec** (gate J in [`sanity-checks.md`](./sanity-checks.md)).

Do **not** use full mixed-case ink height, lowercase extenders, or blue awning
shadow below the fascia. See exclusion rules in [`sanity-checks.md`](./sanity-checks.md).

**CosmoProf permitting:** When frontage is known, wall sign width is often limited
to **≤ 80% of storefront width** (city / landlord). Photo overlay must still show
building dimensions; some cities require photo elevations at architectural scale
(e.g. **3/8" = 1'-0"**) — see [`smartsheet-standards-intake.md`](./smartsheet-standards-intake.md).

### Dual-color wordmark (Sally Beauty, etc.)

Primary + secondary **channel letters in different colors** on white fascia —
**not** logo+globe, **not** single cap-line tier.

Follow [`dual-color-wordmark.md`](./dual-color-wordmark.md):

| Block | Typical fab (Sally Beauty) |
|-------|----------------------------|
| Primary (red) | **9'-10 1/4"** W × **2'-6"** H |
| Secondary (black) | **4'-1"** W × **10 1/2"** H |
| Gap | **3 3/4"** (baseline, not cap line) |
| Overall width | **13'-4"** (may ≠ sum of word widths + gap — gate N) |

**Fab from art page 2** (Mode S) or user spec — not photo iteration. When
survey-first path ran, labels are locked; photo is tick placement only. Separate
red vs black masks; separate height lines (primary left, secondary right by
default). Gap callout between wordmarks; **overall width** on bottom span.

**Door:** confirm **6'-0" × 7'-0"** double — pixel aspect **0.86–0.95**. Reject
full-storefront dark mask as door (gate C fail ~1.5–2.0).

**Y width:** include full **right arm at cap line** for primary width ticks.

**Do not** apply gate A failure on secondary height — use gate L instead.

### User-provided dimensions → overlay only

When fab size is known, draw **dimension lines** at spec size via homography; do
not argue photo-derived height/width against the spec. Example: 3'-0" × 7'-0"
door + sign **17'-11" W × 24" H** (CosmoProf 24" tier) as horizontal/vertical
red lines on the cap band (not filled rectangles). Photo letter-face width may
scale narrower (~13') — labels still use fab; ticks stay on C/f faces.

Deliverables:

```text
tmp/<slug>-sign-dimensions.png
~/Desktop/<slug>-sign-dimensions.pdf   (when user asks for red-line packet)
```

### Angled photos — homography (preferred)

**Recommended chain for channel letters:**

```bash
# 1) Detect letter-face ticks (tan fascia safe)
python3 .agents/skills/vixxo-sign-scale-from-photo/scripts/detect_channel_letters.py \
  --image <photo> --json --debug tmp/<slug>-letter-edges-debug.png

# 2) Scale with confirmed door quad on same wall plane (each corner is x,y)
python3 .agents/skills/vixxo-sign-scale-from-photo/scripts/measure_facade.py \
  --image <photo> \
  --door 346,248 396,248 396,365 346,365 \
  --door-width "3'" --door-height "7'" \
  --sign 210,156 424,156 210,178 424,178 --json
```

Substitute door/sign coordinates from your photo. Detection JSON includes
`sign_quad` strings ready for `--sign`. Verify door quad aspect (gate C or **C2**
for double doors) before trusting inches. Single **3'-0" × 7'-0"** leaf is OK
when jamb-to-jamb on the same plane as the sign. **6'-0" × 7'-0"** double →
aspect **0.86–0.95**; reject storefront-glass quads ([`dual-color-wordmark.md`](./dual-color-wordmark.md)).

### Flat quick estimate

```bash
python3 .agents/skills/vixxo-sign-scale-from-photo/scripts/scale_from_reference.py \
  --ref-pixels <REF_PX> \
  --ref-size "7'" \
  --target letter_height:<PX> \
  --target sign_overall_width:<PX> \
  --tolerance-pct 8
```

Emit [`output-template.md`](./output-template.md). Match client standard tiers via
Smartsheet workbook when available ([`smartsheet-standards-intake.md`](./smartsheet-standards-intake.md)),
else [`reference-dimensions.md`](./reference-dimensions.md).

---

## Measurement discipline

- Height reference → height targets only (unless dual-axis mockup mode).
- State pixel edges used and detection caveats.
- Widen tolerance to **12–15%** on angled or low-res photos.
- Never fabricate dimensions the pixels do not support.
- **Run [`sanity-checks.md`](./sanity-checks.md) before any point estimate.**
- **Save deliverable overlay before final numbers** — ticks must sit on cap/logo
  edges, not awning shadow ([`overlay-conventions.md`](./overlay-conventions.md)).
- **Cap ÷ door pixel ratio** should be ~0.28–0.36 for typical 7'-0" doors; flag
  if outside 0.25–0.45.
- **Height-ref vs width-ref** estimates must agree within **15%** or fix the
  door/sign quads.
- **Brand tier ratio** (cap ÷ overall width ≈ 0.10–0.12 for CosmoProf) — fail
  means wrong boxes, not "non-standard sign." Use **fab overall width** for the
  ratio when user gives raceway/permitting width; photo letter-face width alone
  will fail gate D and gate J on raceway signs.
- **Logo ÷ cap** (≥ 1.5 when logo dominates) and **logo ÷ door vs spec** — see
  gates E/F in [`sanity-checks.md`](./sanity-checks.md). Failed logo gates →
  letters only in the packet until user confirms logo fab size.
- **Dual-color wordmarks** — separate masks per color; gate L not gate A for
  secondary height; overall width may not sum (gate N). See
  [`dual-color-wordmark.md`](./dual-color-wordmark.md).

## Example — Select Medical mockup @ 4'-3" × 10'-0"

```bash
python3 .agents/skills/vixxo-sign-scale-from-photo/scripts/measure_panel_sign.py \
  --image assets/select-medical-mockup.png \
  --panel-height "4'-3\"" \
  --panel-width "10'-0\"" \
  --out-png tmp/select-medical-sign-dimensions.png \
  --out-pdf ~/Desktop/select-medical-sign-dimensions.pdf
```

Typical output band after user tuning: panel **4'-3" H × 10'-0" W**; primary
lines ~7–8½" cap height; taglines ~4½–5½" cap height.
