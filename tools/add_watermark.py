from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color
from reportlab.lib.pagesizes import A4
import tempfile
from PIL import Image

def _draw_position(c, w, h, position):
    if position == "center":
        return w/2, h/2, 0
    if position == "bottom-right":
        return w-120, 80, 0
    return w/2, h/2, 45   # diagonal default

def add_text_watermark(input_pdf, output_pdf, text, position):
    reader = PdfReader(input_pdf)
    writer = PdfWriter()

    for page in reader.pages:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            c = canvas.Canvas(tmp.name, pagesize=A4)
            w,h = A4

            x,y,angle = _draw_position(c,w,h,position)
            c.setFillColor(Color(1,1,1,alpha=0.15))
            c.setFont("Helvetica-Bold", 42)

            c.saveState()
            c.translate(x,y)
            c.rotate(angle)
            c.drawCentredString(0,0,text)
            c.restoreState()
            c.save()

            page.merge_page(PdfReader(tmp.name).pages[0])
        writer.add_page(page)

    with open(output_pdf,"wb") as f:
        writer.write(f)

def add_image_watermark(input_pdf, output_pdf, image_path, position):
    reader = PdfReader(input_pdf)
    writer = PdfWriter()
    img = Image.open(image_path)
    iw, ih = img.size

    for page in reader.pages:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            c = canvas.Canvas(tmp.name, pagesize=A4)
            w,h = A4
            x,y,angle = _draw_position(c,w,h,position)

            scale = 0.35
            c.saveState()
            c.translate(x,y)
            c.rotate(angle)
            c.setFillAlpha(0.2)
            c.drawImage(image_path, -iw*scale/2, -ih*scale/2,
                        iw*scale, ih*scale, mask="auto")
            c.restoreState()
            c.save()

            page.merge_page(PdfReader(tmp.name).pages[0])
        writer.add_page(page)

    with open(output_pdf,"wb") as f:
        writer.write(f)
