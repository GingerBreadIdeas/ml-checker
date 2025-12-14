FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (needed for building some Python packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    libopenblas-dev \
    gfortran \
    pkg-config \
    libhdf5-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Create directories for Hugging Face cache
RUN mkdir -p /root/.cache/huggingface
RUN mkdir -p /root/.huggingface

# Copy application code first (needed for pyproject.toml install)
COPY . .

# Install torch first
RUN uv pip install --system torch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cpu

# Install dependencies from pyproject.toml
RUN uv pip install --system .

# Set environment variables for better performance
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/root/.huggingface \
    TOKENIZERS_PARALLELISM=false

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8000 ${UVICORN_PROXY_HEADERS:+--proxy-headers} --forwarded-allow-ips=${UVICORN_FORWARDED_ALLOW_IPS:-'*'}"]
