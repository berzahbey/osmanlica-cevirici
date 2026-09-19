FROM python:3.11-slim

# Sistem bağımlılıkları: Tesseract OCR (Türkçe dil paketiyle), font araçları, unzip
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr tesseract-ocr-tur tesseract-ocr-eng \
    curl unzip fontconfig \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Scheherazade New (Nesih tarzı) fontunu Google Fonts'tan indir
RUN mkdir -p /app/fonts && \
    curl -L "https://github.com/google/fonts/raw/main/ofl/scheherazadenew/ScheherazadeNew-Regular.ttf" \
      -o /app/fonts/ScheherazadeNew-Regular.ttf && \
    fc-cache -f

COPY app/ /app/

ENV WORK_DIR=/data/jobs
ENV OTTOMAN_FONT_PATH=/app/fonts/ScheherazadeNew-Regular.ttf
VOLUME ["/data"]

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
