from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color
from reportlab.lib.pagesizes import A4
import tempfile
from PIL import Image


def add_text_watermark(input_pdf, output_pdf, text):
    reader = PdfReader(input_pdf)
    writer = PdfWriter()

    for page in reader.pages:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            c = canvas.Canvas(tmp.name, pagesize=A4)
            w, h = A4

            c.setFillColor(Color(1, 1, 1, alpha=0.15))
            c.setFont("Helvetica-Bold", 42)

            c.saveState()
            c.translate(w / 2, h / 2)
            c.rotate(45)
            c.drawCentredString(0, 0, text)
            c.restoreState()

            c.save()

            watermark = PdfReader(tmp.name)
            page.merge_page(watermark.pages[0])

        writer.add_page(page)

    with open(output_pdf, "wb") as f:
        writer.write(f)


def add_image_watermark(input_pdf, output_pdf, image_path):
    reader = PdfReader(input_pdf)
    writer = PdfWriter()

    img = Image.open(image_path)
    img_width, img_height = img.size

    for page in reader.pages:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            c = canvas.Canvas(tmp.name, pagesize=A4)
            w, h = A4

            scale = 0.4
            c.saveState()
            c.translate(w / 2, h / 2)
            c.rotate(30)
            c.setFillAlpha(0.2)
            c.drawImage(
                image_path,
                -img_width * scale / 2,
                -img_height * scale / 2,
                img_width * scale,
                img_height * scale,
                mask="auto"
            )
            c.restoreState()
            c.save()

            watermark = PdfReader(tmp.name)
            page.merge_page(watermark.pages[0])

        writer.add_page(page)

    with open(output_pdf, "wb") as f:
        writer.write(f)