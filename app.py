import os
import time
import logging
import tempfile
import shutil
import hashlib
from flask import Flask, request, jsonify, send_file, after_this_request, g
from werkzeug.utils import secure_filename
from flask_cors import CORS
from collections import defaultdict
import threading

# === Import tool functions ===
from tools.word_to_pdf    import word_to_pdf
from tools.pdf_to_word    import pdf_to_word
from tools.merge_pdf      import merge_pdf
from tools.split_pdf      import split_selected_pages
from tools.remove_pages   import remove_pages
from tools.organize_pdf   import organize_pdf
from tools.repair_pdf     import repair_pdf
from tools.ocr_pdf        import run_ocr
from tools.excel_to_pdf   import excel_to_pdf
from tools.pdf_to_excel   import pdf_to_excel
from tools.pdf_to_image   import pdf_to_image
from tools.rotate_pdf     import rotate_pdf
from tools.add_watermark  import add_text_watermark, add_image_watermark
from tools.protect_pdf    import protect_pdf
from tools.unlock_pdf     import unlock_pdf
from tools.sign_pdf       import sign_pdf
from tools.compress_pdf   import compress_pdf as _compress_pdf_tool

# ══════════════════════════════════════════════════════
# FLASK APP SETUP
# ══════════════════════════════════════════════════════
app = Flask(__name__)

# ── CORS: ONLY allow requests from your own sites ─────
ALLOWED_ORIGINS = [
    "https://tools.srjahir.in",
    "https://www.tools.srjahir.in",
    "http://localhost:3000",   # local dev only
    "http://127.0.0.1:5500",  # VS Code Live Server dev
]
CORS(app, origins=ALLOWED_ORIGINS, supports_credentials=False)

# ── File size limit: 50 MB max ────────────────────────
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB

# ── Temp folders ──────────────────────────────────────
UPLOAD_FOLDER = "/tmp/uploads"
OUTPUT_FOLDER = "/tmp/outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ── Logging ───────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("srj-api")


# ══════════════════════════════════════════════════════
# RATE LIMITER (simple in-memory, per IP)
# ══════════════════════════════════════════════════════
_rate_store = defaultdict(list)
_rate_lock  = threading.Lock()

RATE_LIMIT      = 20    # requests
RATE_WINDOW     = 60    # per 60 seconds
BURST_LIMIT     = 5     # max in 5 seconds
BURST_WINDOW    = 5

def get_client_ip():
    """Get real client IP even behind Render proxy."""
    return (request.headers.get('X-Forwarded-For', '').split(',')[0].strip()
            or request.remote_addr or '0.0.0.0')

def check_rate_limit(ip: str) -> tuple[bool, str]:
    now = time.time()
    with _rate_lock:
        times = _rate_store[ip]
        # Clean old entries
        times[:] = [t for t in times if now - t < RATE_WINDOW]

        # Burst check (5 req in 5 sec)
        burst_times = [t for t in times if now - t < BURST_WINDOW]
        if len(burst_times) >= BURST_LIMIT:
            return False, f"Too many requests. Slow down (max {BURST_LIMIT} per {BURST_WINDOW}s)."

        # Window check (20 req in 60 sec)
        if len(times) >= RATE_LIMIT:
            return False, f"Rate limit exceeded (max {RATE_LIMIT} per {RATE_WINDOW}s)."

        times.append(now)
        return True, ""

# ══════════════════════════════════════════════════════
# FILE VALIDATION (magic bytes — not just extension)
# ══════════════════════════════════════════════════════
# Magic bytes for allowed file types
FILE_SIGNATURES = {
    'pdf':  [(0, b'%PDF')],
    'docx': [(0, b'PK\x03\x04')],   # ZIP-based (docx, xlsx)
    'xlsx': [(0, b'PK\x03\x04')],
    'doc':  [(0, b'\xd0\xcf\x11\xe0')],  # OLE compound document
    'xls':  [(0, b'\xd0\xcf\x11\xe0')],
    'jpg':  [(0, b'\xff\xd8\xff')],
    'png':  [(0, b'\x89PNG')],
    'webp': [(8, b'WEBP')],
}

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'jpg', 'jpeg', 'png', 'webp'}

