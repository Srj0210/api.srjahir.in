# ✅ Base Image
FROM python:3.11-slim

# ✅ Avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8
ENV DOCKER_BUILDKIT=0

# ✅ Install LibreOffice + Indian Fonts (lightweight, stable)
RUN apt-get update && apt-get install -y \
    libreoffice \
    libreoffice-writer \
    libreoffice-draw \
    libreoffice-calc \
    libreoffice-impress \
    fonts-dejavu-core \
    fonts-noto-core \
    fonts-noto-color-emoji \
    fonts-noto-cjk \
    fonts-noto-sans \
    fonts-noto-mono \
    fonts-noto-extra \
    fonts-noto-ui-core \
    fonts-noto-sans-devanagari \
    fonts-noto-sans-gujarati \
    fonts-noto-sans-bengali \
    fonts-noto-sans-tamil \
    fonts-noto-sans-telugu \
    fonts-noto-sans-malayalam \
    locales \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# ✅ Generate locale (important for Indic text)
RUN sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && locale-gen

# ✅ Working directory
WORKDIR /app

# ✅ Copy app files
COPY . /app

# ✅ Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# ✅ Expose Render port
EXPOSE 10000
ENV PORT=10000

# ✅ Start app using Gunicorn
CMD exec gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 180