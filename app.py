import os
import subprocess
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from PyPDF2 import PdfMerger
from fpdf import FPDF

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


# ✅ Auto-delete after processing
def safe_remove(path):
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        print(f"⚠️ Failed to delete {path}: {e}")


# ✅ Word → PDF (Perfect formatting)
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

        subprocess.run([
            "libreoffice", "--headless", "--convert-to", "pdf",
            "--outdir", OUTPUT_FOLDER, input_path
        ], check=True)

        safe_remove(input_path)

        response = send_file(output_path, as_attachment=True, download_name=output_filename)
        safe_remove(output_path)
        return response

    except subprocess.CalledProcessError:
        return jsonify({"error": "LibreOffice conversion failed"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ PDF → Word (Accurate formatting)
@app.route("/pdf-to-word", methods=["POST"])
def pdf_to_word():
    try:
        file = request.files.get("file")
        if not file:
            return jsonify({"error": "No file uploaded"}), 400

        filename = secure_filename(file.filename)
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(input_path)

        original_name = os.path.splitext(filename)[0]
        output_filename = f"{original_name}.docx"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)

        subprocess.run([
            "libreoffice", "--headless", "--convert-to", "docx",
            "--outdir", OUTPUT_FOLDER, input_path
        ], check=True)

        safe_remove(input_path)

        response = send_file(output_path, as_attachment=True, download_name=output_filename)
        safe_remove(output_path)
        return response

    except subprocess.CalledProcessError:
        return jsonify({"error": "LibreOffice conversion failed"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ Merge PDF (100% Original Quality)
@app.route("/merge-pdf", methods=["POST"])
def merge_pdf():
    try:
        files = request.files.getlist("files")
        if not files or len(files) < 2:
            return jsonify({"error": "Please upload at least 2 PDF files"}), 400

        merger = PdfMerger()
        temp_paths = []

        for file in files:
            filename = secure_filename(file.filename)
            path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(path)
            merger.append(path)
            temp_paths.append(path)

        output_filename = "merged_output.pdf"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)

        merger.write(output_path)
        merger.close()

        # Clean inputs
        for path in temp_paths:
            safe_remove(path)

        # Return merged file
        response = send_file(output_path, as_attachment=True, download_name=output_filename)
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

        output_path = os.path.join(OUTPUT_FOLDER, "text_output.pdf")
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)

        for line in text.split("\n"):
            pdf.multi_cell(0, 10, line)

        pdf.output(output_path)

        response = send_file(output_path, as_attachment=True, download_name="text_output.pdf")
        safe_remove(output_path)
        return response

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/", methods=["GET"])
def home():
    return "✅ SRJahir Tools PRO — All-in-One Accurate Conversion API is Live!"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)