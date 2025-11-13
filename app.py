import os
import tempfile
import shutil
from flask import Flask, request, jsonify, send_file, after_this_request
from werkzeug.utils import secure_filename
from flask_cors import CORS

# === Import conversion tools ===
from tools.word_to_pdf import word_to_pdf
from tools.pdf_to_word import pdf_to_word
from tools.merge_pdf import merge_pdf
from tools.split_pdf import split_selected_pages
from tools.remove_pages import remove_pages
from tools.organize_pdf import organize_pdf












# === Flask Setup ===
app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "/tmp/uploads"
OUTPUT_FOLDER = "/tmp/outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# === Root ===
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "SRJ Tools API is Live 🚀",
        "status": "ok",
        "routes": [
            "/word-to-pdf",
            "/pdf-to-word",
            "/merge-pdf",
            "/split-pdf"
        ]
    })

# === Word → PDF ===
@app.route("/word-to-pdf", methods=["POST"])
def convert_word_to_pdf():
    try:
        file = request.files.get("file")
        if not file:
            return jsonify({"error": "No file uploaded"}), 400

        name = os.path.splitext(secure_filename(file.filename))[0]
        in_path = os.path.join(UPLOAD_FOLDER, file.filename)
        out_path = os.path.join(OUTPUT_FOLDER, f"{name}.pdf")

        file.save(in_path)
        word_to_pdf(in_path, out_path)

        @after_this_request
        def cleanup(res):
            for p in (in_path, out_path):
                if os.path.exists(p):
                    os.remove(p)
            return res

        return send_file(out_path, as_attachment=True, download_name=f"{name}.pdf")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# === PDF → Word ===
@app.route("/pdf-to-word", methods=["POST"])
def convert_pdf_to_word():
    try:
        file = request.files.get("file")
        if not file:
            return jsonify({"error": "No file uploaded"}), 400

        name = os.path.splitext(secure_filename(file.filename))[0]
        in_path = os.path.join(UPLOAD_FOLDER, file.filename)
        out_path = os.path.join(OUTPUT_FOLDER, f"{name}.docx")

        file.save(in_path)
        pdf_to_word(in_path, out_path)

        @after_this_request
        def cleanup(res):
            for p in (in_path, out_path):
                if os.path.exists(p):
                    os.remove(p)
            return res

        return send_file(out_path, as_attachment=True, download_name=f"{name}.docx")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# === Merge PDFs ===
@app.route("/merge-pdf", methods=["POST"])
def merge_pdfs():
    try:
        files = request.files.getlist("files")
        if len(files) < 2:
            return jsonify({"error": "Upload at least 2 PDFs"}), 400

        tempdir = tempfile.mkdtemp(dir="/tmp")
        out_path = os.path.join(tempdir, "merged.pdf")

        merge_pdf(files, out_path)

        @after_this_request
        def cleanup(res):
            if os.path.exists(out_path):
                os.remove(out_path)
            shutil.rmtree(tempdir, ignore_errors=True)
            return res

        return send_file(out_path, as_attachment=True, download_name="Merged_File.pdf")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# === Split PDF Pages ===
@app.route("/split-pdf", methods=["POST"])
def split_pdf_api():
    try:
        file = request.files.get("file")
        pages = request.form.get("pages")

        if not file or not pages:
            return jsonify({"error": "Missing file or pages"}), 400

        pages_list = [int(p) for p in pages.split(",") if p.strip().isdigit()]

        name = os.path.splitext(secure_filename(file.filename))[0]
        in_path = os.path.join(UPLOAD_FOLDER, file.filename)
        out_path = os.path.join(OUTPUT_FOLDER, f"{name}_split.pdf")

        file.save(in_path)

        split_selected_pages(in_path, out_path, pages_list)

        @after_this_request
        def cleanup(res):
            for p in (in_path, out_path):
                if os.path.exists(p):
                    os.remove(p)
            return res

        return send_file(out_path, as_attachment=True, download_name=f"{name}_split.pdf")

    except Exception as e:
        return jsonify({"error": str(e)}), 500



from tools.remove_pages import remove_pages

@app.route("/remove-pages", methods=["POST"])
def remove_pages_api():
    try:
        file = request.files.get("file")
        pages = request.form.get("pages")

        if not file or not pages:
            return jsonify({"error": "Missing file or pages"}), 400

        pages_to_delete = [int(p) for p in pages.split(",") if p.strip().isdigit()]

        filename = os.path.splitext(secure_filename(file.filename))[0]
        input_path = os.path.join(UPLOAD_FOLDER, file.filename)
        output_path = os.path.join(OUTPUT_FOLDER, f"{filename}_cleaned.pdf")
        file.save(input_path)

        remove_pages(input_path, output_path, pages_to_delete)

        @after_this_request
        def cleanup(response):
            for p in (input_path, output_path):
                if os.path.exists(p):
                    os.remove(p)
            return response

        return send_file(output_path, as_attachment=True, download_name=f"{filename}_cleaned.pdf")

    except Exception as e:
        return jsonify({"error": str(e)}), 500





@app.route("/organize-pdf", methods=["POST"])
def organize_pdf_route():
    try:
        file = request.files.get("file")
        order = request.form.get("order")

        if not file:
            return jsonify({"error": "No file uploaded"}), 400

        if not order:
            return jsonify({"error": "Page order missing"}), 400

        order = list(map(int, order.split(",")))

        original_name = os.path.splitext(secure_filename(file.filename))[0]
        input_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(input_path)

        output_filename = f"{original_name}_organized.pdf"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)

        organize_pdf(input_path, output_path, order)

        @after_this_request
        def cleanup(response):
            for p in (input_path, output_path):
                if os.path.exists(p):
                    os.remove(p)
            return response

        return send_file(output_path, as_attachment=True, download_name=output_filename)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
# === Run ===
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
