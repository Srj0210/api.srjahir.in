from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PyPDF2 import PdfMerger, PdfReader
from fpdf import FPDF
from docx import Document
import os
import uuid
import threading
import time

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# 🧹 Auto delete file after download (30 sec delay)
def schedule_delete(path, delay=30):
    def delete_file():
        time.sleep(delay)
        try:
            if os.path.exists(path):
                os.remove(path)
                print(f"[CLEANUP] Deleted file: {path}")
        except Exception as e:
            print(f"[ERROR] Cleanup failed for {path}: {e}")
    threading.Thread(target=delete_file, daemon=True).start()


# 🧹 Periodic cleanup every 6 hours
def periodic_cleanup():
    while True:
        time.sleep(6 * 60 * 60)  # 6 hours
        for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
            for f in os.listdir(folder):
                try:
                    path = os.path.join(folder, f)
                    if os.path.isfile(path):
                        os.remove(path)
                except Exception as e:
                    print(f"[ERROR] Cleanup failed for {path}: {e}")
        print("[CLEANUP] Periodic cleanup completed.")


# Start cleanup thread
threading.Thread(target=periodic_cleanup, daemon=True).start()


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "API is running",
        "tools": ["word-to-pdf", "merge-pdf", "split-pdf", "text-to-pdf", "pdf-to-word"]
    })


# 🟢 Word → PDF
@app.route("/word-to-pdf", methods=["POST"])
def word_to_pdf():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files["file"]
        original_name = os.path.splitext(file.filename)[0]
        filepath = os.path.join(UPLOAD_FOLDER, str(uuid.uuid4()) + ".docx")
        file.save(filepath)

        document = Document(filepath)
        pdf_filename = f"{original_name}_converted.pdf"
        pdf_path = os.path.join(OUTPUT_FOLDER, pdf_filename)

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        for para in document.paragraphs:
            text = para.text.encode("latin-1", "replace").decode("latin-1")
            pdf.multi_cell(0, 10, text)

        pdf.output(pdf_path)
        schedule_delete(pdf_path)
        schedule_delete(filepath)

        return send_file(pdf_path, as_attachment=True, download_name=pdf_filename)

    except Exception as e:
        print("❌ Error in word_to_pdf:", e)
        return jsonify({"error": str(e)}), 500


# 🟢 Text → PDF
@app.route("/text-to-pdf", methods=["POST"])
def text_to_pdf():
    text = request.form.get("text", "")
    if not text:
        return jsonify({"error": "No text provided"}), 400

    pdf_filename = f"text_to_pdf_{uuid.uuid4().hex[:6]}.pdf"
    pdf_path = os.path.join(OUTPUT_FOLDER, pdf_filename)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, text)
    pdf.output(pdf_path)

    schedule_delete(pdf_path)
    return send_file(pdf_path, as_attachment=True, download_name=pdf_filename)


# 🟢 Merge PDF
@app.route("/merge-pdf", methods=["POST"])
def merge_pdf():
    files = request.files.getlist("files")
    if not files:
        return jsonify({"error": "No files uploaded"}), 400

    merger = PdfMerger()
    saved_files = []
    for file in files:
        temp_path = os.path.join(UPLOAD_FOLDER, str(uuid.uuid4()) + ".pdf")
        file.save(temp_path)
        merger.append(temp_path)
        saved_files.append(temp_path)

    pdf_filename = f"merged_{uuid.uuid4().hex[:6]}.pdf"
    pdf_path = os.path.join(OUTPUT_FOLDER, pdf_filename)
    merger.write(pdf_path)
    merger.close()

    for f in saved_files:
        schedule_delete(f)
    schedule_delete(pdf_path)

    return send_file(pdf_path, as_attachment=True, download_name=pdf_filename)


# 🟢 Split PDF
@app.route("/split-pdf", methods=["POST"])
def split_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    filepath = os.path.join(UPLOAD_FOLDER, str(uuid.uuid4()) + ".pdf")
    file.save(filepath)

    reader = PdfReader(filepath)
    output_files = []

    for i, page in enumerate(reader.pages):
        pdf_filename = f"page_{i+1}_{uuid.uuid4().hex[:5]}.pdf"
        pdf_path = os.path.join(OUTPUT_FOLDER, pdf_filename)

        merger = PdfMerger()
        merger.append(filepath, pages=(i, i + 1))
        merger.write(pdf_path)
        merger.close()

        output_files.append(pdf_filename)
        schedule_delete(pdf_path)

    schedule_delete(filepath)
    return jsonify({"message": "PDF Split Successful", "files": output_files})


# 🟢 PDF → Word
@app.route("/pdf-to-word", methods=["POST"])
def pdf_to_word():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    filepath = os.path.join(UPLOAD_FOLDER, str(uuid.uuid4()) + ".pdf")
    file.save(filepath)

    reader = PdfReader(filepath)
    doc = Document()

    for page in reader.pages:
        text = page.extract_text()
        doc.add_paragraph(text if text else "")

    word_filename = f"{os.path.splitext(file.filename)[0]}_converted.docx"
    word_path = os.path.join(OUTPUT_FOLDER, word_filename)
    doc.save(word_path)

    schedule_delete(word_path)
    schedule_delete(filepath)

    return send_file(word_path, as_attachment=True, download_name=word_filename)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")