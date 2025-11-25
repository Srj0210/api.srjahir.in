import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, PageBreak
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os


# Register a full Unicode font (Gujarati, Hindi, Tamil etc.)
FONT_PATH = "/usr/share/fonts/truetype/noto/NotoSans.ttf"
pdfmetrics.registerFont(TTFont("NotoSans", FONT_PATH))


def excel_to_pdf(input_path, output_path):
    # Load Excel using pandas
    df = pd.read_excel(input_path)

    # Convert to list of lists for ReportLab table
    data = [df.columns.tolist()] + df.values.tolist()

    # PDF document
    pdf = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=20,
        rightMargin=20,
        topMargin=30,
        bottomMargin=30
    )

    # Auto column width calculation
    max_col_chars = df.astype(str).applymap(len).max()
    col_widths = [(c * 7) + 30 for c in max_col_chars]

    # Create table
    table = Table(data, colWidths=col_widths)

    # Basic professional table style (white background)
    style = TableStyle([
        ("FONT", (0, 0), (-1, -1), "NotoSans", 9),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
    ])

    table.setStyle(style)

    pdf.build([table])
