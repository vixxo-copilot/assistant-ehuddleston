# Sanity checks — channel letter / reference scaling

Run **every check** before publishing a point estimate from a photo. If a check
fails, fix pixel edges or widen tolerance — do **not** ship a single number.

## Intake (ask first)

0. **Client/brand named?** → Pull Smartsheet standards row + dimension xlsx
   ([`smartsheet-standards-intake.md`](./smartsheet-standards-intake.md)) before
   trusting photo tiers.
1. Any **known fab size** (letter height, overall width, **logo/globe height**)?
   → spec overrides photo (matches latest New Design Log “revise per survey”).
2. **Reference size on site** (door jamb-to-jamb, door height head-to-sill)?
   → prefer user-confirmed over defaults in [`reference-dimensions.md`](./reference-dimensions.md).
3. **Sign composition** — letters only, or **logo + letters** (globe, medallion,
   icon)? If logo + letters, ask for **each element's fab height** when known.

If the user gives fab dimensions, use the photo for **overlay placement only**.
Do not re-estimate height/width from pixels against their spec.

When a **3D logo** is present and no logo fab size is known, **do not publish a
logo height point estimate** from the photo. Report letter cap height only (if
gates pass) and ask for logo spec before drawing logo dimension lines.

## Mixed-case cap line (CosmoProf, etc.)

| Measure | Use | Do not use |
|---------|-----|------------|
| **Cap height** | Top of **C/P** → bottom of **C/P** on the **cap line** | Full word top-to-bottom, lowercase extenders, awning shadow |
| **Overall width (photo)** | Outermost letter faces at the **same cap-line band** | Full-frame color smear, shadow below the fascia |
| **Overall width (fab)** | Raceway / permitting width from user or Smartsheet tier | Letter-face span alone when fab is wider (gate J) |

Height and width must share the **same horizontal band** (cap line), not the
full mixed-case body.

## Logo / globe / icon (separate from cap line)

Signs with **logo + letters** (AT&T globe, medallions, brand marks) require
**separate edge marks** per element internally. Never reuse the letter cap-line
span for logo height. On the **deliverable**, draw one **dimension line set** per
requested dimension — see [`overlay-conventions.md`](./overlay-conventions.md).

| Element | Measure | Do not use |
|---------|---------|------------|
| **Letter cap height** | Cap line on text only | Logo ink, globe stripes |
| **Logo height** | Top of logo form → bottom of logo form (full 3D extent) | Color-mask stripe band, partial sphere highlight |
| **Overall width** | Outermost logo edge → outermost letter edge **at cap line** | Logo-only cluster width when user asked for full sign width |

### 3D logo trap (color mask)

Dimensional logos (striped spheres, molded icons, raised medallions) often show
as **narrow contrast bands** in photos. A blue/red color mask typically captures
**middle stripes**, not the full fabrication height.

**Stop rule:** If logo pixel height is **≤ 1.25× letter cap height** on a sign
where the logo is visibly taller than the letters (globe, round mark, etc.),
the logo edges are wrong — **do not scale it**. Ask for fab spec or mark edges
manually (full top/bottom of the form, not ink alone).

Example failure: AT&T globe read **~14.6"** from ~60 px stripe band; fab spec
**4'-0"** needs ~**198 px** on the same door reference (~3× taller).

### Logo vs letter ratio gate

When both logo and letter edge marks exist:

```text
logo_h_px / cap_h_px  should be ≥ 1.5
```

when the logo **visually dominates** height (round mark beside lowercase/small caps).

If logo ÷ cap **< 1.5** but the logo looks taller in the photo → wrong logo edges.
If gate A (cap ÷ door) **fails** because letters are small dimensional type,
**do not infer logo height from the same failed mask** — dimensional letters and
3D logos need independent edge marks and specs.

## Shadow / smear exclusion

- Cut off fascia band **above awning transition** (typical y cutoff before shadow).
- **Cornice trap:** if ink centroid y is **above** tan fascia (well above glass top),
  reset search band — see [`tan-fascia-detection.md`](./tan-fascia-detection.md).
- Exclude connected components wider than ~350 px (horizontal smear).
- **Horizontal panel seams:** zero any row with ink on **> 35%** of fascia width.
- Exclude ink below the cap line when measuring **cap height**.
- If blue mask spans full image width, tighten x-bounds to letter clusters or run
  `detect_channel_letters.py`.

## Automated gates

Compute from the **same door quad** and internal edge marks used for homography.

### A. Cap height ÷ door height (pixels)

Typical channel letters on a 7'-0" door: cap is **~28–36%** of door height.

```text
cap_px / door_h_px  should be 0.25 – 0.45
```

Example: 28" letters on 84" door → 28/84 ≈ **0.33**. Flag if outside band.

### B. Height-ref vs width-ref agreement

Scale cap height from door **height**; scale sign width from door **width**.

