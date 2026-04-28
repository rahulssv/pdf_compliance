FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY templates/ ./templates/

# Expose port
EXPOSE 8000

# Run the application with logging
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--timeout", "120", "--workers", "2", "--access-logfile", "-", "--error-logfile", "-", "--log-level", "info", "src.app:app"]
