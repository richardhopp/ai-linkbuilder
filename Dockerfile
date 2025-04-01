# Multi-stage build to reduce image size
FROM python:3.9-slim AS builder

# Install essential build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set up work directory
WORKDIR /build

# Create and activate virtual environment
RUN python -m venv /build/venv
ENV PATH="/build/venv/bin:$PATH"

# Copy requirements file
COPY requirements.txt .

# Install dependencies in the virtual environment
RUN pip install --upgrade pip && \
    pip install --no-cache-dir wheel setuptools && \
    pip install --no-cache-dir -r requirements.txt

# Second stage - Selenium with Chrome
FROM selenium/standalone-chrome:latest

USER root

# Install Python
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Set up work directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /build/venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Copy application code
COPY . .

# Create directories for logs and config with proper permissions
RUN mkdir -p /app/logs /app/config && \
    chmod 755 /app/logs /app/config

# Create a non-root user to run the application
RUN groupadd -r appuser && \
    useradd -r -g appuser -d /app appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PORT=8000

# Default command using the virtual environment Python
CMD exec /app/venv/bin/python app.py
