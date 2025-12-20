# ML-Checker

A FastAPI/React application with Taskiq-based prompt checking using PostgreSQL as message broker.

## Quick Start

### Setup the env variables:

```bash
cp .env.example .env
```

Load the .env for external variables:

```bash
source .env
```

### Start the Application

```bash
# Start the full stack (backend, frontend, postgres)
docker compose up -d
```

### Run the Runner Worker

The runner worker processes prompt checks and ML metrics. Run it locally with one of these options:

**CPU only:**
```bash
cd runner
uv run taskiq worker runner:broker
```

**CUDA support (GPU):**
```bash
cd runner
uv run --extra cu126 taskiq worker runner:broker
```

## Filling in with examplary data

Use `uv run scripts/upload_sample_messages.py --token {insert token here}` to fill in the examplary data

## Using th service

The default username and password are: `testusername` and `testpassword`. 
