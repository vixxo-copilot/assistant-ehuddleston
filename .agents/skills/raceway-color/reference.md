# Paint and color reference — sign fabrication

> **Fast lookup:** [`color-registry.md`](./color-registry.md) — registered Vixxo
> colors by tier. This file adds fabrication context and workflows.

## Three color systems (do not conflate)

| System | Used for | Example |
|--------|----------|---------|
| **Acrylic / Plex stock #** | Channel letter **faces** (sheet goods) | `#2793` red, `#2447` white, `#7328` white |
| **Pantone (PMS)** | Brand print, some fascia/raceway callouts | `PMS 482 C` |
| **Sherwin-Williams (SW ####)** | **Field paint** on fascia, raceway, building | `SW 7100 Arcade White` |

Pantone ≠ Sherwin-Williams without a documented crossover or site brush-out.
Target **ΔE ≤ 2** (CIE2000) when matching raceway to fascia in retail work.

---

## What gets paint vs what does not

| Component | Material | Color source |
|-----------|----------|--------------|
| **Letter faces** | 3/16" translucent acrylic | Stock color # — not wall paint |
| **Returns** | .050 aluminum | Pre-painted (often black on Sally SB30) |
| **Trim cap** | Vinyl/aluminum cap | Black (Sally SB30) |
| **Raceway** | 5"×7" extruded aluminum | **Painted to match building sign-band fascia** |
| **Fascia / wall** | EIFS, panel, brick, etc. | SW / PMS / survey note — **site-specific** |

Sally standards CDR language (2026 US):

> **PAINTED TO MATCH BUILDING SIGN BAND FASCIA**

---

## Acrylic face stock numbers

| Code | Type | Light transmission | Typical use |
|------|------|-------------------|-------------|
| **#2793** | Translucent red | ~25% | SALLY face (SB30 red sets) |
| **#2447** | Milky translucent white | ~47–55% | BEAUTY face base (split-color jobs) |
| **#7328** | Translucent white | ~8% | All-white Sally sets (SB30WR) |
| **#2025** | Opaque black | 0% | Solid black faces (other brands) |

Face thickness: 3/16" standard on Sally SB30 per 2026 standards CDR.

---

## Sally Beauty — SB30RB (2026 standards CDR)

Source: `SALLY BEAUTY STANDARDS - 5-2026 US W Part#s.cdr` (Smartsheet Design
Standards Collection).

| Element | Fab spec |
|---------|----------|
| **Part#** | SB30RB — 30" linear, 2'-6" × 13'-4", 33.3 SF |
| **SALLY** | `#2793` red 3/16" Plex |
| **BEAUTY** | `#2447` white acrylic + **70/30 black perforated vinyl** |
| **Returns** | 3" deep .050 alum, pre-painted **black** |
| **Trim cap** | **Black** |
| **LED** | Red `PL-FS2-RR1-P` (SALLY); White `PL-OP2-SF3-P-TW` (BEAUTY) |
| **Raceway** | 5"×7" extruded alum → **match fascia** |

**SB30WR** (white rebrand): `#7328` white acrylic faces.

---

## Fascia / raceway paints (Sally jobs)

| Code | Actual color | When used |
|------|--------------|-----------|
| **SW 7100** | **Arcade White** (`#F3EEE7`) | Default US white fascia/raceway |
| **PMS 482 C** | Warm light beige (~`#D7C5B3`) | Survey-specified raceway (e.g. Cary) |
| **SW 6099 Sand Dollar** | Closest common SW to PMS 482 C | Field substitute |
| **SW 7647 Crushed Ice** | Warm off-white/cream (`#D6D3CA`) | Banded fascia center band |
| **SW 2823 Classic Sand** | Warm tan (`#D6BDA3`) | Banded fascia tan bands + raceway |
| **PMS 4685 C** | Warm tan buff (~`#E0C6AD`) | Canadian / stucco fascia (Halifax survey) |
| **SW 7723 Colony Buff** | Closest common SW to PMS 4685 C | Field substitute — brush-out |
| **PMS 474 C** | Dusty rose-tan | Wall color on some SP elevations |
| **PMS 7403 U** | Golden ochre (uncoated) | Stucco wall match via chip photo |

Survey label examples (see [`survey-reading-exemplars.md`](./survey-reading-exemplars.md)):

- `Sign Area Fascia Color Pantone 4685C`
- `WALL COLOR | PANTONE 474C`
- `RW Color - SW 7100 Arcade White`
- `Wall color match` → `SW 7669`

---

## Raceway paint — SP field practice

1. Extruded aluminum; weld, degrease, etch/prime.
2. Common: **SW Pro Industrial DTM Acrylic**.
3. Raceway = fascia (**same code, same sheen**).
4. Brush-out on site under installed lighting.

---

## Photo → paint workflow

1. Sample pixels away from letters, shadow, glazing.
2. Map to nearest SW fan deck chip.
3. Multi-band fascias: sample each band separately.
4. State photo match is estimate until survey confirms.

### Exemplar — Canadian banded fascia

| Surface | SW callout | Sampled hex |
|---------|-----------|-------------|
| Center band (cream) | SW 7647 Crushed Ice | ~`#D8D1C9` |
| Upper/lower tan bands | SW 2823 Classic Sand | ~`#DBB6A3` |
| Raceway (lit face) | SW 2823 Classic Sand | ~`#DBC7AF` |

---

## Pantone → SW crossovers (approximate)

| Pantone | Close SW matches |
|---------|------------------|
| **482 C** | SW 6099 Sand Dollar, SW 9094 Playa Arenosa, SW 2859 Beige |
| **185 C** | SW 6866 Real Red |

Always brush-out on site — fan deck beats screen conversion.
