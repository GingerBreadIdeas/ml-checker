# ML-Checker

A FastAPI/React application with Kafka-based prompt checking.

## Quick Start

### Setup the env variables:

```
cp .env.example .env
```

### Option 1: Full Stack with Kafka (for prompt checks)

```bash
# Then start the main application 
docker compose up

# Run prompt checking service
cd runner
python main.py
```

The prompt-save service is now containerized and will start automatically with the Kafka services. The order of startup is important - Kafka services must be started first.

### Option 2: Basic Stack without Kafka

If you don't need heavy duty stuff:

```bash
# Start just the core application (without Kafka)
docker compose -f docker-compose-no-kafka.yml up
```

Dev stack with docker:

### Option 3: Full Stack for developement

```bash
docker compose -f docker-compose.yml -f docker-compose-dev.yml up
```

The application will start with Kafka functionality disabled, but all other features will work normally.

## Filling in with examplary data

Use `uv run scripts/upload_sample_messages.py --token {insert token here}` to fill in the examplary data

### Prompt Checking Services
- `KAFKA_HOST`: Kafka address (default: localhost)
- `KAFKA_PORT`: Kafka port (default: 9092)
- `DB_HOST`: PostgreSQL host (default: localhost)
- `DB_PORT`: PostgreSQL port (default: 5432)
- `DB_USER`: PostgreSQL user (default: postgres)
- `DB_PASSWORD`: PostgreSQL password (default: postgres)
- `DB_NAME`: PostgreSQL database (default: ml-checker)


