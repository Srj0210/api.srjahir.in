import os
import uuid
from flask import Flask, request, send_file, jsonify, after_this_request
from werkzeug.utils import secure_filename
from PyPDF2 import PdfMerger
from fpdf import FPDF
from docx import Document

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
FONTS_FOLDER = "fonts"
ALLOWED_EXTENSIONS = {"pdf", "docx", "doc", "txt"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(FONTS_FOLDER, exist_ok=True)


# ============= Helper Functions =============
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def save_upload_file(file):
    filename = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4().hex}_{filename}")
    file.save(file_path)
    return file_path, filename

def send_and_cleanup(output_path, filename, mimetype):
    @after_this_request
    def cleanup(response):
        try:
            if os.path.exists(output_path):
                os.remove(output_path)
        except Exception as e:
            print(f"Cleanup error: {e}")
        return response

    return send_file(output_path, as_attachment=True, download_name=filename, mimetype=mimetype)

# ============= 1️⃣ Word → PDF =============
@app.route("/word-to-pdf", methods=["POST"])
def word_to_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files["file"]
    if not file.filename or not allowed_file(file.filename):
        return jsonify({"error": "Invalid file"}), 400

    uploaded_path, original_name = save_upload_file(file)
    base_name = os.path.splitext(original_name)[0]
    out_pdf_name = f"{base_name}.pdf"
    out_pdf_path = os.path.join(OUTPUT_FOLDER, f"{uuid.uuid4().hex}_{out_pdf_name}")

    try:
        doc = Document(uploaded_path)
        pdf = FPDF()
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
            if not text:
                pdf.ln(5)
                continue

            style = para.style.name.lower()
            if "heading" in style:
                pdf.set_font("Arial", "B", 14)
            elif any(run.bold for run in para.runs):
                pdf.set_font("Arial", "B", 12)
            else:
                pdf.set_font("Arial", "", 12)

            pdf.multi_cell(0, 8, text)
            pdf.ln(2)

        pdf.output(out_pdf_path)

    except Exception as e:
        return jsonify({"error": f"Conversion failed: {str(e)}"}), 500
    finally:
        os.remove(uploaded_path)

    return send_and_cleanup(out_pdf_path, out_pdf_name, "application/pdf")


# ============= 2️⃣ PDF → Word =============
@app.route("/pdf-to-word", methods=["POST"])
def pdf_to_word():
    import fitz  # PyMuPDF

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files["file"]
    if not file.filename or not allowed_file(file.filename):
        return jsonify({"error": "Invalid file"}), 400

    uploaded_path, original_name = save_upload_file(file)
    base_name = os.path.splitext(original_name)[0]
    out_docx_name = f"{base_name}.docx"
    out_docx_path = os.path.join(OUTPUT_FOLDER, f"{uuid.uuid4().hex}_{out_docx_name}")

    try:
        doc = Document()
        pdf = fitz.open(uploaded_path)
        for page in pdf:
            text = page.get_text("text")
            doc.add_paragraph(text)
            doc.add_page_break()
        doc.save(out_docx_path)

    except Exception as e:
        return jsonify({"error": f"Conversion failed: {str(e)}"}), 500
    finally:
        os.remove(uploaded_path)

    return send_and_cleanup(out_docx_path, out_docx_name,
                            "application/vnd.openxmlformats-officedocument.wordprocessingml.document")


# ============= 3️⃣ Merge PDFs =============
@app.route("/merge-pdf", methods=["POST"])
def merge_pdf():
    if "files" not in request.files:
        return jsonify({"error": "No files uploaded"}), 400
    files = request.files.getlist("files")
    if not files:
        return jsonify({"error": "No PDFs provided"}), 400

    merger = PdfMerger()
    temp_files = []

    out_pdf_name = "merged.pdf"
    out_pdf_path = os.path.join(OUTPUT_FOLDER, f"{uuid.uuid4().hex}_{out_pdf_name}")

    try:
        for file in files:
            if file.filename and allowed_file(file.filename):
                temp_path, _ = save_upload_file(file)
                temp_files.append(temp_path)
                merger.append(temp_path)
        merger.write(out_pdf_path)
        merger.close()

    except Exception as e:
        return jsonify({"error": f"Merge failed: {str(e)}"}), 500
    finally:
        for f in temp_files:
            os.remove(f)

    return send_and_cleanup(out_pdf_path, out_pdf_name, "application/pdf")


# ============= 4️⃣ Text → PDF =============
@app.route("/text-to-pdf", methods=["POST"])
def text_to_pdf():
    text = request.form.get("text", "").strip()
    if not text:
        return jsonify({"error": "No text provided"}), 400

    out_pdf_name = f"text_{uuid.uuid4().hex[:6]}.pdf"
    out_pdf_path = os.path.join(OUTPUT_FOLDER, out_pdf_name)

    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, text)
        pdf.output(out_pdf_path)

    except Exception as e:
        return jsonify({"error": f"Conversion failed: {str(e)}"}), 500

    return send_and_cleanup(out_pdf_path, out_pdf_name, "application/pdf")


# ============= Home Route =============
@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "SRJahir Tools API is running ✅"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)