# ✅ Base Image (Lightweight & Stable)
FROM python:3.11-slim

# ✅ Environment setup
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8
ENV HOME=/tmp
ENV SAL_USE_VCLPLUGIN=gen
ENV SAL_VCL_QT5_NO_GLYPH_HINTING=1

# ✅ Fix missing sources.list (Render issue)
RUN echo "deb http://deb.debian.org/debian bookworm main contrib non-free non-free-firmware\n\
deb http://security.debian.org/debian-security bookworm-security main contrib non-free non-free-firmware\n\
deb http://deb.debian.org/debian bookworm-updates main contrib non-free non-free-firmware" > /etc/apt/sources.list

# ✅ Install system dependencies: LibreOffice + OCR + Fonts + Utilities
RUN apt-get update --fix-missing && apt-get install -y \
    libreoffice \
    libreoffice-writer \
    libreoffice-draw \
    libreoffice-calc \
    libreoffice-impress \
    libreoffice-core \
    libreoffice-common \
    libreoffice-java-common \
    python3-uno \
    default-jre \
    poppler-utils \
    tesseract-ocr \
    fonts-dejavu-core \
    fonts-dejavu-extra \
    fonts-noto-core \
    fonts-noto-mono \
    fonts-noto-color-emoji \
    fonts-liberation \
    fonts-roboto-unhinted \
    locales \
    && sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && locale-gen \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# ✅ Fix for LibreOffice X11 display error in Render
ENV DISPLAY=:99
RUN apt-get update && apt-get install -y xvfb && apt-get clean

# ✅ Set working directory
WORKDIR /app

# ✅ Copy project files
COPY . /app

# ✅ Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# ✅ Create required directories & set permissions
RUN mkdir -p /tmp/uploads /tmp/outputs /tmp/.config && chmod -R 777 /app /tmp

# ✅ Verify LibreOffice installation (with virtual framebuffer)
RUN xvfb-run --auto-servernum libreoffice --headless --version || echo "LibreOffice ready"

# ✅ Expose API port
EXPOSE 10000
ENV PORT=10000

# ✅ Start Gunicorn Server
CMD exec gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 180