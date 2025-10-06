import os
import uuid
import io
from zipfile import ZipFile
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader, PdfWriter, PdfMerger
from fpdf import FPDF
from docx import Document

# ==============================
# FOLDERS (auto create)
# ==============================
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
FONTS_FOLDER = "fronts"

for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER, FONTS_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# ==============================
# APP SETUP
# ==============================
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# ==============================
# HELPERS
# ==============================
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in {"pdf", "docx", "txt"}

def save_upload_file(file_storage):
    filename = secure_filename(file_storage.filename)
    unique = f"{uuid.uuid4().hex}_{filename}"
    path = os.path.join(UPLOAD_FOLDER, unique)
    file_storage.save(path)
    return path, filename

def send_and_cleanup(file_path, download_name, mimetype="application/pdf"):
    buf = io.BytesIO()
    with open(file_path, "rb") as f:
        buf.write(f.read())
    buf.seek(0)
    try:
        os.remove(file_path)
    except Exception:
        pass
    return send_file(buf, as_attachment=True, download_name=download_name, mimetype=mimetype)

# ==============================
# WORD ➜ PDF
# ==============================
def docx_to_pdf_simple(docx_path, pdf_out_path):
    """Convert DOCX → PDF using python-docx + fpdf with DejaVuSans.ttf support."""
    doc = Document(docx_path)
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    font_path = os.path.join(FONTS_FOLDER, "DejaVuSans.ttf")
    if os.path.exists(font_path):
        pdf.add_font("DejaVu", "", font_path, uni=True)
        font_name = "DejaVu"
    else:
        font_name = "Arial"

    pdf.set_font(font_name, size=12)

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            pdf.ln(5)
        else:
            pdf.multi_cell(0, 8, text)
            pdf.ln(2)

    pdf.output(pdf_out_path)

# ==============================
# ROUTES
# ==============================
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "API is running fine 🚀",
        "tools": ["word-to-pdf", "pdf-to-word", "merge-pdf", "split-pdf", "text-to-pdf"]
    })

@app.route("/word-to-pdf", methods=["POST"])
def word_to_pdf():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        file = request.files["file"]
        if file.filename == "" or not allowed_file(file.filename):
            return jsonify({"error": "Invalid file"}), 400

        uploaded_path, original_name = save_upload_file(file)
        base_name = os.path.splitext(original_name)[0]
        out_pdf_name = f"{base_name}.pdf"
        out_pdf_path = os.path.join(OUTPUT_FOLDER, f"{uuid.uuid4().hex}_{out_pdf_name}")

        docx_to_pdf_simple(uploaded_path, out_pdf_path)

        os.remove(uploaded_path)
        return send_and_cleanup(out_pdf_path, out_pdf_name, mimetype="application/pdf")

    except Exception as e:
        return jsonify({"error": "Conversion failed", "detail": str(e)}), 500

# ==============================
# TEXT ➜ PDF
# ==============================
@app.route("/text-to-pdf", methods=["POST"])
def text_to_pdf():
    try:
        text = request.form.get("text", "")
        if not text.strip():
            return jsonify({"error": "No text provided"}), 400

        out_pdf_name = f"text_{uuid.uuid4().hex}.pdf"
        out_pdf_path = os.path.join(OUTPUT_FOLDER, out_pdf_name)

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        font_path = os.path.join(FONTS_FOLDER, "DejaVuSans.ttf")
        if os.path.exists(font_path):
            pdf.add_font("DejaVu", "", font_path, uni=True)
            font_name = "DejaVu"
        else:
            font_name = "Arial"
        pdf.set_font(font_name, size=12)
        pdf.multi_cell(0, 6, text)
        pdf.output(out_pdf_path)

        return send_and_cleanup(out_pdf_path, out_pdf_name, "application/pdf")
    except Exception as e:
        return jsonify({"error": "Text-to-PDF failed", "detail": str(e)}), 500

# ==============================
# MERGE PDF
# ==============================
@app.route("/merge-pdf", methods=["POST"])
def merge_pdf():
    try:
        files = request.files.getlist("files")
        if not files:
            return jsonify({"error": "No files uploaded"}), 400

        merger = PdfMerger()
        paths = []
        for f in files:
            path, _ = save_upload_file(f)
            paths.append(path)
            merger.append(path)

        out_name = f"merged_{uuid.uuid4().hex}.pdf"
        out_path = os.path.join(OUTPUT_FOLDER, out_name)
        merger.write(out_path)
        merger.close()

        for p in paths:
            os.remove(p)
        return send_and_cleanup(out_path, out_name, "application/pdf")
    except Exception as e:
        return jsonify({"error": "Merge failed", "detail": str(e)}), 500

# ==============================
# RUN
# ==============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)