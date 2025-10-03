from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
from tools import pdf_tools, text_tools, image_tools

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/")
def home():
    return jsonify({
        "status": "API is running",
        "tools": ["merge-pdf", "split-pdf", "word-to-pdf", "pdf-to-word", "text-case", "image-compress"]
    })

# -------- PDF TOOLS --------
@app.route("/merge-pdf", methods=["POST"])
def merge_pdf():
    files = request.files.getlist("files")
    output_file = os.path.join(UPLOAD_FOLDER, "merged.pdf")
    pdf_tools.merge_pdfs(files, output_file)
    return send_file(output_file, as_attachment=True)

@app.route("/split-pdf", methods=["POST"])
def split_pdf():
    file = request.files["file"]
    output_files = pdf_tools.split_pdf(file, UPLOAD_FOLDER)
    return jsonify({"files": output_files})

@app.route("/word-to-pdf", methods=["POST"])
def word_to_pdf():
    file = request.files["file"]
    output_file = os.path.join(UPLOAD_FOLDER, "converted.pdf")
    pdf_tools.word_to_pdf(file, output_file)
    return send_file(output_file, as_attachment=True)

@app.route("/pdf-to-word", methods=["POST"])
def pdf_to_word():
    file = request.files["file"]
    output_file = os.path.join(UPLOAD_FOLDER, "converted.docx")
    pdf_tools.pdf_to_word(file, output_file)
    return send_file(output_file, as_attachment=True)

# -------- TEXT TOOLS --------
@app.route("/text-case", methods=["POST"])
def text_case():
    data = request.json
    text = data.get("text", "")
    mode = data.get("mode", "upper")  # upper, lower, title
    result = text_tools.convert_case(text, mode)
    return jsonify({"result": result})

# -------- IMAGE TOOLS --------
@app.route("/image-compress", methods=["POST"])
def image_compress():
    file = request.files["file"]
    output_file = os.path.join(UPLOAD_FOLDER, "compressed.jpg")
    image_tools.compress_image(file, output_file)
    return send_file(output_file, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
