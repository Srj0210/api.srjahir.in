# ---- SRJahir Tools : Render Docker build ----
FROM python:3.11-slim

# Install LibreOffice + fonts
RUN apt-get update && apt-get install -y libreoffice && apt-get clean

# Create working directories
WORKDIR /app
COPY . /app

# Install Python deps
RUN pip install --no-cache-dir -r requirements.txt

# Expose port (Render reads $PORT automatically)
EXPOSE 5000
CMD ["python", "app.py"]