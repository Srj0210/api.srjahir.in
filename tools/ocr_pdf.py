import os
import tempfile
from PIL import Image
import pytesseract
import pypdfium2 as pdfium

pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

def ocr_pdf(input_path, output_path, output_type="text"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    ext = input_path.lower().split(".")[-1]
    pages = []

    if ext in ["jpg", "jpeg", "png", "bmp", "webp"]:
        pages = [Image.open(input_path)]

    else:
        pdf = pdfium.PdfDocument(input_path)
        n = len(pdf)

        for i in range(n):
            page = pdf[i]
            pil = page.render(scale=2).to_pil()
            pages.append(pil)

    if output_type == "text":
        extracted = []
        for img in pages:
            extracted.append(pytesseract.image_to_string(img))

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n\n--- PAGE BREAK ---\n\n".join(extracted))

    else:
        from PyPDF2 import PdfMerger
        merger = PdfMerger()

        with tempfile.TemporaryDirectory() as tmp:
            for idx, img in enumerate(pages):
                pdf_bytes = pytesseract.image_to_pdf_or_hocr(img, extension="pdf")
                temp_page = os.path.join(tmp, f"{idx}.pdf")
                with open(temp_page, "wb") as f:
                    f.write(pdf_bytes)
                merger.append(temp_page)

            merger.write(output_path)
            merger.close()

def run_ocr(input_path, output_path, output_type="text"):
    return ocr_pdf(input_path, output_path, output_type)
