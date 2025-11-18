import os
import subprocess
from PIL import Image
import pytesseract

def ocr_process(input_path, output_path, output_type="text"):
    filename, ext = os.path.splitext(input_path)

    # If input is image - open directly
    if ext.lower() in [".jpg", ".jpeg", ".png"]:
        image = Image.open(input_path)

        if output_type == "text":
            text = pytesseract.image_to_string(image)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(text)
            return

        elif output_type == "pdf":
            pytesseract.image_to_pdf_or_hocr(image, extension='pdf')
            pdf_bytes = pytesseract.image_to_pdf_or_hocr(image, extension='pdf')
            with open(output_path, "wb") as f:
                f.write(pdf_bytes)
            return

    # If input is PDF → run OCR on full PDF
    if ext.lower() == ".pdf":
        if output_type == "pdf":
            # Convert scanned PDF → searchable PDF
            subprocess.run([
                "tesseract",
                input_path,
                filename,
                "pdf"
            ], check=True)
            os.rename(filename + ".pdf", output_path)
            return

        elif output_type == "text":
            # Extract raw text from scanned PDF
            text = subprocess.check_output([
                "tesseract",
                input_path,
                "stdout"
            ], encoding="utf-8", errors="ignore")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(text)
            return

    raise Exception("Unsupported file format")
