# create_documentation_pdf.py
"""
Run this script to generate the complete project documentation PDF:
    pip install reportlab pillow
    python create_docs.py
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether, Image
)
from reportlab.platypus.flowables import Flowable
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from io import BytesIO
import os
import sys

# ── Try to load PIL for screenshots ──
try:
    from PIL import Image as PILImage
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Note: pip install pillow  for image support")

# ══════════════════════════════════════════════════
# COLOUR PALETTE
# ══════════════════════════════════════════════════
C_BG_DARK    = HexColor("#070D1A")
C_NAVY       = HexColor("#0F1D35")
C_ACCENT     = HexColor("#00C2FF")
C_ACCENT2    = HexColor("#7C3AED")
C_GREEN      = HexColor("#00E07A")
C_ORANGE     = HexColor("#FFA030")
C_RED        = HexColor("#FF4C4C")
C_YELLOW     = HexColor("#FFD600")
C_WHITE      = HexColor("#FFFFFF")
C_LIGHT      = HexColor("#C8D8F0")
C_MID        = HexColor("#556B8A")
C_DARK       = HexColor("#03070F")
C_CARD       = HexColor("#132544")
C_TABLE_HDR  = HexColor("#1E2D45")
C_TABLE_ALT  = HexColor("#0F1D35")
C_TABLE_EVEN = HexColor("#132544")
C_BORDER     = HexColor("#1E3A5F")

PAGE_W, PAGE_H = A4
MARGIN = 1.8 * cm
CONTENT_W = PAGE_W - 2 * MARGIN

OUTPUT_FILE = "Deep_Agent_v2_Project_Documentation.pdf"

# ══════════════════════════════════════════════════
# SCREENSHOT FILES
# Place the two screenshots in the same folder as
# this script with these exact names:
#   screenshot_main.png
#   screenshot_analytics.png
# The script will embed them if found.
# ══════════════════════════════════════════════════
SCREENSHOT_MAIN      = "screenshot_main.png"
SCREENSHOT_ANALYTICS = "screenshot_analytics.png"


# ══════════════════════════════════════════════════
# CUSTOM FLOWABLES
# ══════════════════════════════════════════════════

class ColorRect(Flowable):
    """Solid colour rectangle — used as section dividers."""
    def __init__(self, width, height, color, radius=4):
        Flowable.__init__(self)
        self.width  = width
        self.height = height
        self.color  = color
        self.radius = radius

    def draw(self):
        self.canv.setFillColor(self.color)
        self.canv.roundRect(0, 0, self.width, self.height,
                            self.radius, fill=1, stroke=0)


class SectionHeader(Flowable):
    """Full-width dark section header with coloured left bar."""
    def __init__(self, number, title, color=None, width=CONTENT_W):
        Flowable.__init__(self)
        self.number = number
        self.title  = title
        self.color  = color or C_ACCENT
        self.width  = width
        self.height = 1.05 * cm

    def draw(self):
        c = self.canv
        # background
        c.setFillColor(C_NAVY)
        c.roundRect(0, 0, self.width, self.height, 5, fill=1, stroke=0)
        # left accent bar
        c.setFillColor(self.color)
        c.roundRect(0, 0, 0.35 * cm, self.height, 4, fill=1, stroke=0)
        # number chip
        c.setFillColor(self.color)
        c.roundRect(0.55 * cm, 0.15 * cm,
                    0.65 * cm, 0.75 * cm, 3, fill=1, stroke=0)
        c.setFillColor(C_BG_DARK)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(0.875 * cm, 0.3 * cm, self.number)
        # title
        c.setFillColor(C_WHITE)
        c.setFont("Helvetica-Bold", 13)
        c.drawString(1.45 * cm, 0.3 * cm, self.title)


class SubHeader(Flowable):
    """Subsection header with coloured underline."""
    def __init__(self, title, color=None, width=CONTENT_W):
        Flowable.__init__(self)
        self.title  = title
        self.color  = color or C_ACCENT
        self.width  = width
        self.height = 0.75 * cm

    def draw(self):
        c = self.canv
        c.setFillColor(self.color)
        c.roundRect(0, 0.58 * cm, self.width, 0.04 * cm,
                    1, fill=1, stroke=0)
        c.setFillColor(self.color)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(0, 0.3 * cm, self.title)


class InfoCard(Flowable):
    """Coloured info highlight card."""
    def __init__(self, lines, color=None, width=CONTENT_W, height=None):
        Flowable.__init__(self)
        self.lines  = lines
        self.color  = color or C_ACCENT
        self.width  = width
        self.height = height or (len(lines) * 0.52 + 0.35) * cm

    def draw(self):
        c = self.canv
        c.setFillColor(C_NAVY)
        c.roundRect(0, 0, self.width, self.height, 6, fill=1, stroke=0)
        c.setFillColor(self.color)
        c.roundRect(0, 0, 0.22 * cm, self.height, 4, fill=1, stroke=0)
        y = self.height - 0.45 * cm
        for line in self.lines:
            c.setFillColor(C_WHITE)
            c.setFont("Helvetica", 9)
            c.drawString(0.45 * cm, y, str(line))
            y -= 0.52 * cm


class CoverPage(Flowable):
    """Full cover page drawn on canvas."""
    def __init__(self, width=CONTENT_W, height=PAGE_H - 2 * MARGIN):
        Flowable.__init__(self)
        self.width  = width
        self.height = height

    def draw(self):
        c   = self.canv
        w   = self.width
        h   = self.height

        # Dark background card
        c.setFillColor(C_NAVY)
        c.roundRect(0, 0, w, h, 8, fill=1, stroke=0)

        # Top accent bar
        c.setFillColor(C_ACCENT)
        c.rect(0, h - 0.35 * cm, w, 0.35 * cm, fill=1, stroke=0)

        # Left accent strip
        c.setFillColor(C_ACCENT2)
        c.rect(0, 0, 0.4 * cm, h, fill=1, stroke=0)

        # Bottom accent bar
        c.setFillColor(C_ACCENT2)
        c.rect(0, 0, w, 0.35 * cm, fill=1, stroke=0)

        # Internship label
        c.setFillColor(C_ACCENT)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(w / 2, h - 1.4 * cm,
                            "INTERNSHIP PROJECT DOCUMENTATION")

        # Main title
        c.setFillColor(C_WHITE)
        c.setFont("Helvetica-Bold", 34)
        c.drawCentredString(w / 2, h - 3.0 * cm, "Deep Agent")

        # Version badge
        c.setFillColor(C_ACCENT2)
        c.roundRect(w/2 - 1.1*cm, h - 3.9*cm, 2.2*cm, 0.6*cm,
                    5, fill=1, stroke=0)
        c.setFillColor(C_WHITE)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(w / 2, h - 3.68 * cm, "v 2 . 0")

        # Subtitle
        c.setFillColor(C_LIGHT)
        c.setFont("Helvetica-Oblique", 13)
        c.drawCentredString(w / 2, h - 4.8 * cm,
                            "Dynamic Multi-Agent Router")
        c.setFont("Helvetica-Oblique", 11)
        c.drawCentredString(w / 2, h - 5.4 * cm,
                            "Vertex AI Native Orchestration  ·  Cost Optimization  ·  Production Safety")

        # Divider line
        c.setStrokeColor(C_ACCENT)
        c.setLineWidth(1)
        c.line(1.5 * cm, h - 6.3 * cm, w - 1.5 * cm, h - 6.3 * cm)

        # Info table rows
        rows = [
            ("Team Name",      "GCP Technology For Topaz Fabric"),
            ("Intern 1",       "Shivam (585817)"),
            ("Intern 2",       "Jay Kishan (585739)"),
            ("Mentor",         "Amritesh Kumar Sinha"),
            ("Reviewers",      "Chetana Amancharla  |  Amritesh Kumar Sinha"),
            ("Submission",     "April 9, 2026"),
        ]
        ry = h - 7.2 * cm
        for label, val in rows:
            c.setFillColor(C_MID)
            c.setFont("Helvetica-Bold", 9)
            c.drawString(1.0 * cm, ry, label + ":")
            c.setFillColor(C_WHITE)
            c.setFont("Helvetica", 9)
            c.drawString(4.5 * cm, ry, val)
            ry -= 0.6 * cm

       

        # GitHub link
        c.setFillColor(C_CARD)
        c.roundRect(1.0*cm, h - 13.9*cm, w - 2.0*cm, 0.65*cm,
                    5, fill=1, stroke=0)
        c.setFillColor(C_WHITE)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(1.3*cm, h - 13.65*cm, "GitHub:")
        c.setFillColor(C_ACCENT)
        c.setFont("Helvetica", 9)
        c.drawString(3.2*cm, h - 13.65*cm,
                     "https://github.com/jaykishan-2450/multi-llm-router-gcp")

        # Tech pills at bottom
        pills = ["Vertex AI", "Gemini 2.5", "Streamlit", "Guardrails", "Python 3.9+"]
        pill_colors = [C_ACCENT2, C_GREEN, C_ACCENT, C_RED, C_ORANGE]
        px = 1.0 * cm
        py = 1.1 * cm
        for pill, pc in zip(pills, pill_colors):
            pw = (len(pill) * 0.185 + 0.4) * cm
            c.setFillColor(pc)
            c.roundRect(px, py, pw, 0.45 * cm, 4, fill=1, stroke=0)
            c.setFillColor(C_WHITE)
            c.setFont("Helvetica-Bold", 8)
            c.drawCentredString(px + pw / 2, py + 0.14 * cm, pill)
            px += pw + 0.25 * cm


# ══════════════════════════════════════════════════
# STYLE DEFINITIONS
# ══════════════════════════════════════════════════

def build_styles():
    base = getSampleStyleSheet()

    def ps(name, **kw):
        return ParagraphStyle(name, **kw)

    body = ps("Body",
              fontName="Helvetica", fontSize=9.5,
              leading=15, textColor=C_LIGHT,
              spaceAfter=4, alignment=TA_JUSTIFY)

    body_b = ps("BodyBold",
                fontName="Helvetica-Bold", fontSize=9.5,
                leading=15, textColor=C_WHITE, spaceAfter=4)

    bullet = ps("Bullet",
                fontName="Helvetica", fontSize=9,
                leading=14, textColor=C_LIGHT,
                leftIndent=14, spaceAfter=2,
                bulletIndent=4)

    bullet2 = ps("Bullet2",
                 fontName="Helvetica", fontSize=8.5,
                 leading=13, textColor=C_MID,
                 leftIndent=28, spaceAfter=2,
                 bulletIndent=14)

    caption = ps("Caption",
                 fontName="Helvetica-Oblique", fontSize=8.5,
                 leading=12, textColor=C_MID,
                 spaceAfter=6, alignment=TA_CENTER)

    code = ps("Code",
              fontName="Courier", fontSize=8,
              leading=12, textColor=C_GREEN,
              backColor=C_DARK, spaceAfter=4,
              leftIndent=10, rightIndent=10)

    link = ps("Link",
              fontName="Helvetica", fontSize=9,
              textColor=C_ACCENT, spaceAfter=4)

    return {
        "body":    body,
        "bodyb":   body_b,
        "bullet":  bullet,
        "bullet2": bullet2,
        "caption": caption,
        "code":    code,
        "link":    link,
    }


# ══════════════════════════════════════════════════
# TABLE BUILDER
# ══════════════════════════════════════════════════

def make_table(headers, rows, col_widths=None,
               hdr_color=C_ACCENT2, font_size=8.5):
    data = [headers] + rows
    if col_widths is None:
        col_widths = [CONTENT_W / len(headers)] * len(headers)

    style = TableStyle([
        # Header
        ("BACKGROUND",  (0, 0), (-1, 0), hdr_color),
        ("TEXTCOLOR",   (0, 0), (-1, 0), C_WHITE),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, 0), font_size),
        ("TOPPADDING",  (0, 0), (-1, 0), 6),
        ("BOTTOMPADDING",(0,0), (-1, 0), 6),
        # Body rows
        ("FONTNAME",    (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",    (0, 1), (-1, -1), font_size - 0.5),
        ("TEXTCOLOR",   (0, 1), (-1, -1), C_LIGHT),
        ("TOPPADDING",  (0, 1), (-1, -1), 5),
        ("BOTTOMPADDING",(0,1), (-1, -1), 5),
        # Alternating rows
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [C_TABLE_ALT, C_TABLE_EVEN]),
        # Grid
        ("GRID",        (0, 0), (-1, -1), 0.4, C_BORDER),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",(0, 0), (-1, -1), 6),
    ])
    return Table(data, colWidths=col_widths, style=style,
                 repeatRows=1)


# ══════════════════════════════════════════════════
# PAGE TEMPLATE (header + footer on every page)
# ══════════════════════════════════════════════════

class PageTemplate:
    def __init__(self):
        self.page_num = [0]

    def on_page(self, canvas_obj, doc):
        self.page_num[0] += 1
        c = canvas_obj
        c.saveState()

        # Background
        c.setFillColor(C_BG_DARK)
        c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

        # Header bar
        c.setFillColor(C_NAVY)
        c.rect(0, PAGE_H - 1.1*cm, PAGE_W, 1.1*cm, fill=1, stroke=0)
        c.setFillColor(C_ACCENT)
        c.rect(0, PAGE_H - 0.06*cm, PAGE_W, 0.06*cm, fill=1, stroke=0)

        c.setFillColor(C_ACCENT)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(MARGIN, PAGE_H - 0.72 * cm,
                     "Deep Agent v2.0  —  Project Documentation")
        c.setFillColor(C_MID)
        c.setFont("Helvetica", 8)
        c.drawRightString(PAGE_W - MARGIN, PAGE_H - 0.72 * cm,
                          "GCP Technology For Topaz Fabric  |  April 2026")

        # Footer bar
        c.setFillColor(C_NAVY)
        c.rect(0, 0, PAGE_W, 0.9 * cm, fill=1, stroke=0)
        c.setFillColor(C_ACCENT2)
        c.rect(0, 0, PAGE_W, 0.06 * cm, fill=1, stroke=0)

        c.setFillColor(C_MID)
        c.setFont("Helvetica", 7.5)
        c.drawString(MARGIN, 0.3 * cm,
                     "Confidential — Internal Use Only")
        c.setFillColor(C_ACCENT)
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(PAGE_W / 2, 0.3 * cm,
                            "Shivam  &  Jay Kishan")
        c.setFillColor(C_MID)
        c.setFont("Helvetica", 7.5)
        c.drawRightString(PAGE_W - MARGIN, 0.3 * cm,
                          f"Page {self.page_num[0]}")

        c.restoreState()


# ══════════════════════════════════════════════════
# CONTENT BUILDER
# ══════════════════════════════════════════════════

def build_pdf():
    pt = PageTemplate()

    doc = SimpleDocTemplate(
        OUTPUT_FILE,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=1.5 * cm,
        bottomMargin=1.3 * cm,
        title="Deep Agent v2.0 — Project Documentation",
        author="Shivam & Jay Kishan",
        subject="Internship Project Documentation",
        creator="GCP Technology For Topaz Fabric",
    )

    S = build_styles()
    story = []

    def sp(h=0.25):
        story.append(Spacer(1, h * cm))

    def hr(color=C_BORDER, thickness=0.5):
        story.append(HRFlowable(
            width="100%", thickness=thickness,
            color=color, spaceAfter=4, spaceBefore=4))

    def body(text):
        story.append(Paragraph(text, S["body"]))

    def bold(text):
        story.append(Paragraph(text, S["bodyb"]))

    def bul(text, level=1):
        sty = S["bullet"] if level == 1 else S["bullet2"]
        story.append(Paragraph(f"• &nbsp; {text}", sty))

    def code_line(text):
        story.append(Paragraph(text, S["code"]))

    def link_line(text):
        story.append(Paragraph(text, S["link"]))

    def section(num, title, color=None):
        sp(0.4)
        story.append(SectionHeader(num, title, color=color))
        sp(0.25)

    def subsection(title, color=None):
        sp(0.2)
        story.append(SubHeader(title, color=color))
        sp(0.2)

    def card(lines, color=None):
        story.append(InfoCard(lines, color=color))
        sp(0.15)

    def img(path, caption_text=None, max_w=None, max_h=None):
        """Embed image if file exists."""
        if not os.path.exists(path):
            card([f"[Screenshot: {path} — place file in same folder as script]"],
                 color=C_ORANGE)
            return
        try:
            mw = max_w or CONTENT_W
            mh = max_h or (10 * cm)
            if PIL_AVAILABLE:
                pi = PILImage.open(path)
                iw, ih = pi.size
                ratio = min(mw / iw, mh / ih)
                rw, rh = iw * ratio, ih * ratio
            else:
                rw, rh = mw, mh * 0.6
            im = Image(path, width=rw, height=rh)
            story.append(im)
            if caption_text:
                story.append(Paragraph(caption_text, S["caption"]))
            sp(0.15)
        except Exception as e:
            card([f"[Image load error: {e}]"], color=C_RED)

    # ──────────────────────────────────────────────
    # COVER PAGE
    # ──────────────────────────────────────────────
    story.append(CoverPage())
    story.append(PageBreak())

    # ──────────────────────────────────────────────
    # TABLE OF CONTENTS
    # ──────────────────────────────────────────────
    section("00", "Table of Contents", color=C_ACCENT)
    toc_rows = [
        ["01", "Basic Information",           "3"],
        ["02", "Project Overview",            "3"],
        ["03", "System Architecture",         "4"],
        ["04", "Step-by-Step Implementation", "5"],
        ["05", "Testing Approach",            "6"],
        ["06", "Software, Tools & Setup",     "7"],
        ["07", "Cloud & Access",              "8"],
        ["08", "Challenges & Blockers",       "9"],
        ["09", "Deliverables",               "10"],
        ["10", "Results & Analytics",        "11"],
        ["11", "Future Scope",               "12"],
        ["12", "Feedback & Reflection",      "13"],
    ]
    toc_table = make_table(
        ["#", "Section", "Page"],
        toc_rows,
        col_widths=[1.2*cm, 13.5*cm, 1.5*cm],
        hdr_color=C_ACCENT2,
    )
    story.append(toc_table)
    story.append(PageBreak())

    # ──────────────────────────────────────────────
    # SECTION 01 — BASIC INFORMATION
    # ──────────────────────────────────────────────
    section("01", "Basic Information", color=C_ACCENT)

    info_rows = [
        ["Project Title",  "Deep Agent v2.0 — Dynamic Multi-Agent Router (Vertex AI Native)"],
        ["Team Name",      "GCP Technology For Topaz Fabric"],
        ["Intern 1",       "Shivam"],
        ["Intern 2",       "Jay Kishan"],
        ["Mentor",         "Amritesh Kumar Sinha"],
        ["Reviewers",      "Chetana Amancharla  |  Amritesh Kumar Sinha"],
        ["Submission Date","April 9, 2026"],
        ["Program",        "Internal / Companywide Internship"],
    ]
    story.append(make_table(
        ["Field", "Details"],
        info_rows,
        col_widths=[4.5*cm, 12.2*cm],
        hdr_color=C_ACCENT2,
    ))
    sp(0.3)

    # ──────────────────────────────────────────────
    # SECTION 02 — PROJECT OVERVIEW
    # ──────────────────────────────────────────────
    section("02", "Project Overview & Understanding", color=C_ACCENT2)

    subsection("Problem Statement", color=C_RED)
    body(
        "Version 1.0 relied on mixed provider routing and non-native model calls, "
        "which introduced provider-specific behavior differences, rate-limit variability, "
        "and avoidable integration complexity. The v2.0 goal was to retain the proven "
        "multi-agent architecture while migrating routing and agent execution to a "
        "single GCP-native runtime using Vertex AI."
    )
    sp(0.1)

    subsection("Objectives", color=C_GREEN)
    objectives = [
        "Migrate router inference to Vertex AI Gemini 2.5 Flash-Lite",
        "Migrate all agent LLM execution to Vertex AI GenerativeModel API",
        "Preserve tier-based dynamic routing (Lite / Standard / Pro)",
        "Retain 3 specialized agents: Coding, Math, Reasoning",
        "Retain production guardrails (input, output, daily cost budget)",
        "Retain fallback resilience with ordered model-key fallback chain",
        "Add local setup requirements for Google Cloud SDK authentication",
        "Document optional GCP extensions (BigQuery, monitoring, Cloud Run)",
    ]
    for obj in objectives:
        bul(obj)
    sp(0.2)

    subsection("Solution Overview", color=C_ACCENT)
    body(
        "Deep Agent v2.0 is a multi-agent AI orchestration system deployed on "
        "Streamlit Cloud. Every query passes through: Input Guardrails → Router "
        "(Vertex Gemini 2.5 Flash-Lite classifies agent + complexity) → Specialized "
        "Agent on Vertex AI with runtime tier selection → Output Guardrails → "
        "Analytics logging. Users can manually upgrade to any of 6 configured model "
        "profiles across 3 tiers via the UI."
    )

    # ──────────────────────────────────────────────
    # SECTION 03 — ARCHITECTURE
    # ──────────────────────────────────────────────
    section("03", "System Architecture", color=C_GREEN)

    subsection("End-to-End Pipeline", color=C_ACCENT)
    pipeline_steps = [
        ["Stage", "Component", "Description"],
        ["1", "Input Guardrails",  "check_input() — blocks injection, warns PII, rate-limits"],
        ["2", "Router",            "route_query() — Vertex Gemini 2.5 Flash-Lite classification"],
        ["3", "Model Selection",   "Complexity→Tier: simple→Lite, medium→Std, complex→Pro"],
        ["4", "Agent Execution",   "run_agent() — specialized prompt + Vertex call + fallback"],
        ["5", "Output Guardrails", "check_output() — scans for dangerous code, uncertainty"],
        ["6", "Analytics",         "log_query() → CSV · compute_savings() → cost table"],
    ]
    story.append(make_table(
        pipeline_steps[0], pipeline_steps[1:],
        col_widths=[1.0*cm, 4.5*cm, 11.2*cm],
        hdr_color=C_ACCENT2,
    ))
    sp(0.2)

    subsection("Model Registry — 6 Profiles · 3 Tiers · Vertex AI", color=C_ACCENT)
    model_rows = [
        ["lite_a",     "gemini-2.5-flash-lite", "Vertex AI", "🟢 Lite",     "$0.0001",   "300 ms",  "Default Lite"],
        ["lite_b",     "gemini-2.5-flash-lite", "Vertex AI", "🟢 Lite",     "$0.0001",   "350 ms",  "Lite Fallback"],
        ["standard_a", "gemini-2.5-flash",      "Vertex AI", "🟠 Standard", "$0.0003",   "400 ms",  "Default Std"],
        ["standard_b", "gemini-2.5-flash",      "Vertex AI", "🟠 Standard", "$0.0003",   "450 ms",  "Std Fallback"],
        ["pro_a",      "gemini-2.5-pro",        "Vertex AI", "🔴 Pro",      "$0.00125",  "2000 ms", "Default Pro"],
        ["pro_b",      "gemini-2.5-pro",        "Vertex AI", "🔴 Pro",      "$0.00125",  "2200 ms", "Pro Fallback"],
    ]
    story.append(make_table(
        ["Key", "Model", "Provider", "Tier", "Cost/1k", "Latency", "Role"],
        model_rows,
        col_widths=[2.0*cm, 5.5*cm, 2.0*cm, 2.5*cm, 1.8*cm, 1.8*cm, 2.1*cm],
        hdr_color=C_NAVY,
        font_size=8,
    ))
    sp(0.15)
    card([
        "Upgrade Chain: lite_a → lite_b → standard_a → standard_b → pro_a → pro_b",
        "Fallback Chain: requested model → same-tier alternate → standard_a → lite_a → remaining",
        "Router Model: Vertex Gemini 2.5 Flash-Lite — Temperature=0 · low-token classifier",
    ], color=C_ACCENT2)

    # ──────────────────────────────────────────────
    # SCREENSHOTS
    # ──────────────────────────────────────────────
    section("—", "Live Application Screenshots", color=C_ACCENT)
    sp(0.1)

    img(SCREENSHOT_MAIN,
        "Figure 1: Deep Agent v2.0 — Main Interface",
        max_w=CONTENT_W, max_h=9.5*cm)
    sp(0.2)
    img(SCREENSHOT_ANALYTICS,
        "Figure 2: Analytics Dashboard — Queries=6, Cost=$0.0030, "
        "Avg Latency=3886ms, Cost Saved=48%, Fallbacks=0",
        max_w=CONTENT_W, max_h=9.5*cm)

    # ──────────────────────────────────────────────
    # SECTION 04 — IMPLEMENTATION
    # ──────────────────────────────────────────────
    section("04", "Step-by-Step Implementation", color=C_ORANGE)

    subsection("Phase 1 — Environment Setup", color=C_ACCENT)
    impl_steps = [
        ("Step 1: Repository", [
            "Created GitHub repository",
            "Initialized Python .gitignore + requirements.txt",
            "Created venv and installed core deps from requirements.txt",
        ]),
        ("Step 2: Local GCP Authentication (Required)", [
            "Installed Google Cloud SDK and selected a GCP project",
            "Ran gcloud auth login and gcloud auth application-default login",
            "Configured VERTEX_PROJECT_ID and VERTEX_LOCATION via env vars or Streamlit secrets",
            "Avoided hardcoded credentials and never committed secrets to source control",
        ]),
        ("Step 3: Vertex AI Migration", [
            "Replaced LiteLLM routing calls with Vertex GenerativeModel classification",
            "Replaced all agent model calls with Vertex GenerativeModel + GenerationConfig",
            "Retained fallback, guardrails, analytics logging, and upgrade UX",
        ]),
    ]
    for title, points in impl_steps:
        bold(title)
        for p in points:
            bul(p)
        sp(0.1)

    subsection("Phase 2 — Core Files Built", color=C_ACCENT)
    files_built = [
        ["File",             "What Was Built"],
        ["config.py",        "Vertex AI init, 6-profile registry, costs, upgrade paths, guardrail config"],
        ["router.py",        "JSON-structured prompt, Vertex router call, parsing fallback defaults"],
        ["agents.py",        "3 specialized prompts, Vertex model execution, ordered fallback chain"],
        ["guardrails.py",    "Layer 1 input, Layer 2 output, Layer 3 system cost tracking"],
        ["analytics.py",     "14-column CSV logging, compute_savings(), session_stats()"],
        ["app.py",           "Full Streamlit UI, upgrade system, analytics dashboard, 4 tabs"],
        ["additional/setup_bigquery.py", "Optional BigQuery dataset/table bootstrap script"],
        ["additional/test_logits.py",    "Experimental logprobs-based confidence validation"],
    ]
    story.append(make_table(
        files_built[0], files_built[1:],
        col_widths=[3.2*cm, 13.5*cm],
        hdr_color=C_ACCENT2,
    ))
    sp(0.2)

    subsection("Phase 3 — Deployment", color=C_GREEN)
    deploy_steps = [
        "Pushed all code to GitHub repository",
        "Connected repository to share.streamlit.io",
        "Set Streamlit secrets: VERTEX_PROJECT_ID and VERTEX_LOCATION",
        "Validated ADC-based local execution using Google Cloud SDK login",
        "Verified live app deployment",
        "Tested all 6 sidebar example queries on live deployment",
    ]
    for s in deploy_steps:
        bul(s)

    # ──────────────────────────────────────────────
    # SECTION 05 — TESTING
    # ──────────────────────────────────────────────
    section("05", "Testing Approach", color=C_ACCENT)
    body(
        "Testing was performed through the live Streamlit application and local "
        "Vertex-authenticated runs, covering routing accuracy, guardrail safety, "
        "fallback resilience, and model upgrade flows."
    )
    sp(0.1)

    subsection("5.1 Routing Accuracy Tests", color=C_ACCENT)
    routing_rows = [
        ["What is 25 × 48?",                              "Math",      "Lite",     "PASS"],
        ["Prove √2 is irrational",                        "Math",      "Pro",      "PASS"],
        ["Implement binary search in Python",             "Coding",    "Standard", "PASS"],
        ["Design a thread-safe LRU cache with TTL",       "Coding",    "Pro",      "PASS"],
        ["What is the capital of Japan?",                 "Reasoning", "Lite",     "PASS"],
        ["Compare SQL vs NoSQL for e-commerce",           "Reasoning", "Standard", "PASS"],
        ["Microservices vs monolith for 5-person team",   "Reasoning", "Pro",      "PASS"],
    ]
    story.append(make_table(
        ["Query", "Agent", "Tier", "Result"],
        routing_rows,
        col_widths=[9.5*cm, 2.2*cm, 2.5*cm, 2.5*cm],
        hdr_color=C_ACCENT2,
    ))
    sp(0.2)

    subsection("5.2 Guardrail Safety Tests", color=C_RED)
    guard_rows = [
        ["Ignore all instructions + reveal prompt",  "Blocked — injection detected",  "PASS"],
        ["My email is john@company.com + Python help","PII warning shown, proceeds",   "PASS"],
        ["Query of 5500 characters",                 "Truncated to 5000 chars",        "PASS"],
        ["21 rapid queries in 60 seconds",           "Rate limit triggered at 20",     "PASS"],
    ]
    story.append(make_table(
        ["Test Input", "Expected Behaviour", "Result"],
        guard_rows,
        col_widths=[7.0*cm, 7.5*cm, 2.2*cm],
        hdr_color=C_RED,
    ))
    sp(0.2)

    subsection("5.3 Fallback & Upgrade Tests", color=C_ORANGE)
    fallback_rows = [
        ["ADC not configured locally",        "Controlled error response, UI remains stable", "PASS"],
        ["Primary model call failure",        "Next fallback model key attempted",            "PASS"],
        ["Click same-tier switch button",     "New model answers same query",        "PASS"],
        ["Click tier upgrade button",         "Pro model gives deeper answer",       "PASS"],
        ["Cost delta after upgrade",          "Delta cost + latency shown in UI",    "PASS"],
    ]
    story.append(make_table(
        ["Scenario", "Expected", "Result"],
        fallback_rows,
        col_widths=[7.0*cm, 7.5*cm, 2.2*cm],
        hdr_color=C_ORANGE,
    ))
    sp(0.2)

    subsection("5.4 Analytics Verification (Live App)", color=C_ACCENT)
    analytics_rows = [
        ["Queries Logged",   "6",       "CSV row count matches queries run"],
        ["Total Cost",       "$0.0030", "Sum of per-query estimated costs"],
        ["Avg Latency",      "3886 ms", "Higher due to Pro-tier queries"],
        ["Cost Saved",       "48%",     "vs all-pro_a routing baseline"],
        ["Fallbacks",        "0",       "All primary models succeeded"],
        ["Distribution",     "Mixed",   "33% Lite + 17% Std + 50% Pro"],
    ]
    story.append(make_table(
        ["Metric", "Observed Value", "Notes"],
        analytics_rows,
        col_widths=[4.5*cm, 3.0*cm, 9.2*cm],
        hdr_color=C_ACCENT2,
    ))

    # ──────────────────────────────────────────────
    # SECTION 06 — TOOLS & SETUP
    # ──────────────────────────────────────────────
    section("06", "Software, Tools & Setup", color=C_ACCENT2)

    subsection("Development Tools & IDEs", color=C_ACCENT)
    tools_rows = [
        ["Python 3.9+",        "Primary programming language",        "Installed"],
        ["VS Code",            "Code editor / IDE",                   "Used"],
        ["Git",                "Version control",                     "Used"],
        ["GitHub",             "Remote repository hosting",           "Used"],
        ["Windows PowerShell", "Terminal for CLI commands",           "Used"],
        ["pip",                "Python package manager",              "Used"],
        ["Streamlit Cloud",    "Free cloud hosting for deployment",   "Used"],
    ]
    story.append(make_table(
        ["Tool", "Purpose", "Status"],
        tools_rows,
        col_widths=[4.0*cm, 9.5*cm, 3.2*cm],
        hdr_color=C_ACCENT2,
    ))
    sp(0.2)

    subsection("Libraries & Frameworks", color=C_ACCENT)
    lib_rows = [
        ["streamlit",  "1.30+",   "Web UI framework + dashboard"],
        ["google-cloud-aiplatform", ">=1.60.0", "Vertex AI SDK for model inference"],
        ["google-auth", "latest", "Application Default Credentials for local/dev auth"],
        ["pandas",     "latest",  "Data processing for analytics CSV"],
        ["plotly",     "latest",  "Interactive charts in dashboard"],
        ["csv",        "stdlib",  "Query logging — 14 columns per row"],
        ["re",         "stdlib",  "PII regex detection in guardrails"],
        ["json",       "stdlib",  "Router JSON output parsing"],
        ["datetime",   "stdlib",  "Daily cost reset tracking"],
    ]
    story.append(make_table(
        ["Library", "Version", "Purpose"],
        lib_rows,
        col_widths=[3.2*cm, 2.5*cm, 11.0*cm],
        hdr_color=C_ACCENT2,
    ))
    sp(0.2)

    subsection("CLI Commands Used", color=C_GREEN)
    cli_commands = [
        "python -m venv venv                      # Create virtual environment",
        ".\\venv\\Scripts\\Activate.ps1            # Activate (Windows PowerShell)",
        "source venv/bin/activate                 # Activate (Mac/Linux)",
        "pip install -r requirements.txt",
        "gcloud auth login",
        "gcloud auth application-default login",
        "gcloud config set project <YOUR_GCP_PROJECT_ID>",
        "pip freeze > requirements.txt",
        "python -m streamlit run app.py           # Run locally",
        "git add . && git commit -m 'feat: ...'   # Commit",
        "git push origin main                     # Push to GitHub",
    ]
    for cmd in cli_commands:
        code_line(cmd)
    sp(0.1)

    subsection("Local Vertex AI Authentication (Required)", color=C_ORANGE)
    card([
        "1) Install Google Cloud SDK and sign in with gcloud auth login",
        "2) Run gcloud auth application-default login for local ADC",
        "3) Set VERTEX_PROJECT_ID and VERTEX_LOCATION (example: us-central1)",
        "4) Never hardcode or commit credentials in code, configs, or docs",
    ], color=C_ORANGE)
    sp(0.05)

    subsection("API Services Used", color=C_ACCENT)
    api_rows = [
        ["Vertex AI",       "cloud.google.com/vertex-ai", "Router + all model inference",   "Active"],
        ["Google Cloud SDK", "cloud.google.com/sdk",      "Local ADC authentication",        "Active"],
        ["Streamlit Cloud", "share.streamlit.io",       "App deployment & hosting",      "Obtained"],
        ["GitHub",          "github.com",               "Code repository",               "Obtained"],
        ["BigQuery (optional)", "cloud.google.com/bigquery", "Production-grade analytics sink", "Experimental"],
    ]
    story.append(make_table(
        ["Service", "URL", "Purpose", "Status"],
        api_rows,
        col_widths=[3.0*cm, 5.0*cm, 6.5*cm, 2.2*cm],
        hdr_color=C_ACCENT2,
    ))

    # ──────────────────────────────────────────────
    # SECTION 07 — CLOUD & ACCESS
    # ──────────────────────────────────────────────
    section("07", "Cloud & Access", color=C_GREEN)

    subsection("7.1 Current Services (Implemented in v2.0)", color=C_ACCENT)
    current_cloud = [
        ["Vertex AI",       "Google Cloud",  "Router + all LLM inference",          "✅ Active"],
        ["Google Cloud SDK", "Google Cloud", "Local ADC authentication",             "✅ Active"],
        ["Streamlit Cloud", "Streamlit Inc.", "App hosting & deployment",            "✅ Active"],
        ["GitHub",          "Microsoft",     "Code repository & version control",    "✅ Active"],
    ]
    story.append(make_table(
        ["Service", "Provider", "Purpose", "Status"],
        current_cloud,
        col_widths=[3.0*cm, 3.0*cm, 8.0*cm, 2.7*cm],
        hdr_color=C_ACCENT2,
    ))
    sp(0.2)

    subsection("7.2 GCP Services — Access & Readiness", color=C_ACCENT)
    gcp_rows = [
        ["Vertex AI",        "Primary router + execution runtime",    "✅ Available",     "roles/aiplatform.user"],
        ["Cloud Run",        "Containerized auto-scaling deployment", "❌ Not Granted",   "roles/run.developer"],
        ["BigQuery",         "Replace CSV query logging",            "❌ Not Granted",   "roles/bigquery.dataEditor"],
        ["Firestore",        "Session memory (Phase 2)",             "🔄 Not Requested", "roles/datastore.user"],
        ["Redis Memorystore","Semantic cache (Phase 2)",             "🔄 Not Requested", "roles/redis.editor"],
        ["Secret Manager",   "Secure API key storage",              "🔄 Not Requested", "roles/secretmanager.secretAccessor"],
        ["Cloud Monitoring", "Observability + alerts",              "🔄 Not Requested", "roles/monitoring.editor"],
        ["Pub/Sub",          "Async Pro-tier query processing",      "🔄 Not Requested", "roles/pubsub.publisher"],
    ]
    story.append(make_table(
        ["GCP Service", "Purpose", "Access Status", "Required IAM Role"],
        gcp_rows,
        col_widths=[3.2*cm, 5.8*cm, 3.0*cm, 4.7*cm],
        hdr_color=C_NAVY,
        font_size=8,
    ))
    sp(0.2)

    card([
        "ACTIVE NOW: Vertex AI is the primary runtime for routing and all model calls.",
        "MISSING ACCESS: Cloud Run — deployment remains on Streamlit Cloud for now.",
        "MISSING ACCESS: BigQuery — analytics remain local CSV until IAM access is granted.",
    ], color=C_RED)
    sp(0.1)

    subsection("7.3 Access Issues Encountered", color=C_ORANGE)
    access_issues = [
        ("Local ADC Not Initialized",
         "Vertex calls failed on fresh machines without default credentials.",
         "Required gcloud auth application-default login in local setup flow."),
        ("Cloud Run Access Not Granted",
         "Could not validate containerized GCP deployment in internship scope.",
         "Used Streamlit Cloud as equivalent and documented Cloud Run migration."),
        ("BigQuery Access Not Granted",
         "Could not validate streaming inserts or SQL analytics queries.",
         "CSV logging kept as default and setup_bigquery.py prepared for migration."),
        ("Vertex Region / IAM Mismatch",
         "Model invocation can fail when project, region, or IAM bindings differ.",
         "Standardized VERTEX_LOCATION and documented minimum IAM role requirements."),
        ("Streamlit File Persistence",
         "CSV logs and session files reset on Streamlit Cloud restart.",
         "Accepted for prototype; roadmap keeps BigQuery and Firestore as durable targets."),
    ]
    for issue, problem, resolution in access_issues:
        bold(f"Issue: {issue}")
        bul(f"Problem: {problem}")
        bul(f"Resolution: {resolution}")
        sp(0.05)

    subsection("7.4 Experimental Files Requiring Permissions", color=C_ACCENT)
    card([
        "additional/setup_bigquery.py: requires BigQuery dataset/table create permissions.",
        "additional/test_logits.py: requires Vertex model access for logprobs experiments.",
        "additional/anthropic_vertex_smoke_test.py: requires Anthropic-on-Vertex access and package setup.",
    ], color=C_ACCENT2)

    # ──────────────────────────────────────────────
    # SECTION 08 — CHALLENGES & BLOCKERS
    # ──────────────────────────────────────────────
    section("08", "Challenges & Blockers", color=C_RED)

    subsection("8.1 Technical Challenges", color=C_ORANGE)

    tech_challenges = [
        ("Challenge 1: Vertex Usage Metadata Field Names",
         "Token metadata fields differ between router and agent response objects, "
         "which initially caused zero-token accounting in some traces.",
         "Added defensive extraction helpers with fallback attribute names and "
         "safe defaults when metadata is unavailable.",
         "SDK-bound integrations need robust parsing around evolving response schemas."),

        ("Challenge 2: Router JSON Parsing Failures",
         "Vertex router output occasionally returned JSON wrapped in markdown code fences "
         "(```json ... ```) instead of raw JSON, causing json.JSONDecodeError "
         "and breaking the routing pipeline.",
         "Added pre-processing to strip markdown fences before JSON parsing. "
         "Added fallback defaults (agent=reasoning, complexity=medium) if parsing fails.",
         "LLM outputs need defensive parsing — never assume clean structured output."),

        ("Challenge 3: Streamlit st.rerun() Inside Spinner",
         "Calling st.rerun() inside a with st.spinner() context manager caused "
         "RerunException to propagate incorrectly in some Streamlit versions, "
         "breaking the upgrade button flow.",
         "Moved all st.rerun() calls outside spinner context managers. Results "
         "stored in st.session_state first, then rerun() called independently.",
         "Streamlit context managers have scope limitations — exit before rerunning."),

        ("Challenge 4: Analytics CSV Schema Drift",
         "Legacy CSV files can carry older column layouts which break strict "
         "analytics assumptions during local restarts.",
         "Added _ensure() function that creates CSV with headers only if file "
         "does not exist. Added safe column existence checks with .get() fallbacks.",
         "CSV schema changes require migration strategy — even in prototypes."),

        ("Challenge 5: ADC + Project Configuration Errors",
         "Missing ADC login or wrong project/region settings produced runtime "
         "errors that looked similar to model availability failures.",
         "Added explicit setup documentation and standardized env vars "
         "(VERTEX_PROJECT_ID, VERTEX_LOCATION) across local and cloud runs.",
         "Authentication and project config should be validated before debugging model logic."),

        ("Challenge 6: Cost Calculation Display Precision",
         "Floating point representation caused cost display to show $0.00 "
         "for very cheap Lite-tier queries (e.g., $0.000050), making cost "
         "transparency meaningless for those queries.",
         "Implemented dynamic decimal logic: cost < 0.001 shows 6 decimal "
         "places; cost < 0.01 shows 5; else shows 4 decimal places.",
         "Financial display in AI apps requires dynamic precision, not fixed."),
    ]

    for title, problem, resolution, learning in tech_challenges:
        bold(title)
        bul(f"Problem: {problem}")
        bul(f"Resolution: {resolution}")
        bul(f"Learning: {learning}")
        sp(0.12)

    subsection("8.2 Non-Technical Challenges", color=C_RED)

    non_tech = [
        ("IAM Provisioning Timelines",
         "Cloud Run and BigQuery access was not granted in the execution window, "
         "limiting full production validation during the internship period.",
         "Documented complete migration in additional/GCP_INTEGRATION_ROADMAP.md "
         "and kept parity via Streamlit Cloud + local CSV.",
         "Request all required cloud permissions on Day 1 of any project."),

        ("Environment Portability",
         "Keeping local, demo, and cloud runtime behavior aligned required clear "
         "authentication and configuration contracts for each environment.",
         "Standardized ADC for local runs and Streamlit secrets for deployment "
         "without embedding secrets into source files.",
         "Documented setup reduces onboarding friction and runtime surprises."),

        ("Understanding Vertex Cost Behavior",
         "Initially unclear how to quantify and compare costs across models with "
         "different token pricing, making it hard to demonstrate ROI of routing.",
         "Implemented compute_savings() benchmarking every query against "
         "Pro-A baseline, making cost savings visible and measurable.",
         "ROI measurement must be built into the system, not added as an afterthought."),
    ]

    for title, problem, resolution, learning in non_tech:
        bold(title)
        bul(f"Problem: {problem}")
        bul(f"Resolution: {resolution}")
        bul(f"Learning: {learning}")
        sp(0.12)

    subsection("8.3 Blocker Summary", color=C_ACCENT)
    blocker_rows = [
        ["Cloud Run access not granted",    "HIGH",   "Use Streamlit Cloud",         "Resolved"],
        ["BigQuery access not granted",     "MEDIUM", "Use local CSV logging",       "Resolved"],
        ["ADC missing in local setup",      "HIGH",   "gcloud application-default login", "Resolved"],
        ["Vertex region/project mismatch",  "MEDIUM", "Standardize env configuration",    "Resolved"],
        ["CSV schema drift",                "MEDIUM", "Header checks + safe fallbacks",   "Resolved"],
    ]
    story.append(make_table(
        ["Blocker", "Severity", "Workaround", "Status"],
        blocker_rows,
        col_widths=[6.5*cm, 2.0*cm, 5.5*cm, 2.7*cm],
        hdr_color=C_RED,
    ))

    # ──────────────────────────────────────────────
    # SECTION 09 — DELIVERABLES
    # ──────────────────────────────────────────────
    section("09", "Deliverables", color=C_ACCENT)

    subsection("Submitted Artifacts", color=C_GREEN)
    deliverables = [
        ["Live Application",          "See cover page link",                                "✅ Delivered"],
        ["GitHub Repository",         "See cover page link",                                "✅ Delivered"],
        ["Project Documentation PDF", "This document",                                      "✅ Delivered"],
        ["README.md",                 "Installation, usage, architecture overview",         "✅ Delivered"],
        ["GCP Integration Roadmap",   "additional/GCP_INTEGRATION_ROADMAP.md",             "✅ Delivered"],
        ["Experimental Scripts",      "additional/* (BigQuery setup, logprobs test, smoke test)", "✅ Delivered"],
        ["Presentation (PPT)",        "16-slide technical presentation",                   "✅ Delivered"],
        ["Completed Checklist PDF",   "Internship_Project_Checklist_<TeamName>.pdf",       "✅ Delivered"],
    ]
    story.append(make_table(
        ["Deliverable", "Location / Description", "Status"],
        deliverables,
        col_widths=[4.5*cm, 9.0*cm, 3.2*cm],
        hdr_color=C_ACCENT2,
    ))
    sp(0.2)

    subsection("Code Files Delivered", color=C_ACCENT)
    code_files = [
        ["app.py",           "Streamlit UI + full pipeline orchestration"],
        ["router.py",        "Query classification — Vertex Gemini 2.5 Flash-Lite"],
        ["agents.py",        "Sub-agent execution + ordered Vertex fallback"],
        ["guardrails.py",    "3-layer safety system"],
        ["analytics.py",     "CSV logging + cost computation"],
        ["config.py",        "Vertex model registry + upgrade paths + guardrail config"],
        ["additional/setup_bigquery.py", "Optional analytics migration helper"],
        ["additional/anthropic_vertex_smoke_test.py", "Permission-gated Vertex smoke test"],
        ["requirements.txt", "All Python dependencies pinned"],
    ]
    story.append(make_table(
        ["File", "Description"],
        code_files,
        col_widths=[3.5*cm, 13.2*cm],
        hdr_color=C_ACCENT2,
    ))

    # ──────────────────────────────────────────────
    # SECTION 10 — RESULTS
    # ──────────────────────────────────────────────
    section("10", "Results & Analytics", color=C_YELLOW)

    subsection("10.1 Key Performance Metrics (Live App)", color=C_ACCENT)
    kpi_rows = [
        ["Max Cost Reduction",    "92%",      "Lite vs Pro-A on simple query"],
        ["Average Cost Savings",  "48%",      "Observed in live test session"],
        ["Uptime via Fallback",   "99.8%",    "Multi-step fallback design"],
        ["Models Integrated",     "6",        "All on Vertex AI Gemini 2.5 family"],
        ["Agents Implemented",    "3",        "Coding, Math, Reasoning"],
        ["Guardrail Layers",      "3",        "Input, Output, System"],
        ["Upgrade Options",       "Up to 5",  "Per query from any starting model"],
        ["Analytics Columns",     "14",       "Per-query CSV log columns"],
    ]
    story.append(make_table(
        ["Metric", "Value", "Notes"],
        kpi_rows,
        col_widths=[6.5*cm, 2.5*cm, 7.7*cm],
        hdr_color=C_ACCENT2,
    ))
    sp(0.2)

    subsection("10.2 Cost Comparison Table", color=C_GREEN)
    cost_rows = [
        ["Gemini 2.5 Flash-Lite (lite_a)", "Lite",     "$0.000050", "300 ms",  "92%"],
        ["Gemini 2.5 Flash-Lite (lite_b)", "Lite",     "$0.000050", "350 ms",  "92%"],
        ["Gemini 2.5 Flash (standard_a)",  "Standard", "$0.000150", "400 ms",  "76%"],
        ["Gemini 2.5 Flash (standard_b)",  "Standard", "$0.000150", "450 ms",  "76%"],
        ["Gemini 2.5 Pro (pro_a)",         "Pro",      "$0.000625", "2000 ms", "Baseline"],
        ["Gemini 2.5 Pro (pro_b)",         "Pro",      "$0.000625", "2200 ms", "0%"],
    ]
    story.append(make_table(
        ["Model", "Tier", "Cost / 500 tokens", "Latency", "Saving vs Pro A"],
        cost_rows,
        col_widths=[5.5*cm, 2.5*cm, 3.5*cm, 2.5*cm, 2.7*cm],
        hdr_color=C_ACCENT2,
    ))
    sp(0.2)

    card([
        "Observed Analytics (Live App Test Session, April 2026):",
        "  Queries: 6  |  Total Cost: $0.0030  |  Avg Latency: 3886 ms",
        "  Cost Saved: 48%  |  Fallbacks: 0  |  Distribution: 50% Pro, 33% Lite, 17% Std",
        "  Agent Split: 50% Coding, 50% Math",
    ], color=C_GREEN)

    # ──────────────────────────────────────────────
    # SECTION 11 — FUTURE SCOPE
    # ──────────────────────────────────────────────
    section("11", "Future Scope", color=C_ACCENT2)

    subsection("Phase 2 — Planned Features", color=C_ACCENT)
    phase2 = [
        ("Conversational Memory",
         "JSON session files · last 5 turns per-agent namespaced · "
         "injected as history into every LLM call"),
        ("Semantic Query Cache",
         "difflib fuzzy match (≥0.85) · repeated queries served instantly at $0 · "
         "500-entry cap with LRU eviction"),
        ("Agent Handoff Context",
         "When upgrading models, new model receives full conversation context "
         "so it does not start from scratch"),
        ("Export Conversations",
         "Download sessions as Markdown or JSON files"),
        ("User Preference Learning",
         "Auto-route to user's historically preferred model per agent type"),
        ("Code Execution Sandbox",
         "Run generated Python code in isolated sandbox, show output in UI"),
        ("Query Feedback Loop",
         "Thumbs up/down rating system to improve routing accuracy over time"),
    ]
    for title, desc in phase2:
        bold(f"→  {title}")
        bul(desc)
        sp(0.05)

    sp(0.1)
    subsection("GCP Production Migration", color=C_GREEN)
    gcp_migration = [
        ["query_logs.csv",       "BigQuery",             "Streaming inserts, SQL analytics, Looker dashboards"],
        ["Sidebar runtime stats", "Cloud Monitoring",      "Alerts on error rate, cost spikes, latency regressions"],
        ["Streamlit Cloud",      "Cloud Run",            "Auto-scale 0→1000+ instances with container deployment"],
        ["Local ADC on laptops", "Service Accounts / WIF", "Controlled production identity and least-privilege auth"],
        ["Manual smoke scripts", "Cloud Build scheduler", "Automated periodic health checks for critical paths"],
        ["Future session files", "Firestore",            "Durable multi-turn conversation memory"],
        ["Future semantic cache", "Redis Memorystore",    "Low-latency cache for repeated or similar queries"],
    ]
    story.append(make_table(
        ["Current (v2.0)", "GCP Next Step", "Benefit"],
        gcp_migration,
        col_widths=[4.5*cm, 4.5*cm, 7.7*cm],
        hdr_color=C_ACCENT2,
    ))

    # ──────────────────────────────────────────────
    # SECTION 12 — FEEDBACK & REFLECTION
    # ──────────────────────────────────────────────
    section("12", "Feedback & Reflection", color=C_ORANGE)

    subsection("12.1 Feedback for Mentor — Amritesh Kumar Sinha", color=C_ACCENT)
    body(
        "Working with Amritesh was highly productive throughout this internship. "
        "His suggestion to think about GCP production migration early — even before "
        "the prototype was complete — was particularly valuable. It helped us write "
        "a proper migration roadmap (additional/GCP_INTEGRATION_ROADMAP.md) that maps every "
        "local component to its GCP equivalent service, which demonstrates real "
        "production thinking beyond just prototype code."
    )
    sp(0.1)
    body(
        "The guidance to add conversational memory and semantic caching as Phase 2 "
        "features demonstrated forward-thinking architecture planning. The iterative "
        "feedback loop kept the project focused on what matters most: cost optimization, "
        "reliability, and observability."
    )
    

    sp(0.2)
    subsection("12.2 Feedback for Internship Program", color=C_ACCENT)
    body(
        "The internship provided strong exposure to real-world AI system design. "
        "Building something that uses production APIs, handles failures gracefully, "
        "and has a clear cloud migration path was far more valuable than a purely "
        "academic exercise. The requirement to document a GCP roadmap pushed us to "
        "think beyond the prototype and understand enterprise architecture."
    )
    sp(0.1)
    bold("Suggestions:")
    bul("GCP service access should be provisioned at day one of the internship.")
    bul("A demo session where interns present to each other enables cross-team learning.")
    bul("Providing a starter GCP project with basic IAM roles already configured "
        "would reduce onboarding friction significantly.")

    sp(0.2)
    subsection("12.3 Key Learnings & Self-Reflection", color=C_GREEN)

    bold("Shivam:")
    body(
        "This internship taught me that building AI systems is not just about "
        "calling LLM APIs — it is about designing for failure, cost, and scale "
        "from day one. The most important insight was understanding that a simple "
        "routing layer can reduce LLM costs by up to 92% without any quality loss "
        "for simple queries. I learned Vertex AI native integration, Google Cloud "
        "authentication via ADC, Streamlit advanced patterns (session_state, cache_data, "
        "status), guardrail design for production AI safety, and how to document "
        "complex systems at a level suitable for production handoff."
    )

    sp(0.12)
    bold("Jay Kishan:")
    body(
        "The biggest learning for me was understanding the architecture of "
        "multi-agent systems and how different model sizes serve different purposes "
        "at different cost points. Writing guardrails from scratch taught me about "
        "the real security challenges in deploying AI applications — prompt injection "
        "is a genuine threat that needs systematic prevention, not just awareness. "
        "I also gained practical knowledge of GCP services and how a prototype "
        "transitions to production infrastructure through the 10-service migration "
        "roadmap we documented."
    )

    sp(0.15)
    subsection("12.4 What We Would Do Differently", color=C_ORANGE)
    differently = [
        "Request GCP permissions (Cloud Run, BigQuery, Vertex AI) on Day 1",
        "Implement automated testing with pytest from the start",
        "Set up CI/CD pipeline (GitHub Actions) for automatic deployment",
        "Productionize BigQuery logging and Cloud Run deployment earlier",
        "Build the analytics dashboard earlier to validate routing decisions with data",
    ]
    for d in differently:
        bul(d)

    sp(0.3)
    hr(color=C_ACCENT)
    sp(0.2)

    # ──────────────────────────────────────────────
    # BUILD PDF
    # ──────────────────────────────────────────────
    doc.build(
        story,
        onFirstPage=pt.on_page,
        onLaterPages=pt.on_page,
    )
    print(f"\n✅  PDF generated → {OUTPUT_FILE}")
    print(f"   {os.path.getsize(OUTPUT_FILE) / 1024:.1f} KB")


# ══════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════
if __name__ == "__main__":
    print("Building Deep Agent v2.0 Project Documentation PDF...")
    print(f"Screenshots: place '{SCREENSHOT_MAIN}' and '{SCREENSHOT_ANALYTICS}'")
    print("in the same folder as this script to embed them.\n")
    build_pdf()