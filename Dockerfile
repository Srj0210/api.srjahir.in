# Use Ubuntu base so we can install LibreOffice
FROM ubuntu:22.04

# Install system dependencies
RUN apt-get update && \
    apt-get install -y python3 python3-pip libreoffice && \
    apt-get clean

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose Render port
ENV PORT=10000
EXPOSE 10000

# Run app using gunicorn
CMD gunicorn app:app --bind 0.0.0.0:$PORT