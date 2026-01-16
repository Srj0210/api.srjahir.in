from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import tempfile
from PIL import Image

def sign_pdf(
    input_pdf, output_pdf,
    text=None, image_path=None,
    page_mode="all", page=None,
    position_mode="same",
    x=0.1, y=0.1, w=0.3, h=0.15
):
    reader = PdfReader(input_pdf)
    writer = PdfWriter()

    for i, page_obj in enumerate(reader.pages):
        apply = (
            page_mode == "all" or
            (page_mode == "single" and i == page-1)
        )

        if apply:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                c = canvas.Canvas(tmp.name, pagesize=A4)
                pw, ph = A4

                rx = x * pw
                ry = y * ph
                rw = w * pw
                rh = h * ph

                if image_path:
                    c.drawImage(image_path, rx, ry, rw, rh, mask="auto")
                elif text:
                    c.setFont("Helvetica-Bold", 20)
                    c.drawString(rx, ry, text)

                c.save()
                overlay = PdfReader(tmp.name)
                page_obj.merge_page(overlay.pages[0])

        writer.add_page(page_obj)

    with open(output_pdf, "wb") as f:
        writer.write(f)