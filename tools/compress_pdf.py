import subprocess
import os
import pikepdf


def compress_pdf(input_path: str, output_path: str, level: str = "balanced") -> str:
    """
    Compress PDF using Ghostscript with pikepdf fallback.

    Levels:
        high     → /screen   (max compression, lower quality)
        balanced → /ebook    (recommended for most use cases)
        low      → /prepress (best quality, least compression)
    """

    quality_map = {
        "high":     "/screen",
        "balanced": "/ebook",
        "low":      "/prepress",
    }
    gs_quality = quality_map.get(level, "/ebook")

    # ── Primary: Ghostscript ──────────────────────────────────
    try:
        subprocess.run([
            "gs",
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.5",
            f"-dPDFSETTINGS={gs_quality}",
            "-dNOPAUSE",
            "-dQUIET",
            "-dBATCH",
            f"-sOutputFile={output_path}",
            input_path,
        ], check=True, timeout=120)

        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return output_path

    except Exception as gs_err:
        print(f"[compress_pdf] Ghostscript failed: {gs_err}")

    # ── Fallback: pikepdf (lossless optimisation) ─────────────
    try:
        with pikepdf.open(input_path) as pdf:
            pdf.save(
                output_path,
                compress_streams=True,
                object_stream_mode=pikepdf.ObjectStreamMode.generate,
            )
        return output_path

    except Exception as pk_err:
        raise RuntimeError(f"Compression failed (GS + pikepdf): {pk_err}")
