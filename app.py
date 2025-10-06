import os, uuid, io, time, subprocess, threading
from zipfile import ZipFile
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader, PdfWriter, PdfMerger
from fpdf import FPDF
from docx import Document

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
for f in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
    os.makedirs(f, exist_ok=True)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# ---------------- Auto cleanup (every 6h) ----------------
def cleanup_old_files(hours=6):
    cutoff = time.time() - hours * 3600
    for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
        for f in os.listdir(folder):
            p = os.path.join(folder, f)
            if os.path.isfile(p) and os.path.getmtime(p) < cutoff:
                try: os.remove(p)
                except: pass
    threading.Timer(hours * 3600, cleanup_old_files).start()
cleanup_old_files()

# ---------------- Helpers ----------------
def save_upload_file(fs):
    fn = secure_filename(fs.filename)
    path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4().hex}_{fn}")
    fs.save(path)
    return path, fn

def send_and_cleanup(path, name, mime):
    buf = io.BytesIO()
    with open(path, "rb") as f: buf.write(f.read())
    buf.seek(0)
    try: os.remove(path)
    except: pass
    return send_file(buf, as_attachment=True, download_name=name, mimetype=mime)

# ---------------- Routes ----------------
@app.route("/")
def home():
    return jsonify({"status":"API running","tools":["word-to-pdf","pdf-to-word","merge-pdf","split-pdf","text-to-pdf"]})

# Word → PDF  (pixel-perfect)
@app.route("/word-to-pdf", methods=["POST"])
def word_to_pdf():
    if "file" not in request.files:
        return jsonify({"error":"No file uploaded"}),400
    f = request.files["file"]
    if not f.filename.lower().endswith(".docx"):
        return jsonify({"error":"Only .docx supported"}),400

    in_path, orig = save_upload_file(f)
    out_name = os.path.splitext(orig)[0]+".pdf"
    try:
        subprocess.run(["libreoffice","--headless","--convert-to","pdf","--outdir",OUTPUT_FOLDER,in_path],check=True)
    except subprocess.CalledProcessError as e:
        return jsonify({"error":"Conversion failed","detail":str(e)}),500
    finally:
        try: os.remove(in_path)
        except: pass

    out_path = os.path.join(OUTPUT_FOLDER,out_name)
    return send_and_cleanup(out_path,out_name,"application/pdf")

# Text → PDF
@app.route("/text-to-pdf", methods=["POST"])
def text_to_pdf():
    text = request.form.get("text","")
    if not text.strip():
        return jsonify({"error":"No text"}),400
    out_name=f"text_{uuid.uuid4().hex}.pdf"
    out_path=os.path.join(OUTPUT_FOLDER,out_name)
    pdf=FPDF();pdf.add_page();pdf.set_font("Arial",size=12);pdf.multi_cell(0,6,text);pdf.output(out_path)
    return send_and_cleanup(out_path,out_name,"application/pdf")

# Merge PDF
@app.route("/merge-pdf",methods=["POST"])
def merge_pdf():
    files=request.files.getlist("files")
    if not files: return jsonify({"error":"No files"}),400
    merger=PdfMerger();paths=[]
    for f in files:
        p,_=save_upload_file(f);paths.append(p);merger.append(p)
    out_name=f"merged_{uuid.uuid4().hex}.pdf"
    out_path=os.path.join(OUTPUT_FOLDER,out_name)
    merger.write(out_path);merger.close()
    for p in paths:
        try: os.remove(p)
        except: pass
    return send_and_cleanup(out_path,out_name,"application/pdf")

# Split PDF
@app.route("/split-pdf",methods=["POST"])
def split_pdf():
    if "file" not in request.files: return jsonify({"error":"No file"}),400
    f=request.files["file"]
    path,_=save_upload_file(f)
    reader=PdfReader(path)
    zip_path=os.path.join(OUTPUT_FOLDER,f"{uuid.uuid4().hex}.zip")
    with ZipFile(zip_path,"w") as z:
        for i,p in enumerate(reader.pages,1):
            w=PdfWriter();w.add_page(p)
            single=os.path.join(OUTPUT_FOLDER,f"page_{i}.pdf")
            with open(single,"wb") as out: w.write(out)
            z.write(single,f"page_{i}.pdf");os.remove(single)
    os.remove(path)
    return send_and_cleanup(zip_path,"split_pages.zip","application/zip")

# PDF → Word
@app.route("/pdf-to-word",methods=["POST"])
def pdf_to_word():
    if "file" not in request.files: return jsonify({"error":"No file"}),400
    f=request.files["file"]
    path,orig=save_upload_file(f)
    try:
        r=PdfReader(path);d=Document()
        for p in r.pages:
            t=p.extract_text() or "";d.add_paragraph(t)
        out=os.path.join(OUTPUT_FOLDER,f"{uuid.uuid4().hex}.docx")
        d.save(out)
    except Exception as e:
        return jsonify({"error":"PDF→Word failed","detail":str(e)}),500
    finally: os.remove(path)
    return send_and_cleanup(out,"converted.docx","application/vnd.openxmlformats-officedocument.wordprocessingml.document")

# Optional cleanup endpoint (for JS)
@app.route("/cleanup",methods=["POST"])
def cleanup_endpoint():
    data=request.get_json(force=True)
    p=data.get("path")
    if p and os.path.exists(p):
        try: os.remove(p);return jsonify({"status":"deleted"})
        except Exception as e: return jsonify({"error":str(e)}),500
    return jsonify({"status":"not_found"})

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)),debug=False)