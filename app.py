import os
import subprocess
from flask import Flask, request, send_file, jsonify, after_this_request
from flask_cors import CORS
from werkzeug.utils import secure_filename
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from fpdf import FPDF

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def safe_remove(path):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception as e:
        print(f"⚠️ Failed to delete {path}: {e}")


def parse_pages_spec(spec: str, total_pages: int):
    """
    Parse user-supplied pages spec (supports commas, ranges, or compact digits).
    Returns sorted unique list of 1-based page numbers within [1, total_pages].
    Examples:
      "1,3,5-7" -> [1,3,5,6,7]
      "5689" -> [5,6,8,9]
      "2-4,7" -> [2,3,4,7]
    """
    if not spec:
        return []

    spec = spec.strip()
    pages = set()

    # If spec contains commas or hyphen, standard parse
    if "," in spec or "-" in spec:
        parts = [p.strip() for p in spec.split(",") if p.strip()]
        for part in parts:
            if "-" in part:
                try:
                    a, b = part.split("-", 1)
                    a = int(a.strip())
                    b = int(b.strip())
                    if a > b:
                        a, b = b, a
                    for n in range(a, b + 1):
                        pages.add(n)
                except Exception:
                    continue
            else:
                try:
                    n = int(part)
                    pages.add(n)
                except Exception:
                    # ignore invalid
                    continue
    else:
        # If no commas/hyphens, treat as compact digits sequence or single number
        # e.g., "5689" -> [5,6,8,9]; "10" -> [10]
        if spec.isdigit():
            # if multi-digit like "10" should be 10 not [1,0]
            # Heuristic: if spec length <= 3 and each char is single-digit pages, parse as digits
            if len(spec) <= 4:  # small heuristic
                # If parsed as full number <= total_pages and length>1, treat as number
                try:
                    full = int(spec)
                    if 1 <= full <= total_pages:
                        pages.add(full)
                    else:
                        # parse each digit as page
                        for ch in spec:
                            pages.add(int(ch))
                except Exception:
                    for ch in spec:
                        pages.add(int(ch))
            else:
                # fallback: parse as digits
                for ch in spec:
                    pages.add(int(ch))
        else:
            # try to parse numbers inside string
            import re
            found = re.findall(r"\d+", spec)
            for f in found:
                pages.add(int(f))

    # keep valid range
    result = sorted([p for p in pages if 1 <= p <= total_pages])
    return result


# ---------------------------
# Word -> PDF (LibreOffice)
# ---------------------------
@app.route("/word-to-pdf", methods=["POST"])
def word_to_pdf():
    try:
        file = request.files.get("file")
        if not file:
            return jsonify({"error": "No file uploaded"}), 400

        filename = secure_filename(file.filename)
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(input_path)

        original_name = os.path.splitext(filename)[0]
        output_filename = f"{original_name}.pdf"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)

        # convert via LibreOffice
        subprocess.run([
            "libreoffice", "--headless", "--convert-to", "pdf",
            "--outdir", OUTPUT_FOLDER, input_path
        ], check=True)

        # LibreOffice typically creates <inputbase>.pdf; ensure rename if necessary
        converted = os.path.join(OUTPUT_FOLDER, os.path.splitext(filename)[0] + ".pdf")
        if os.path.exists(converted) and converted != output_path:
            try:
                os.replace(converted, output_path)
            except Exception:
                pass

        @after_this_request
        def cleanup(response):
            # delete input and output after response delivered
            safe_remove(input_path)
            # don't remove output until after response has been returned to client by send_file
            return response

        resp = send_file(output_path, as_attachment=True, download_name=output_filename)
        # schedule output removal after response has been created
        safe_remove(output_path)
        return resp

    except subprocess.CalledProcessError:
        safe_remove(input_path)
        return jsonify({"error": "Conversion failed — LibreOffice error"}), 500
    except Exception as e:
        safe_remove(input_path)
        return jsonify({"error": str(e)}), 500


