import os
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color
from reportlab.lib.pagesizes import A4
import tempfile


def add_watermark(input_pdf_path: str, output_pdf_path: str, watermark_text: str):
    """
    Add text watermark to PDF (center, light opacity)
    Lossless & secure
    """

    reader = PdfReader(input_pdf_path)
    writer = PdfWriter()

    for page in reader.pages:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            c = canvas.Canvas(tmp.name, pagesize=A4)

            width, height = A4

            # Light transparent color
            c.setFillColor(Color(0.3, 0.3, 0.3, alpha=0.15))
            c.setFont("Helvetica-Bold", 40)

            c.saveState()
            c.translate(width / 2, height / 2)
            c.rotate(45)
            c.drawCentredString(0, 0, watermark_text)
            c.restoreState()

            c.save()

            watermark_pdf = PdfReader(tmp.name)
            page.merge_page(watermark_pdf.pages[0])

        writer.add_page(page)

    with open(output_pdf_path, "wb") as f:
        writer.write(f)