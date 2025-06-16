# ML-Checker

A FastAPI/React application with Kafka-based prompt checking.

## Quick Start

### Option 1: Full Stack with Kafka (for prompt checks)

```bash
# Start Kafka and prompt-save service first
docker compose -f docker-compose.kafka.yml up -d

# Then start the main application 
docker compose up -d

# Run prompt checking service
cd runner
python main.py
```

The prompt-save service is now containerized and will start automatically with the Kafka services. The order of startup is important - Kafka services must be started first.

### Option 2: Basic Stack without Kafka

If you don't need the prompt checking functionality, you can run just the core application:

```bash
# Start just the core application (without Kafka)
docker compose up -d
```

The application will start with Kafka functionality disabled, but all other features will work normally.

## Environment Variables

### Prompt Checking Services
- `KAFKA_HOST`: Kafka address (default: localhost)
- `KAFKA_PORT`: Kafka port (default: 9092)
- `DB_HOST`: PostgreSQL host (default: localhost)
- `DB_PORT`: PostgreSQL port (default: 5432)
- `DB_USER`: PostgreSQL user (default: postgres)
- `DB_PASSWORD`: PostgreSQL password (default: postgres)
- `DB_NAME`: PostgreSQL database (default: ml-checker)

## Developement new

- Run kafka compose
- ssh -R 9092 to strong machine
- Run the runner main.py in separate stron maching
- run backend

## Development old

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Backend
```bash
cd backend
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

