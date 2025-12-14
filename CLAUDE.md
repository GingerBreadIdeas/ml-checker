# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build/Test Commands
- Frontend Dev: `cd frontend && npm run dev`
- Frontend Build: `cd frontend && npm run build`
- Frontend Lint: `cd frontend && npm run lint`
- Backend Run: `cd backend && uv pip install -r requirements.txt && uvicorn app.main:app --reload --log-config=logging_config.yaml`
- Backend Format: `cd backend && black app && isort app`
- Backend Type Check: `cd backend && mypy app`
- Backend Test: `cd backend && pytest tests/`
- Run Single Test: `cd backend && pytest tests/path_to_test.py::test_name`
- Backend Venv: `cd backend && uv venv .venv && source .venv/bin/activate`
- Backend Install Dev: `cd backend && uv pip install -r requirements-dev.txt`
- Full Stack: `docker-compose up -d`
- Stack without Kafka: `docker-compose -f docker-compose-no-kafka.yml up -d`

## Code Style Guidelines

### Frontend (TypeScript/React)
- **Framework**: React with TypeScript
- **Styling**: Tailwind CSS
- **Naming Conventions**:
  - Variables/functions: `camelCase`
  - Components/classes: `PascalCase`
  - Files: Component files use `PascalCase.tsx`, utility files use `kebab-case.ts`
- **API Integration**: All API calls use centralized config from `frontend/src/config/api.ts`
- **State Management**: React hooks (useState, useEffect)
- **Routing**: React Router v6

### Backend (Python/FastAPI)
- **Framework**: FastAPI with SQLAlchemy ORM
- **Python Version**: >=3.11
- **Code Formatting**:
  - Use `black` for code formatting (line length: 70 for backend/ or 79 for root)
  - Use `isort` for import sorting (profile: "black")
  - Run both before committing: `black app && isort app`
- **Naming Conventions**:
  - Variables/functions: `snake_case`
  - Classes: `PascalCase`
  - Constants: `UPPER_CASE`
- **Database**:
  - Use snake_case for table and column names
  - SQLAlchemy models in `backend/app/models.py`
  - Alembic migrations for schema changes
- **Error Handling**:
  - Use FastAPI HTTPException with proper status codes
  - Include detailed error messages in responses
- **API Routes**:
  - RESTful design with versioned endpoints (e.g., `/api/v1/resource`)
  - All routes in `backend/app/routes/`
- **Environment Management**: Use `uv` instead of poetry or pip

### Database
- **ORM**: SQLAlchemy 2.0+
- **Migrations**: Alembic
- **Naming**: snake_case for all tables and columns
- **Relationships**: Explicitly define relationships in models

### Environment Variables
- **Frontend**: Variables must start with `VITE_` to be accessible in browser
  - `VITE_BACKEND_HOST`: Full backend URL including protocol (e.g., `https://api.example.com`)
  - `VITE_API_PATH`: API path prefix (default: `/api/v1`)
- **Backend**: Configure in `.env` file
  - `FRONTEND_HOST`: Frontend domain for CORS (e.g., `app.example.com`)
  - `DATABASE_URL`: PostgreSQL connection string
  - `SECRET_KEY`: JWT secret key

### Docker
- Use `docker-compose.yml` for full stack (backend, frontend, postgres, processing worker)
- Use `docker-compose-no-kafka.yml` for simplified stack
- All services use `env_file: - .env` for configuration
- Ports configurable via environment variables
- Runner service runs locally (not dockerized)

### Task Queue (Taskiq)
- Uses PostgreSQL as message broker
- **Runner worker**: Runs locally, processes prompt checks and ML metrics
- **Processing worker**: Runs in Docker, saves results to database
- Task timeout: 600 seconds
- No automatic retries (max_retries=0)

Note: Update this file as project conventions evolve.