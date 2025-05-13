FROM python:3.9-slim

WORKDIR /app

# Install system dependencies (needed for building some Python packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    libatlas-base-dev \
    gfortran \
    pkg-config \
    libhdf5-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Install NumPy first to avoid compatibility issues
RUN pip install numpy==1.24.0

# Pre-install PyTorch to save build time (CPU-only version)
RUN pip install torch==2.1.0 --extra-index-url https://download.pytorch.org/whl/cpu --no-cache-dir

# Create directories for Hugging Face cache
RUN mkdir -p /root/.cache/huggingface
RUN mkdir -p /root/.huggingface

# Copy requirements file
COPY requirements.txt .

# Install other dependencies, excluding torch which we've already installed
RUN grep -v -E "torch|torchvision|torchaudio" requirements.txt > requirements_no_torch.txt && \
    uv pip install --system -r requirements_no_torch.txt && \
    rm requirements_no_torch.txt

# Copy application code
COPY . .

# Set environment variables for better performance
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/root/.huggingface \
    TOKENIZERS_PARALLELISM=false

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
