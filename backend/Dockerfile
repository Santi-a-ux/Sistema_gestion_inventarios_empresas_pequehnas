# Use Python 3.9 slim as base image
FROM python:3.9

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py \
    FLASK_ENV=production

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all Python files first
COPY *.py .

# Make test script executable
RUN chmod +x test_logging.py

# Expose port
EXPOSE 5000

# Run the application with Gunicorn
CMD ["gunicorn", "--preload", "-b", "0.0.0.0:5000", "app:app", "--log-level=info", "--capture-output", "--access-logfile=-", "--error-logfile=-", "--logger-class=gunicorn.glogging.Logger"] 