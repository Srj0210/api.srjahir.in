import os
import tempfile
from PyPDF2 import PdfMerger

def merge_pdf(input_files, output_path):
    """
    Merge multiple PDFs into one single file.
    """
    try:
        temp_dir = tempfile.mkdtemp(dir="/tmp")
        merger = PdfMerger()
        saved_paths = []

        for file in input_files:
            save_path = os.path.join(temp_dir, file.filename)
            file.save(save_path)
            saved_paths.append(save_path)
            merger.append(save_path)

        merger.write(output_path)
        merger.close()

        # Cleanup temp directory after merging
        for path in saved_paths:
            if os.path.exists(path):
                os.remove(path)
        os.rmdir(temp_dir)

    except Exception as e:
        raise RuntimeError(f"PDF merge failed: {e}")
