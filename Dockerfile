# ✅ Base Image
FROM python:3.11-slim

# ✅ Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

# ✅ Install LibreOffice + Fonts
RUN apt-get update && apt-get install -y \
    libreoffice \
    libreoffice-writer \
    libreoffice-draw \
    libreoffice-calc \
    libreoffice-impress \
    fonts-dejavu-core \
    fonts-noto-core \
    fonts-noto-ui-core \
    fonts-noto-mono \
    fonts-noto-color-emoji \
    locales \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# ✅ Generate UTF-8 locale (for Indian languages)
RUN sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && locale-gen

# ✅ Install Unoconv via pip (since apt package is deprecated)
RUN pip install --no-cache-dir unoconv

# ✅ Set working directory
WORKDIR /app

# ✅ Copy project files
COPY . /app

# ✅ Install Python dependencies + Gunicorn
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# ✅ Expose Render port
EXPOSE 10000
ENV PORT=10000

# ✅ Start app with Gunicorn
CMD exec gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 180