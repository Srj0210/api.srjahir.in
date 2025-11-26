# tools/html_to_pdf.py

from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
import os

FONT_PATH = "/usr/share/fonts/truetype/noto/NotoSans.ttf"
pdfmetrics.registerFont(TTFont("NotoSans", FONT_PATH))

def html_to_pdf(html_path, output_path):
    with open(html_path, "r", encoding="utf-8") as f:
        html_data = f.read()

    pdf = SimpleDocTemplate(output_path, pagesize=A4)

    styles = getSampleStyleSheet()
    normal = ParagraphStyle(
        "normal",
        parent=styles["Normal"],
        fontName="NotoSans",
        fontSize=11,
        leading=15,
        alignment=TA_LEFT,
    )

    story = [Paragraph(html_data.replace("\n", "<br/>"), normal)]
    pdf.build(story)
