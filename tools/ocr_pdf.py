import pytesseract
from pdf2image import convert_from_path
from PIL import Image
from fpdf import FPDF
import os

def run_ocr(input_path, output_path, output_type):

    # Check if file is image or PDF
    ext = os.path.splitext(input_path)[1].lower()

    text_output = ""

    if ext in [".png", ".jpg", ".jpeg", ".webp"]:
        # ---- IMAGE OCR ----
        text_output = pytesseract.image_to_string(Image.open(input_path))

    else:
        # ---- PDF OCR ----
        pages = convert_from_path(input_path)

        for page in pages:
            text_output += pytesseract.image_to_string(page) + "\n\n"

    # ---- OUTPUT TEXT ----
    if output_type == "text":
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text_output)

    # ---- OUTPUT PDF ----
    else:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=10)
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        for line in text_output.split("\n"):
            pdf.multi_cell(0, 8, line)

        pdf.output(output_path)
