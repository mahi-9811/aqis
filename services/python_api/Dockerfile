FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV ENV=PROD
ENV PIP_DEFAULT_TIMEOUT=1000

WORKDIR /app

# Install system dependencies (combined for single layer)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    tesseract-ocr \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY services/python_api/requirements.txt /tmp/requirements.txt

# Install Python dependencies with extended timeout and retries
RUN pip install --no-cache-dir --default-timeout=1000 \
    --retries 5 \
    -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

# Create non-root user
RUN useradd --create-home --shell /bin/bash aqis

# Copy application code
COPY --chown=aqis:aqis . /app

# Switch to non-root user
USER aqis

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl --fail http://127.0.0.1:8000/health/live || exit 1

CMD ["uvicorn", "services.python_api.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-server-header"]
