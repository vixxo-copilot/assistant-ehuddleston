# Overlay conventions — dimension lines (deliverables)

Final PNG/PDF overlays use **red dimension lines only**. Never ship colored
bounding boxes on deliverables.

## Deliverable vs internal edge work

| Phase | What to draw | Where |
|-------|----------------|-------|
| **Internal** | Pixel edges, door quad, cap line, logo form (mental notes or optional `tmp/<slug>-debug-edges.png`) | Agent only — not for the user |
| **Deliverable** | Red dimension lines + feet-inches labels | `tmp/<slug>-sign-dimensions.png`, `~/Desktop/<slug>-sign-dimensions.pdf` |

**Do not** put verification boxes on the deliverable:

- No **green** door quad
- No **yellow** logo / globe box
- No **red** letter cap-line rectangle
- No solid red fill column spanning element height

Those colors were draft aids; users expect **shop-drawing style** red lines.

## Line style (all modes)

| Property | Value |
|----------|--------|
| Line color | `(220, 20, 30)` |
| Line weight | 2 px |
| Font | Arial Bold, 15–16 px |
| Label color | Red text; **white backing optional** (user may request plain red labels) |
| Label format | **Default:** feet-inches only — `4'-0"`, `22'-0"`, `2'-4"`. **Never**
  append `EVO` unless the user explicitly asks for evo labels in that request. |
| Title bar | **No** photo title strip on the overlay image |

### Vertical height (one element)

Use when user asks for **one** dimension (e.g. globe height only):

1. **Top tick** — horizontal segment at element top; aligned to top edge.
2. **Bottom tick** — horizontal segment at element bottom; aligned to bottom edge.
3. **Vertical line** — immediately left (or right) of the element, from top tick to bottom tick.
4. **Ticks point toward** the element (from the vertical line toward the sign).
5. **Label** — beside the line at vertical center; white pad behind text when used.
6. **Line gap** — split the vertical line above/below the label (do not run line through text).

Do **not** use a solid red rectangle the full height of the element.

### Horizontal width

1. Dimension line **below** (or above) the element span.
2. Vertical ticks at left and right extents.
3. Label centered on the horizontal line; white backing when used.

### Corner-to-letter (shop drawing callout)

When revs ask to show placement (Smartsheet art-team pattern), add a **horizontal
dimension line** from a building corner (or lease edge) to the first/last letter
face — same red line style, feet-inches label (add `EVO` only if user asked).
Use when user or standards intake requests “measurement from corner to letter”;
omit if user asked for element size only.

### Multiple dimensions

Draw **separate line sets** per requested dimension. If the user asks for globe
height only, deliver **one** vertical line — no letter width, no door reference.

When user asks for cap height **and** overall width (CosmoProf spec):

- Width: horizontal line below sign, ticks at outermost letter faces.
- Height: vertical line at right (or left), ticks at cap line top/bottom.
- Optional: thin red outline of panel/sign face is OK when it **is** the dimension
  line path (Mode A panel script) — not a filled box.

## Placement rules

- Align ticks to **fab spec edges** when user gave spec; use photo only for placement.
- **Globe / sphere (tick placement)** — label comes from **fab spec**; ticks come
  from **sphere pixel edges**, not the widest blue mask in frame.
  1. Restrict to a **tight x-band** over the globe only (exclude AT&T letters and
     spill to the right — e.g. globe center column ± ~40 px).
  2. Per row: count blue/stripe pixels in that band; keep rows with enough signal
     (≥ ~12 px).
  3. Split into **contiguous vertical blocks**; break when a row gap exceeds ~8 px.
  4. Use the **largest block** as the sphere — `y_top` = first row, `y_bot` = last
     row of that block only.
  5. **Do not** use “last blue row in slice” — that pulls ticks onto siding/brick
     or stray blobs below the sphere (common AT&T failure).
  6. Vertical line ~10–14 px left of the globe’s left edge at mid-height; ticks
     point toward the sphere.

  **Wrong vs right (AT&T):** first pass `y_bot` ≈ 293 (siding line); corrected
  block `y_bot` ≈ 253 (true sphere bottom). Label **4'-0"** (add `EVO` only on request).
- **Cap line** — ticks at C/P top and bottom; width at outermost letter faces on
  the same band. Exclude awning shadow below fascia.
- **User reference overlay** — match their line weight, tick direction, and label
  placement when they provide an example PDF/PNG.

## AT&T globe example (spec overlay)

User spec: globe **4'-0"**. Deliverable:

- One vertical red line beside the globe, ticks aligned to sphere top/bottom.
- Label `4'-0"` (or `4'-0" EVO` if requested) on white backing, mid-height, left of line.
- No letter dimensions, no door box, no red column.

## CosmoProf example (spec overlay)

User spec e.g. **17'-11" W × 24" H** (or **22'-0" W × 2'-4" H**). Deliverable:

- Ticks on **letter faces** (C left, f right) and **C/P cap** — from
  `detect_channel_letters.py` or CLAHE QA ([`tan-fascia-detection.md`](./tan-fascia-detection.md)).
- Labels from **user fab spec**, not photo letter-face scale, when gates J/K fail.
- Default callout: width **below**, height **right**; **mirror** (width above,
  height left) when user asks — same tick anchors, flip line side only.
- Homography from confirmed door; never stretch ticks to fake a wider fab width.

**Photo-only estimate** (no fab): report letter-face width and cap height with
±12–15% band; state that raceway/cabinet width may be larger.

## Sally Beauty example (dual-color wordmark)

Fab spec (labels from user; ticks from photo):

| Callout | Label | Placement |
|---------|-------|-----------|
| Primary (red) width | **9'-10 1/4"** | Above red word |
| Primary height | **2'-6"** | Left of red |
| Secondary (black) width | **4'-1"** | Above black word |
| Secondary height | **10 1/2"** | Right of black |
| Gap | **3 3/4"** | Between words (baseline ticks) |
| Overall width | **13'-4"** | Below full outer span |

- Overall **13'-4"** may **not** equal primary W + gap + secondary W (gate N) —
  do not stretch ticks to force arithmetic.
- Gap ticks: **Y stem right → B left** at baseline; cap-line gap may be zero.
- Primary width ticks: include **full Y** right arm at cap.
- When user says "decrease by 1'", confirm **which** callouts change.

Full workflow: [`dual-color-wordmark.md`](./dual-color-wordmark.md).

## Checklist before saving deliverable

- [ ] Only red dimension lines + labels (white backing only if requested)
- [ ] Ticks aligned to correct edges (shadow and stripe bands excluded)
- [ ] User-requested dimensions only (omit extra callouts)
- [ ] Spec labels match user fab size, not photo estimate, when spec was given