# ---------------------------
# PDF -> Word (Unoconv + LibreOffice)
# ---------------------------
@app.route("/pdf-to-word", methods=["POST"])
def pdf_to_word():
    try:
        file = request.files.get("file")
        if not file:
            return jsonify({"error": "No file uploaded"}), 400

        filename = secure_filename(file.filename)
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(input_path)

        original_name = os.path.splitext(filename)[0]
        output_filename = f"{original_name}.docx"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)

        # ✅ Try conversion via unoconv (most reliable for PDF -> DOCX)
        subprocess.run([
            "unoconv", "-f", "docx", "-o", output_path, input_path
        ], check=True)

        @after_this_request
        def cleanup(response):
            safe_remove(input_path)
            return response

        resp = send_file(output_path, as_attachment=True, download_name=output_filename)
        safe_remove(output_path)
        return resp

    except subprocess.CalledProcessError:
        safe_remove(input_path)
        return jsonify({
            "error": "Conversion failed — LibreOffice or unoconv not available"
        }), 500
    except Exception as e:
        safe_remove(input_path)
        return jsonify({"error": str(e)}), 500


# ---------------------------
# Merge PDF (lossless)
# ---------------------------
@app.route("/merge-pdf", methods=["POST"])
def merge_pdf():
    try:
        files = request.files.getlist("files")
        if not files or len(files) < 1:
            return jsonify({"error": "No files uploaded"}), 400

        merger = PdfMerger()
        temp_paths = []

        for file in files:
            fn = secure_filename(file.filename)
            p = os.path.join(UPLOAD_FOLDER, fn)
            file.save(p)
            merger.append(p)
            temp_paths.append(p)

        output_filename = "merged.pdf"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        merger.write(output_path)
        merger.close()

        @after_this_request
        def cleanup(response):
            for t in temp_paths:
                safe_remove(t)
            return response

        resp = send_file(output_path, as_attachment=True, download_name=output_filename)
        safe_remove(output_path)
        return resp

    except Exception as e:
        for t in temp_paths:
            safe_remove(t)
        return jsonify({"error": str(e)}), 500


# ---------------------------
# Split PDF (custom pages selection)
# ---------------------------
@app.route("/split-pdf", methods=["POST"])
def split_pdf():
    try:
        file = request.files.get("file")
        pages_spec = request.form.get("pages", "").strip()  # user input string
        if not file:
            return jsonify({"error": "No file uploaded"}), 400

        filename = secure_filename(file.filename)
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(input_path)

        reader = PdfReader(input_path)
        total_pages = len(reader.pages)

        # If pages_spec empty, default to all pages
        if not pages_spec:
            selected = list(range(1, total_pages + 1))
        else:
            selected = parse_pages_spec(pages_spec, total_pages)

        if not selected:
            safe_remove(input_path)
            return jsonify({"error": "No valid pages selected"}), 400

        writer = PdfWriter()
        for p in selected:
            # pages are 1-indexed for users
            idx = p - 1
            if 0 <= idx < total_pages:
                writer.add_page(reader.pages[idx])

        output_filename = f"split_{'_'.join(str(x) for x in selected)}.pdf"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)

        with open(output_path, "wb") as f_out:
            writer.write(f_out)

        @after_this_request
        def cleanup(response):
            safe_remove(input_path)
            return response

        resp = send_file(output_path, as_attachment=True, download_name=output_filename)
        safe_remove(output_path)
        return resp

    except Exception as e:
        safe_remove(input_path)
        return jsonify({"error": str(e)}), 500


# ---------------------------
# Text -> PDF
# ---------------------------
@app.route("/text-to-pdf", methods=["POST"])
def text_to_pdf():
    try:
        text = request.form.get("text", "")
        if not text.strip():
            return jsonify({"error": "No text provided"}), 400

        output_filename = f"text_{os.urandom(6).hex()}.pdf"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)

        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Helvetica", size=12)
        for line in text.splitlines():
            pdf.multi_cell(0, 10, line)
        pdf.output(output_path)

        @after_this_request
        def cleanup(response):
            return response

        resp = send_file(output_path, as_attachment=True, download_name="text.pdf")
        safe_remove(output_path)
        return resp

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Root
@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "SRJahir Tools API", "ready": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))