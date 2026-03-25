# api.srjahir.in — Backend API for SRJ Tools

**Live API:** [api.srjahir.in](https://api.srjahir.in)  
**Frontend:** [tools.srjahir.in](https://tools.srjahir.in)  
**Built by:** [SRJahir Tech](https://srjahir.in) ([@Srj0210](https://github.com/Srj0210))  
**Status:** Live on Render

---

## What Is This?

This is the backend API that powers [SRJ Tools](https://tools.srjahir.in) — a free online PDF toolkit. When someone uses a tool on the frontend that needs server-side processing (like converting a Word document to PDF, merging files, running OCR, etc.), the request comes here.

The frontend sends the file, this API processes it, and sends the result back. Files are automatically deleted after every request — nothing is stored.

It's a Flask app running inside a Docker container on Render.

---

## How It Works (The Big Picture)

```
User uploads file on tools.srjahir.in
        ↓
Frontend sends POST request with file to api.srjahir.in
        ↓
Flask receives the file, saves it to /tmp/uploads
        ↓
The right tool function processes it (convert, merge, compress, etc.)
        ↓
Result is saved to /tmp/outputs
        ↓
Flask sends the processed file back to the user
        ↓
Both input and output files are deleted automatically
```

That's the entire flow. No database, no user accounts, no file storage. Upload → process → return → cleanup.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| **Language** | Python 3.11 |
| **Framework** | Flask 3.0 + Gunicorn |
| **CORS** | Flask-CORS (allows requests from tools.srjahir.in) |
| **PDF Engine** | PyPDF2, pikepdf, pdfminer.six, pypdfium2 |
| **Document Conversion** | LibreOffice (headless mode) |
| **OCR** | Tesseract OCR (English + Gujarati) |
| **Compression** | Ghostscript + pikepdf fallback |
| **PDF Repair** | Ghostscript + QPDF |
| **Excel Handling** | pandas, openpyxl, pdfplumber, reportlab |
| **Image Processing** | Pillow |
| **Containerization** | Docker |
| **Hosting** | Render (Web Service) |

---

## API Endpoints

Every endpoint accepts a `POST` request with files sent as `multipart/form-data`. The response is the processed file as a downloadable blob.

### Organize PDF

| Endpoint | What It Does | Input | Extra Params |
|----------|-------------|-------|-------------|
| `POST /merge-pdf` | Combine multiple PDFs into one | `files` (multiple PDFs) | — |
| `POST /split-pdf` | Extract selected pages | `file` (PDF) | `pages` — comma-separated page numbers (e.g., `1,3,5`) |
| `POST /remove-pages` | Delete specific pages | `file` (PDF) | `pages` — comma-separated page numbers to remove |
| `POST /organize-pdf` | Reorder pages | `file` (PDF) | `order` — comma-separated new page order (0-indexed) |

### Optimize PDF

| Endpoint | What It Does | Input | Extra Params |
|----------|-------------|-------|-------------|
| `POST /compress-pdf` | Reduce file size | `file` (PDF) | `level` — `high`, `balanced` (default), or `low` |
| `POST /repair-pdf` | Fix corrupted PDFs | `file` (PDF) | — |
| `POST /ocr-pdf` | Extract text from scanned PDFs | `file` (PDF or image) | `type` — `text` (default) or `pdf` |

### Convert To PDF

| Endpoint | What It Does | Input | Extra Params |
|----------|-------------|-------|-------------|
| `POST /word-to-pdf` | Convert .doc/.docx to PDF | `file` (Word doc) | — |
| `POST /excel-to-pdf` | Convert .xls/.xlsx to PDF | `file` (Excel file) | — |

### Convert From PDF

| Endpoint | What It Does | Input | Extra Params |
|----------|-------------|-------|-------------|
| `POST /pdf-to-word` | Convert PDF to editable .docx | `file` (PDF) | — |
| `POST /pdf-to-excel` | Extract tables from PDF to .xlsx | `file` (PDF) | — |
| `POST /pdf-to-image` | Convert pages to JPG (returns ZIP) | `file` (PDF) | — |

### Edit PDF

| Endpoint | What It Does | Input | Extra Params |
|----------|-------------|-------|-------------|
| `POST /rotate-pdf` | Rotate all pages | `file` (PDF) | `rotation` — `90`, `180`, or `270` |
| `POST /add-watermark` | Add text or image watermark | `file` (PDF) | `text` or `image` (file), `position` — `center`, `bottom-right`, `diagonal` |
| `POST /sign-pdf` | Add signature to PDF | `file` (PDF) | `text` or `image`, `x`, `y`, `w`, `h`, `page_mode`, `page` |

### PDF Security

| Endpoint | What It Does | Input | Extra Params |
|----------|-------------|-------|-------------|
| `POST /protect-pdf` | Lock PDF with password | `file` (PDF) | `password` — the password to set |
| `POST /unlock-pdf` | Remove password protection | `file` (PDF) | `password` — the existing password |

### Health Check

| Endpoint | What It Does |
|----------|-------------|
| `GET /` | Returns API status and list of available routes |

---

## Project Structure

```
api.srjahir.in/
├── app.py                  # Main Flask app — all routes defined here
├── Dockerfile              # Docker config for Render deployment
├── requirements.txt        # Python dependencies
├── README.md               # You're reading it
│
├── tools/                  # Individual tool modules
│   ├── __init__.py         # Makes /tools a Python package
│   ├── word_to_pdf.py      # Word → PDF (via LibreOffice headless)
│   ├── pdf_to_word.py      # PDF → Word (via pdf2docx)
│   ├── merge_pdf.py        # Merge multiple PDFs (PyPDF2)
│   ├── split_pdf.py        # Extract selected pages (PyPDF2)
│   ├── remove_pages.py     # Delete pages from PDF (PyPDF2)
│   ├── organize_pdf.py     # Reorder pages (PyPDF2)
│   ├── repair_pdf.py       # Fix corrupted PDFs (Ghostscript + QPDF)
│   ├── ocr_pdf.py          # OCR scanned PDFs/images (Tesseract)
│   ├── excel_to_pdf.py     # Excel → PDF (LibreOffice headless)
│   ├── pdf_to_excel.py     # PDF → Excel (pdfplumber + OCR fallback)
│   ├── pdf_to_image.py     # PDF → JPG ZIP (pypdfium2)
│   ├── rotate_pdf.py       # Rotate pages (PyPDF2)
│   ├── add_watermark.py    # Text/image watermark (ReportLab + PyPDF2)
│   ├── sign_pdf.py         # Digital signature overlay (ReportLab + PyPDF2)
│   ├── protect_pdf.py      # Password encrypt PDF (PyPDF2 AES-128)
│   └── unlock_pdf.py       # Remove PDF password (PyPDF2)
│
├── fronts/                 # Font files for watermark/sign rendering
│   └── DejaVuSans.ttf
│
├── uploads/                # Temp upload dir (auto-created at runtime)
│   └── .gitkeep
│
└── outputs/                # Temp output dir (auto-created at runtime)
    └── .gitkeep
```

---

## How Each Tool Works Under the Hood

### Document Conversion (Word/Excel ↔ PDF)
Word-to-PDF and Excel-to-PDF both use **LibreOffice in headless mode**. The Dockerfile installs `libreoffice-writer` and `libreoffice-calc`. When a file comes in, LibreOffice converts it in a temp directory, and the result is sent back. This approach handles complex formatting, tables, charts, and even Indic language fonts (Gujarati, Hindi) because the Docker image includes Noto fonts.

PDF-to-Word uses the `pdf2docx` library, which rebuilds the PDF layout into a Word document — preserving text, images, tables, and basic formatting.

### PDF Manipulation (Merge, Split, Remove, Organize, Rotate)
These all use **PyPDF2**. They read the PDF, manipulate pages (combine, extract, delete, reorder, or rotate), and write a new PDF. It's fast and runs entirely in Python — no external tools needed.

### Compression
PDF compression uses a two-tier approach. First, it tries **Ghostscript** with configurable quality presets (`/screen` for max compression, `/ebook` for balanced, `/prepress` for best quality). If Ghostscript fails for any reason, it falls back to **pikepdf** for lossless optimization.

### PDF Repair
Damaged PDFs go through **Ghostscript** first (which can fix many structural issues by re-writing the file). If that fails, **QPDF** is used as a second-pass repair tool. Between the two, most common PDF corruption issues can be resolved.

### OCR (Optical Character Recognition)
Scanned PDFs and images are processed using **Tesseract OCR**. The tool first renders PDF pages to images using `pypdfium2`, then feeds each image through Tesseract. Currently supports English and Gujarati. The result can be plain text or a searchable PDF.

### PDF to Excel
This uses a smart approach. First, **pdfplumber** tries to detect and extract structured tables. If no tables are found (common with scanned PDFs), it falls back to OCR → text → Excel. This way, even image-based PDFs produce usable output.

### PDF to Image
Pages are rendered to JPG using **pypdfium2** (fast, no Poppler dependency). All images are zipped and returned as a single download.

### Watermark & Signature
Both use **ReportLab** to create an overlay PDF with the watermark/signature, which is then merged onto each page of the original PDF using **PyPDF2**. Text watermarks support custom positioning (center, diagonal, bottom-right). Signatures support precise x/y/w/h placement with per-page or all-pages mode.

### PDF Security (Protect & Unlock)
Protection uses **PyPDF2's AES-128 encryption**. The user provides a password, and the PDF is encrypted with that password. Unlocking reverses the process — you provide the correct password, and a new unprotected PDF is generated.

---

## System Dependencies (Installed via Dockerfile)

These are installed at the OS level inside the Docker container:

| Package | Why It's Needed |
|---------|----------------|
| `libreoffice-writer` | Word → PDF, Excel → PDF conversion |
| `libreoffice-calc` | Excel → PDF conversion |
| `poppler-utils` | PDF rendering utilities |
| `ghostscript` | PDF compression, repair |
| `qpdf` | PDF repair (fallback) |
| `tesseract-ocr` | OCR engine |
| `tesseract-ocr-eng` | English OCR language data |
| `tesseract-ocr-guj` | Gujarati OCR language data |
| `libcairo2` | PDF rendering support |
| `fonts-dejavu` | Fallback fonts |
| `NotoSansGujarati` | Gujarati font support (downloaded in Dockerfile) |

---

## Python Dependencies

```
Flask==3.0.3
gunicorn==22.0.0
Flask-Cors==4.0.0
pdf2docx==0.5.8
python-docx==1.1.2
docx2pdf==0.1.8
PyPDF2==3.0.1
pikepdf==7.0.0
pdfminer.six==20231228
Pillow==10.1.0
pytesseract==0.3.10
pypdfium2==4.21.0
pandas==2.2.2
openpyxl==3.1.2
reportlab==4.1.0
pdfplumber==0.11.0
```

---

## Deployment

The API runs on **Render** as a Docker-based web service.

### How to deploy:

1. Push code to the `main` branch on GitHub
2. Render automatically picks up the change, builds the Docker image, and deploys
3. The service is available at `https://api.srjahir.in`

### Docker build process:
1. Starts from `python:3.11-slim`
2. Installs system packages (LibreOffice, Ghostscript, Tesseract, QPDF, fonts)
3. Installs Python packages from `requirements.txt`
4. Creates temp directories (`/tmp/uploads`, `/tmp/outputs`)
5. Runs the app with Gunicorn (2 workers, 300s timeout)

### Environment:
- **Port:** 10000 (configurable via `PORT` env var)
- **Workers:** 2 Gunicorn workers
- **Timeout:** 300 seconds (to handle large file conversions)

---

## File Handling & Security

- All uploaded files are saved to `/tmp/uploads` temporarily
- Processed output goes to `/tmp/outputs`
- **Both input and output files are deleted immediately** after the response is sent (using Flask's `@after_this_request` decorator)
- No files are retained on the server between requests
- CORS is configured to accept requests (currently open — can be restricted to `tools.srjahir.in` in production)
- File names are sanitized using `werkzeug.utils.secure_filename`
- All communication happens over HTTPS (handled by Render's SSL termination)

---

## Testing Locally

```bash
# Clone the repo
git clone https://github.com/Srj0210/api.srjahir.in.git
cd api.srjahir.in

# Build Docker image
docker build -t srj-api .

# Run container
docker run -p 10000:10000 srj-api

# Test the API
curl http://localhost:10000/
# Should return: {"message": "SRJ Tools API is Live", "status": "ok", ...}

# Test a conversion
curl -X POST -F "file=@test.docx" http://localhost:10000/word-to-pdf --output result.pdf
```

Without Docker (requires LibreOffice, Ghostscript, Tesseract installed locally):
```bash
pip install -r requirements.txt
python app.py
```

---

## How Frontend Talks to This API

The frontend at [tools.srjahir.in](https://tools.srjahir.in) sends requests using the Fetch API:

```javascript
// Example: Word to PDF conversion
const formData = new FormData();
formData.append("file", fileInput.files[0]);

const response = await fetch("https://api.srjahir.in/word-to-pdf", {
  method: "POST",
  body: formData,
});

const blob = await response.blob();
// → Create download link from blob
```

Every tool on the frontend follows this same pattern: upload file(s) → call the right endpoint → get back a blob → trigger download.

---

## Related Repositories

| Repo | What It Is |
|------|-----------|
| [tools.srjahir.in](https://github.com/Srj0210/tools.srjahir.in) | Frontend — the website users interact with |
| **api.srjahir.in** (this repo) | Backend API — processes files and returns results |
| [stocks.srjahir.in](https://github.com/Srj0210/stocks.srjahir.in) | Stock market learning platform |
| [cloudai.srjahir.in](https://github.com/Srj0210/cloudai.srjahir.in) | AI chat assistant |

---

## Contributing

This is a personal project by SRJahir Tech. Found a bug or have an idea? Open an issue on GitHub or reach out at **surajmaitra1996@gmail.com**.

---

**Built by SRJahir Tech. Handles your files, then forgets they existed.**