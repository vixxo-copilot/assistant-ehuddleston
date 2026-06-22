# Dual-color wordmark (Sally Beauty pattern)

Red primary + black secondary channel letters on a **white fascia** — same
baseline, **different cap heights**. Lessons from Sally Beauty storefront
overlays (2026).

Use when the sign is **two color blocks** (not logo+globe, not mixed-case
single tier like CosmoProf).

## Intake (survey + art first)

**Default:** Load fab from **shop drawing page 2** and survey via Mode S
([`survey-first-intake.md`](./survey-first-intake.md)). Photo iteration comes
**after** fab is locked.

When no survey/art exists, ask for **fab spec per block** — do not loop photo
estimates against user numbers.

| Field | Example (Sally Beauty) |
|-------|------------------------|
| Primary (red) width × height | **9'-10 1/4"** × **2'-6"** |
| Secondary (black) width × height | **4'-1"** × **10 1/2"** |
| Gap (red → black) | **3 3/4"** |
| Overall / permitting width | **13'-4"** (often **≠** sum of word widths + gap) |
| Door reference on site | **6'-0" × 7'-0"** double (confirm) |

**Stop rule:** Once any fab field is known, labels come from spec; photo is for
**tick placement only**.

## Detection (white fascia)

Band: white panel between blue trim lines; letters in upper fascia `y` band only.

### Red primary (SALLY)

```text
r >= 155, g <= 75, b <= 110, r > g + 60, r > b + 40, r+g+b < 500
cap band: y ~118–150 for width splits
full height: y ~118–205 for red cap ticks
```

### Black secondary (BEAUTY)

```text
r,g,b <= 45–50 on white fascia
restrict x to secondary cluster (right of primary)
cap band: y ~174–200 (lower than red — same baseline, shorter caps)
```

**Do not** use one mask or one cap box for both colors.

### Door reference (critical)

Use **double-door opening only** — jamb-to-jamb, head-to-sill on same wall plane.

| Reference | Pixel aspect `door_w / door_h` |
|-----------|------------------------------|
| **6'-0" × 7'-0"** double | **0.86 – 0.95** ✓ |
| Whole dark storefront | **~1.5 – 2.0** ✗ |

Auto dark-mask on glass often spans **entire window wall** → scales all
dimensions wrong (~5–15%). Mark door quad **manually**; verify gate C before
homography.

## Width rules

### Per-word width (top overlay)

Ticks on **outermost letter faces** per color block at that block's cap band.

**Y and diagonal letters:** width includes **full right arm at cap line** (not
stem bottom only). Cap-line right face of **Y** can sit **20–30 px** right of
stem bottom tick.

### Gap (red → black)

| Band | Behavior |
|------|----------|
| **Cap line** | Y right arm may **overlap** black ink → gap **≤ 0 px** |
| **Baseline** | Measure **Y stem right face → B left face** for gap callout |

Default gap overlay: **baseline band** between wordmarks (not cap line).

### Overall width (bottom overlay)

**Permitting / raceway / cabinet** width — ticks on **outermost sign faces**
(primary left → secondary right, or panel corners when defined).

Often **narrower** than `primary_w + gap + secondary_w` (letter-face widths).
See gate N in [`sanity-checks.md`](./sanity-checks.md).

Example (Sally Beauty fab):

| Label | Inches |
|-------|--------|
| SALLY W | 118.25 |
| Gap | 3.75 |
| BEAUTY W | 49.00 |
| Sum of parts | 171.00 (14'-3") |
| **Overall (fab)** | **160.00 (13'-4")** |

Do **not** force bottom label to equal sum of top labels without user confirmation
of which width definition applies.

## Height rules

| Block | Measure |
|-------|---------|
| **Primary (red)** | Top of tallest red caps → baseline / bottom of red body |
| **Secondary (black)** | Top of black caps → baseline ( **not** red cap height) |

Expected ratio (gate L):

```text
secondary_h / primary_h  ≈  0.30 – 0.45
```

Sally Beauty: **10.5" / 30" ≈ 0.35** ✓

**Gate A** (cap ÷ door) applies to **primary block only**. Secondary failing
gate A is **expected** — not a detection error.

## Deliverable overlay layout

Default Sally-style packet (all from fab when known):

| Callout | Placement | Notes |
|---------|-----------|-------|
| Primary width | Above red word | e.g. `9'-10 1/4"` |
| Primary height | Left of red | e.g. `2'-6"` |
| Secondary width | Above black word | e.g. `4'-1"` |
| Secondary height | Right of black | e.g. `10 1/2"` |
| Gap | Between words, below cap | e.g. `3 3/4"` |
| Overall width | Below full span | e.g. `13'-4"` |

See [`overlay-conventions.md`](./overlay-conventions.md) Sally Beauty example.

## User feedback traps

| User says | Wrong agent move | Correct move |
|-----------|------------------|--------------|
| "Decrease both by 1'" | Shrink primary **height** and overall width | Ask **which labels**; often overall + gap only |
| "Count the whole Y" | Width at stem only | Extend right tick to Y cap arm |
| "Very close" | Keep tuning photo scale | Ask for **fab deck**; switch to spec labels |
| "Put widths back" | Drop overall/gap callouts | Restore per-word widths; **keep** gap + overall |

When user corrects one label, **do not** auto-rescale unrelated labels from pixels.

## Photo-only estimate band

If no fab spec: report primary and secondary separately with **±12–15%**;
note overall permitting width may differ from sum of letter-face spans + gap.

## Debug artifacts

```text
tmp/<slug>-sally-beauty-debug.png   — red/black boxes + door quad
tmp/<slug>-letter-edges-debug.png  — per-color cap ticks
```
