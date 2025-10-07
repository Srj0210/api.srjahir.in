# ✅ Use official Ubuntu base (for LibreOffice support)
FROM ubuntu:22.04

# ✅ Avoid interactive prompts during install
ENV DEBIAN_FRONTEND=noninteractive

# ✅ Install system dependencies (LibreOffice + Python + fonts)
RUN apt-get update && \
    apt-get install -y python3 python3-pip libreoffice libreoffice-writer fonts-dejavu-core && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# ✅ Set working directory
WORKDIR /app

# ✅ Copy all project files
COPY . /app

# ✅ Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# ✅ Expose Render default port
EXPOSE 10000

# ✅ Start Flask app with Gunicorn (Render will set $PORT automatically)
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000"]