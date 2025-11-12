from PyPDF2 import PdfReader, PdfWriter
import os

def split_selected_pages(input_path, output_path, selected_pages):
    reader = PdfReader(input_path)
    writer = PdfWriter()

    for page_num in selected_pages:
        if 1 <= page_num <= len(reader.pages):
            writer.add_page(reader.pages[page_num - 1])

    with open(output_path, "wb") as f:
        writer.write(f)
