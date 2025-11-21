import os
import tempfile
from PIL import Image
import pytesseract
import pypdfium2 as pdfium


pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"


def ocr_pdf(input_path, output_path, output_type="text"):
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    ext = input_path.lower().split(".")[-1]

    # Pages list
    pages = []

    # If IMAGE
    if ext in ["jpg", "jpeg", "png", "bmp", "webp"]:
        pages = [Image.open(input_path)]

    # If PDF → use pypdfium2 (very low RAM usage)
    else:
        pdf = pdfium.PdfDocument(input_path)
        for i in range(len(pdf)):
            page = pdf[i]
            pil_img = page.render(scale=2).to_pil()   # scale=2 → HD OCR
            pages.append(pil_img)

    if output_type == "text":
        full = []
        for img in pages:
            full.append(pytesseract.image_to_string(img))

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n\n--- PAGE BREAK ---\n\n".join(full))

    else:
        from PyPDF2 import PdfMerger
        merger = PdfMerger()

        with tempfile.TemporaryDirectory() as tmpdir:
            for idx, img in enumerate(pages):
                pdf_bytes = pytesseract.image_to_pdf_or_hocr(img, extension='pdf')
                temp_page = os.path.join(tmpdir, f"p{idx}.pdf")
                with open(temp_page, "wb") as f:
                    f.write(pdf_bytes)
                merger.append(temp_page)

            merger.write(output_path)
            merger.close()


def run_ocr(input_path, output_path, output_type="text"):
    return ocr_pdf(input_path, output_path, output_type)
