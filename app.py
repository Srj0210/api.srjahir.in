from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PyPDF2 import PdfMerger, PdfReader
from fpdf import FPDF
from docx import Document
import os
import uuid
import traceback

app = Flask(__name__)
CORS(app)

# Use /tmp for Render
UPLOAD_FOLDER = "/tmp/uploads"
OUTPUT_FOLDER = "/tmp/outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "API is running (DEBUG MODE)",
        "tools": ["word-to-pdf", "merge-pdf", "split-pdf", "text-to-pdf", "pdf-to-word"]
    })


# Error handler to log full traceback
@app.errorhandler(Exception)
def handle_exception(e):
    error_message = "".join(traceback.format_exception(type(e), e, e.__traceback__))
    print("🔥 ERROR TRACEBACK 🔥\n", error_message)
    return jsonify({"error": str(e), "traceback": error_message}), 500


# 🟢 Word → PDF
@app.route("/word-to-pdf", methods=["POST"])
def word_to_pdf():
    print("📥 Word to PDF request received")

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    filename = str(uuid.uuid4()) + ".docx"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    print(f"✅ File saved: {filepath}")

    document = Document(filepath)
    pdf_filename = str(uuid.uuid4()) + ".pdf"
    pdf_path = os.path.join(OUTPUT_FOLDER, pdf_filename)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for para in document.paragraphs:
        pdf.multi_cell(0, 10, para.text)
    pdf.output(pdf_path)
    print(f"✅ PDF generated: {pdf_path}")

    return send_file(pdf_path, as_attachment=True)


# 🟢 Text → PDF
@app.route("/text-to-pdf", methods=["POST"])
def text_to_pdf():
    print("📥 Text to PDF request received")
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
    print(f"✅ Text PDF generated: {pdf_path}")

    return send_file(pdf_path, as_attachment=True)


# 🟢 Merge PDF
@app.route("/merge-pdf", methods=["POST"])
def merge_pdf():
    print("📥 Merge PDF request received")
    files = request.files.getlist("files")
    if not files:
        return jsonify({"error": "No files uploaded"}), 400

    merger = PdfMerger()
    for file in files:
        filepath = os.path.join(UPLOAD_FOLDER, str(uuid.uuid4()) + ".pdf")
        file.save(filepath)
        merger.append(filepath)
        print(f"✅ Added to merger: {filepath}")

    pdf_filename = str(uuid.uuid4()) + ".pdf"
    pdf_path = os.path.join(OUTPUT_FOLDER, pdf_filename)
    merger.write(pdf_path)
    merger.close()
    print(f"✅ Merged PDF saved: {pdf_path}")

    return send_file(pdf_path, as_attachment=True)


# 🟢 Split PDF
@app.route("/split-pdf", methods=["POST"])
def split_pdf():
    print("📥 Split PDF request received")
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    filepath = os.path.join(UPLOAD_FOLDER, str(uuid.uuid4()) + ".pdf")
    file.save(filepath)
    print(f"✅ File saved for splitting: {filepath}")

    reader = PdfReader(filepath)
    output_files = []

    for i, page in enumerate(reader.pages):
        pdf_filename = f"{uuid.uuid4()}_{i+1}.pdf"
        pdf_path = os.path.join(OUTPUT_FOLDER, pdf_filename)

        merger = PdfMerger()
        merger.append(filepath, pages=(i, i+1))
        merger.write(pdf_path)
        merger.close()

        output_files.append(pdf_path)
        print(f"✅ Page {i+1} saved: {pdf_path}")

    return jsonify({"message": "PDF Split Successful", "files": output_files})


# 🟢 PDF → Word
@app.route("/pdf-to-word", methods=["POST"])
def pdf_to_word():
    print("📥 PDF to Word request received")
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    filepath = os.path.join(UPLOAD_FOLDER, str(uuid.uuid4()) + ".pdf")
    file.save(filepath)
    print(f"✅ PDF file saved: {filepath}")

    reader = PdfReader(filepath)
    doc = Document()

    for page in reader.pages:
        text = page.extract_text()
        doc.add_paragraph(text if text else "")

    word_filename = str(uuid.uuid4()) + ".docx"
    word_path = os.path.join(OUTPUT_FOLDER, word_filename)
    doc.save(word_path)
    print(f"✅ Word file generated: {word_path}")

    return send_file(word_path, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
