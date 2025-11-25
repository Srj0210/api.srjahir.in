FROM python:3.11-slim

WORKDIR /app
COPY . /app

# Install required system tools + SAFE Indic fonts
RUN apt-get update && apt-get install -y \
    libreoffice-writer \
    libreoffice-calc \
    poppler-utils \
    ghostscript \
    qpdf \
    tesseract-ocr \
    tesseract-ocr-eng \
    libcairo2 \
    fonts-dejavu \
    fonts-noto-core \
    fonts-noto-sans-gujarati \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /tmp/uploads /tmp/outputs && chmod -R 777 /tmp

ENV PORT=10000
EXPOSE 10000

CMD exec gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 240
