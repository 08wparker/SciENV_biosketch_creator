# SciENcv Biosketch Creator - Cloud Run Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app
ENV PORT=8080

# Set work directory
WORKDIR /app

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libatspi2.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    libx11-6 \
    libxcb1 \
    libxext6 \
    libgtk-3-0 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads browser_state && chmod 777 uploads browser_state

# Create non-root user for security
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port (Cloud Run uses 8080 by default)
EXPOSE 8080

# Run with gunicorn for production
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 "app:create_app('production')"
