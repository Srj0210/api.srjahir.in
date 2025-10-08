import os
import subprocess
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from PyPDF2 import PdfMerger
from fpdf import FPDF
from docx import Document
import fitz  # PyMuPDF

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


# ✅ Auto-delete helper
def safe_remove(path):
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        print(f"⚠️ Failed to delete {path}: {e}")


# ✅ Word → PDF
@app.route("/word-to-pdf", methods=["POST"])
def word_to_pdf():
    try:
        file = request.files.get("file")
        if not file:
            return jsonify({"error": "No file uploaded"}), 400

        filename = secure_filename(file.filename)
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(input_path)

        original_name = os.path.splitext(filename)[0]
        output_filename = f"{original_name}.pdf"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)

        # LibreOffice conversion
        subprocess.run([
            "libreoffice", "--headless", "--convert-to", "pdf",
            "--outdir", OUTPUT_FOLDER, input_path
        ], check=True)

        # LibreOffice output path (actual file)
        converted_name = os.path.splitext(filename)[0] + ".pdf"
        converted_path = os.path.join(OUTPUT_FOLDER, converted_name)

        # Rename file (in case LibreOffice named differently)
        if converted_path != output_path and os.path.exists(converted_path):
            os.rename(converted_path, output_path)

        # Delete input file
        safe_remove(input_path)

        # Return + delete output after sending
        response = send_file(output_path, as_attachment=True, download_name=output_filename)
        safe_remove(output_path)
        return response

    except subprocess.CalledProcessError:
        return jsonify({"error": "Conversion failed — LibreOffice not available"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ PDF → Word
@app.route("/pdf-to-word", methods=["POST"])
def pdf_to_word():
    try:
        file = request.files.get("file")
        if not file:
            return jsonify({"error": "No file uploaded"}), 400

        filename = secure_filename(file.filename)
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(input_path)

        output_name = os.path.splitext(filename)[0] + ".docx"
        output_path = os.path.join(OUTPUT_FOLDER, output_name)

        doc = Document()
        pdf = fitz.open(input_path)
        for page in pdf:
            text = page.get_text("text")
            doc.add_paragraph(text)
        doc.save(output_path)

        # Delete input after conversion
        safe_remove(input_path)

        # Send + delete output
        response = send_file(output_path, as_attachment=True, download_name=output_name)
        safe_remove(output_path)
        return response

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ Merge PDF
@app.route("/merge-pdf", methods=["POST"])
def merge_pdf():
    try:
        files = request.files.getlist("files")
        if not files:
            return jsonify({"error": "No files uploaded"}), 400

        merger = PdfMerger()
        temp_files = []

        for file in files:
            filename = secure_filename(file.filename)
            path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(path)
            merger.append(path)
            temp_files.append(path)

        output_path = os.path.join(OUTPUT_FOLDER, "merged.pdf")
        merger.write(output_path)
        merger.close()

        # Delete all input files
        for f in temp_files:
            safe_remove(f)

        # Send + delete output
        response = send_file(output_path, as_attachment=True, download_name="merged.pdf")
        safe_remove(output_path)
        return response

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ Text → PDF
@app.route("/text-to-pdf", methods=["POST"])
def text_to_pdf():
    try:
        text = request.form.get("text", "")
        if not text:
            return jsonify({"error": "No text provided"}), 400

        output_path = os.path.join(OUTPUT_FOLDER, "output.pdf")

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)
        for line in text.split("\n"):
            pdf.multi_cell(0, 10, line)
        pdf.output(output_path)

        response = send_file(output_path, as_attachment=True, download_name="text.pdf")
        safe_remove(output_path)
        return response

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ Root Check
@app.route("/", methods=["GET"])
def home():
    return "✅ SRJahir Tools API running successfully!"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)