import os
import zipfile
import tempfile
import pypdfium2 as pdfium
from PIL import Image


def pdf_to_jpg(input_pdf_path: str, output_zip_path: str):
    """
    Convert PDF pages to JPG images
    Render-safe, fast, no Ghostscript
    """

    images = []
    pdf = pdfium.PdfDocument(input_pdf_path)
    page_indices = list(range(len(pdf)))

    renderer = pdf.render_to(
        pdfium.BitmapConv.pil_image,
        page_indices=page_indices,
        scale=2  # good quality
    )

    with tempfile.TemporaryDirectory() as tmp:
        for i, img in zip(page_indices, renderer):
            img_path = os.path.join(tmp, f"page_{i+1}.jpg")
            img.save(img_path, "JPEG", quality=90)
            images.append(img_path)

        # ZIP all images
        with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for img_path in images:
                zipf.write(img_path, os.path.basename(img_path))

    return output_zip_path
