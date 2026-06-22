#!/usr/bin/env python3
"""Generate printable Vixxo Sign & Lighting study guide PDF."""

from __future__ import annotations

from pathlib import Path

from fpdf import FPDF

OUT = Path(__file__).resolve().parent.parent / "vixxo-sign-lighting-study-guide.pdf"


class StudyGuidePDF(FPDF):
    def header(self) -> None:
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, "Vixxo Sign & Lighting Study Guide", align="L")
        self.ln(4)

    def footer(self) -> None:
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, f"Page {self.page_no()}", align="C")

    def title_page(self) -> None:
        self.add_page()
        self.ln(40)
        self.set_font("Helvetica", "B", 24)
        self.set_text_color(20, 20, 20)
        self.multi_cell(0, 12, "Vixxo Sign & Lighting\nStudy Guide", align="C")
        self.ln(8)
        self.set_font("Helvetica", "", 12)
        self.set_text_color(60, 60, 60)
        self.multi_cell(
            0,
            7,
            "Shop drawings, surveys, Smartsheet, dimensions,\ncolor, and permitting",
            align="C",
        )
        self.ln(20)
        self.set_font("Helvetica", "", 10)
        self.multi_cell(
            0,
            6,
            "Work reference for Sign & Lighting PM and art support.\n"
            "Authority: survey > shop drawing page 2 > Smartsheet standards > photo estimate.",
            align="C",
        )

    def _margin_x(self) -> None:
        self.set_x(self.l_margin)

    def h1(self, text: str) -> None:
        self._margin_x()
        self.ln(4)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(20, 20, 20)
        self.multi_cell(0, 8, text)
        self.ln(2)

    def h2(self, text: str) -> None:
        self._margin_x()
        self.ln(2)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(40, 40, 40)
        self.multi_cell(0, 6, text)
        self.ln(1)

    def body(self, text: str) -> None:
        self._margin_x()
        self.set_font("Helvetica", "", 9.5)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 5, text)
        self.ln(1)

    def bullet(self, text: str) -> None:
        self._margin_x()
        self.set_font("Helvetica", "", 9.5)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 5, f"  -  {text}")

    def table(self, headers: list[str], rows: list[list[str]], widths: list[float]) -> None:
        self._margin_x()
        self.set_font("Helvetica", "B", 8)
        self.set_fill_color(230, 230, 230)
        for i, h in enumerate(headers):
            self.cell(widths[i], 6, h, border=1, fill=True)
        self.ln()
        self.set_font("Helvetica", "", 7.5)
        for row in rows:
            if self.get_y() > 250:
                self.add_page()
                self._margin_x()
            line_counts = []
            for i, cell in enumerate(row):
                lines = self.multi_cell(widths[i], 4, cell, dry_run=True, output="LINES")
                line_counts.append(len(lines) if isinstance(lines, list) else int(lines))
            row_h = max(6, max(line_counts) * 4)
            x0 = self.get_x()
            y0 = self.get_y()
            if y0 + row_h > 270:
                self.add_page()
                self._margin_x()
                x0 = self.get_x()
                y0 = self.get_y()
            for i, cell in enumerate(row):
                self.set_xy(x0 + sum(widths[:i]), y0)
                self.multi_cell(widths[i], 4, cell, border=1)
            self.set_xy(x0, y0 + row_h)
        self.ln(2)

    def cheat_box(self, text: str) -> None:
        self._margin_x()
        self.set_fill_color(245, 245, 245)
        self.set_font("Courier", "", 8)
        self.multi_cell(0, 4.5, text, border=1, fill=True)
        self.ln(2)


