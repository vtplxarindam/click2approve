FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create filestorage directory
RUN mkdir -p /filestorage

# Expose port
EXPOSE 5555

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5555"]