import subprocess
import os
import shutil
import tempfile


def excel_to_pdf(input_path: str, output_path: str):
    """
    Convert Excel → PDF using LibreOffice (Headless)

    ✔ Best quality
    ✔ Works with Gujarati / Hindi / Marathi / Indic fonts
    ✔ Render-safe
    ✔ No memory leak
    """

    # Create temp working directory (Render allows /tmp)
    temp_dir = tempfile.mkdtemp(dir="/tmp")

    try:
        # ---- 1. Copy Excel file to temp (LibreOffice requirement)
        input_filename = os.path.basename(input_path)
        local_input = os.path.join(temp_dir, input_filename)
        shutil.copy(input_path, local_input)

        # ---- 2. LibreOffice headless command
        cmd = [
            "libreoffice",
            "--headless",
            "--nologo",
            "--nofirststartwizard",
            "--convert-to", "pdf",
            "--outdir", temp_dir,
            local_input
        ]

        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # ---- 3. Detect generated PDF
        base_name, _ = os.path.splitext(input_filename)
        generated_pdf = os.path.join(temp_dir, f"{base_name}.pdf")

        if not os.path.exists(generated_pdf):
            raise RuntimeError("LibreOffice did not generate PDF")

        # ---- 4. Move PDF to final output path
        shutil.move(generated_pdf, output_path)

        return output_path

    except subprocess.CalledProcessError:
        raise RuntimeError("LibreOffice failed to convert Excel to PDF")

    except Exception as e:
        raise RuntimeError(f"Excel to PDF conversion failed: {str(e)}")

    finally:
        # ---- 5. Cleanup temp files (IMPORTANT for Render)
        shutil.rmtree(temp_dir, ignore_errors=True)
