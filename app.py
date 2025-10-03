from flask import Flask, request, send_file
from werkzeug.utils import secure_filename
from fpdf import FPDF
import os
from PyPDF2 import PdfMerger

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def home():
    return {"status": "API is running", "tools": ["word-to-pdf", "merge-pdf"]}

# Text/Word → PDF (simple demo with .txt)
@app.route('/word-to-pdf', methods=['POST'])
def word_to_pdf():
    if 'file' not in request.files:
        return {"error": "No file uploaded"}, 400

    file = request.files['file']
    filename = secure_filename(file.filename)
    path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(path)

    # Convert txt to PDF (demo)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            pdf.multi_cell(0, 10, line)

    output_file = os.path.join(UPLOAD_FOLDER, filename + ".pdf")
    pdf.output(output_file)

    return send_file(output_file, as_attachment=True)

# Merge multiple PDFs
@app.route('/merge-pdf', methods=['POST'])
def merge_pdf():
    files = request.files.getlist("files")
    if not files:
        return {"error": "No PDFs uploaded"}, 400

    merger = PdfMerger()
    for f in files:
        filename = secure_filename(f.filename)
        path = os.path.join(UPLOAD_FOLDER, filename)
        f.save(path)
        merger.append(path)

    output_file = os.path.join(UPLOAD_FOLDER, "merged.pdf")
    merger.write(output_file)
    merger.close()

    return send_file(output_file, as_attachment=True)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
