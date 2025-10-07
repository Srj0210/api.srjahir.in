# ✅ Base Image
FROM python:3.11-slim

# ✅ Install required system packages (for LibreOffice conversion and fonts)
RUN apt-get update && apt-get install -y \
    libreoffice \
    libreoffice-writer \
    fonts-dejavu-core && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# ✅ Set working directory
WORKDIR /app

# ✅ Copy all project files
COPY . /app

# ✅ Install Python packages (including gunicorn)
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# ✅ Expose Render port
EXPOSE 10000

# ✅ Set environment variable for Render’s dynamic port
ENV PORT=10000

# ✅ Start Gunicorn properly bound to $PORT
CMD exec gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120