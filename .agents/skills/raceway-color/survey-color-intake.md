# Survey color intake

What to pull from **Survey.pdf** (and survey photos) before reconciling with a
storefront image. Pair with `scripts/extract_survey_paint.py` or `lookup.py`.

**Worked examples:** [`survey-reading-exemplars.md`](./survey-reading-exemplars.md)

## Source order

1. **Art & EPS** page 2 spec block (raceway SW/BM/PMS, custom mixes, mount notes)
2. **Survey** sketch / field photos (may be PO-only — verify before extracting)
3. **Site photo** when spec says "match existing" or descriptive fascia only

## Survey folder

`{client}/{storeId}/{year} Signage/Survey/`

Download via Microsoft 365 MCP (`download-bytes`). Run:

```bash
python3 .agents/skills/raceway-color/scripts/extract_survey_paint.py Art.pdf Survey.pdf
```

Or fast raceway answer:

```bash
python3 .agents/skills/raceway-color/scripts/lookup.py VX######## \
  --art Art.pdf --survey Survey.pdf --raceway-only
```

If PDF text is empty (scanned sketch), **Read** rendered pages or OCR — then
pass `--text survey.txt` to extract/reconcile, or answer from visual read when
JSON shows `"needs_visual_read": true`.

---

## Fields to extract (priority)

| Priority | Field | Examples | Maps to |
|----------|-------|----------|---------|
| 1 | **Fascia / wall paint** | `SW 7100`, `SW 7011`, `PMS 482 C` | Field paint — fascia |
| 2 | **Raceway / trim paint** | `RW Color - SW 6091`, `match fascia`, `Raceway color is black` | Field paint — raceway |
| 3 | **Painted-to-match lines** | `PAINTED SW 7008`, `PAINTED ... BM Iron Mountain 2134-30` | Raceway + fascia |
| 4 | **Custom mix** | `EAST END CANOPY MATCH`, `CUSTOM SHER-COLOR MATCH` | Field paint — reorder by label |
| 5 | **Descriptive fascia** | `Red brick`, `tan stucco` | Photo + SW family; brush-out |
| 6 | **Sign part#** | `SB30RB`, `SB30WR` | Letter material set (standards CDR) |
| 7 | **Letter face notes** | `#2793`, `#2447`, perf vinyl | Letter materials |
| 8 | **Wall type** | Dryvit, stucco, EIFS, panel | Paint system / primer (not color) |

---

## SharePoint search strings

Use with Microsoft 365 drive search when folder path unknown:

- `{storeId} Signage Survey`
- `{storeId} Art EPS`
- `VX########` (design number on art title block)

Open first hit — confirm PDF is sketch/art, not invoice/PO.

---

## Survey vendor patterns

### McCorkle Survey Order

- Typed header + checklist ("color match" often checked)
- Pink dimensions on sketch — **paint code in header or notes block**
- Follow-on pages: annotated photos (use for photo reconcile, not text extract)

### Coast2Coast / graph-paper sketch

- **Paint code in header** (e.g. `SW 7100` stucco)
- Lease width + existing sign sizes on same page

### SCA / field photo package

- Paint may appear only on **annotated photo captions** — read images, not PDF text

---

## Reconcile with photo

When **both** survey and site photo exist:

```bash
python3 .agents/skills/raceway-color/scripts/reconcile_colors.py \
  --image site.jpg \
  --survey Art.pdf \
  --survey Survey.pdf \
  --markdown
```

**Rules:**

1. **Survey SW/PMS/BM wins** for fascia/raceway when explicitly stated.
2. **Photo** fills per-band colors when survey says "match fascia" or is silent.
3. **Flag conflict** when photo nearest-SW ≠ survey SW (Δ band or wrong family).
4. **Multi-band fascia** — survey may cite one code; photo may show two bands →
   list each band; raceway matches the band the raceway mounts on.
5. **Beam mount** — raceway matches beam color (often BM), not stucco below.

---

## SharePoint discovery

Same as [`vixxo-sign-scale-from-photo/survey-first-intake.md`](../vixxo-sign-scale-from-photo/survey-first-intake.md):

- New L Drive → `{Client}{storeId}` → `{year} Signage/Survey/`
- Cross-check **Art & EPS** page-2 spec block for letter acrylic #s when absent
  from survey text.
