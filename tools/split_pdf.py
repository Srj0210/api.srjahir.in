# tools/split_pdf.py
from PyPDF2 import PdfReader, PdfWriter

def split_selected_pages(input_path: str, output_path: str, pages):
    """
    pages: iterable of ints (1-based page numbers)
    """
    reader = PdfReader(input_path)
    writer = PdfWriter()
    total = len(reader.pages)

    for p in pages:
        try:
            pi = int(p)
        except:
            continue
        if 1 <= pi <= total:
            writer.add_page(reader.pages[pi - 1])

    with open(output_path, "wb") as f:
        writer.write(f)
