import os
import tempfile
import shutil
from flask import Flask, request, jsonify, send_file, after_this_request
from werkzeug.utils import secure_filename
from flask_cors import CORS

# === Import tool functions ===
from tools.word_to_pdf import word_to_pdf
from tools.pdf_to_word import pdf_to_word
from tools.merge_pdf import merge_pdf
from tools.split_pdf import split_selected_pages
from tools.remove_pages import remove_pages
from tools.organize_pdf import organize_pdf


# ========== FLASK BASE SETUP ==========
app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "/tmp/uploads"
OUTPUT_FOLDER = "/tmp/outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


# ========== GLOBAL CLEANUP FUNCTION ==========
def cleanup_files(*paths):
    """Delete multiple temp files/folders safely."""
    for p in paths:
        try:
            if os.path.isdir(p):
                shutil.rmtree(p, ignore_errors=True)
            elif os.path.exists(p):
                os.remove(p)
        except:
            pass


# ========== HOME ROUTE ==========
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "SRJ Tools API is Live 🚀",
        "status": "ok",
        "routes": [
            "/word-to-pdf",
            "/pdf-to-word",
            "/merge-pdf",
            "/split-pdf",
            "/remove-pages",
            "/organize-pdf",
            "/compress-pdf"
        ]
    })


# ========== WORD → PDF ==========
@app.route("/word-to-pdf", methods=["POST"])
def convert_word_to_pdf():
    try:
        file = request.files.get("file")
        if not file:
            return {"error": "No file uploaded"}, 400

        name = os.path.splitext(secure_filename(file.filename))[0]
        in_path = os.path.join(UPLOAD_FOLDER, file.filename)
        out_path = os.path.join(OUTPUT_FOLDER, f"{name}.pdf")

        file.save(in_path)
        word_to_pdf(in_path, out_path)

        @after_this_request
        def cleanup(response):
            cleanup_files(in_path, out_path)
            return response

        return send_file(out_path, as_attachment=True, download_name=f"{name}.pdf")

    except Exception as e:
        return {"error": str(e)}, 500



# ========== PDF → WORD ==========
@app.route("/pdf-to-word", methods=["POST"])
def convert_pdf_to_word():
    try:
        file = request.files.get("file")
        if not file:
            return {"error": "No file uploaded"}, 400

        name = os.path.splitext(secure_filename(file.filename))[0]
        in_path = os.path.join(UPLOAD_FOLDER, file.filename)
        out_path = os.path.join(OUTPUT_FOLDER, f"{name}.docx")

        file.save(in_path)
        pdf_to_word(in_path, out_path)

        @after_this_request
        def cleanup(response):
            cleanup_files(in_path, out_path)
            return response

        return send_file(out_path, as_attachment=True, download_name=f"{name}.docx")

    except Exception as e:
        return {"error": str(e)}, 500



# ========== MERGE PDF ==========
@app.route("/merge-pdf", methods=["POST"])
def merge_pdfs():
    try:
        files = request.files.getlist("files")
        if len(files) < 2:
            return {"error": "Upload at least 2 PDFs"}, 400

        tempdir = tempfile.mkdtemp(dir="/tmp")
        out_path = os.path.join(tempdir, "merged.pdf")

        merge_pdf(files, out_path)

        @after_this_request
        def cleanup(response):
            cleanup_files(out_path, tempdir)
            return response

        return send_file(out_path, as_attachment=True, download_name="Merged_File.pdf")

    except Exception as e:
        return {"error": str(e)}, 500



# ========== SPLIT SELECTED PAGES ==========
@app.route("/split-pdf", methods=["POST"])
def split_pdf_api():
    try:
        file = request.files.get("file")
        pages = request.form.get("pages")

        if not file or not pages:
            return {"error": "Missing file or pages"}, 400

        pages_list = [int(p) for p in pages.split(",") if p.strip().isdigit()]

        name = os.path.splitext(secure_filename(file.filename))[0]
        in_path = os.path.join(UPLOAD_FOLDER, file.filename)
        out_path = os.path.join(OUTPUT_FOLDER, f"{name}_split.pdf")

        file.save(in_path)
        split_selected_pages(in_path, out_path, pages_list)

        @after_this_request
        def cleanup(response):
            cleanup_files(in_path, out_path)
            return response

        return send_file(out_path, as_attachment=True, download_name=f"{name}_split.pdf")

    except Exception as e:
        return {"error": str(e)}, 500



