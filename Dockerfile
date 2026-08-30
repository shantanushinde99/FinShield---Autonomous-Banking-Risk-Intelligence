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
# Using requirements.txt or copying site-packages if requirements.txt isn't present
# Assuming a standard pip install process. Let's write a generic requirement fetch or pip freeze equivalent.
# Since we know the stack (FastAPI, Uvicorn, Pydantic, DuckDB, Lyzr, Qdrant):
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY finshield /app/finshield
COPY scripts /app/scripts

# Do not copy .env or local DuckDB files!
# DuckDB files should be mounted via volumes if persistent storage is needed.

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Start application
CMD ["python", "scripts/run_api.py"]
