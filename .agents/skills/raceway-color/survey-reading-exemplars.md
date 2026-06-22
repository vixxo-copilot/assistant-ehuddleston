# Survey reading exemplars — paint and color

Patterns learned from real Vixxo survey PDFs, design-request forms, shop
drawings, and SP field packages on SharePoint. Use when `extract_survey_paint.py`
returns empty or when reconciling photo vs document.

Pair with [`survey-color-intake.md`](./survey-color-intake.md) and
`scripts/extract_survey_paint.py`.

---

## Document types (where color hides)

| Type | What it looks like | Where color lives | Text extract? |
|------|-------------------|-------------------|---------------|
| **Handwritten photo survey** | Site photo on letter page, blue/pink ink dims | Bottom margin or arrow to fascia | Usually **no** — render + read |
| **Shop drawing / Art PDF** | Typed spec block page 2 | `Sign Area Fascia Color`, letter Plex lines | **Yes** — preferred |
| **SP elevation package** | CAD front elevation + existing photo | Legend: `WALL COLOR \| PANTONE ###C` | **Yes** |
| **Vixxo D.R. 1.b form** | Typed header + embedded JPGs | Page 2 **Special Notes** (`RW Color - SW ####`) | **Yes** on notes page |
| **SP typed survey (Mister Sign Man style)** | Branded template, leader lines | `Wall color match` box → `SW ####` | **Yes** — may be sparse |
| **Pantone chip PDF** | Fan-deck photo or scan | Filename + visual chip (`7403 U`) | **No** — visual / filename |
| **Design request + attachment** | Email/DR references `Pantone 7403U.pdf` | Separate chip file in same folder | Parse filename + open chip |

**Trap:** filenames containing `Survey` may be **invoices** (e.g. McCorkle
`Inv. 221176 - … Survey 1.pdf` = billing doc, not sketch). Open the PDF; if no
sketch, search the PO folder for the actual field sketch or annotated photos.

---

## Exemplar 1 — Handwritten PMS on photo (VX1109266, Sally #5556 Halifax)

**Source:** `Survey/Sally-site-survey.pdf` (2 pp, scanned)

**Read visually:**

- Photo of tan stucco fascia + raceway-mounted Sally set
- Handwritten: `Pantone 4685 C` (underlined, bottom of page)
- Notes: `Wall is Stucco`, `Sally Sign is on Raceway`
- Dims: 239½" × 107½" available fascia

**Maps to:**

| Surface | Spec |
|---------|------|
| Fascia | PMS 4685 C |
| Raceway | PMS 4685 C (same band) |
| Letters | `#2793` SALLY, `#2447` + perf vinyl BEAUTY (from art PDF) |

**SW order starting point:** SW 7723 Colony Buff (brush-out on stucco)

**Lesson:** run extract script → empty `merged` → render page 1 with PyMuPDF
→ read ink. Pass OCR text via `--text` if batching.

---

## Exemplar 2 — Shop drawing spec block (VX1109266 Art PDF)

**Source:** `Art & EPS/VX1109266-art.pdf` page 2 text layer

**Lines to grep:**

```
Sign Area Fascia Color Pantone 4685C
“SALLY” #2793 RED 3/16” PLEX.
“ BEAUTY” #2447 WHITE ACRYLIC WITH 70/30 BLACK
PAINTED PANTONE PMS 4685 C
```

**Maps to:** fascia + raceway paint **and** letter acrylic in one file.

**Lesson:** when survey scan is empty, **always** pull Art PDF page 2. Codes
may appear as `4685C` (no space before C) — extractor handles inline suffix.

---

## Exemplar 3 — Elevation legend (Sally #10439, Manalapan NJ)

**Source:** `Sally10439 SURVEY.pdf` page 2 (Sign Management)

**Legend text:**

```
WALL COLOR | PANTONE 474C
```

Plus `EXISTING CONDITIONS` photo (tan cement wall) and channel-letter dims.

**Maps to:** field paint on **cement wall** behind sign — not letter faces.

**Lesson:** `WALL COLOR` in elevation legend = fascia/wall paint spec even when
the drawing labels the surface "CEMENT WALL". Pipe-separated legend format is
common on Sign Management / similar SP CAD exports.

---

## Exemplar 4 — Raceway in special notes (Sally #2183, Laura Carlile)

**Source:** Vixxo D.R. 1.b PDF page 2

**Typed note:**

```
RW Color - SW 7100 Arcade White
```

