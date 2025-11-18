import subprocess
import os

def repair_pdf(input_path, output_path):
    temp_fixed = input_path.replace(".pdf", "_gs_fixed.pdf")

    try:
        subprocess.run([
            "gs",
            "-o", temp_fixed,
            "-sDEVICE=pdfwrite",
            "-dPDFSETTINGS=/prepress",
            "-dNOPAUSE",
            "-dBATCH",
            "-dQUIET",
            input_path
        ], check=True)

    except Exception:
        raise Exception("Ghostscript repair failed")

    if os.path.exists(temp_fixed):
        os.rename(temp_fixed, output_path)
    else:
        raise Exception("Output not generated")
