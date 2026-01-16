from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import Color
from PIL import Image
import tempfile

def sign_pdf(input_pdf, output_pdf, text=None, image_path=None, position="bottom-right"):
    reader = PdfReader(input_pdf)
    writer = PdfWriter()

    for page in reader.pages:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            c = canvas.Canvas(tmp.name, pagesize=A4)
            w, h = A4

            x, y = {
                "bottom-right": (w - 220, 40),
                "bottom-left": (40, 40),
                "center": (w / 2 - 100, h / 2)
            }.get(position, (w - 220, 40))

            if text:
                c.setFont("Helvetica-Bold", 16)
                c.setFillColor(Color(0, 0, 0, alpha=0.85))
                c.drawString(x, y, text)

            if image_path:
                img = Image.open(image_path)
                iw, ih = img.size
                c.drawImage(image_path, x, y, iw * 0.25, ih * 0.25, mask="auto")

            c.save()
            watermark = PdfReader(tmp.name)
            page.merge_page(watermark.pages[0])

        writer.add_page(page)

    with open(output_pdf, "wb") as f:
        writer.write(f)
