# Sign scale packet

Copy this template into chat. Replace bracketed fields.

```markdown
## Sign scale estimate — [client / site label]

**Photo:** [filename or source]
**Reference:** [object] = [known size] ([pixel extent] px)
**Method:** [height|width] scaling, [single|dual|homography] reference
**Perspective / quality flags:** [none | angled | low-res | partial occlusion]
**Source:** [photo estimate | user fab spec + overlay placement]
**Smartsheet standards:** [workbook + tier pulled | not queried | unavailable]

### Sanity checks (required before point estimate)

| Check | Result | Notes |
|-------|--------|-------|
| Cap ÷ door height (px) | [ratio] | Pass band 0.25–0.45 |
| Height-ref vs width-ref | [±%] | Must be ≤ 15% |
| Door quad aspect (px) | [w/h] | Pass band 0.38–0.55 for 3'×7' |
| Brand tier ratio (cap÷width) | [ratio] | ~0.10–0.12 CosmoProf; use fab width not letter-face |
| Logo ÷ cap height (px) | [ratio] | ≥ 1.5 when logo+letters; else withhold logo height |
| Logo ÷ door vs spec (px) | [actual vs expected] | Gate F when logo fab size known |
| AT&T cap ÷ globe (in) | [ratio] | Gate G: ~0.55–0.65 when both known |
| Wall sign ÷ frontage | [ratio] | Gate H: CosmoProf ≤ 80% when frontage known |
| Sign ÷ lease wall width | [fits?] | Gate I when wall limit given |
| Letter-face vs fab width | [photo vs fab] | Gate J: >20% gap → label from fab |
| Cap px vs fab tier | [ratio] | Gate K: cap÷door <0.20 on tan fascia |
| Detection method | [CLAHE/leaf/Sobel/script] | See tan-fascia-detection.md |
| Secondary ÷ primary height | [ratio] | Gate L: dual-color ~0.30–0.45 |
| Gap (baseline) | [in] | Gate M; cap gap may be ≤0 |
| Overall vs sum of parts | [compare] | Gate N: permitting vs letter-face sum |
| Double-door aspect (px) | [w/h] | Gate C2: 0.80–0.95 for 6'×7' |
| Overlay reviewed | [yes/no] | Deliverable = dimension lines only; ticks on correct edges |

If any check fails, state **low** confidence and list failing checks. Do not
ship a tight point estimate until edges are fixed or user confirms fab spec.

### Measured in photo (pixels)

| Dimension | Pixels | Scaled | Range (+/- [n]%) |
|-----------|--------|--------|------------------|
| [letter_height] | [px] | [ft-in] | [low] – [high] |
| [sign_overall_width] | [px] | [ft-in] | [low] – [high] |
| [logo_height] (optional) | [px] | [ft-in] | [low] – [high] |

Omit the logo row (or mark **spec only / withheld**) when gate E fails — do not
ship color-mask stripe height as a point estimate.

Deliverable overlay must use **red dimension lines**, not colored bounding boxes
— see [`overlay-conventions.md`](./overlay-conventions.md).

### Nearest standard size (if known)

| Field | Estimate | Closest standard | Delta |
|-------|----------|------------------|-------|
| Letter height | [in] | [12"/18"/24"/etc.] | [+/- in] |
| Overall width | [ft-in] | [standard width] | [+/-] |

### Confidence

- **Point estimate:** [size call]
- **Confidence:** [high | medium | low]
- **Why:** [1–2 sentences on reference quality and perspective]

### Deliverables

- Draft overlay PNG: `tmp/[slug]-sign-dimensions.png`
- PDF (if requested): `~/Desktop/[slug]-sign-dimensions.pdf`

### Next step

- [ ] Confirm reference dimension on site
- [ ] Capture straight-on photo for tighter estimate
- [ ] Pull brand workbook from Smartsheet Design Standards Collection (see smartsheet-standards-intake.md)
- [ ] Check New Design Log for recent survey/rescale comments on this client
- [ ] If user provided fab size, treat photo as layout only — do not override spec
- [ ] If permitting: note architectural scale on photo elevations when city requires it
```
