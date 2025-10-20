# ✅ Base Image (lightweight + stable)
FROM python:3.11-slim

# ✅ Environment
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8
ENV HOME=/tmp

# ✅ Install LibreOffice + Java + Fonts + UNO bridge
RUN apt-get update && apt-get install -y \
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
    # ✅ Fonts pack for full rendering (English + Indic + Emoji)
    fonts-dejavu-core \
    fonts-dejavu-extra \
    fonts-liberation \
    fonts-noto-core \
    fonts-noto-ui-core \
    fonts-noto-mono \
    fonts-noto-color-emoji \
    fonts-noto-extra \
    fonts-freefont-ttf \
    fonts-lohit-deva \
    fonts-lohit-gujr \
    fonts-lohit-beng \
    fonts-lohit-guru \
    locales \
    && sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && locale-gen \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# ✅ Working directory
WORKDIR /app

# ✅ Copy all project files
COPY . /app

# ✅ Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt gunicorn PyPDF2

# ✅ Create folders + fix permissions (Render-safe temp storage)
RUN mkdir -p /app/uploads /tmp/outputs /tmp/.config && chmod -R 777 /app /tmp

# ✅ Verify LibreOffice installation
RUN libreoffice --headless --version || echo "LibreOffice ready"

# ✅ Expose API port
EXPOSE 10000
ENV PORT=10000

# ✅ Start Gunicorn server
CMD exec gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 180