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
FONTS_FOLDER = "fonts"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(FONTS_FOLDER, exist_ok=True)

app = Flask(__name__)
CORS(app, origins="*")

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in {"pdf","docx","doc","txt"}

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
    except:
        pass
    return send_file(buf, as_attachment=True, download_name=download_name, mimetype=mimetype)

def docx_to_pdf_simple(docx_path, pdf_out_path):
    doc = Document(docx_path)
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    font_path = os.path.join(FONTS_FOLDER, "DejaVuSans.ttf")
    if os.path.exists(font_path):
        pdf.add_font("DejaVu", "", font_path, uni=True)
        pdf.set_font("DejaVu", size=12)
    else:
        pdf.set_font("Arial", size=12)

    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            pdf.multi_cell(0, 8, txt=text)
            pdf.ln(2)
        else:
            pdf.ln(4)

    pdf.output(pdf_out_path)

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "API is running", "tools": ["word-to-pdf", "pdf-to-word", "merge-pdf", "split-pdf", "text-to-pdf"]})

@app.route("/word-to-pdf", methods=["POST"])
def word_to_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files["file"]
    if file.filename == "" or not allowed_file(file.filename):
        return jsonify({"error": "Invalid file"}), 400

    uploaded_path, original_name = save_upload_file(file)
    out_pdf_path = os.path.join(OUTPUT_FOLDER, f"{uuid.uuid4().hex}.pdf")

    try:
        docx_to_pdf_simple(uploaded_path, out_pdf_path)
    except Exception as e:
        try:
            os.remove(uploaded_path)
        except:
            pass
        return jsonify({"error": "Conversion failed", "detail": str(e)}), 500

    try:
        os.remove(uploaded_path)
    except:
        pass

    return send_and_cleanup(out_pdf_path, "converted.pdf", mimetype="application/pdf")

@app.route("/pdf-to-word", methods=["POST"])
def pdf_to_word():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    f = request.files["file"]
    path, orig_name = save_upload_file(f)

    try:
        reader = PdfReader(path)
        doc = Document()
        for page in reader.pages:
            text = page.extract_text() or ""
            doc.add_paragraph(text)
        out_path = os.path.join(OUTPUT_FOLDER, f"{uuid.uuid4().hex}.docx")
        doc.save(out_path)
    except Exception as e:
        try:
            os.remove(path)
        except:
            pass
        return jsonify({"error": "PDF→Word failed", "detail": str(e)}), 500

    try:
        os.remove(path)
    except:
        pass

    return send_and_cleanup(out_path, "converted.docx", mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

@app.route("/text-to-pdf", methods=["POST"])
def text_to_pdf():
    text = request.form.get("text", "")
    if not text:
        return jsonify({"error": "No text provided"}), 400

    out_pdf_path = os.path.join(OUTPUT_FOLDER, f"{uuid.uuid4().hex}.pdf")
    pdf = FPDF()
    pdf.add_page()

    font_path = os.path.join(FONTS_FOLDER, "DejaVuSans.ttf")
    if os.path.exists(font_path):
        pdf.add_font("DejaVu", "", font_path, uni=True)
        pdf.set_font("DejaVu", size=12)
    else:
        pdf.set_font("Arial", size=12)

    pdf.multi_cell(0, 8, text)
    pdf.output(out_pdf_path)
    return send_and_cleanup(out_pdf_path, "text.pdf")

@app.route("/merge-pdf", methods=["POST"])
def merge_pdf():
    files = request.files.getlist("files")
    if not files:
        return jsonify({"error": "No files uploaded"}), 400

    saved = []
    merger = PdfMerger()
    try:
        for f in files:
            p, _ = save_upload_file(f)
            saved.append(p)
            merger.append(p)
        out_path = os.path.join(OUTPUT_FOLDER, f"{uuid.uuid4().hex}.pdf")
        merger.write(out_path)
    except Exception as e:
        for s in saved:
            os.remove(s)
        return jsonify({"error": "Merge failed", "detail": str(e)}), 500
    finally:
        merger.close()
        for s in saved:
            os.remove(s)
    return send_and_cleanup(out_path, "merged.pdf")

@app.route("/split-pdf", methods=["POST"])
def split_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    f = request.files["file"]
    path, _ = save_upload_file(f)

    try:
        reader = PdfReader(path)
        zip_path = os.path.join(OUTPUT_FOLDER, f"{uuid.uuid4().hex}.zip")
        with ZipFile(zip_path, "w") as zf:
            for i, page in enumerate(reader.pages, start=1):
                w = PdfWriter()
                w.add_page(page)
                single_path = os.path.join(OUTPUT_FOLDER, f"page_{i}.pdf")
                with open(single_path, "wb") as out:
                    w.write(out)
                zf.write(single_path, f"page_{i}.pdf")
                os.remove(single_path)
    except Exception as e:
        return jsonify({"error": "Split failed", "detail": str(e)}), 500
    finally:
        os.remove(path)

    return send_and_cleanup(zip_path, "split_pages.zip", mimetype="application/zip")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))