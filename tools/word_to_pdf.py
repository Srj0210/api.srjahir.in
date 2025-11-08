import subprocess, tempfile, shutil, os

def word_to_pdf(input_docx_path, output_pdf_path):
    """
    Convert Word (.doc / .docx) to PDF using LibreOffice.
    Works in Render Linux environment with headless mode.
    """
    try:
        temp_dir = tempfile.mkdtemp(dir="/tmp")

        subprocess.run([
            "libreoffice",
            "--headless",
            "--convert-to", "pdf",
            "--outdir", temp_dir,
            input_docx_path
        ], check=True)

        files = [f for f in os.listdir(temp_dir) if f.lower().endswith(".pdf")]
        if not files:
            raise RuntimeError("Conversion failed: No PDF generated")

        shutil.move(os.path.join(temp_dir, files[0]), output_pdf_path)

    except subprocess.CalledProcessError:
        raise RuntimeError("LibreOffice conversion failed — check DOCX integrity")
    except Exception as e:
        raise RuntimeError(f"Conversion error: {e}")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)