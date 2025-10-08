FROM python:3.12-slim

# Install system dependencies for Pillow and AVIF
RUN apt-get update && apt-get install -y \
    libwebp-dev \
    libjpeg-dev \
    libpng-dev \
    libavif-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create www-data user if not exists
RUN groupadd -g 33 www-data || true && \
    useradd -u 33 -g www-data -s /bin/bash -m www-data || true

WORKDIR /app

# Copy dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY config.yml .

# Create log directory
RUN mkdir -p /var/log/webp && chown -R www-data:www-data /var/log/webp

USER www-data

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8088/health || exit 1

ENTRYPOINT ["python", "-m", "app.main"]
