# Smartsheet standards intake

Pull **before** photo scaling when the user names a client/brand. Photo scale
estimates layout; **Smartsheet standards + survey** set fabrication size.

Use the **Smartsheet MCP** (read-only unless the user asks to update sheets).

## Sheets

| Sheet | ID | Use |
|-------|-----|-----|
| **Design Standards Collection** | `4309901242224516` | Brand standards CDR/PDF + dimension workbooks |
| **New Design Log 1.B** | `4809130754658180` | Recent revision comments (photo overlay, rescale, survey) |

Sort design-log rows by **Latest Revision Date** descending when checking how
the art team handled the same brand recently.

## Design Standards — brand rows and latest attachments

| Client | Row focus | Latest standards (as of 2026-06) | Dimension workbook |
|--------|-----------|----------------------------------|--------------------|
| **AT&T** | Prime Communication | `Prime Communication Standards 4-6-2026.cdr` (2026-04-06) | `ATT DImensions Table with layout.xlsx` |
| **CosmoProf** | Green/Blue CL | `VX Cosmo Starting Template 5-26.cdr` (2026-05-28); `CosmoProf Standards 11.2025.cdr` | In CDR/PDF — no separate xlsx on standards row |
| **Smart Stop** | SS layouts | `SmartStop Standards 12.2025.cdr` / `.pdf` (2025-12-17) | `SMART STOP alt layout COLLECTION Dimensions Table with layout.xlsx` |
| **Secure Space** | Outlined CL | `Secure Space Sign Standards 5.2021 1.a.pdf` | `Secure Space DImensions Tables 3.xlsx` |

**Download path:** `list_row_attachments` on the brand row → `get_attachment` →
parse `.xlsx` locally or cite tier from workbook. CDR/PDF are authoritative for
copy deck; xlsx is authoritative for **letter-height tiers and overall widths**.

## AT&T — dimension workbook (`ATT DImensions Table with layout.xlsx`)

Sheet **CHANNEL LETTERS DIMENSIONS**. Column **A** = letter cap-height tier (in).

| Cap tier (A) | Globe perimeter | AT&T word perimeter |
|--------------|-----------------|---------------------|
| 12" | 19.5" | 17.5" |
| 18" | 29.3" | 26.3" |
| 24" | 39.0" | 35.1" |
| 30" | 48.8" | 43.8" |
| 36" | 58.5" | 52.6" |

**Active brand rule** (New Design Log revs, 2025–2026): **letter cap height ≈ 60%
of globe height** (fab). Example: **4'-0"** globe → **~29"** cap (30" tier row).

- Globe is a **separate** fab element — do not read globe height from letter
  color masks or stripe bands.
- When no survey: revs cite **EagleView** for globe size; SP may give letter
  heights (e.g. **37"** cap height on **t**).
- **Survey overrides photo** — common latest comment: “revise measurements on
  artwork per survey attached.”

## CosmoProf — standards + permitting patterns

No dimension xlsx on the standards row; use **CDR/PDF** tiers and cap-line
discipline ([`reference-dimensions.md`](./reference-dimensions.md)).

Recent revision rules (New Design Log):

- **Wall sign width ≤ 80% of storefront frontage** when city limits one frontage
  callout (e.g. Rochester Hills R4, 2026-06-09).
- **Photo elevations to scale** for permitting — e.g. architectural scale
  **3/8" = 1'-0"** on pylon photo pages (Leesburg R1, 2025-12-12).
- **Rescale front/rear sign** when survey measurements are attached
  (Shallotte: “Add survey measurements and rescale”).
- Show **building height** and **unit width** on elevation when split frontages
  would confuse sign placement (Fort Myers R2).

## Smart Stop — dimension workbook

**SMART STOP alt layout COLLECTION Dimensions Table with layout.xlsx**

- **Sheet1** — wall sign decimals + **CHANNEL LETTER STACKED SIGN — ALT LAYOUT**
- **Sheet2** — alternate stacked layout widths

At **24"** cap (alt layout Sheet1): overall width **~144"**, stacked height **~57"**.

Revisions often reference **brand book codes** (e.g. `SS-CL-H36`), **aerial +
screenshots** for placement, and **EagleView** canopy length (e.g. **20'-0"**
canopy for letter scale on Louetta Spring).

## Secure Space — dimension workbook

**Secure Space DImensions Tables 3.xlsx** — multiple tabs (Outlined CL, White CL,
Self Storage linear/stacked, Climate Controlled, Lock logo, tower types).

Tables use feet-inches notation (`2'-0"`, `12'-10.32"`) in decimal-entry columns —
same as default overlay labels. Append **`EVO` to labels only when the user
requests it**; Smartsheet workbook format does not imply evo on deliverables.

Fit-check example from revisions (N Hollywood R7): wall **6'-4"** wide vs letter
run **7'-7/8"** — flag when scaled width exceeds lease-wall limit.

## Photo-overlay SOP (from New Design Log discussions)

Art-team instructions recur on high-rev rows. Apply when producing overlays:

1. **Use the attached site photo** as the overlay base (named page in PDF pack).
2. **Show building size** — height, frontage, or unit width on the drawing.
3. **Place letters/signs to scale** on the photo (homography from confirmed reference).
4. **Adjust scaling slightly** when needed; **call out horizontal measure from
   building corner to a letter** (Peter Cardinal, Sally San Tan Valley).
5. **Update cabinet/sign dimensions per survey** when survey is attached.
6. **Split elements** around obstructions (downspout, etc.) when rev specifies.
7. **Reduce letter size** if full deck does not fit on fascia.

## Workflow hook

When client is known:

```
- [ ] list_row_attachments → Design Standards Collection brand row
- [ ] Pull dimension xlsx (or standards PDF) → nearest cap tier + overall width
- [ ] search New Design Log for client + "photo overlay" / "rescale" / "survey"
- [ ] Apply brand rules (AT&T 60%, CosmoProf 80% frontage, etc.)
- [ ] Prefer survey/fab spec over photo estimate
```

If Smartsheet is unavailable, state that in the packet and use
[`reference-dimensions.md`](./reference-dimensions.md) defaults.
