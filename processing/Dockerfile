FROM python:3.9-slim

WORKDIR /app

# Copy the prompt_save script
COPY prompt_save.py .
COPY __init__.py .

# Install dependencies
RUN pip install --no-cache-dir \
    sqlalchemy>=2.0.17 \
    psycopg2-binary>=2.9.6 \
    python-dotenv>=1.0.0 \
    pydantic==1.10.9 \
    python-jose[cryptography]>=3.3.0 \
    confluent-kafka

# Set environment variable to identify Docker environment
ENV MLCHECKER_ENV_TYPE=docker
# Force Python to run in unbuffered mode
ENV PYTHONUNBUFFERED=1

# Run the prompt_save script with explicit unbuffering
CMD ["python", "-u", "prompt_save.py"]
