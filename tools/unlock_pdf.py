import os
from PyPDF2 import PdfReader, PdfWriter

def unlock_pdf(input_pdf_path: str, output_pdf_path: str, password: str):
    reader = PdfReader(input_pdf_path)

    if reader.is_encrypted:
        if not reader.decrypt(password):
            raise RuntimeError("Invalid password")

    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    with open(output_pdf_path, "wb") as f:
        writer.write(f)

    return output_pdf_path