def validate_file(file_storage, expected_types: list) -> tuple[bool, str]:
    """Validate file by magic bytes, not just extension."""
    filename = secure_filename(file_storage.filename)
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''

    if ext not in ALLOWED_EXTENSIONS:
        return False, f"File type .{ext} not allowed."

    if ext not in expected_types:
        return False, f"Expected {expected_types}, got .{ext}."

    # Read first 16 bytes for magic check
    file_storage.seek(0)
    header = file_storage.read(16)
    file_storage.seek(0)

    if ext in ('jpeg', 'jpg'):
        ext = 'jpg'

    sigs = FILE_SIGNATURES.get(ext, [])
    if sigs:
        valid = any(header[offset:offset+len(sig)] == sig for offset, sig in sigs)
        if not valid:
            return False, f"File content does not match .{ext} format."

    return True, ""

# ══════════════════════════════════════════════════════
# SECURITY HEADERS MIDDLEWARE
# ══════════════════════════════════════════════════════
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options']  = 'nosniff'
    response.headers['X-Frame-Options']         = 'DENY'
    response.headers['X-XSS-Protection']        = '1; mode=block'
    response.headers['Referrer-Policy']          = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy']       = 'geolocation=(), microphone=(), camera=()'
    # Don't cache sensitive file outputs
    if request.path != '/':
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
    return response

# ══════════════════════════════════════════════════════
# REQUEST MIDDLEWARE — rate limit + logging
# ══════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════
# ALLOWED ORIGINS / REFERERS
# ══════════════════════════════════════════════════════
TRUSTED_ORIGINS = {
    "https://tools.srjahir.in",
    "https://www.tools.srjahir.in",
}
# Allow localhost only when DEBUG env var is set
if os.environ.get("DEBUG"):
    TRUSTED_ORIGINS.update({
        "http://localhost:3000",
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    })

def is_trusted_request() -> bool:
    """
    Check Origin + Referer headers.
    Both are set automatically by browsers and cannot be
    faked by other websites (CORS policy enforces this).
    Direct curl/Postman calls from outside will be blocked.
    """
    origin  = request.headers.get("Origin", "").rstrip("/")
    referer = request.headers.get("Referer", "")

    # Origin check (present on cross-origin requests)
    if origin and origin in TRUSTED_ORIGINS:
        return True

    # Referer check (present on same-origin + form submits)
    if any(referer.startswith(o) for o in TRUSTED_ORIGINS):
        return True

    return False


@app.before_request
def before_request():
    g.start_time = time.time()
    ip     = get_client_ip()
    origin = request.headers.get("Origin", "no-origin")

    # Health check — always allow
    if request.path == "/":
        return

    # ── ORIGIN / REFERER GUARD ────────────────────────
    if not is_trusted_request():
        logger.warning(
            f"BLOCKED | ip={ip} | path={request.path} | "
            f"origin={origin} | referer={request.headers.get('Referer','none')}"
        )
        return jsonify({"error": "Access denied"}), 403

    # ── RATE LIMIT ────────────────────────────────────
    allowed, msg = check_rate_limit(ip)
    if not allowed:
        logger.warning(f"RATE_LIMIT | ip={ip} | path={request.path}")
        return jsonify({"error": msg}), 429

    logger.info(
        f"REQUEST | ip={ip} | {request.method} {request.path} | origin={origin}"
    )

@app.after_request
def log_response(response):
    if request.path != '/':
        elapsed = round((time.time() - g.get('start_time', time.time())) * 1000)
        ip = get_client_ip()
        logger.info(f"RESPONSE | ip={ip} | {request.path} | {response.status_code} | {elapsed}ms")
    return response

# ══════════════════════════════════════════════════════
# ERROR HANDLERS (no stack trace leakage)
# ══════════════════════════════════════════════════════
@app.errorhandler(400)
def bad_request(e):
    return jsonify({"error": "Bad request"}), 400

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(413)
def file_too_large(e):
    return jsonify({"error": "File too large. Maximum size is 50MB."}), 413

@app.errorhandler(429)
def too_many_requests(e):
    return jsonify({"error": "Too many requests. Please wait and try again."}), 429

