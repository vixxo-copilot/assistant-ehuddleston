# Reference dimensions for photo scaling

Use when the user does not supply a known measurement. **Always prefer a
user-confirmed dimension** over these defaults.

## How to pick a reference

1. Choose an object on the **same image plane** as the sign (same wall face).
2. Measure the **same axis** for reference and target (height-to-height or
   width-to-width). Do not mix axes.
3. Measure **outermost usable edges** consistently (e.g., door head to sill,
   not just glass).
4. Prefer references that span a large share of the frame — small references
   amplify error.

## Common references (verify on site when possible)

| Object | Typical size | Notes |
|--------|--------------|-------|
| Commercial entry door (single) | 3'-0" x 6'-8" or 3'-0" x 7'-0" | Measure jamb to jamb, head to sill |
| Commercial double door | 6'-0" x 6'-8" or 6'-0" x 7'-0" | Two 3'-0" leaves; pixel aspect **0.80–0.95** (gate C2). Do not use full storefront glass. |
| Storefront door (user override) | **Ask user** | Example: 7'-0" height |
| Standard parking space width | 9'-0" | Striping centerline to centerline |
| Concrete parking stop | ~6'-0" long | Parallel to stall |
| ADA handicap sign face | 12" x 18" | If visible and current code |
| Standard brick (face) | 2-1/4" x 7-5/8" | Course height ~2-1/4" |
| 4x8 plywood sheet | 4'-0" x 8'-0" | Temporary hoarding only |

## Pixel measurement tips

- Read the image file to get `pixelWidth` / `pixelHeight` first.
- Estimate pixel extents from the photo; state which edges you used.
- If perspective skew is obvious (camera angled up/down), call it out and widen
  the tolerance band to **12–15%**.
- When possible, take a second reference (e.g., door height **and** door
  width) and average the scale factors.

## Client standard matching

After scaling, if the user names a client/brand, **pull the dimension workbook
first** via Smartsheet MCP — see [`smartsheet-standards-intake.md`](./smartsheet-standards-intake.md)
(sheet `4309901242224516` Design Standards Collection). Fallback: SharePoint
`00000000standards`. Match **letter height** and **overall sign width** to the
nearest standard tier in the brand xlsx or CDR/PDF.

Example CosmoProf channel-letter tiers (Smartsheet workbook — **fab / permitting
overall width**, not letter-face ink span):

| Letter height | Typical overall width |
|---------------|----------------------|
| 12" | ~9'-1" |
| 18" | ~13'-7" |
| 24" | ~17'-11" |
| 30" | ~22'-8" |
| 36" | ~26'-11" |

Photo scale from letter faces often reads **20–40% narrower** than the overall
width column above (raceway/cabinet extends past outer letters). Match tier from
fab spec or workbook; use [`tan-fascia-detection.md`](./tan-fascia-detection.md)
and gate J when photo and fab disagree.

## Logo + letter signs

Pull **logo height** and **letter height** from the client standards sheet when
available. Photo scale is unreliable for **3D logos** (globes, medallions).

Example AT&T storefront (from `ATT DImensions Table with layout.xlsx` + design log):

| Element | Standard lookup | Photo trap |
|---------|-----------------|------------|
| Globe | Fab height per survey / EagleView / user spec (often **4'-0"**) | Color stripe ~1'-2" — not full sphere |
| "AT&T" letters | Cap tier column **A** in xlsx (12"–36"); **~60% of globe height** | Separate cap-line measurement |
| Overall width | **AT&T word perimeter** column at chosen cap tier | Do not use stripe width |

| Cap tier (A) | Globe perimeter | AT&T word perimeter |
|--------------|-----------------|---------------------|
| 24" | 39.0" | 35.1" |
| 30" | 48.8" | 43.8" |
| 36" | 58.5" | 52.6" |

If only letter height is known from the photo, **do not infer logo height** —
ask for logo spec before dimension lines on the globe.
