import os
import tempfile
from pdf2image import convert_from_path
from PIL import Image
import pytesseract

# Force tesseract binary path for Render
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"
os.environ["PATH"] += ":/usr/bin:/usr/local/bin"

def ocr_pdf(input_path: str, output_path: str, output_type: str = "text", dpi: int = 300):

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    # Detect if input is image instead of PDF
    file_ext = input_path.lower().split(".")[-1]

    with tempfile.TemporaryDirectory() as tmpdir:
        try:

            # If IMAGE → load directly
            if file_ext in ["jpg", "jpeg", "png", "webp", "bmp"]:
                pages = [Image.open(input_path)]
            else:
                # If PDF → convert pages
                pages = convert_from_path(input_path, dpi=dpi, output_folder=tmpdir, fmt='png')

            if not pages:
                raise RuntimeError("No pages extracted from file")

            # TEXT OUTPUT
            if output_type == "text":
                full_text = []
                for img in pages:
                    txt = pytesseract.image_to_string(img)
                    full_text.append(txt)

                with open(output_path, "w", encoding="utf-8") as f:
                    f.write("\n\n--- PAGE BREAK ---\n\n".join(full_text))

            else:
                # SEARCHABLE PDF OUTPUT
                pdf_bytes_list = []
                for img in pages:
                    pdf_bytes = pytesseract.image_to_pdf_or_hocr(img, extension='pdf')
                    pdf_bytes_list.append(pdf_bytes)

                from PyPDF2 import PdfMerger
                merger = PdfMerger()

                for i, b in enumerate(pdf_bytes_list):
                    temp_page = os.path.join(tmpdir, f"page_{i}.pdf")
                    with open(temp_page, "wb") as f:
                        f.write(b)
                    merger.append(temp_page)

                merger.write(output_path)
                merger.close()

        except Exception as e:
            raise RuntimeError(f"OCR processing failed: {e}") from e


def run_ocr(input_path, output_path, output_type="text", dpi=300):
    return ocr_pdf(input_path, output_path, output_type, dpi)
