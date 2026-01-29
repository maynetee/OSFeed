FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
# - netcat-openbsd: for healthchecks/wait scripts
# - curl: for generic tools
# - build-essential: for compiling some python deps if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    netcat-openbsd \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Entrypoint runs migrations before starting
ENTRYPOINT ["/app/entrypoint.sh"]

# Start command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
