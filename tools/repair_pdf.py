# tools/repair_pdf.py
import pikepdf

def repair_pdf(input_path, output_path):
    pdf = pikepdf.open(input_path, allow_overwriting_input=True)
    pdf.save(output_path)
    pdf.close()
