# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build/Test Commands
- Frontend Dev: `cd frontend && npm run dev`
- Frontend Build: `cd frontend && npm run build`
- Frontend Lint: `cd frontend && npm run lint`
- Backend Run: `cd backend && uv pip install -r requirements.txt && uvicorn app.main:app --reload --log-config=logging_config.yaml`
- Backend Format: `cd backend && black app`
- Backend Test: `cd backend && pytest tests/`
- Run Single Test: `cd backend && pytest tests/path_to_test.py::test_name`
- Backend Venv: `cd backend && uv venv .venv && source .venv/bin/activate`
- Backend Install Dev: `cd backend && uv pip install -r requirements-dev.txt`
- Full Stack: `docker-compose up -d`

## Code Style Guidelines
- **Frontend**: TypeScript, React, and Tailwind CSS
- **Backend**: Python with FastAPI, SQLAlchemy ORM
- **Python**: Follow PEP 8 and use Black formatter (88 character line limit)
- **TypeScript**: Use camelCase for variables/functions, PascalCase for components/classes
- **Database**: Use snake_case for table and column names
- **Error Handling**: Use try/catch in frontend, exception handling in backend with proper HTTP status codes
- **API Routes**: RESTful design with versioned endpoints (e.g., /api/v1/resource)
- **Python Env Management**: Use uv instead of poetry or pip for dependency management

Note: Update this file as project conventions evolve.