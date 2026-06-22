# Tan fascia / low-contrast channel letters

Lessons from CosmoProf (and similar green/blue CL on beige EIFS). Use when
standard blue-channel masks fail or gates fire on the **wrong horizontal band**.

## The cornice trap (stop first)

On many storefronts the **gray cornice / trim band sits above the tan fascia**
where letters are mounted. A loose blue mask often locks onto the **cornice**
(y ≈ 70–95 px in typical phone screenshots), not the letters (y ≈ 130–210).

| Band | Typical y (screenshot) | RGB cue | Mask behavior |
|------|------------------------|---------|---------------|
| Cornice | 55–95 | High `bb` (~230), uniform | Full-width false “ink” |
| Tan fascia + letters | 125–215 | Low contrast `bb` ≈ wall + 3–8 | Real letters weak |
| Stone / transom | 105–140 | Warm gray ~150 RGB | Not letters |

**Stop rule:** If detected ink sits **above** the glass line and never overlaps
the tan panel between cornice and storefront glass, you are on the cornice — reset
`y0` lower. Save `tmp/<slug>-bands.png` with horizontal lines at y = 90, 130,
180, 250 to confirm before scaling.

## Detection pipeline (Mode B)

Run in order; do not skip band localization.

### 1. Localize fascia letter band

```text
y_search: storefront glass top upward ~120 px (e.g. y 125–220)
x_search: center third of frame, expand with leaf anchor (below)
```

### 2. Green leaf anchor (CosmoProf / dual-leaf logos)

Reliable on mixed-case Cosmo layouts:

```text
g > r + 18, g > b + 12, g in [115, 200], r < 120
restrict y to fascia band only (exclude cornice y < 130)
```

Use leaf bbox center to bound letter search: `x0 = leaf_l - 200`, `x1 = leaf_r + 200`.

### 3. CLAHE + cap-row ink (not full-height mask)

On crop `arr[y0:y1, x0:x1]`:

1. Convert to LAB; CLAHE on **L** only (`clipLimit` 4–5, tile 4×4 or 8×8).
2. Letter ink on **cap rows only** — anchor to green-leaf top when present
   (`row_lo ≈ leaf_t − y0 − 2`; absolute y often 154–168 on phone screenshots):
   - `(bb > rr + 3) & (bb > gg + 1)` on enhanced RGB
3. **Kill horizontal panel seams:** any row with ink on **> 35%** of width → zero row.
4. Width span = leftmost/rightmost `x` with ink on **≥ 3** cap rows (not one row).

Do **not** use full-band blue mask — tan wall tint reads as ink across full width.

### 4. Sobel outer faces (when ink span is still full-width)

On CLAHE gray, use the **same leaf-anchored cap rows** as step 3 (absolute y
~154–168 on the CosmoProf reference photo — not a fixed crop offset):

1. `sobelx = |Sobel(gray, x)|`; column-sum profile.
2. Left outer face = strongest edge cluster in `x` range **leaf_l − 150** to **leaf_l − 20**.
3. Right outer face = strongest cluster in **leaf_r + 20** to **leaf_r + 150**.
4. QA: save `tmp/<slug>-edge-candidates.png` with vertical lines on candidate edges.

Letter-face ticks often land near **C** left and **f** right — **not** at building
seams or fascia panel joints.

### 5. Cap height (C/P columns)

Per-column ink in CLAHE crop, full letter body band `y0+10` to `y0+70`:

- Keep columns with height ≥ **70%** of max column height (uppercase tier).
- `cap_top` = median top of tallest columns; `cap_bot` = median bottom.
- **Do not** include lowercase descenders below baseline for cap-height ticks.

Validate with gate **A** (cap ÷ door_h px ≈ 0.25–0.45). If cap reads **< 0.20**,
ticks are likely too tight — re-check CLAHE zoom before publishing.

## Letter-face width vs fab overall width

Photo edge detection returns **outermost letter faces at the cap line**. Fab
drawings and permitting often use **overall sign / raceway / cabinet width**,
which can be **25–40% wider** than letter ink alone.

Example (CosmoProf site photo, 3'×7' door ref):

| Source | Width | Cap height |
|--------|-------|------------|
| Letter-face pixels + homography | ~12'–13' | ~15" |
| User / fab spec | **17'-11"** | **24"** |

When photo letter-face width is **> 20% below** user fab width:

1. Report **both** photo letter span and fab overall width in the packet.
2. Use **fab spec for overlay labels**; keep letter-face ticks unless user asks
   for raceway/corner-to-corner ticks.
3. Do **not** stretch ticks to match fab numbers without a defined edge (raceway,
   panel seam, or corner callout).

## Run the helper script

```bash
python3 .agents/skills/vixxo-sign-scale-from-photo/scripts/detect_channel_letters.py \
  --image <photo> \
  --json \
  --debug tmp/<slug>-letter-edges-debug.png
```

Then pass returned corners to `measure_facade.py` for scaled inches. Use
`sign_quad` from JSON for `--sign` (`x,y` TL TR BR BL). Output
`sign_overall_width_in` is **letter-face width** only — compare to fab width
via gate J.

## Overlay notes (user prefs)

- **Mirrored callouts:** width line **above** sign, height line **left** of sign
  (ticks still point toward letters). Mirror from default below/right when asked.
- **Label backing:** omit white rectangles when user requests plain red text.
- **Font size:** default 16–20 px Arial Bold for legibility on storefront photos.
