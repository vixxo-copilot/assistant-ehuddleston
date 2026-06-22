# Raceway cheat sheet

One-page reference. **Full registered list:**
[`color-registry.md`](./color-registry.md).

## Raceway paint rule

**Raceway = paint the surface it mounts on** (sign pocket, fascia band, beam, or
canopy — not the wall below unless spec says so).

| Mount context | Paint to match |
|---------------|----------------|
| Flat sign-band fascia | Survey/art SW/PMS/BM on fascia line |
| Recessed sign pocket | Pocket panel color (may differ from outer frame) |
| Architectural beam | **Beam color** — not stucco below |
| "Awaiting wall color match" | Art revision code when present |
| Descriptive only ("Red brick") | Photo sample + SW brick family; brush-out |
| Custom SW label on art | Reorder by label name + formula (not catalog SW #) |

## Authority (short)

1. Survey paint note → 2. Art spec block (page 2) → 3. Brand standards → 4. Photo

## Letter faces (do not paint)

| Client | SALLY | BEAUTY |
|--------|-------|--------|
| Sally SB30RB | #2793 red Plex | #2447 + perf vinyl |
| Sally white set | #7328 white Plex | — |
| CosmoProf | 2648 blue Plex | logo = 3M #3630-136 vinyl |

Returns/trim: factory **black** — not raceway paint.

## Common traps

- **SW 7100** = Arcade White (not Fractured Ice **SW 7647**)
- **PMS 482 C** = warm beige — not red
- Survey file named "Survey" may be an **invoice/PO** — open before trusting
- **Art before survey** for raceway codes (survey POs often have no paint)

## Scripts (repo root)

```bash
# Registry — no PDF
python3 .agents/skills/raceway-color/scripts/list_colors.py --code 7100
python3 .agents/skills/raceway-color/scripts/list_colors.py --tier 1

# Fast path — raceway lookup (shows color swatch + hex)
python3 .agents/skills/raceway-color/scripts/lookup.py \
  --art path/to/Art.pdf [--survey Survey.pdf] [--image site.jpg]

# Extract only (multiple PDFs merge)
python3 .agents/skills/raceway-color/scripts/extract_survey_paint.py Art.pdf Survey.pdf
```
