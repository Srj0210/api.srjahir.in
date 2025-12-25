# ========== PDF → EXCEL ==========
@app.route("/pdf-to-excel", methods=["POST"])
def convert_pdf_to_excel():
    try:
        file = request.files.get("file")
        if not file:
            return jsonify({"error": "No PDF uploaded"}), 400

        name = os.path.splitext(secure_filename(file.filename))[0]

        in_path = os.path.join(UPLOAD_FOLDER, file.filename)
        out_path = os.path.join(OUTPUT_FOLDER, f"{name}.xlsx")

        # Save uploaded PDF
        file.save(in_path)

        # Convert PDF → Excel (smart hybrid logic inside tool)
        pdf_to_excel(in_path, out_path)

        @after_this_request
        def cleanup(response):
            cleanup_files(in_path, out_path)
            return response

        return send_file(
            out_path,
            as_attachment=True,
            download_name=f"{name}.xlsx"
        )

    except Exception as e:
        # IMPORTANT: log error for Render debugging
        print("PDF TO EXCEL ERROR:", e)
        return jsonify({
            "error": "PDF to Excel conversion failed",
            "details": str(e)
        }), 500
