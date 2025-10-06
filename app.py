def docx_to_pdf_simple(docx_path, pdf_out_path):
    """
    High-fidelity DOCX → PDF conversion for SRJahir Tools.
    Keeps font size, bold, color, bullet points, headings — like Word.
    """

    from docx.shared import RGBColor

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

    def rgb_to_fpdf(rgb):
        """Convert RGBColor object → FPDF color tuple"""
        if not rgb:
            return (0, 0, 0)
        return (rgb.rgb[0], rgb.rgb[1], rgb.rgb[2])

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

        # Check first run for formatting info
        if para.runs:
            run = para.runs[0]
            if run.font.size:
                font_size = run.font.size.pt
            if run.bold:
                font_style = "B"
            if run.font.color and run.font.color.rgb:
                rgb = run.font.color.rgb
                font_color = (rgb >> 16, (rgb >> 8) & 255, rgb & 255)

        # Heading detection overrides color/size
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