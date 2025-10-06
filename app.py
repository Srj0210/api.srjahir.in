from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import uuid
from docx import Document
from PyPDF2 import PdfMerger, PdfReader
import mammoth  # For Word → PDF accurate conversion
import subprocess

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "API is running",
        "tools": ["word-to-pdf", "merge-pdf", "split-pdf", "text-to-pdf", "pdf-to-word"]
    })


# 🟢 WORD → PDF
@app.route("/word-to-pdf", methods=["POST"])
def word_to_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    original_name = os.path.splitext(file.filename)[0]
    upload_path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}_{file.filename}")
    output_path = os.path.join(OUTPUT_FOLDER, f"{original_name}.pdf")

    file.save(upload_path)

    try:
        # Use LibreOffice for preserving formatting
        subprocess.run([
            "libreoffice", "--headless", "--convert-to", "pdf", "--outdir", OUTPUT_FOLDER, upload_path
        ], check=True)

        # Clean up uploaded file
        os.remove(upload_path)

        # Rename output with original filename if needed
        generated_pdf = os.path.join(OUTPUT_FOLDER, f"{os.path.splitext(os.path.basename(upload_path))[0]}.pdf")
        if os.path.exists(generated_pdf) and generated_pdf != output_path:
            os.rename(generated_pdf, output_path)

        return send_file(output_path, as_attachment=True, download_name=f"{original_name}.pdf")

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 🟢 TEXT → PDF
@app.route("/text-to-pdf", methods=["POST"])
def text_to_pdf():
    text = request.form.get("text", "")
    if not text:
        return jsonify({"error": "No text provided"}), 400

    pdf_filename = f"{uuid.uuid4()}.pdf"
    pdf_path = os.path.join(OUTPUT_FOLDER, pdf_filename)

    from fpdf import FPDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, text)
    pdf.output(pdf_path)

    return send_file(pdf_path, as_attachment=True, download_name="text_output.pdf")


# 🟢 MERGE PDF
@app.route("/merge-pdf", methods=["POST"])
def merge_pdf():
    files = request.files.getlist("files")
    if not files:
        return jsonify({"error": "No files uploaded"}), 400

    merger = PdfMerger()
    for file in files:
        path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}.pdf")
        file.save(path)
        merger.append(path)

    merged_pdf = os.path.join(OUTPUT_FOLDER, f"merged_{uuid.uuid4()}.pdf")
    merger.write(merged_pdf)
    merger.close()

    for file in os.listdir(UPLOAD_FOLDER):
        os.remove(os.path.join(UPLOAD_FOLDER, file))

    return send_file(merged_pdf, as_attachment=True, download_name="merged.pdf")


# 🟢 PDF → WORD
@app.route("/pdf-to-word", methods=["POST"])
def pdf_to_word():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    upload_path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}.pdf")
    output_path = os.path.join(OUTPUT_FOLDER, f"{uuid.uuid4()}.docx")
    file.save(upload_path)

    try:
        # Convert via libreoffice again
        subprocess.run([
            "libreoffice", "--headless", "--convert-to", "docx", "--outdir", OUTPUT_FOLDER, upload_path
        ], check=True)

        os.remove(upload_path)
        return send_file(output_path, as_attachment=True, download_name="converted.docx")

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Allow OPTIONS request
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    return response


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")