# ✅ Base Image
FROM python:3.11-slim

# ✅ Environment setup
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

# ✅ Install LibreOffice FULL suite (with all writer filters)
RUN apt-get update && apt-get install -y \
    software-properties-common \
    libreoffice \
    libreoffice-writer \
    libreoffice-draw \
    libreoffice-impress \
    libreoffice-calc \
    libreoffice-core \
    libreoffice-common \
    libreoffice-java-common \
    python3-uno \
    fonts-dejavu-core \
    fonts-noto-core \
    fonts-noto-ui-core \
    fonts-noto-mono \
    fonts-noto-color-emoji \
    default-jre \
    locales && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# ✅ Generate UTF-8 locale
RUN sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && locale-gen

# ✅ Set working directory
WORKDIR /app

# ✅ Copy project files
COPY . /app

# ✅ Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt gunicorn PyPDF2

# ✅ Expose port
EXPOSE 10000
ENV PORT=10000

# ✅ Start the app
CMD exec gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 180