---
name: raceway-color
description: >-
  Raceway and field paint colors from survey PDFs and storefront photos — SW,
  BM, Pantone, custom mixes, with hex color swatches. Use when the user asks
  what to paint the raceway, fascia/sign-pocket color, what paint to order,
  PMS/SW/BM codes, or color match from a photo plus survey.
---

# Raceway color

Identify **raceway paint** (and the fascia/pocket/beam surface it matches).
Always show **color swatch + hex** in answers.

**Registry:** [`color-registry.md`](./color-registry.md) (includes visual swatches).
CLI: `list_colors.py --code 7100`. Quick ref: [`raceway-cheat-sheet.md`](./raceway-cheat-sheet.md).

## Authority order

1. Survey paint note → 2. Art page 2 → 3. Brand standards → 4. Photo sample

When **survey + photo** both exist, **reconcile** — do not pick one silently.

---

## Choose a path

| Ask | Path | Output |
|-----|------|--------|
| "What is SW 7100?" | `list_colors.py --code 7100` | Swatch + hex + name |
| "What paint the raceway?" | `lookup.py --art Art.pdf` | Raceway table with swatches |
| Survey + photo | `reconcile_colors.py --image site.jpg --survey Art.pdf` | Raceway + photo sample hex |
| List common raceway colors | `list_colors.py --tier 1` | Tier-1 with swatches |

---

## Workflow

```
Task progress:
- [ ] 1. Load art + survey — art page 2 before survey PO
- [ ] 2. Run lookup.py (default markdown includes color swatches)
- [ ] 3. Reconcile photo if site image available
- [ ] 4. Emit raceway answer with swatch + hex for every code
```

### Scripts (repo root)

```bash
# Raceway lookup — markdown with color swatches (default)
python3 .agents/skills/raceway-color/scripts/lookup.py VX1105135 \
  --art path/to/Art.pdf [--survey Survey.pdf] [--image site.jpg]

# Registry lookup with swatch
python3 .agents/skills/raceway-color/scripts/list_colors.py --code 7100

# JSON instead of markdown
python3 .agents/skills/raceway-color/scripts/lookup.py VX1105135 --art Art.pdf --json
```

**Always include in answers:** HTML color swatch + **#HEX** for each paint code
(from registry or photo sample). Example output row:

| Color | Code | Name | System | Confidence |
|-------|------|------|--------|------------|
| ■ **#F3EEE7** | SW 7100 | Arcade White | SW | high |

---

## Output format

```markdown
## Raceway color
| Color | Code | Name | System | Confidence |

## Photo sample (raceway band)
- Sampled: ■ **#EDEAE0** nearest SW 7008 Alabaster

## Order note
- SW Pro Industrial DTM Acrylic; same code + sheen as matched surface.
```

---

## Traps

- **PMS 482 C** = warm beige `#D7C5B3` — not red.
- **SW 7100** = Arcade White `#F3EEE7` — not Fractured Ice (**SW 7647**).
- **Raceway** = match mount surface (fascia, pocket, or beam).
- **BM Iron Mountain** `#443D46` — beam mounts, not stucco below.

---

## Related skills

- [`vixxo-sign-scale-from-photo`](../vixxo-sign-scale-from-photo/SKILL.md) — survey discovery; dimensions separate.

## Dependencies

- **Microsoft 365 MCP** — Survey PDF (optional).
- **Smartsheet MCP** — standards CDR (optional).
- **Python 3** — Pillow, numpy, pypdf; PyMuPDF optional.
