# tools/html_to_pdf.py
import pdfkit
import os
import tempfile

def html_to_pdf(input_html_path, output_pdf_path):
    """
    Convert uploaded HTML file → PDF using wkhtmltopdf.
    """

    # wkhtmltopdf config (Linux path inside Docker)
    config = pdfkit.configuration(wkhtmltopdf="/usr/bin/wkhtmltopdf")

    # Read HTML
    with open(input_html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    # Temporary cleaned HTML file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
        tmp.write(html_content.encode("utf-8"))
        temp_html = tmp.name

    # PDF options (Unicode + Gujarati + Layout correct)
    options = {
        "encoding": "UTF-8",
        "margin-top": "10mm",
        "margin-bottom": "10mm",
        "margin-left": "10mm",
        "margin-right": "10mm",
        "no-outline": None,
        "print-media-type": None,
        "user-style-sheet": None,
        "custom-header": [
            ("Accept-Encoding", "gzip")
        ],
        "enable-local-file-access": None,
        "dpi": 300
    }

    # Convert (safe & stable)
    pdfkit.from_file(temp_html, output_pdf_path, configuration=config, options=options)

    # Clean temp
    try:
        os.remove(temp_html)
    except:
        pass

    return output_pdf_path