```text
|cap_h_ref − cap_w_ref| / cap_h_ref  should be ≤ 15%
|width_h_ref − width_w_ref| / width_h_ref  should be ≤ 15%
```

If either fails, the **door quad** or **edge marks** are wrong — fix before reporting.

### C. Door quad aspect (pixel check)

For a **3'-0" × 7'-0"** single-leaf reference:

```text
door_w_px / door_h_px  should be 0.38 – 0.55
```

For a **6'-0" × 7'-0"** double-door reference, use gate **C2** instead (below).

Much wider → sidelites/frame included, or entire storefront glass marked as door.
Much narrower → leaf only with wrong height.

### D. Brand tier ratio (when client known)

Letter height ÷ **fab overall width** ≈ **0.10 – 0.12** for standard CosmoProf
tiers. Use Smartsheet/workbook permitting width — **not** photo letter-face span
(gate J).

Examples: 24" ÷ 215" (17'-11") = **0.112** ✓ · 28" ÷ 264" (22'-0") = **0.106** ✓
· 38" ÷ 140" (letter-face only) = **0.27** ✗

Fails → cap height mark too tall, width mark too narrow, or letter-face width
used where fab raceway width was required.

### E. Logo ÷ cap height (pixels) — when logo + letters

Only when **separate logo edge marks** exist (internal; not drawn on deliverable):

```text
logo_h_px / cap_h_px  should be ≥ 1.5
```

when the logo is a round/tall mark beside the wordmark.

Fails → logo measured on stripe/ink band, not full form. **Withhold logo scaled
height**; request fab spec or manual edge fix.

Passing E does **not** prove logo height — it only catches the common under-measure.
Prefer user fab spec for logos.

### F. Logo ÷ door height (pixels) — sanity when spec known

When user gives logo fab height (e.g. **4'-0"** on **7'-0"** door):

```text
expected logo_h_px ≈ (logo_in / door_in) × door_h_px
```

Example: 48" ÷ 84" × 346 px ≈ **198 px**. If marked logo span is **< 70%** of
expected px, edges are wrong — fix before drawing dimension lines.

### G. AT&T letter cap ÷ globe height (when both specs known)

From Smartsheet design-log practice: letter cap ≈ **60% of globe height**.

```text
cap_in / globe_in  should be 0.55 – 0.65
```

Example: **4'-0"** globe (48") → cap **28"–30"** ✓ · cap **12"** ✗ (wrong tier
or globe/letter conflated).

Fails → check separate globe vs letter specs; use xlsx cap tier column A.

### H. CosmoProf wall sign ÷ storefront frontage (when frontage known)

Permitting revs limit wall sign to **≤ 80% of facade width**.

```text
sign_width_ft / frontage_ft  should be ≤ 0.80
```

Example: 17.916' sign on 19' frontage → **94%** ✗ (Rochester Hills R4 pattern).

Fails → narrow sign on overlay to compliant width or ask user which frontage is
authoritative.

### I. Sign fit on lease wall (Secure Space / tight fascia)

When user gives **available wall width**, scaled letter run must fit:

```text
scaled_sign_width_in  should be ≤ wall_width_in
```

Example: **7'-7/8"** letter run on **6'-4"** wall ✗ — reduce cap tier or report
conflict (N Hollywood revision pattern).

### J. Letter-face width vs fab overall width (CosmoProf / raceway signs)

Photo detection measures **outermost letter faces** at the cap line. Fab /
permitting **overall width** is often **20–40% wider**.

```text
(fab_width_in − photo_letter_width_in) / fab_width_in  > 0.20  →  gate fails for “photo = fab”
```

Example: letter faces scale to **~13'**; user fab **17'-11"** → report both; use
**fab for overlay labels** unless user asks for letter-face-only width.

Fails → do not stretch ticks to match fab without a defined raceway/panel edge;
ask which width definition applies.

### K. Cap height vs fab tier (low-contrast tan fascia)

When user or Smartsheet tier implies cap **≥ 22"** (e.g. **24"**) but photo
cap span scales to **< 18"** at the same door reference:

```text
cap_px / door_h_px  < 0.20  with visible uppercase letters  →  likely under-measured cap ticks
```

Re-run CLAHE zoom QA on C/P columns ([`tan-fascia-detection.md`](./tan-fascia-detection.md)).
Use fab cap for overlay labels when user confirms; photo ticks stay on visible C/P.

### L. Secondary ÷ primary cap height (dual-color wordmarks)

When primary and secondary blocks share a baseline but differ in height (Sally
Beauty red + black):

```text
secondary_h_in / primary_h_in  should be 0.30 – 0.45
```