@app.errorhandler(500)
def server_error(e):
    logger.error(f"SERVER_ERROR | {request.path} | {str(e)}")
    return jsonify({"error": "Internal server error. Please try again."}), 500

# ══════════════════════════════════════════════════════
# HELPER: safe temp file cleanup
# ══════════════════════════════════════════════════════
def cleanup_files(*paths):
    @after_this_request
    def do_cleanup(response):
        for p in paths:
            try:
                if p and os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass
        return response
    return do_cleanup

# ══════════════════════════════════════════════════════
# ROUTES INFO
# ══════════════════════════════════════════════════════
ROUTES_INFO = {
    "service": "SRJahir Tools API",
    "status":  "live",
    "version": "2.0.0",
    "endpoints": {
        "merge":       "/merge-pdf",
        "split":       "/split-pdf",
        "remove":      "/remove-pages",
        "organize":    "/organize-pdf",
        "compress":    "/compress-pdf",
        "repair":      "/repair-pdf",
        "ocr":         "/ocr-pdf",
        "word_to_pdf": "/word-to-pdf",
        "excel_to_pdf":"/excel-to-pdf",
        "pdf_to_word": "/pdf-to-word",
        "pdf_to_excel":"/pdf-to-excel",
        "pdf_to_image":"/pdf-to-image",
        "rotate":      "/rotate-pdf",
        "watermark":   "/add-watermark",
        "sign":        "/sign-pdf",
        "protect":     "/protect-pdf",
        "unlock":      "/unlock-pdf",
    }
}

@app.route("/")
def index():
    return jsonify(ROUTES_INFO)

# ══════════════════════════════════════════════════════
# ALL TOOL ROUTES
# ══════════════════════════════════════════════════════

@app.route("/merge-pdf", methods=["POST"])
def route_merge_pdf():
    if "files" not in request.files:
        return jsonify({"error": "No files uploaded"}), 400
    files = request.files.getlist("files")
    if len(files) < 2:
        return jsonify({"error": "At least 2 PDFs required"}), 400
    for f in files:
        ok, msg = validate_file(f, ['pdf'])
        if not ok:
            return jsonify({"error": msg}), 400

    output = tempfile.mktemp(suffix="_merged.pdf", dir="/tmp")
    try:
        merge_pdf(files, output)
        cleanup_files(output)
        return send_file(output, as_attachment=True,
                        download_name="merged.pdf", mimetype="application/pdf")
    except Exception as e:
        logger.error(f"merge-pdf error: {e}")
        return jsonify({"error": "Merge failed"}), 500


@app.route("/split-pdf", methods=["POST"])
def route_split_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file  = request.files["file"]
    pages = request.form.get("pages", "")
    ok, msg = validate_file(file, ['pdf'])
    if not ok:
        return jsonify({"error": msg}), 400

    inp = tempfile.mktemp(suffix="_in.pdf", dir="/tmp")
    out = tempfile.mktemp(suffix="_split.pdf", dir="/tmp")
    file.save(inp)
    try:
        page_list = [int(p.strip()) for p in pages.split(",") if p.strip().isdigit()]
        if not page_list:
            return jsonify({"error": "Invalid page numbers"}), 400
        split_selected_pages(inp, out, page_list)
        cleanup_files(inp, out)
        return send_file(out, as_attachment=True,
                        download_name="split.pdf", mimetype="application/pdf")
    except Exception as e:
        logger.error(f"split-pdf error: {e}")
        return jsonify({"error": "Split failed"}), 500


@app.route("/remove-pages", methods=["POST"])
def route_remove_pages():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file  = request.files["file"]
    pages = request.form.get("pages", "")
    ok, msg = validate_file(file, ['pdf'])
    if not ok:
        return jsonify({"error": msg}), 400

    inp = tempfile.mktemp(suffix="_in.pdf", dir="/tmp")
    out = tempfile.mktemp(suffix="_removed.pdf", dir="/tmp")
    file.save(inp)
    try:
        page_list = [int(p.strip()) for p in pages.split(",") if p.strip().isdigit()]
        remove_pages(inp, out, page_list)
        cleanup_files(inp, out)
        return send_file(out, as_attachment=True,
                        download_name="removed.pdf", mimetype="application/pdf")
    except Exception as e:
        logger.error(f"remove-pages error: {e}")
        return jsonify({"error": "Remove pages failed"}), 500


