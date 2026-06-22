# Raceway color registry

**Raceway paint only** — field paint for the extruded alum raceway (match mount
surface). Registry: [`color-registry.json`](./color-registry.json). CLI:

```bash
python3 .agents/skills/raceway-color/scripts/list_colors.py --code 7100
python3 .agents/skills/raceway-color/scripts/list_colors.py --tier 1
```

**Rule:** paint raceway to match fascia band, pocket, beam, or canopy — same
code + sheen. Product: **SW Pro Industrial DTM Acrylic**.

---

## Tier 1 — check first

| Color | Code | Name | Use |
|-------|------|------|-----|
| <span style="display:inline-block;width:18px;height:18px;background:#F3EEE7;border:1px solid #666;border-radius:3px"></span> **#F3EEE7** | SW 7100 | Arcade White | Default US white raceway |
| <span style="display:inline-block;width:18px;height:18px;background:#D7C5B3;border:1px solid #666;border-radius:3px"></span> **#D7C5B3** | PMS 482 C | Warm light beige | Survey raceway — **not red** |
| <span style="display:inline-block;width:18px;height:18px;background:#D7C5B3;border:1px solid #666;border-radius:3px"></span> **#D7C5B3** | SW 6099 | Sand Dollar | SW substitute for PMS 482 C |

---

## Tier 2 — frequent surveys

| Color | Code | Name | Use |
|-------|------|------|-----|
| <span style="display:inline-block;width:18px;height:18px;background:#E8E4DA;border:1px solid #666;border-radius:3px"></span> **#E8E4DA** | SW 6091 | Reliable White | Cream/off-white buildings |
| <span style="display:inline-block;width:18px;height:18px;background:#EDEAE0;border:1px solid #666;border-radius:3px"></span> **#EDEAE0** | SW 7008 | Alabaster | Warm white stucco |
| <span style="display:inline-block;width:18px;height:18px;background:#E4DED2;border:1px solid #666;border-radius:3px"></span> **#E4DED2** | SW 7011 | Natural Choice | Off-white stucco |
| <span style="display:inline-block;width:18px;height:18px;background:#DFD9CD;border:1px solid #666;border-radius:3px"></span> **#DFD9CD** | SW 7570 | Egret White | Off-white fascia |
| <span style="display:inline-block;width:18px;height:18px;background:#DDC6AB;border:1px solid #666;border-radius:3px"></span> **#DDC6AB** | SW 7723 | Colony Buff | Substitute for PMS 4685 C |
| <span style="display:inline-block;width:18px;height:18px;background:#E0C6AD;border:1px solid #666;border-radius:3px"></span> **#E0C6AD** | PMS 4685 C | Warm tan buff | Canadian / stucco |
| <span style="display:inline-block;width:18px;height:18px;background:#443D46;border:1px solid #666;border-radius:3px"></span> **#443D46** | BM Iron Mountain 2134-30 | Dark charcoal | **Beam mount** raceway |
| — | EAST END CANOPY MATCH | Custom SW mix | Reorder by label + formula |

---

## Tier 3 — specialty

| Color | Code | Name | Use |
|-------|------|------|-----|
| <span style="display:inline-block;width:18px;height:18px;background:#D6D3CA;border:1px solid #666;border-radius:3px"></span> **#D6D3CA** | SW 7647 | Crushed Ice | Banded fascia center |
| <span style="display:inline-block;width:18px;height:18px;background:#D6BDA3;border:1px solid #666;border-radius:3px"></span> **#D6BDA3** | SW 2823 | Classic Sand | Tan bands + raceway |
| <span style="display:inline-block;width:18px;height:18px;background:#8EA0AA;border:1px solid #666;border-radius:3px"></span> **#8EA0AA** | SW 7669 | Mooring Buoy | Blue-gray wall/fascia |
| <span style="display:inline-block;width:18px;height:18px;background:#7A4841;border:1px solid #666;border-radius:3px"></span> **#7A4841** | SW 2802 | Rookwood Red | Red brick pocket |
| <span style="display:inline-block;width:18px;height:18px;background:#824C42;border:1px solid #666;border-radius:3px"></span> **#824C42** | SW 2804 | Rookwood Brick | Red brick pocket (alt) |

---

## Pantone → SW (brush-out on site)

| Pantone | Color | SW starting point |
|---------|-------|-------------------|
| 482 C | <span style="display:inline-block;width:18px;height:18px;background:#D7C5B3;border:1px solid #666;border-radius:3px"></span> **#D7C5B3** | SW 6099 Sand Dollar |
| 4685 C | <span style="display:inline-block;width:18px;height:18px;background:#E0C6AD;border:1px solid #666;border-radius:3px"></span> **#E0C6AD** | SW 7723 Colony Buff |

---

## Traps

| Wrong | Correct |
|-------|---------|
| PMS 482 C is red | Warm beige `#D7C5B3` |
| SW 7100 = Fractured Ice | **SW 7647** Crushed Ice |
| Default raceway = SW 7100 | **Site-specific** — verify art/survey |
| Beam mount → match stucco | Paint **beam** (often BM Iron Mountain) |
