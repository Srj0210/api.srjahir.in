# ✅ Base Image
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
    fonts-dejavu-core \
    fonts-noto-core \
    fonts-noto-ui-core \
    fonts-noto-mono \
    fonts-noto-color-emoji \
    locales \
    && sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && locale-gen \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# ✅ Set working directory
WORKDIR /app

# ✅ Copy everything
COPY . /app

# ✅ Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt gunicorn PyPDF2

# ✅ Create folders + fix permissions
RUN mkdir -p /app/uploads /app/outputs /tmp/.config && chmod -R 777 /app /tmp

# ✅ Verify LibreOffice
RUN libreoffice --headless --version || echo "LibreOffice ready"

# ✅ Expose port
EXPOSE 10000
ENV PORT=10000

# ✅ Start Gunicorn server
CMD exec gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 180