@app.route("/organize-pdf", methods=["POST"])
def route_organize_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file  = request.files["file"]
    order = request.form.get("order", "")
    ok, msg = validate_file(file, ['pdf'])
    if not ok:
        return jsonify({"error": msg}), 400

    inp = tempfile.mktemp(suffix="_in.pdf", dir="/tmp")
    out = tempfile.mktemp(suffix="_organized.pdf", dir="/tmp")
    file.save(inp)
    try:
        order_list = [int(p.strip()) for p in order.split(",") if p.strip().isdigit()]
        organize_pdf(inp, out, order_list)
        cleanup_files(inp, out)
        return send_file(out, as_attachment=True,
                        download_name="organized.pdf", mimetype="application/pdf")
    except Exception as e:
        logger.error(f"organize-pdf error: {e}")
        return jsonify({"error": "Organize failed"}), 500


@app.route("/compress-pdf", methods=["POST"])
def route_compress_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file  = request.files["file"]
    level = request.form.get("level", "balanced")
    if level not in ("high", "balanced", "low"):
        level = "balanced"
    ok, msg = validate_file(file, ['pdf'])
    if not ok:
        return jsonify({"error": msg}), 400

    inp = tempfile.mktemp(suffix="_in.pdf", dir="/tmp")
    out = tempfile.mktemp(suffix="_compressed.pdf", dir="/tmp")
    file.save(inp)
    try:
        _compress_pdf_tool(inp, out, level)
        cleanup_files(inp, out)
        return send_file(out, as_attachment=True,
                        download_name="compressed.pdf", mimetype="application/pdf")
    except Exception as e:
        logger.error(f"compress-pdf error: {e}")
        return jsonify({"error": "Compression failed"}), 500


@app.route("/repair-pdf", methods=["POST"])
def route_repair_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files["file"]
    ok, msg = validate_file(file, ['pdf'])
    if not ok:
        return jsonify({"error": msg}), 400

    inp = tempfile.mktemp(suffix="_in.pdf", dir="/tmp")
    out = tempfile.mktemp(suffix="_repaired.pdf", dir="/tmp")
    file.save(inp)
    try:
        repair_pdf(inp, out)
        cleanup_files(inp, out)
        return send_file(out, as_attachment=True,
                        download_name="repaired.pdf", mimetype="application/pdf")
    except Exception as e:
        logger.error(f"repair-pdf error: {e}")
        return jsonify({"error": "Repair failed"}), 500


@app.route("/ocr-pdf", methods=["POST"])
def route_ocr_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file        = request.files["file"]
    output_type = request.form.get("output_type", "text")
    if output_type not in ("text", "pdf"):
        output_type = "text"
    ok, msg = validate_file(file, ['pdf'])
    if not ok:
        return jsonify({"error": msg}), 400

    inp = tempfile.mktemp(suffix="_in.pdf", dir="/tmp")
    ext = ".txt" if output_type == "text" else ".pdf"
    out = tempfile.mktemp(suffix=f"_ocr{ext}", dir="/tmp")
    file.save(inp)
    try:
        run_ocr(inp, out, output_type)
        mime = "text/plain" if output_type == "text" else "application/pdf"
        name = f"ocr_output{ext}"
        cleanup_files(inp, out)
        return send_file(out, as_attachment=True,
                        download_name=name, mimetype=mime)
    except Exception as e:
        logger.error(f"ocr-pdf error: {e}")
        return jsonify({"error": "OCR failed"}), 500


@app.route("/word-to-pdf", methods=["POST"])
def route_word_to_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files["file"]
    ok, msg = validate_file(file, ['doc', 'docx'])
    if not ok:
        return jsonify({"error": msg}), 400

    inp = tempfile.mktemp(suffix=f"_{secure_filename(file.filename)}", dir="/tmp")
    out = tempfile.mktemp(suffix="_output.pdf", dir="/tmp")
    file.save(inp)
    try:
        word_to_pdf(inp, out)
        cleanup_files(inp, out)
        return send_file(out, as_attachment=True,
                        download_name="converted.pdf", mimetype="application/pdf")
    except Exception as e:
        logger.error(f"word-to-pdf error: {e}")
        return jsonify({"error": "Word to PDF failed"}), 500


