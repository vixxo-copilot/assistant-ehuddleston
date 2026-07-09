---
name: vixxo-brand-guidelines
description: >
  Apply Vixxo Facility Solutions brand guidelines to any document, presentation, dashboard, or visual output.
  Use this skill whenever anyone at Vixxo asks to create or style a Word doc, PowerPoint,
  HTML dashboard, React component, report, email template, or any other visual deliverable — even if they
  don't explicitly say "brand guidelines." Triggers include: make it on-brand, apply Vixxo branding,
  use our colors/fonts/logo, creating any Vixxo report, tracker, dashboard, or document.
  Always consult this skill before writing styling code or document formatting for Vixxo deliverables.
---

# Vixxo Brand Guidelines

Reference this skill before styling ANY Vixxo deliverable: documents, dashboards, presentations, emails, HTML/React artifacts.

## Logo
- **File:** `assets/vixxo_logo.png` (PNG, 1058x379 px, RGBA)
- **Full name:** VIXXO | Facility Solutions
- **Placement:** Top-right header in Word docs; top-left or top-right in presentations/dashboards
- **Word header size:** ~0.625" wide x 0.224" tall (cx=900000 EMU, cy=322349 EMU)
- **Never distort** the logo; always preserve aspect ratio

---

## Color Palette

### Primary (use most)
| Name | Hex | Use |
|---|---|---|
| Vixxo Green | `#8E992E` | Primary brand, positive indicators |
| Vixxo Gray | `#3E4543` | Dark backgrounds, headers, body text on light |

### Secondary (use freely)
| Name | Hex | Use |
|---|---|---|
| Vixxo Teal | `#2C7B80` | Section headings, chart bars, callouts, links |
| Vixxo Yellow | `#EDA200` | Warnings, flags, at-risk items, highlights |

### Tertiary (use as accents)
| Name | Hex | Use |
|---|---|---|
| Vixxo Blue | `#395389` | Additional data series, tertiary accents |
| Vixxo Copper | `#956125` | Warm accent, decorative highlights |

### Supporting (from official template)
| Name | Hex | Use |
|---|---|---|
| Dark Teal | `#215B5F` | H1/Heading 1 text color |
| Olive Green | `#788536` | HEADLINE style (doc titles) |
| Medium Gray | `#87938F` | Subheadlines, secondary text |

---

## AR-Specific Color Conventions
| Status | Color | Hex |
|---|---|---|
| Current / On track | Vixxo Green | `#8E992E` |
| At risk / Aging | Vixxo Yellow | `#EDA200` |
| Overdue / Critical | Red | `#C0392B` |
| Resolved / Posted | Vixxo Teal | `#2C7B80` |
| Pending / In progress | Vixxo Blue | `#395389` |
| Unapplied / Unknown | Vixxo Copper | `#956125` |

---

## Typography
| Role | Font | Notes |
|---|---|---|
| Display / Headings | Calibri Light | Official VIXXO theme majorFont |
| Body text | Calibri | Official VIXXO theme minorFont |
| Fallback (web/HTML) | `'Calibri Light', Calibri, sans-serif` | Use in CSS |

---

## Word Document Styles (from official template)
Use these style IDs in docx-js when building `.docx` files:

| Style ID | Size | Color | Purpose |
|---|---|---|---|
| `HEADLINE` | 26pt | `#788536` | Main document title |
| `SUBHEADLINE` | - | `#87938F` | Subtitle |
| `Heading1` | - | `#215B5F` | Section headings |
| `ACCENT` | - | `#A16125` | Intro/accent body text |
| `TEXT1` | 12pt | Black | Primary body text |
| `TEXT-BULLET` | - | - | Bulleted lists |
| `CALLOUTS` | - | `#2C7B80` | Callout/highlight boxes |
| `QUOTES` | - | - | Pull quotes |

**Page setup:** US Letter (8.5"x11"), 1" margins all sides.
**Header:** Vixxo logo, right-aligned, no visible border.

---

## CSS Variables (HTML/React)
```css
:root {
  --vixxo-green:     #8E992E;
  --vixxo-gray:      #3E4543;
  --vixxo-teal:      #2C7B80;
  --vixxo-yellow:    #EDA200;
  --vixxo-blue:      #395389;
  --vixxo-copper:    #956125;
  --vixxo-dark-teal: #215B5F;
  --vixxo-olive:     #788536;
  --vixxo-mid-gray:  #87938F;
  --vixxo-white:     #FFFFFF;
  --font-display:    'Calibri Light', Calibri, sans-serif;
  --font-body:       'Calibri', sans-serif;
}
```

## docx-js Color Constants
```javascript
const VIXXO = {
  green:    "8E992E",   // Primary brand
  gray:     "3E4543",   // Dark backgrounds
  teal:     "2C7B80",   // Headings, callouts
  yellow:   "EDA200",   // Warnings/flags
  blue:     "395389",   // Accents
  copper:   "956125",   // Warm accent
  darkTeal: "215B5F",   // H1 color
  olive:    "788536",   // Headline style
  midGray:  "87938F",   // Subheadlines
  white:    "FFFFFF",
  black:    "000000",
};
```

---

## Checklist — Before Delivering Any Vixxo Output
- [ ] Logo included in header (Word) or top of layout (HTML/pptx)
- [ ] Primary colors used for headers and key data (Teal, Green, Gray)
- [ ] Yellow/Red used only for flags, warnings, or overdue items
- [ ] Font is Calibri Light (headings) + Calibri (body), or web fallback
- [ ] AR status colors match the convention table above
- [ ] No off-brand colors (no purple gradients, no generic blue defaults)