Example: **10 1/2"** black ÷ **2'-6"** (30") red = **0.35** ✓

Fails → blocks were conflated in one cap box, or wrong color mask. See
[`dual-color-wordmark.md`](./dual-color-wordmark.md). **Do not** judge secondary
height with gate A (cap ÷ door) — it will fail by design.

### M. Inter-word gap (baseline vs cap line)

Gap between color blocks must be measured at **baseline** (Y stem → B left), not
cap line when Y right arm overlaps secondary ink.

```text
cap_line_gap_px ≤ 0  with visible baseline white space  →  use baseline for gap callout
```

Photo cap gap **0 or negative** is normal; baseline gap scales to inches for the
gap label. Label from **user fab gap** when known.

### N. Overall width vs word widths + gap (dual-color / permitting)

Bottom **overall** width often differs from sum of per-word letter-face widths +
gap (same class of error as gate J on raceway signs).

```text
|overall_fab_in − (primary_w_in + gap_in + secondary_w_in)| / overall_fab_in  > 0.05
  →  do not force arithmetic consistency on overlay labels
```

Example: **9'-10 1/4" + 3 3/4" + 4'-1" = 14'-3"** but overall fab **13'-4"** —
use **13'-4"** on bottom line; keep per-word labels from user spec. Report both
in packet; ticks on outermost faces / panel edges per [`dual-color-wordmark.md`](./dual-color-wordmark.md).

### C2. Double-door aspect (6'-0" × 7'-0" reference)

When reference is a **pair of doors**, not a single leaf:

```text
door_w_px / door_h_px  should be 0.80 – 0.95
```

Much wider (~1.5+) → entire storefront glass was marked as door — rescale will be
wrong (~10–15%). See [`dual-color-wordmark.md`](./dual-color-wordmark.md).

## Overlay approval (required)

Before final numbers:

1. **Internally** verify pixel edges (door quad, cap line, logo form). Optional
   debug file: `tmp/<slug>-debug-edges.png` — never ship colored boxes to the user.
2. **Deliverable** must follow [`overlay-conventions.md`](./overlay-conventions.md):
   red dimension lines; white label backing only when not omitted by user.

**Stop** if height ticks would include awning shadow or sit below letter caps.

**Stop** if logo ticks span only a color stripe or sit inside letter cap height
while the globe visibly extends above/below the wordmark.

**Stop** if the globe bottom tick sits on the **siding/brick transition** or below
the visible sphere while the label still calls out globe height — re-run **contiguous
block** detection in a tight globe x-band ([`overlay-conventions.md`](./overlay-conventions.md)).
Spec label can be correct while tick placement is wrong; both must pass review.

**Stop** if the deliverable uses solid red fill columns or green/yellow/red
bounding boxes instead of dimension lines.

## User feedback

"Height smaller / width bigger" may mean:

- **Correcting your estimate** (adjust math), or
- **Stating field truth** (fab size differs from estimate)

Ask: *"Are you correcting the photo estimate, or giving the fabrication size?"*

Do **not** widen the cap band because height "feels small" without re-checking
the overlay. User fab spec **replaces** photo estimates — do not iterate pixels
against confirmed dimensions.

## Confidence downgrade

Set **low** confidence and list failing checks when:

- Any gate above fails after one edge fix attempt
- Screenshot / heavy compression / strong perspective
- User has not confirmed reference size on site
- **3D logo present** and logo height was estimated from color mask without fab spec
- Logo ÷ cap gate (E) fails — report letter dimensions only; omit logo height until spec
- AT&T gate (G) or CosmoProf gate (H) fails — state brand rule conflict in packet
- Gate J fails **and user did not provide fab width** — withhold tight width estimate;
  ask for raceway/permitting width
- Gate J fails **but user gave fab width** — expected on raceway signs; label from
  fab, report photo letter-face separately (do **not** downgrade overlay confidence)
- Gate K fails **and no fab cap known** — re-run CLAHE QA before publishing cap height
- Gate K fails **but user gave fab cap** — expected on tan fascia; label from fab,
  ticks stay on visible C/P (do **not** downgrade overlay confidence)
- Gate L fails on dual-color sign — conflated masks; split per
  [`dual-color-wordmark.md`](./dual-color-wordmark.md)
- Gate N fails **but user gave overall + per-word specs** — expected; do not
  force labels to sum; use fab for each callout
- Gate C2 fails — door quad is storefront glass, not door opening
- Smartsheet workbook unavailable — note fallback to [`reference-dimensions.md`](./reference-dimensions.md)

## Photo estimate vs fab spec (multi-element)

| User provides | Agent action |
|---------------|--------------|
| Letter height only | Scale letters; logo overlay at spec or **ask** for logo height |
| Logo height only (e.g. 4'-0") | Vertical dimension line at spec; letters separate or ask |
| Full deck (letters + logo + width) | Homography + dimension lines at spec — **no pixel re-estimate** |
| Dual-color deck (primary + secondary + gap + overall) | Per-block lines at spec — see [`dual-color-wordmark.md`](./dual-color-wordmark.md) |
| Nothing | Cap-line estimate OK for letters; **no logo height line** unless gates E/F pass |