def build() -> Path:
    pdf = StudyGuidePDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.title_page()

    pdf.add_page()
    pdf.h1("Part 1 - Big Picture")
    pdf.h2("What you are producing")
    pdf.body(
        "Every sign job ends in a shop drawing package: a multi-page PDF from CorelDraw "
        "showing what gets fabricated and installed. It is the contract between PM, art, "
        "city, landlord, and fabricator."
    )
    pdf.h2("Sources of truth (in order)")
    pdf.bullet("Field survey - tape-measured site conditions")
    pdf.bullet("Approved shop drawing - fab block on page 2 of latest VX number R# PDF")
    pdf.bullet("Brand standards - CDR/PDF/xlsx on Smartsheet Design Standards Collection")
    pdf.bullet("Photo scaling is research only - not fabrication proof")
    pdf.ln(1)
    pdf.h2("Pipeline")
    pdf.cheat_box(
        "Design Standards (CDR/xlsx)\n"
        "  -> R0 shop drawing (EagleView if no survey)\n"
        "  -> Survey PO -> Survey/ on L Drive\n"
        "  -> R1+ rescale / permit pages\n"
        "  -> PPR Approved as (manufacturing lock)\n"
        "  -> Fab -> Install -> Completion"
    )

    pdf.h1("Part 2 - Terminology")
    pdf.table(
        ["Term", "Meaning"],
        [
            ["VX number", "Auto ID VX1... base art (e.g. VX1109424)"],
            ["R# / Rev #", "Revision - R0 first release, R4 fifth"],
            ["VX# + R#", "Full design ID - VX1108945 R4"],
            ["Shop drawing / Art", "PDF in Art & EPS/ folder"],
            ["Fab block", "Page 2 - letter heights, OAW, materials"],
            ["Cap height", "Capital letters on cap line only"],
            ["Overall width (fab)", "Raceway/cabinet/permit width - often > letter faces"],
            ["Raceway", "Mount bar behind CLs - paint matches fascia/pocket"],
            ["Returns / trim", "Letter sides/edges - usually factory black"],
            ["Faces", "Front illuminated surface (Plex, vinyl, flex)"],
            ["PPR", "Pre-Production Review - approval before fab"],
            ["Design Log", "Smartsheet New Design Log 1.B - all jobs"],
            ["EagleView", "Aerial measure when no field survey yet"],
        ],
        [32, 153],
    )

    pdf.add_page()
    pdf.h1("Part 3 - Where Things Live")
    pdf.h2("SharePoint - New L Drive")
    pdf.cheat_box(
        "{Client} / {Client}{storeId} / {year} Signage /\n"
        "  Survey/          field survey PDF + photos\n"
        "  Art & EPS/       VX###### R# ... .pdf\n"
        "  Purchase Orders/\n"
        "  Completion Photos/\n"
        "\nLatest artwork = highest R# in current year folder."
    )
    pdf.h2("Smartsheet")
    pdf.table(
        ["Sheet", "ID", "Purpose"],
        [
            ["Design Standards Collection", "4309901242224516", "Brand CDR, PDF, dimension xlsx"],
            ["New Design Log 1.B", "4809130754658180", "4000+ jobs, rev comments, site fields"],
            ["Pre-Production Review", "8908088876001156", "Approved Design #, Sales Order #"],
        ],
        [52, 42, 88],
    )
    pdf.h2("Design Log columns to know")
    pdf.table(
        ["Column", "Use"],
        [
            ["Site Number", "Free text - Sally 3622 Cary NC"],
            ["VX# + R#", "Current design ID"],
            ["Latest Comment", "PM instruction to art - read first"],
            ["PPR Approved as", "Rev locked for production"],
            ["Existing Fascia L/H", "Pre-draw site intel"],
            ["Front CLs scope of work", "Standard install scope text"],
        ],
        [52, 133],
    )

    pdf.add_page()
    pdf.h1("Part 4 - Shop Drawing Package")
    pdf.table(
        ["Page", "Shows", "When"],
        [
            ["Cover", "Job ID, address, rev table", "Always"],
            ["Fab / spec (p.2)", "Tiers, OAW x OAH, materials", "Always - dimension authority"],
            ["Elevation", "Existing + proposed overlay", "After survey; permitting"],
            ["Site plan", "Lease space, north arrow, sign loc", "City permit"],
            ["Code check", "Sq ft vs allowed frontage", "Strict codes"],
            ["Night view", "Illumination rendering", "Many cities"],
            ["Details", "Disconnect, attachment", "City redlines"],
        ],
        [28, 82, 75],
    )

    pdf.h1("Part 5 - Dimension Authority")
    pdf.cheat_box(
        "Survey > Shop drawing page 2 > Smartsheet xlsx > Design Log fields > EagleView > Photo"
    )
    pdf.h2("Survey outcomes (Sally pattern)")
    pdf.table(
        ["Outcome", "When", "Example"],
        [
            ["Confirm template", "Band fits standard 30\" set", "Sally 10063 - page 2 unchanged"],
            ["Rescale template", "Fascia/lease too tight", "Sally 3622 - 30\" -> 24\" set"],
        ],
        [32, 52, 101],
    )
    pdf.h2("Extract from survey")
    pdf.bullet("Envelope: sign-band width, sign-area height, raceway length, lease width")
    pdf.bullet("Existing sign: OAL x OAH, straight-on photo")
    pdf.bullet("Anchors: door H x L, window grid, corner offsets")

    pdf.add_page()
    pdf.h1("Part 6 - Sign Types")
    pdf.h2("A. Single-tier channel letters (CosmoProf, Smart Stop)")
    pdf.bullet("Cap height on cap line - top of C/P to bottom of C/P")
    pdf.bullet("Do not use lowercase extenders or awning shadow")
    pdf.bullet("Fab overall width from workbook - not letter-face pixels")
    pdf.bullet("CosmoProf: wall sign <= 80% storefront frontage when city limits one callout")
    pdf.table(
        ["Cap", "~Fab overall width"],
        [["12\"", "~9'-1\""], ["24\"", "~17'-11\""], ["30\"", "~22'-8\""]],
        [38, 147],
    )
    pdf.body("Photo often reads 20-40% narrower than fab width (raceway extends past letters).")

    pdf.h2("B. Dual-color wordmark (Sally Beauty)")
    pdf.bullet("Red SALLY + black BEAUTY on white fascia; same baseline, different cap heights")
    pdf.bullet("Measure each color block separately")
    pdf.bullet("Permitting width (e.g. 13'-4\") != sum of word widths + gap")
    pdf.bullet("Once fab spec known, photo is tick placement only")

    pdf.h2("C. Logo + letters (AT&T globe)")
    pdf.bullet("Globe and letters are separate fab elements")
    pdf.bullet("Cap height ~ 60% of globe height (e.g. 4'-0\" globe -> ~29\" cap / 30\" tier)")
    pdf.bullet("Never read globe height from color stripe bands in photos")
    pdf.table(
        ["Cap tier", "Globe perim.", "AT&T word perim."],
        [["24\"", "39.0\"", "35.1\""], ["30\"", "48.8\"", "43.8\""]],
        [38, 48, 99],
    )

    pdf.add_page()
    pdf.h1("Part 7 - Photo Scaling (estimate only)")
    pdf.table(
        ["Reference", "Typical size"],
        [["Single door", "3'-0\" x 6'-8\" or 7'-0\""], ["Double door", "6'-0\" x 7'-0\""], ["Parking stall", "9'-0\" wide"]],
        [66, 119],
    )
    pdf.h2("Sanity gates")
    pdf.table(
        ["Gate", "Rule"],
        [
            ["A - Cap / door", "Cap height 25-45% of door height in pixels"],
            ["J - Fab vs photo", "Photo letter span != fab/permitting width"],
            ["Logo ratio", "Logo px / cap px >= 1.5 if logo dominates visually"],
            ["3D logo trap", "If logo <= 1.25x cap but looks taller - wrong edges"],
        ],
        [38, 147],
    )
    pdf.body("If user gives fab dimensions, use photo for overlay placement only.")

    pdf.h1("Part 8 - Color & Raceway")
    pdf.cheat_box("Survey paint note > Art page 2 > Brand standards > Photo sample")
    pdf.body("Raceway = paint the surface the sign mounts on (fascia, pocket, beam) - not letter faces.")
    pdf.table(
        ["Sally element", "Material"],
        [
            ["SALLY red", "#2793 red Plex"],
            ["BEAUTY black", "#2447 + perf vinyl"],
            ["Returns/trim", "Factory dark bronze/black - not raceway paint"],
        ],
        [50, 140],
    )
    pdf.bullet("SW 7100 = Arcade White (not Fractured Ice SW 7647)")
    pdf.bullet("File named Survey may be an invoice - open before trusting")

    pdf.add_page()
    pdf.h1("Part 9 - Permitting (Design Log patterns)")
    pdf.table(
        ["City asks for", "Drawing response"],
        [
            ["Site plan", "Lease outlined, north arrow, 2 streets, sign location"],
            ["Building dims", "Wall length/height on elevation"],
            ["Height to grade", "Top of sign to finished grade"],
            ["Sq ft calc", "Code check - allowed vs proposed"],
            ["Night view", "Illuminated rendering"],
            ["Disconnect", "Electrical detail page"],
        ],
        [45, 145],
    )

    pdf.h1("Part 10 - Comment taxonomy (Latest Comment)")
    pdf.table(
        ["Category", "Language", "Action"],
        [
            ["Survey rescale", "revise to match survey", "Survey/ + rescale p.2"],
            ["Permit add", "site plan, height to grade", "New drawing pages"],
            ["Code resize", "reduce sq ft, 8% wall", "Rescale + code page"],
            ["Color/fab", "returns bronze, SW code", "Art + raceway lookup"],
            ["EagleView", "use EagleView for size", "Aerial before survey"],
        ],
        [32, 52, 101],
    )

    pdf.h1("Part 11 - Brand quick reference")
    pdf.table(
        ["Brand", "Template", "Dimensions", "Special"],
        [
            ["Sally", "VX Sally Template 5-2026.cdr", "Sally CL 2023.xlsx", "Dual-color wordmark"],
            ["CosmoProf", "VX Cosmo Template 5-26.cdr", "In CDR", "80% frontage; cap line"],
            ["AT&T", "Prime Comm Standards 4-6-2026.cdr", "ATT Dimensions xlsx", "Globe; cap ~60% globe"],
            ["Smart Stop", "SmartStop Standards 12.2025.cdr", "SS alt layout xlsx", "SS-CL codes; EagleView"],
            ["Secure Space", "Standards PDF 5.2021", "Dimensions Tables 3.xlsx", "Ft-in notation"],
        ],
        [28, 52, 52, 58],
    )

    pdf.add_page()
    pdf.h1("Part 12 - Common mistakes")
    mistakes = [
        "Using photo letter width as fab width (Gate J)",
        "Measuring CosmoProf on full word height instead of cap line",
        "Reading AT&T globe from color stripes",
        "One mask for Sally red + black blocks",
        "Skipping survey when comment says revise per survey",
        "Trusting Survey.pdf filename without opening",
        "Publishing photo scale as fab proof",
        "Missing site plan on permit jobs",
        "Painting letter faces as raceway color",
        "Assuming dims on R0 rows with blank Existing Fascia fields",
    ]
    for i, m in enumerate(mistakes, 1):
        pdf.bullet(f"{i}. {m}")

    pdf.h1("Part 13 - Self-test")
    questions = [
        "What beats what: survey vs art vs photo?",
        "What is VX1108945 R4?",
        "Where is the fab block?",
        "CosmoProf: what line for cap height?",
        "AT&T: 4'-0\" globe -> what cap tier?",
        "Why is Sally 13'-4\" overall != word widths + gap?",
        "Name the three Smartsheet sheets.",
        "Which Design Log column is PM instruction to art?",
        "Raceway paint authority order?",
        "Name four site plan requirements.",
    ]
    for i, q in enumerate(questions, 1):
        pdf.body(f"{i}. {q}")

    pdf.ln(4)
    pdf.h1("One-page cheat sheet")
    pdf.cheat_box(
        "SURVEY > ART PAGE 2 > SMARTSHEET XLSX > PHOTO ESTIMATE\n\n"
        "Cap line != full word height (CosmoProf)\n"
        "Globe != letter stripe band (AT&T)\n"
        "Fab width != letter-face span (Gate J)\n"
        "Raceway = mount surface paint, not letter faces\n"
        "R0 = template; survey triggers R1+ rescale\n"
        "Latest Comment = read first on every job\n"
        "PPR Approved as = manufacturing lock rev"
    )

    pdf.output(str(OUT))
    return OUT


if __name__ == "__main__":
    path = build()
    print(path)