**Context:** Channel letters on raceway; front elevation 2'-6" × 13'-4";
Meridian Village / Bellingham WA.

**Maps to:**

| Surface | Spec |
|---------|------|
| Raceway | SW 7100 Arcade White |
| Fascia | White in photos — cross-check; survey note is raceway-specific |

**Lesson:** `RW` = raceway. Color often only in **Special Notes**, not header.
Page 1 photos supply fascia when notes only mention raceway.

---

## Exemplar 5 — Wall color match callout (Life Storage, Survey Information.pdf)

**Source:** Mister Sign Man / Vixxo Sign & Lighting template page 2

**Layout:**

- Box label: `Wall color match-`
- Inside box: `SW 7669` (Mooring Buoy)
- Leader arrow to building diagram fascia
- Footer: `Paint Color Match Required` + brand list (SW, BM, Matthews, Pantone)

**Also in package:** page 5 → `SW 7100` (separate elevation / canopy note).

**Lesson:** SW code may sit in a **graphic callout**, not a sentence. Grep all
pages; one PDF can carry **multiple SW codes** for different surfaces.

---

## Exemplar 6 — Pantone chip attachment (Sally #3086, Connie Keck)

**Sources:**

- `Connie Keck Sally 3086.pdf` — Vixxo D.R. with storefront / pylon photos
- `Pantone 7403U.pdf` — field photo of fan deck against **ochre stucco**

**Extracted:** page 3 text references `PDF Pantone 7403U.pdf`; chip shows
**PANTONE 7403 U** held to yellow-gold stucco.

**Maps to:** fascia / wall field paint (uncoated U chip = matte wall read).

**Lesson:** color may be **only** in a sidecar chip PDF. Search folder for
`Pantone*.pdf`, `Wall Color.pdf`, `WALL COLORS.pdf`. U vs C matters — exterior
stucco usually matches **U** chips or architectural paint, not glossy C.

---

## Exemplar 7 — Photo-only fascia bands (Canadian Sally, not survey-backed)

**Source:** user storefront photo (banded fascia)

**Sampled (photo script):**

| Band | Hex | Nearest SW |
|------|-----|------------|
| Center cream | ~`#D8D1C9` | SW 7647 Crushed Ice |
| Upper/lower tan + raceway | ~`#DBBAA3` | SW 2823 Classic Sand |

**Lesson:** multi-band fascias need **per-band** rows. Raceway follows the band
it mounts on (here: tan). No survey → label confidence **photo-estimate** and
require brush-out.

---

## Reading checklist (any survey)

```
1. Classify PDF type (table above)
2. Run extract_survey_paint.py on Survey.pdf AND Art.pdf
3. If merged empty → render pages → read handwriting / callout boxes
4. Search same folder: Pantone*.pdf, Wall Color*, *chip*
5. Split letter materials (#2793, #2447) from field paint (SW/PMS)
6. Note surface each code applies to (fascia vs raceway vs wall)
7. If photos exist → reconcile_colors.py; survey wins on explicit codes
```

---

## Common label → surface map

| Survey label | Usually means |
|--------------|---------------|
| `Sign Area Fascia Color` | Fascia paint behind sign |
| `WALL COLOR` / `Wall color match` | Building wall / fascia paint |
| `RW Color` | Raceway paint |
| `PAINTED PANTONE` / `PAINTED TO MATCH` | Raceway or returns — read next words |
| `match fascia` / `match existing` | Photo or chip required |
| `#2793` / `#2447` | Letter face acrylic — **not** field paint |
| `PRE-PAINTED BLACK` (returns) | Factory aluminum — not site paint |

---

## SharePoint search hints

When survey PDF lacks codes:

- `"WALL COLOR"` → elevation packages, chip scans
- `"RW Color"` → Vixxo D.R. forms
- `"Pantone"` + store number → chip PDFs
- `{store} Signage/Survey/` **and** `Art & EPS/` in same year folder

---

## Script coverage (post-study)

`extract_survey_paint.py` targets these patterns:

- `SW ####`, `Sherwin-Williams ####`
- `PMS #### C`, `Pantone #### C`, inline `474C` / `4685C`
- `WALL COLOR | PANTONE ####C`
- `Sign Area Fascia Color Pantone ####`
- `RW Color - SW ####`
- Plex `#2793`, `#2447`, `#7328`; part `SB30RB`

Still requires visual read: handwritten ink, callout boxes without text layer,
Pantone chip photos, multi-band fascias with one survey code.
