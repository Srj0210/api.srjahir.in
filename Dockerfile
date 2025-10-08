# ✅ Base Image
FROM python:3.11-slim

# ✅ Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8
ENV DOCKER_BUILDKIT=0

# ✅ Install LibreOffice + Indian Fonts (Gujarati, Hindi, Marathi, Bengali)
RUN apt-get update && apt-get install -y \
    libreoffice \
    libreoffice-writer \
    libreoffice-draw \
    libreoffice-calc \
    libreoffice-impress \
    fonts-dejavu-core \
    fonts-noto \
    fonts-noto-core \
    fonts-noto-extra \
    fonts-noto-ui-core \
    fonts-noto-mono \
    fonts-noto-sans-devanagari \
    fonts-noto-sans-gujarati \
    fonts-noto-sans-bengali \
    fonts-noto-color-emoji \
    locales \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# ✅ Generate UTF-8 locale (important for Indic text)
RUN sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && locale-gen

# ✅ Working directory
WORKDIR /app

# ✅ Copy project files
COPY . /app

# ✅ Install dependencies
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# ✅ Expose port for Render
EXPOSE 10000
ENV PORT=10000

# ✅ Start Gunicorn app
CMD exec gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 180