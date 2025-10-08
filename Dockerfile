# ✅ Base Image
FROM python:3.11-slim

# ✅ Environment
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

# ✅ Install LibreOffice + fonts + Java runtime (for filters)
RUN apt-get update && apt-get install -y \
    libreoffice \
    libreoffice-writer \
    libreoffice-draw \
    libreoffice-impress \
    libreoffice-calc \
    libreoffice-core \
    libreoffice-common \
    libreoffice-java-common \
    python3-uno \
    default-jre-headless \
    fonts-dejavu-core \
    fonts-noto-core \
    fonts-noto-ui-core \
    fonts-noto-mono \
    fonts-noto-color-emoji \
    locales \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# ✅ Set working directory
WORKDIR /app

# ✅ Copy everything
COPY . /app

# ✅ Install Python deps
RUN pip install --no-cache-dir -r requirements.txt gunicorn PyPDF2

# ✅ Check LibreOffice install
RUN which libreoffice || which soffice

# ✅ Expose port
EXPOSE 10000
ENV PORT=10000

# ✅ Run Gunicorn
CMD exec gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 180