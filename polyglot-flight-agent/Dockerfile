FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

# Install system dependencies including scipy requirements
RUN apt-get update && \
    apt-get install -y gcc g++ python3-dev curl dnsutils \
    gfortran libopenblas-dev pkg-config && \
    rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent code and utilities
COPY agent.py .
COPY audio_utils.py .

# Download any required model files at build time
RUN python agent.py download-files || true

# Health check that verifies API connectivity
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('${API_SERVER_URL}/health', timeout=5)" || exit 1

# Expose debug server port
EXPOSE 8082

# Run the agent
CMD ["python", "agent.py", "start"]