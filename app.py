import os
import uuid
import io
from zipfile import ZipFile
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename

from PyPDF2 import PdfReader, PdfMerger, PdfWriter
from fpdf import FPDF
from docx import Document

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
FONTS_FOLDER = "fonts"   # place DejaVuSans.ttf here for unicode support

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(FONTS_FOLDER, exist_ok=True)

app = Flask(__name__)
CORS(app, origins="*")  # allow from everywhere (your domain can be limited)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in {"pdf","docx","doc","txt"}

def save_upload_file(file_storage):
    filename = secure_filename(file_storage.filename)
    unique = f"{uuid.uuid4().hex}_{filename}"
    path = os.path.join(UPLOAD_FOLDER, unique)
    file_storage.save(path)
    return path, filename

def send_and_cleanup(file_path, download_name, mimetype="application/pdf"):
    """Read file into memory, delete files, send BytesIO to client (so delete is safe)."""
    buf = io.BytesIO()
    with open(file_path, "rb") as f:
        buf.write(f.read())
    buf.seek(0)
    # delete file from disk
    try:
        os.remove(file_path)
    except Exception:
        pass
    return send_file(buf, as_attachment=True, download_name=download_name, mimetype=mimetype)

def docx_to_pdf_simple(docx_path, pdf_out_path):
    """
    Simple conversion using python-docx + fpdf.
    Better fonts if DejaVuSans.ttf is available in fonts/ folder.
    This keeps paragraphs and basic line breaks.
    """
    doc = Document(docx_path)
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # try to add DejaVu font for Unicode
    dejavu = os.path.join(FONTS_FOLDER, "DejaVuSans.ttf")
    if os.path.exists(dejavu):
        pdf.add_font("DejaVu", "", dejavu, uni=True)
        font_name = "DejaVu"
    else:
        # fallback: some built-in font
        font_name = "Arial"

    pdf.set_font(font_name, size=12)
    line_height = 6

    for para in doc.paragraphs:
        text = para.text
        if text.strip() == "":
            # blank line
            pdf.ln(4)
            continue
        # split into reasonable length so multi_cell wraps
        pdf.multi_cell(0, line_height, txt=text)
        pdf.ln(1)
    pdf.output(pdf_out_path)

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "API is running", "tools": ["word-to-pdf","pdf-to-word","merge-pdf","split-pdf","text-to-pdf"]})

# Word -> PDF
@app.route("/word-to-pdf", methods=["POST"])
def word_to_pdf():
    if "file" not in request.files:
        return jsonify({"error":"No file uploaded"}), 400
    file = request.files["file"]
    if file.filename == "" or not allowed_file(file.filename):
        return jsonify({"error":"Invalid file"}), 400

    uploaded_path, original_name = save_upload_file(file)
    base_name = os.path.splitext(original_name)[0]
    out_pdf_name = f"{base_name}.pdf"
    out_pdf_path = os.path.join(OUTPUT_FOLDER, f"{uuid.uuid4().hex}_{out_pdf_name}")

    try:
        docx_to_pdf_simple(uploaded_path, out_pdf_path)
    except Exception as e:
        # cleanup uploaded file on error
        try: os.remove(uploaded_path)
        except: pass
        return jsonify({"error":"Conversion failed", "detail": str(e)}), 500

    # remove uploaded file and return PDF bytes
    try: os.remove(uploaded_path)
    except: pass

    return send_and_cleanup(out_pdf_path, out_pdf_name, mimetype="application/pdf")

