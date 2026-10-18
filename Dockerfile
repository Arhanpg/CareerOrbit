# CareerOrbit Production Dockerfile for Render / Koyeb / Fly.io / Nebius
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies (fonts, curl, git) - note typst is provided via python package
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    playwright install --with-deps chromium

# Copy full application code
COPY . .

# Set default port and bind dynamically to $PORT provided by host (e.g. Render, Koyeb)
ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
