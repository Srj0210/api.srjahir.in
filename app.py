import os
import tempfile
import shutil
from flask import Flask, request, jsonify, send_file, after_this_request
from werkzeug.utils import secure_filename
from flask_cors import CORS

# === Import conversion tools ===
from tools.word_to_pdf import word_to_pdf
from tools.pdf_to_word import pdf_to_word
from tools.merge_pdf import merge_pdf  # ✅ New added import

# === Flask Setup ===
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend (tools.srjahir.in)

UPLOAD_FOLDER = "/tmp/uploads"
OUTPUT_FOLDER = "/tmp/outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# === Root Route ===
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "SRJ Tools API is Live 🚀",
        "status": "ok",
        "routes": [
            "/word-to-pdf",
            "/pdf-to-word",
            "/merge-pdf"
        ]
    })

# === Word → PDF ===
@app.route("/word-to-pdf", methods=["POST"])
def convert_word_to_pdf():
    try:
        file = request.files.get("file")
        if not file:
            return jsonify({"error": "No file uploaded"}), 400

        original_name = os.path.splitext(secure_filename(file.filename))[0]
        input_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(input_path)

        output_filename = f"{original_name}.pdf"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)

        # Convert DOCX → PDF
        word_to_pdf(input_path, output_path)

        @after_this_request
        def cleanup(response):
            for p in (input_path, output_path):
                if os.path.exists(p):
                    os.remove(p)
            return response

        return send_file(output_path, as_attachment=True, download_name=output_filename)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# === PDF → Word ===
@app.route("/pdf-to-word", methods=["POST"])
def convert_pdf_to_word():
    try:
        file = request.files.get("file")
        if not file:
            return jsonify({"error": "No file uploaded"}), 400

        original_name = os.path.splitext(secure_filename(file.filename))[0]
        input_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(input_path)

        output_filename = f"{original_name}.docx"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)

        pdf_to_word(input_path, output_path)

        @after_this_request
        def cleanup(response):
            for p in (input_path, output_path):
                if os.path.exists(p):
                    os.remove(p)
            return response

        return send_file(output_path, as_attachment=True, download_name=output_filename)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# === Merge Multiple PDFs ===
@app.route("/merge-pdf", methods=["POST"])
def merge_pdfs():
    try:
        files = request.files.getlist("files")
        if not files or len(files) < 2:
            return jsonify({"error": "Please upload at least two PDF files"}), 400

        temp_dir = tempfile.mkdtemp(dir="/tmp")
        output_path = os.path.join(temp_dir, "merged_output.pdf")

        # ✅ Call function from tools/merge_pdf.py
        merge_pdf(files, output_path)

        @after_this_request
        def cleanup(response):
            if os.path.exists(output_path):
                os.remove(output_path)
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
            return response

        return send_file(output_path, as_attachment=True, download_name="Merged_File.pdf")

    except Exception as e:
        return jsonify({"error": str(e)}), 500








from tools.split_pdf import split_selected_pages

@app.route("/split-pdf", methods=["POST"])
def split_pdf_api():
    try:
        file = request.files.get("file")
        pages = request.form.get("pages")
        if not file or not pages:
            return jsonify({"error": "Missing file or pages"}), 400

        selected_pages = [int(p) for p in pages.split(",") if p.strip().isdigit()]

        filename = os.path.splitext(secure_filename(file.filename))[0]
        input_path = os.path.join(UPLOAD_FOLDER, file.filename)
        output_path = os.path.join(OUTPUT_FOLDER, f"{filename}_split.pdf")
        file.save(input_path)

        split_selected_pages(input_path, output_path, selected_pages)

        return send_file(output_path, as_attachment=True, download_name=f"{filename}_split.pdf")

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# === Run App ===
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
