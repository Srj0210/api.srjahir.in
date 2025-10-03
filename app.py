from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PyPDF2 import PdfMerger, PdfReader
from fpdf import FPDF
from docx import Document
import os
import uuid

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "API is running", "tools": ["word-to-pdf", "merge-pdf", "split-pdf", "text-to-pdf", "pdf-to-word"]})


# 🟢 Word → PDF
@app.route("/word-to-pdf", methods=["POST"])
def word_to_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    filename = str(uuid.uuid4()) + ".docx"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    document = Document(filepath)
    pdf_filename = str(uuid.uuid4()) + ".pdf"
    pdf_path = os.path.join(OUTPUT_FOLDER, pdf_filename)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for para in document.paragraphs:
        pdf.multi_cell(0, 10, para.text)
    pdf.output(pdf_path)

    return send_file(pdf_path, as_attachment=True)


# 🟢 Text → PDF
@app.route("/text-to-pdf", methods=["POST"])
def text_to_pdf():
    text = request.form.get("text", "")
    if not text:
        return jsonify({"error": "No text provided"}), 400

    pdf_filename = str(uuid.uuid4()) + ".pdf"
    pdf_path = os.path.join(OUTPUT_FOLDER, pdf_filename)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, text)
    pdf.output(pdf_path)

    return send_file(pdf_path, as_attachment=True)


# 🟢 Merge PDF
@app.route("/merge-pdf", methods=["POST"])
def merge_pdf():
    files = request.files.getlist("files")
    if not files:
        return jsonify({"error": "No files uploaded"}), 400

    merger = PdfMerger()
    for file in files:
        filepath = os.path.join(UPLOAD_FOLDER, str(uuid.uuid4()) + ".pdf")
        file.save(filepath)
        merger.append(filepath)

    pdf_filename = str(uuid.uuid4()) + ".pdf"
    pdf_path = os.path.join(OUTPUT_FOLDER, pdf_filename)
    merger.write(pdf_path)
    merger.close()

    return send_file(pdf_path, as_attachment=True)


# 🟢 Split PDF
@app.route("/split-pdf", methods=["POST"])
def split_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    filepath = os.path.join(UPLOAD_FOLDER, str(uuid.uuid4()) + ".pdf")
    file.save(filepath)

    reader = PdfReader(filepath)
    output_files = []

    for i, page in enumerate(reader.pages):
        pdf_filename = f"{uuid.uuid4()}_{i+1}.pdf"
        pdf_path = os.path.join(OUTPUT_FOLDER, pdf_filename)

        writer = PdfMerger()
        writer.append(filepath, pages=(i, i+1))
        writer.write(pdf_path)
        writer.close()

        output_files.append(pdf_path)

    return jsonify({"message": "PDF Split Successful", "files": output_files})


# 🟢 PDF → Word (basic text extraction)
@app.route("/pdf-to-word", methods=["POST"])
def pdf_to_word():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    filepath = os.path.join(UPLOAD_FOLDER, str(uuid.uuid4()) + ".pdf")
    file.save(filepath)

    reader = PdfReader(filepath)
    doc = Document()

    for page in reader.pages:
        text = page.extract_text()
        doc.add_paragraph(text if text else "")

    word_filename = str(uuid.uuid4()) + ".docx"
    word_path = os.path.join(OUTPUT_FOLDER, word_filename)
    doc.save(word_path)

    return send_file(word_path, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
