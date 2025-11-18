# tools/ocr_pdf.py
import os
import tempfile
from pdf2image import convert_from_path
from PIL import Image
import pytesseract

def ocr_pdf(input_path: str, output_path: str, output_type: str = "text", dpi: int = 300):
    """
    Run OCR on input_path (PDF) and write either plain text or searchable PDF to output_path.
    output_type: "text" or "pdf"
    """
    # Ensure output dir exists
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    # Temporary folder for images
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            # Convert PDF pages to images
            pages = convert_from_path(input_path, dpi=dpi, output_folder=tmpdir, fmt='png')
            if not pages:
                raise RuntimeError("No pages extracted from PDF")

            if output_type == "text":
                full_text = []
                for i, img in enumerate(pages):
                    # pytesseract image_to_string
                    txt = pytesseract.image_to_string(img)
                    full_text.append(txt)
                # join and save
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write("\n\n--- PAGE BREAK ---\n\n".join(full_text))

            else:  # output_type == "pdf" -> create searchable PDF
                # For each page, produce hocr or PDF bytes and combine
                pdf_bytes_list = []
                for img in pages:
                    # image_to_pdf_or_hocr returns bytes for pdf when lang/model used
                    pdf_bytes = pytesseract.image_to_pdf_or_hocr(img, extension='pdf')
                    pdf_bytes_list.append(pdf_bytes)

                # Combine page PDFs into single pdf using PyPDF (Pillow can't merge PDFs)
                try:
                    from PyPDF2 import PdfMerger
                except Exception as e:
                    raise RuntimeError("PyPDF2 is required to merge PDFs. Add 'PyPDF2' to requirements.") from e

                merger = PdfMerger()
                for i, b in enumerate(pdf_bytes_list):
                    # write each page bytes into temp file then append
                    page_temp = os.path.join(tmpdir, f"page_{i}.pdf")
                    with open(page_temp, "wb") as f:
                        f.write(b)
                    merger.append(page_temp)

                merger.write(output_path)
                merger.close()

        except Exception as e:
            # bubble up useful error
            raise RuntimeError(f"OCR processing failed: {e}") from e
