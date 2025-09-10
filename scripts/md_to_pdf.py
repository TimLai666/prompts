from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable

from reportlab.lib import pagesizes
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem, Preformatted
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT


def load_font() -> str:
    """Try to register a Unicode font for CJK; fall back to Helvetica."""
    # Try common fonts available on Windows for zh-TW
    candidates: list[tuple[str, str]] = [
        ("MicrosoftJhengHei", "msjh.ttc"),
        ("MicrosoftJhengHei", "msjh.ttf"),
        ("NotoSansCJK", "NotoSansCJK-Regular.ttc"),
        ("NotoSansTC", "NotoSansTC-Regular.otf"),
    ]
    for family, file in candidates:
        for base in [Path("C:/Windows/Fonts"), Path.cwd() / "fonts", Path.cwd()]:
            p = base / file
            if p.exists():
                try:
                    pdfmetrics.registerFont(TTFont(family, str(p)))
                    return family
                except Exception:
                    continue
    return "Helvetica"


def md_lines(path: Path) -> Iterable[str]:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            yield line.rstrip("\n")


def convert_markdown_to_pdf(md_path: Path, pdf_path: Path) -> None:
    base_font = load_font()

    styles = getSampleStyleSheet()
    normal = ParagraphStyle(
        name="NormalCJK",
        parent=styles["Normal"],
        fontName=base_font,
        fontSize=11,
        leading=15,
        alignment=TA_LEFT,
    )
    h1 = ParagraphStyle(name="H1", parent=normal, fontSize=18, leading=22, spaceAfter=8)
    h2 = ParagraphStyle(name="H2", parent=normal, fontSize=16, leading=20, spaceAfter=6)
    h3 = ParagraphStyle(name="H3", parent=normal, fontSize=14, leading=18, spaceAfter=4)
    code = ParagraphStyle(name="Code", parent=normal, fontName="Courier", fontSize=9, leading=12, backColor=None)

    story: list = []

    def flush_bullets(buf: list[str], indent: int = 12) -> None:
        nonlocal story
        if not buf:
            return
        items = [ListItem(Paragraph(x, normal)) for x in buf]
        story.append(ListFlowable(items, leftIndent=indent))
        story.append(Spacer(1, 4))
        buf.clear()

    bullet_buf: list[str] = []
    in_code = False
    code_buf: list[str] = []

    for raw in md_lines(md_path):
        line = raw.strip("\ufeff")  # strip BOM if any
        if line.startswith("```"):
            if not in_code:
                flush_bullets(bullet_buf)
                in_code = True
                code_buf = []
            else:
                # end code block
                story.append(Preformatted("\n".join(code_buf), code))
                story.append(Spacer(1, 6))
                in_code = False
            continue

        if in_code:
            code_buf.append(raw)
            continue

        if not line:
            flush_bullets(bullet_buf)
            story.append(Spacer(1, 6))
            continue

        if line.startswith("# "):
            flush_bullets(bullet_buf)
            story.append(Paragraph(line[2:], h1))
            continue
        if line.startswith("## "):
            flush_bullets(bullet_buf)
            story.append(Paragraph(line[3:], h2))
            continue
        if line.startswith("### "):
            flush_bullets(bullet_buf)
            story.append(Paragraph(line[4:], h3))
            continue

        if line.startswith(('- ', '* ')):
            bullet_buf.append(line[2:])
            continue

        # naive table handling: keep as preformatted block when line contains pipes
        if "|" in line and ("---" in line or line.count("|") >= 2):
            flush_bullets(bullet_buf)
            story.append(Preformatted(raw, code))
            continue

        # paragraph
        flush_bullets(bullet_buf)
        story.append(Paragraph(line, normal))

    flush_bullets(bullet_buf)

    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=pagesizes.A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=md_path.stem,
    )
    doc.build(story)


def main() -> None:
    docs_dir = Path("docs")
    out_dir = Path("dist/pdf")
    out_dir.mkdir(parents=True, exist_ok=True)

    md_files = [p for p in docs_dir.glob("*.md")]
    if not md_files:
        print("No Markdown files found in docs/.")
        return
    for md in md_files:
        pdf = out_dir / f"{md.stem}.pdf"
        print(f"Converting {md} -> {pdf}")
        convert_markdown_to_pdf(md, pdf)
    print(f"Done. PDFs at: {out_dir}")


if __name__ == "__main__":
    main()