# Text -> PDF
@app.route("/text-to-pdf", methods=["POST"])
def text_to_pdf():
    text = request.form.get("text", "")
    if not text:
        return jsonify({"error":"No text provided"}), 400

    out_pdf_name = f"text_{uuid.uuid4().hex}.pdf"
    out_pdf_path = os.path.join(OUTPUT_FOLDER, out_pdf_name)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    dejavu = os.path.join(FONTS_FOLDER, "DejaVuSans.ttf")
    if os.path.exists(dejavu):
        pdf.add_font("DejaVu", "", dejavu, uni=True)
        font_name = "DejaVu"
    else:
        font_name = "Arial"
    pdf.set_font(font_name, size=12)
    pdf.multi_cell(0, 6, text)
    pdf.output(out_pdf_path)

    return send_and_cleanup(out_pdf_path, out_pdf_name, mimetype="application/pdf")

# Merge PDFs
@app.route("/merge-pdf", methods=["POST"])
def merge_pdf():
    files = request.files.getlist("files")
    if not files:
        return jsonify({"error":"No files uploaded"}), 400

    saved_paths = []
    try:
        merger = PdfMerger()
        for f in files:
            if f and f.filename:
                path, orig = save_upload_file(f)
                saved_paths.append(path)
                merger.append(path)
        out_name = f"merged_{uuid.uuid4().hex}.pdf"
        out_path = os.path.join(OUTPUT_FOLDER, out_name)
        merger.write(out_path)
        merger.close()
    except Exception as e:
        for p in saved_paths:
            try: os.remove(p)
            except: pass
        return jsonify({"error":"Merge failed", "detail":str(e)}), 500

    # cleanup uploaded PDFs
    for p in saved_paths:
        try: os.remove(p)
        except: pass

    return send_and_cleanup(out_path, out_name, mimetype="application/pdf")

# Split PDF -> returns a ZIP of single-page PDFs
@app.route("/split-pdf", methods=["POST"])
def split_pdf():
    if "file" not in request.files:
        return jsonify({"error":"No file uploaded"}), 400
    f = request.files["file"]
    path, orig_name = save_upload_file(f)

    try:
        reader = PdfReader(path)
        page_files = []
        for i, page in enumerate(reader.pages):
            writer = PdfWriter()
            writer.add_page(page)
            page_name = f"{os.path.splitext(orig_name)[0]}_page_{i+1}.pdf"
            page_path = os.path.join(OUTPUT_FOLDER, f"{uuid.uuid4().hex}_{page_name}")
            with open(page_path, "wb") as out_f:
                writer.write(out_f)
            page_files.append((page_path, page_name))

        # create zip
        zip_name = f"{os.path.splitext(orig_name)[0]}_pages_{uuid.uuid4().hex}.zip"
        zip_path = os.path.join(OUTPUT_FOLDER, zip_name)
        with ZipFile(zip_path, "w") as zf:
            for p, name in page_files:
                zf.write(p, arcname=name)
                try: os.remove(p)
                except: pass

    except Exception as e:
        try: os.remove(path)
        except: pass
        return jsonify({"error":"Split failed","detail":str(e)}), 500

    try: os.remove(path)
    except: pass

    return send_and_cleanup(zip_path, zip_name, mimetype="application/zip")

# PDF -> Word (basic text extraction)
@app.route("/pdf-to-word", methods=["POST"])
def pdf_to_word():
    if "file" not in request.files:
        return jsonify({"error":"No file uploaded"}), 400
    f = request.files["file"]
    path, orig_name = save_upload_file(f)

    try:
        reader = PdfReader(path)
        doc = Document()
        for page in reader.pages:
            text = page.extract_text()
            doc.add_paragraph(text if text else "")
        out_name = f"{os.path.splitext(orig_name)[0]}.docx"
        out_path = os.path.join(OUTPUT_FOLDER, f"{uuid.uuid4().hex}_{out_name}")
        doc.save(out_path)
    except Exception as e:
        try: os.remove(path)
        except: pass
        return jsonify({"error":"PDF->Word failed","detail":str(e)}), 500

    try: os.remove(path)
    except: pass

    return send_and_cleanup(out_path, out_name, mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

if __name__ == "__main__":
    # for local dev only; on Render you'll use gunicorn
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)