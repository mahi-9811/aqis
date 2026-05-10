FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV ENV=PROD

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    tesseract-ocr \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY services/python_api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

RUN useradd --create-home --shell /bin/bash aqis

COPY . /app
RUN chown -R aqis:aqis /app

USER aqis

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl --fail http://127.0.0.1:8000/health/live || exit 1

CMD ["uvicorn", "services.python_api.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-server-header"]
