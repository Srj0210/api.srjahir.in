# ✅ Base Image
FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8
ENV DISPLAY=:99
ENV HOME=/tmp

# ✅ Fix missing sources.list (Render issue)
RUN echo "deb http://deb.debian.org/debian bookworm main contrib non-free non-free-firmware\n\
deb http://security.debian.org/debian-security bookworm-security main contrib non-free non-free-firmware\n\
deb http://deb.debian.org/debian bookworm-updates main contrib non-free non-free-firmware" > /etc/apt/sources.list

# ✅ Install dependencies: LibreOffice + unoconv + Fonts + OCR + Xvfb
RUN apt-get update && apt-get install -y \
    libreoffice \
    libreoffice-writer \
    libreoffice-core \
    libreoffice-common \
    libreoffice-java-common \
    python3-uno \
    unoconv \
    default-jre \
    poppler-utils \
    tesseract-ocr \
    ghostscript \
    xvfb \
    fonts-dejavu-core \
    fonts-liberation \
    fonts-noto-core \
    locales && \
    sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && locale-gen && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

# ✅ Install Python packages
RUN pip install --no-cache-dir flask flask-cors PyPDF2 fpdf2 pillow gunicorn

RUN mkdir -p /tmp/uploads /tmp/outputs && chmod -R 777 /app /tmp

# ✅ Verify setup
RUN xvfb-run --auto-servernum libreoffice --headless --version || echo "LibreOffice ready"

EXPOSE 10000
ENV PORT=10000

# ✅ Run with Gunicorn
CMD exec gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 180