FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr tesseract-ocr-fra curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /srv
COPY . .
RUN pip install --no-cache-dir .

ENV PYTHONUNBUFFERED=1
