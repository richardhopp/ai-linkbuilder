FROM selenium/standalone-chrome:latest

USER root

# Install Python and pip
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    build-essential \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Set up work directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Update pip and install dependencies with verbose output
RUN pip3 install --upgrade pip && \
    pip3 install --no-cache-dir -v wheel && \
    pip3 install --no-cache-dir -v setuptools && \
    pip3 install --no-cache-dir -v -r requirements.txt

# Copy application code
COPY . .

# Create directories for logs and config
RUN mkdir -p /app/logs
RUN mkdir -p /app/config

# Default command
CMD ["python3", "app.py"]
