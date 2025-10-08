# ✅ Base Image (Python + Debian-based for full locale/font support)
FROM python:3.11-slim

# Prevent timezone & locale prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

# ✅ Install LibreOffice + All filters + Indic (Indian) fonts
RUN apt-get update && apt-get install -y \
    libreoffice \
    libreoffice-writer \
    libreoffice-draw \
    libreoffice-calc \
    libreoffice-impress \
    libreoffice-base-core \
    fonts-dejavu-core \
    fonts-freefont-ttf \
    fonts-noto-core \
    fonts-noto-cjk \
    fonts-noto-color-emoji \
    fonts-noto-extra \
    fonts-noto-ui-core \
    fonts-noto-mono \
    fonts-noto-unhinted \
    fonts-lohit-deva \
    fonts-lohit-gujr \
    fonts-lohit-beng \
    fonts-lohit-guru \
    fonts-lohit-knda \
    fonts-lohit-mlym \
    fonts-lohit-orya \
    fonts-lohit-taml \
    fonts-lohit-telu \
    fonts-noto-sans \
    fonts-noto-sans-gujarati \
    fonts-noto-sans-devanagari \
    fonts-noto-sans-bengali \
    fonts-noto-sans-malayalam \
    fonts-noto-sans-tamil \
    fonts-noto-sans-telugu \
    locales \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# ✅ Generate UTF-8 locale (for Indian languages)
RUN sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && locale-gen

# ✅ Set working directory
WORKDIR /app

# ✅ Copy app files
COPY . /app

# ✅ Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# ✅ Expose Render port
EXPOSE 10000

# ✅ Set Render environment variable
ENV PORT=10000

# ✅ Start Gunicorn server
CMD exec gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 180