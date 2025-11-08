FROM python:3.11-slim

WORKDIR /app
COPY . /app

RUN apt-get update && apt-get install -y \
    libreoffice-writer unoconv poppler-utils fonts-dejavu fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

ENV PORT=10000
EXPOSE 10000

CMD exec gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 180
