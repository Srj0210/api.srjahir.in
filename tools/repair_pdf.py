import subprocess
import pikepdf
import os

def repair_pdf(input_path, output_path):

    temp_fixed = input_path.replace(".pdf", "_fixed.pdf")

    # Step 1: Use qpdf to rebuild broken xref tables
    try:
        subprocess.run([
            "qpdf", "--repair",
            input_path,
            temp_fixed
        ], check=True)
    except:
        # if qpdf fails → no hope
        raise Exception("Unable to repair structure")

    # Step 2: Use pikepdf to sanitize content
    try:
        pdf = pikepdf.open(temp_fixed, allow_overwriting_input=True)
        pdf.save(output_path)
        pdf.close()
    except:
        raise Exception("Unable to rewrite repaired PDF")

    # Cleanup
    if os.path.exists(temp_fixed):
        os.remove(temp_fixed)
