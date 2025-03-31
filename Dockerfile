FROM selenium/standalone-chrome:latest

USER root

# Install Python and pip
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Set up work directory
WORKDIR /app

# Create and activate virtual environment
RUN python3 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Copy requirements file
COPY requirements.txt .

# Install dependencies in the virtual environment
RUN pip install --upgrade pip && \
    pip install --no-cache-dir wheel setuptools && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for logs and config
RUN mkdir -p /app/logs
RUN mkdir -p /app/config

# Default command using the virtual environment Python
CMD ["/app/venv/bin/python", "app.py"]
