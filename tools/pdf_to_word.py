import os
from pdf2docx import Converter

def pdf_to_word(input_pdf_path, output_docx_path):
    """
    Convert PDF to editable Word (DOCX) file using pdf2docx.
    """
    try:
        cv = Converter(input_pdf_path)
        cv.convert(output_docx_path, start=0, end=None)
        cv.close()
    except Exception as e:
        raise RuntimeError(f"PDF to Word conversion failed: {e}")