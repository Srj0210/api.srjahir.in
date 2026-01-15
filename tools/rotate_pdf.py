import os
from PyPDF2 import PdfReader, PdfWriter


def rotate_pdf(input_path: str, output_path: str, rotation: int):
    """
    Rotate all pages of a PDF by given degrees.
    rotation: 90 | 180 | 270
    """

    if rotation not in [90, 180, 270]:
        raise ValueError("Invalid rotation angle")

    reader = PdfReader(input_path)
    writer = PdfWriter()

    for page in reader.pages:
        page.rotate(rotation)
        writer.add_page(page)

    with open(output_path, "wb") as f:
        writer.write(f)

    return output_path