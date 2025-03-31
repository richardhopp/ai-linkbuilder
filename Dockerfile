FROM python:3.9-slim

# Install Chrome and dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    xvfb \
    libgconf-2-4 \
    libxss1 \
    libappindicator1 \
    libindicator7 \
    fonts-liberation

# Install Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Install ChromeDriver
RUN CHROME_VERSION=$(google-chrome --version | cut -d ' ' -f 3 | cut -d '.' -f 1) \
    && CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION") \
    && wget -q --no-verbose -O /tmp/chromedriver_linux64.zip "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip" \
    && unzip /tmp/chromedriver_linux64.zip -d /usr/local/bin \
    && rm /tmp/chromedriver_linux64.zip \
    && chmod +x /usr/local/bin/chromedriver

# Set up work directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for logs and config
RUN mkdir -p /app/logs
RUN mkdir -p /app/config

# Add a start script with Xvfb for headless browser
RUN echo '#!/bin/bash\nXvfb :99 -screen 0 1280x1024x24 &\nexport DISPLAY=:99\npython "$@"' > /app/start.sh && chmod +x /app/start.sh

# Set entrypoint
ENTRYPOINT ["/app/start.sh"]

# Default command
CMD ["app.py"]
