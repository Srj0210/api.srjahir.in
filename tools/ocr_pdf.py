import subprocess
import os
import tempfile

def ocr_pdf(input_path, output_path):
    # Temporary TXT output inside /tmp
    temp_txt = input_path.replace(".pdf", "_ocr.txt")

    try:
        # Step 1: Run Tesseract OCR
        subprocess.run([
            "tesseract",
            input_path,
            temp_txt.replace(".txt", ""),   # Tesseract removes .txt automatically
            "-l", "eng",                    # English OCR
            "--oem", "1",                   # LSTM OCR Engine
            "--psm", "3"                    # Automatic page segmentation
        ], check=True)

    except Exception:
        raise Exception("OCR failed while processing PDF")

    # Step 2: Move output file to final path
    final_txt = temp_txt
    if os.path.exists(final_txt):
        os.rename(final_txt, output_path)
    else:
        raise Exception("OCR output not generated")
