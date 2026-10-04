# Use official Python lightweight image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_ENV=production

# Create app directory
WORKDIR /app

# Install system dependencies if required for DuckDB / standard tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY finshield /app/finshield
COPY scripts /app/scripts

# Do not copy .env or local DuckDB files!
# The database is streamed from Azure Blob Storage at startup via DUCKDB_DOWNLOAD_URL.

# Expose port
EXPOSE 8000

# Health check (slim image has no curl; long start period covers the DB download)
HEALTHCHECK --interval=30s --timeout=30s --start-period=180s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Start application
CMD ["python", "scripts/run_api.py"]
