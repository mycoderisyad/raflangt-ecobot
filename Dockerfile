# EcoBot WhatsApp Bot Docker Image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for logs and media
RUN mkdir -p logs media/default sessions

# Copy entrypoint script
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Set proper permissions
RUN chmod +x main.py

# Create non-root user for security
RUN useradd -m -u 1000 ecobot && chown -R ecobot:ecobot /app
USER ecobot

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Default environment (can be overridden by docker-compose)
ENV ENVIRONMENT=production
ENV PORT=8000

# Expose port
EXPOSE 8000

# Start command 
CMD ["./entrypoint.sh"]