# ========== REMOVE SELECTED PAGES ==========
@app.route("/remove-pages", methods=["POST"])
def remove_pages_api():
    try:
        file = request.files.get("file")
        pages = request.form.get("pages")

        if not file or not pages:
            return {"error": "Missing file or pages"}, 400

        pages_to_delete = [int(p) for p in pages.split(",") if p.strip().isdigit()]

        name = os.path.splitext(secure_filename(file.filename))[0]
        in_path = os.path.join(UPLOAD_FOLDER, file.filename)
        out_path = os.path.join(OUTPUT_FOLDER, f"{name}_cleaned.pdf")

        file.save(in_path)
        remove_pages(in_path, out_path, pages_to_delete)

        @after_this_request
        def cleanup(response):
            cleanup_files(in_path, out_path)
            return response

        return send_file(out_path, as_attachment=True, download_name=f"{name}_cleaned.pdf")

    except Exception as e:
        return {"error": str(e)}, 500



# ========== ORGANIZE PDF (DRAG & DROP ORDER) ==========
@app.route("/organize-pdf", methods=["POST"])
def organize_pdf_route():
    try:
        file = request.files.get("file")
        order = request.form.get("order")

        if not file:
            return {"error": "No file uploaded"}, 400
        if not order:
            return {"error": "Page order missing"}, 400

        order = list(map(int, order.split(",")))

        name = os.path.splitext(secure_filename(file.filename))[0]
        in_path = os.path.join(UPLOAD_FOLDER, file.filename)
        out_path = os.path.join(OUTPUT_FOLDER, f"{name}_organized.pdf")

        file.save(in_path)
        organize_pdf(in_path, out_path, order)

        @after_this_request
        def cleanup(response):
            cleanup_files(in_path, out_path)
            return response

        return send_file(out_path, as_attachment=True, download_name=f"{name}_organized.pdf")

    except Exception as e:
        return {"error": str(e)}, 500



# ========== COMPRESS PDF ==========
@app.route("/compress-pdf", methods=["POST"])
def compress_pdf():
    import subprocess
    import pikepdf
    from flask import send_file, request, after_this_request
    import os

    if "file" not in request.files:
        return {"error": "No file uploaded"}, 400

    file = request.files["file"]
    level = request.form.get("level", "balanced")

    # Clean filename for safe usage
    original_name = os.path.splitext(secure_filename(file.filename))[0]

    input_path = f"/tmp/{original_name}_input.pdf"
    output_path = f"/tmp/{original_name}_compressed.pdf"

    file.save(input_path)

    # Ghostscript quality levels
    quality_options = {
        "high": "/screen",        # smallest
        "balanced": "/ebook",     # recommended
        "low": "/prepress"        # best quality
    }

    selected_quality = quality_options.get(level, "/ebook")

    # Try Ghostscript
    try:
        gs_cmd = [
            "gs", "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.5",
            f"-dPDFSETTINGS={selected_quality}",
            "-dNOPAUSE", "-dQUIET", "-dBATCH",
            f"-sOutputFile={output_path}",
            input_path
        ]
        subprocess.run(gs_cmd, check=True)

    except Exception as e:
        print("Ghostscript failed:", e)

        # Fallback – pikepdf
        try:
            pdf = pikepdf.open(input_path)
            pdf.save(output_path, compression=pikepdf.CompressionLevel.compression_level_fast)
            pdf.close()
        except Exception as e:
            print("Fallback failed:", e)
            return {"error": "Compression failed"}, 500

    # Auto delete after download
    @after_this_request
    def cleanup(response):
        for p in (input_path, output_path):
            if os.path.exists(p):
                os.remove(p)
        return response

    final_name = f"{original_name}_compressed.pdf"

    return send_file(output_path, as_attachment=True, attachment_filename=final_name)


# ========== RUN SERVER ==========
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
