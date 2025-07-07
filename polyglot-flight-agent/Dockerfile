FROM python:3.11-slim

# Install system dependencies for audio processing
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libffi-dev \
    libssl-dev \
    portaudio19-dev \
    python3-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set environment variables that can be overridden
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# LiveKit environment variables (will be overridden by ECS/docker-compose)
ENV LIVEKIT_URL=""
ENV LIVEKIT_API_KEY=""
ENV LIVEKIT_API_SECRET=""

# OpenAI environment variables
ENV OPENAI_API_KEY=""

# Deepgram environment variables
ENV DEEPGRAM_API_KEY=""

# Cartesia environment variables
ENV CARTESIA_API_KEY=""

# API Server URL - defaults to ECS production ALB
ENV API_SERVER_URL="http://polyglot-rag-prod-alb-1838390148.us-east-1.elb.amazonaws.com"

# Default command to run the agent in dev mode with debug logging
CMD ["python", "agent.py", "dev", "--log-level", "DEBUG"]