FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements-ml.txt .

# Install ML dependencies
RUN pip install --no-cache-dir -r requirements-ml.txt

# Copy training scripts
COPY app/ml /app/ml
COPY data /app/data

# Set environment
ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "ml.pricing.train"]
