FROM python:3.11-slim

WORKDIR /app
COPY . /app

# ===== Install System Tools =====
RUN apt-get update && apt-get install -y \
    libreoffice-writer \
    libreoffice-calc \
    poppler-utils \
    ghostscript \
    qpdf \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-guj \
    libcairo2 \
    fonts-dejavu \
    wget \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*

# ===== Add Safe Gujarati Font =====
RUN mkdir -p /usr/share/fonts/truetype/noto && \
    wget -q https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansGujarati/NotoSansGujarati-Regular.ttf \
        -O /usr/share/fonts/truetype/noto/NotoSansGujarati-Regular.ttf && \
    fc-cache -f -v

# ===== Install Python Dependencies =====
RUN pip install --no-cache-dir -r requirements.txt

# ===== Temp Folders =====
RUN mkdir -p /tmp/uploads /tmp/outputs && chmod -R 777 /tmp

ENV PORT=10000
EXPOSE 10000

# ===== Start App =====
CMD exec gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 300
