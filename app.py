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
from docx.shared import RGBColor

# ==============================
# FOLDER SETUP
# ==============================
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
FONTS_FOLDER = "fronts"

for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER, FONTS_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# ==============================
# FLASK APP
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
# DOCX → PDF (Exact Layout)
# ==============================
def docx_to_pdf_simple(docx_path, pdf_out_path):
    """
    High-fidelity DOCX → PDF conversion for SRJahir Tools.
    Keeps font size, bold, color, bullet points, headings — like Word.
    """

    doc = Document(docx_path)
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # Use DejaVuSans for Unicode and color-safe text
    dejavu = os.path.join(FONTS_FOLDER, "DejaVuSans.ttf")
    if os.path.exists(dejavu):
        pdf.add_font("DejaVu", "", dejavu, uni=True)
        pdf.add_font("DejaVu-Bold", "B", dejavu, uni=True)
        font_name = "DejaVu"
    else:
        pdf.set_font("Arial", size=12)
        font_name = "Arial"

    pdf.set_left_margin(18)
    pdf.set_right_margin(18)

    for para in doc.paragraphs:
        if not para.text.strip():
            pdf.ln(5)
            continue

        # Detect formatting style
        is_heading = para.style.name.startswith("Heading")
        is_bullet = para.style.name in ["List Bullet", "List Paragraph"]

        # Default font setup
        font_style = ""
        font_size = 12
        font_color = (0, 0, 0)

        if para.runs:
            run = para.runs[0]
            if run.font.size:
                font_size = run.font.size.pt
            if run.bold:
                font_style = "B"
            if run.font.color and run.font.color.rgb:
                rgb = run.font.color.rgb
                font_color = (rgb >> 16, (rgb >> 8) & 255, rgb & 255)

        # Heading overrides color/size
        if is_heading:
            font_style = "B"
            font_color = (30, 60, 180)  # blue like Word headings
            font_size = 14 if "1" in para.style.name else 12.5

        pdf.set_font(font_name, style=font_style, size=font_size)
        pdf.set_text_color(*font_color)

        if is_bullet:
            pdf.cell(5)
            pdf.multi_cell(0, 7, f"• {para.text.strip()}")
        else:
            pdf.multi_cell(0, 7, para.text.strip())

        pdf.ln(1.5)

    pdf.output(pdf_out_path)

# ==============================
# ROUTES
# ==============================
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "API running 🚀",
        "tools": ["word-to-pdf", "pdf-to-word", "merge-pdf", "split-pdf", "text-to-pdf"]
    })

# WORD → PDF
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

# TEXT → PDF
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

        dejavu = os.path.join(FONTS_FOLDER, "DejaVuSans.ttf")
        if os.path.exists(dejavu):
            pdf.add_font("DejaVu", "", dejavu, uni=True)
            font_name = "DejaVu"
        else:
            font_name = "Arial"

        pdf.set_font(font_name, size=12)
        pdf.multi_cell(0, 6, text)
        pdf.output(out_pdf_path)

        return send_and_cleanup(out_pdf_path, out_pdf_name, "application/pdf")
    except Exception as e:
        return jsonify({"error": "Text-to-PDF failed", "detail": str(e)}), 500

# MERGE PDF
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

# SPLIT PDF
@app.route("/split-pdf", methods=["POST"])
def split_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    f = request.files["file"]
    path, orig = save_upload_file(f)

    try:
        reader = PdfReader(path)
        zip_path = os.path.join(OUTPUT_FOLDER, f"{uuid.uuid4().hex}.zip")
        with ZipFile(zip_path, "w") as zf:
            for i, page in enumerate(reader.pages, start=1):
                w = PdfWriter()
                w.add_page(page)
                page_path = os.path.join(OUTPUT_FOLDER, f"page_{i}.pdf")
                with open(page_path, "wb") as out:
                    w.write(out)
                zf.write(page_path, f"page_{i}.pdf")
                os.remove(page_path)
    except Exception as e:
        return jsonify({"error": "Split failed", "detail": str(e)}), 500
    finally:
        os.remove(path)

    return send_and_cleanup(zip_path, "split_pages.zip", "application/zip")

# PDF → WORD
@app.route("/pdf-to-word", methods=["POST"])
def pdf_to_word():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        f = request.files["file"]
        path, orig_name = save_upload_file(f)

        reader = PdfReader(path)
        doc = Document()
        for page in reader.pages:
            text = page.extract_text() or ""
            doc.add_paragraph(text)
        out_path = os.path.join(OUTPUT_FOLDER, f"{uuid.uuid4().hex}.docx")
        doc.save(out_path)

        os.remove(path)
        return send_and_cleanup(out_path, "converted.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")

    except Exception as e:
        return jsonify({"error": "PDF-to-Word failed", "detail": str(e)}), 500

# ==============================
# RUN APP
# ==============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)