@app.route("/excel-to-pdf", methods=["POST"])
def route_excel_to_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files["file"]
    ok, msg = validate_file(file, ['xls', 'xlsx'])
    if not ok:
        return jsonify({"error": msg}), 400

    inp = tempfile.mktemp(suffix=f"_{secure_filename(file.filename)}", dir="/tmp")
    out = tempfile.mktemp(suffix="_output.pdf", dir="/tmp")
    file.save(inp)
    try:
        excel_to_pdf(inp, out)
        cleanup_files(inp, out)
        return send_file(out, as_attachment=True,
                        download_name="converted.pdf", mimetype="application/pdf")
    except Exception as e:
        logger.error(f"excel-to-pdf error: {e}")
        return jsonify({"error": "Excel to PDF failed"}), 500


@app.route("/pdf-to-word", methods=["POST"])
def route_pdf_to_word():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files["file"]
    ok, msg = validate_file(file, ['pdf'])
    if not ok:
        return jsonify({"error": msg}), 400

    inp = tempfile.mktemp(suffix="_in.pdf", dir="/tmp")
    out = tempfile.mktemp(suffix="_output.docx", dir="/tmp")
    file.save(inp)
    try:
        pdf_to_word(inp, out)
        cleanup_files(inp, out)
        return send_file(out, as_attachment=True,
                        download_name="converted.docx",
                        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    except Exception as e:
        logger.error(f"pdf-to-word error: {e}")
        return jsonify({"error": "PDF to Word failed"}), 500


@app.route("/pdf-to-excel", methods=["POST"])
def route_pdf_to_excel():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files["file"]
    ok, msg = validate_file(file, ['pdf'])
    if not ok:
        return jsonify({"error": msg}), 400

    inp = tempfile.mktemp(suffix="_in.pdf", dir="/tmp")
    out = tempfile.mktemp(suffix="_output.xlsx", dir="/tmp")
    file.save(inp)
    try:
        pdf_to_excel(inp, out)
        cleanup_files(inp, out)
        return send_file(out, as_attachment=True,
                        download_name="converted.xlsx",
                        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as e:
        logger.error(f"pdf-to-excel error: {e}")
        return jsonify({"error": "PDF to Excel failed"}), 500


@app.route("/pdf-to-image", methods=["POST"])
def route_pdf_to_image():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files["file"]
    ok, msg = validate_file(file, ['pdf'])
    if not ok:
        return jsonify({"error": msg}), 400

    inp = tempfile.mktemp(suffix="_in.pdf", dir="/tmp")
    out = tempfile.mktemp(suffix="_images.zip", dir="/tmp")
    file.save(inp)
    try:
        pdf_to_image(inp, out)
        cleanup_files(inp, out)
        return send_file(out, as_attachment=True,
                        download_name="pdf_pages.zip", mimetype="application/zip")
    except Exception as e:
        logger.error(f"pdf-to-image error: {e}")
        return jsonify({"error": "PDF to Image failed"}), 500


@app.route("/rotate-pdf", methods=["POST"])
def route_rotate_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file     = request.files["file"]
    rotation = request.form.get("rotation", "90")
    ok, msg = validate_file(file, ['pdf'])
    if not ok:
        return jsonify({"error": msg}), 400

    try:
        rotation = int(rotation)
        if rotation not in (90, 180, 270):
            return jsonify({"error": "Rotation must be 90, 180 or 270"}), 400
    except ValueError:
        return jsonify({"error": "Invalid rotation value"}), 400

    inp = tempfile.mktemp(suffix="_in.pdf", dir="/tmp")
    out = tempfile.mktemp(suffix="_rotated.pdf", dir="/tmp")
    file.save(inp)
    try:
        rotate_pdf(inp, out, rotation)
        cleanup_files(inp, out)
        return send_file(out, as_attachment=True,
                        download_name="rotated.pdf", mimetype="application/pdf")
    except Exception as e:
        logger.error(f"rotate-pdf error: {e}")
        return jsonify({"error": "Rotate failed"}), 500


@app.route("/add-watermark", methods=["POST"])
def route_add_watermark():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file          = request.files["file"]
    watermark_text= request.form.get("text", "")
    position      = request.form.get("position", "diagonal")
    ok, msg = validate_file(file, ['pdf'])
    if not ok:
        return jsonify({"error": msg}), 400

    # Sanitise text input
    watermark_text = watermark_text[:100].strip()
    if not watermark_text:
        return jsonify({"error": "Watermark text is required"}), 400

    inp = tempfile.mktemp(suffix="_in.pdf", dir="/tmp")
    out = tempfile.mktemp(suffix="_watermarked.pdf", dir="/tmp")
    file.save(inp)
    try:
        add_text_watermark(inp, out, watermark_text, position)
        cleanup_files(inp, out)
        return send_file(out, as_attachment=True,
                        download_name="watermarked.pdf", mimetype="application/pdf")
    except Exception as e:
        logger.error(f"add-watermark error: {e}")
        return jsonify({"error": "Watermark failed"}), 500


@app.route("/sign-pdf", methods=["POST"])
def route_sign_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file      = request.files["file"]
    sign_text = request.form.get("text", "").strip()[:80]
    page_mode = request.form.get("page_mode", "all")
    if page_mode not in ("all", "single"):
        page_mode = "all"
    ok, msg = validate_file(file, ['pdf'])
    if not ok:
        return jsonify({"error": msg}), 400

    inp = tempfile.mktemp(suffix="_in.pdf", dir="/tmp")
    out = tempfile.mktemp(suffix="_signed.pdf", dir="/tmp")
    file.save(inp)
    try:
        sign_pdf(inp, out, text=sign_text, page_mode=page_mode)
        cleanup_files(inp, out)
        return send_file(out, as_attachment=True,
                        download_name="signed.pdf", mimetype="application/pdf")
    except Exception as e:
        logger.error(f"sign-pdf error: {e}")
        return jsonify({"error": "Sign failed"}), 500


@app.route("/protect-pdf", methods=["POST"])
def route_protect_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file     = request.files["file"]
    password = request.form.get("password", "").strip()
    ok, msg = validate_file(file, ['pdf'])
    if not ok:
        return jsonify({"error": msg}), 400

    if not password or len(password) < 4:
        return jsonify({"error": "Password must be at least 4 characters"}), 400
    if len(password) > 64:
        return jsonify({"error": "Password too long (max 64 chars)"}), 400

    inp = tempfile.mktemp(suffix="_in.pdf", dir="/tmp")
    out = tempfile.mktemp(suffix="_protected.pdf", dir="/tmp")
    file.save(inp)
    try:
        protect_pdf(inp, out, password)
        cleanup_files(inp, out)
        return send_file(out, as_attachment=True,
                        download_name="protected.pdf", mimetype="application/pdf")
    except Exception as e:
        logger.error(f"protect-pdf error: {e}")
        return jsonify({"error": "Protect failed"}), 500


@app.route("/unlock-pdf", methods=["POST"])
def route_unlock_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file     = request.files["file"]
    password = request.form.get("password", "").strip()
    ok, msg = validate_file(file, ['pdf'])
    if not ok:
        return jsonify({"error": msg}), 400

    if len(password) > 64:
        return jsonify({"error": "Password too long"}), 400

    inp = tempfile.mktemp(suffix="_in.pdf", dir="/tmp")
    out = tempfile.mktemp(suffix="_unlocked.pdf", dir="/tmp")
    file.save(inp)
    try:
        unlock_pdf(inp, out, password)
        cleanup_files(inp, out)
        return send_file(out, as_attachment=True,
                        download_name="unlocked.pdf", mimetype="application/pdf")
    except RuntimeError:
        return jsonify({"error": "Invalid password"}), 400
    except Exception as e:
        logger.error(f"unlock-pdf error: {e}")
        return jsonify({"error": "Unlock failed"}), 500


# ══════════════════════════════════════════════════════
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
