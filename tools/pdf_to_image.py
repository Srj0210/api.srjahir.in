import os
import zipfile
import tempfile
from PIL import Image
import pypdfium2 as pdfium


def pdf_to_image(input_pdf_path: str, output_zip_path: str):
    """
    Convert PDF pages to JPG images and return a ZIP file.
    Render-safe, fast, no poppler, no ghostscript.
    """

    with tempfile.TemporaryDirectory() as tmpdir:
        pdf = pdfium.PdfDocument(input_pdf_path)

        image_paths = []

        for i, page in enumerate(pdf):
            # Render page to image
            pil_image = page.render(scale=2).to_pil()

            img_path = os.path.join(tmpdir, f"page_{i + 1}.jpg")
            pil_image.save(img_path, "JPEG", quality=95)

            image_paths.append(img_path)

        # Create ZIP
        with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for img in image_paths:
                zipf.write(img, arcname=os.path.basename(img))

    return output_zip_path
