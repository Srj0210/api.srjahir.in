import os
from flask import Flask, request, jsonify, send_file, after_this_request
from werkzeug.utils import secure_filename
from tools.word_to_pdf import word_to_pdf
import tempfile, shutil

app = Flask(__name__)

UPLOAD_FOLDER = "/tmp/uploads"
OUTPUT_FOLDER = "/tmp/outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "SRJ Tools API is Live 🚀",
        "status": "ok",
        "routes": ["/word-to-pdf"]
    })

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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
