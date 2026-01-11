import subprocess
import os
import shutil
import tempfile

def excel_to_pdf(input_path, output_path):
    """
    Converts Excel → PDF using LibreOffice (Best Quality)
    Works for Gujarati, Hindi, Marathi, all Indic languages.
    Zero crashes on Render.
    """

    temp_dir = tempfile.mkdtemp(dir="/tmp")

    try:
        # Copy input to temp folder (LibreOffice requirement)
        local_input = os.path.join(temp_dir, os.path.basename(input_path))
        shutil.copy(input_path, local_input)

        # LibreOffice headless conversion
        cmd = [
            "libreoffice",
            "--headless",
            "--nologo",
            "--nofirststartwizard",
            "--convert-to", "pdf",
            "--outdir", temp_dir,
            local_input
        ]

        subprocess.run(cmd, check=True)

        # Find generated PDF
        generated_pdf = local_input.replace(".xlsx", ".pdf").replace(".xls", ".pdf")

        # Move to final output
        shutil.move(generated_pdf, output_path)

    except Exception as e:
        raise RuntimeError(f"Excel to PDF conversion failed: {str(e)}")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
