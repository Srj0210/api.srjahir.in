from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from fpdf import FPDF
from docx import Document
import os
import uuid

app = Flask(__name__)
CORS(app)

# ✅ Render safe temporary folders
UPLOAD_FOLDER = "/tmp/uploads"
OUTPUT_FOLDER = "/tmp/outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "API is running",
        "tools": ["word-to-pdf", "text-to-pdf", "merge-pdf", "split-pdf", "pdf-to-word"]
    })


# 🟢 Word → PDF
@app.route("/word-to-pdf", methods=["POST"])
def word_to_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    filepath = os.path.join(UPLOAD_FOLDER, str(uuid.uuid4()) + ".docx")
    file.save(filepath)

    document = Document(filepath)
    pdf_path = os.path.join(OUTPUT_FOLDER, str(uuid.uuid4()) + ".pdf")

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

    pdf_path = os.path.join(OUTPUT_FOLDER, str(uuid.uuid4()) + ".pdf")

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

    pdf_path = os.path.join(OUTPUT_FOLDER, str(uuid.uuid4()) + ".pdf")
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
        pdf_path = os.path.join(OUTPUT_FOLDER, f"{uuid.uuid4()}_{i+1}.pdf")

        writer = PdfWriter()
        writer.add_page(page)
        with open(pdf_path, "wb") as f:
            writer.write(f)

        output_files.append(pdf_path)

    return jsonify({"message": "PDF Split Successful", "files": output_files})


# 🟢 PDF → Word
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

    word_path = os.path.join(OUTPUT_FOLDER, str(uuid.uuid4()) + ".docx")
    doc.save(word_path)

    return send_file(word_path, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
