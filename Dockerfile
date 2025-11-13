FROM python:3.11-slim

WORKDIR /app
COPY . /app

# ===== Install System Tools (Full PDF Suite) =====
RUN apt-get update && apt-get install -y \
    libreoffice-writer \
    libreoffice-calc \
    poppler-utils \
    ghostscript \
    fonts-dejavu \
    fonts-liberation \
    tesseract-ocr \
    tesseract-ocr-eng \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/*

# ===== Python Dependencies =====
RUN pip install --no-cache-dir -r requirements.txt

# ===== Create Temp Folders =====
RUN mkdir -p /tmp/uploads /tmp/outputs && chmod -R 777 /tmp

ENV PORT=10000
EXPOSE 10000

# ===== Start Flask with Gunicorn =====
CMD exec gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 180