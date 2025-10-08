import os
import subprocess
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from fpdf import FPDF
from docx import Document
import fitz  # PyMuPDF

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


# ✅ Safe file delete
def safe_remove(path):
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        print(f"⚠️ Delete failed for {path}: {e}")


# ✅ WORD → PDF
@app.route("/word-to-pdf", methods=["POST"])
def word_to_pdf():
    try:
        file = request.files.get("file")
        if not file:
            return jsonify({"error": "No file uploaded"}), 400

        filename = secure_filename(file.filename)
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(input_path)

        output_name = os.path.splitext(filename)[0] + ".pdf"
        output_path = os.path.join(OUTPUT_FOLDER, output_name)

        subprocess.run([
            "libreoffice", "--headless", "--convert-to", "pdf",
            "--outdir", OUTPUT_FOLDER, input_path
        ], check=True)

        safe_remove(input_path)
        response = send_file(output_path, as_attachment=True, download_name=output_name)
        safe_remove(output_path)
        return response

    except subprocess.CalledProcessError:
        return jsonify({"error": "Conversion failed – LibreOffice not available"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ PDF → WORD
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

        pdf = fitz.open(input_path)
        doc = Document()

        for page in pdf:
            text = page.get_text("text")
            doc.add_paragraph(text if text.strip() else "[Page is blank or image-only]")
        pdf.close()

        doc.save(output_path)
        safe_remove(input_path)

        response = send_file(output_path, as_attachment=True, download_name=output_name)
        safe_remove(output_path)
        return response
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ MERGE PDFs
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

        for f in temp_files:
            safe_remove(f)

        response = send_file(output_path, as_attachment=True, download_name="merged.pdf")
        safe_remove(output_path)
        return response
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ SPLIT PDF
@app.route("/split-pdf", methods=["POST"])
def split_pdf():
    try:
        file = request.files.get("file")
        start_page = int(request.form.get("start", 1))
        end_page = int(request.form.get("end", 1))

        if not file:
            return jsonify({"error": "No file uploaded"}), 400

        filename = secure_filename(file.filename)
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(input_path)

        reader = PdfReader(input_path)
        writer = PdfWriter()

        # Adjust bounds
        start_page = max(1, start_page)
        end_page = min(len(reader.pages), end_page)

        for i in range(start_page - 1, end_page):
            writer.add_page(reader.pages[i])

        output_name = f"split_{start_page}_to_{end_page}.pdf"
        output_path = os.path.join(OUTPUT_FOLDER, output_name)

        with open(output_path, "wb") as out_file:
            writer.write(out_file)

        safe_remove(input_path)
        response = send_file(output_path, as_attachment=True, download_name=output_name)
        safe_remove(output_path)
        return response
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ TEXT → PDF
@app.route("/text-to-pdf", methods=["POST"])
def text_to_pdf():
    try:
        text = request.form.get("text", "")
        if not text.strip():
            return jsonify({"error": "No text provided"}), 400

        output_path = os.path.join(OUTPUT_FOLDER, "text.pdf")

        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Helvetica", size=12)

        for line in text.splitlines():
            pdf.multi_cell(0, 10, line)

        pdf.output(output_path)
        response = send_file(output_path, as_attachment=True, download_name="text.pdf")
        safe_remove(output_path)
        return response
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ ROOT Endpoint
@app.route("/", methods=["GET"])
def home():
    return "✅ SRJahir Tools API running with Merge + Split + Multi-language support!"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)