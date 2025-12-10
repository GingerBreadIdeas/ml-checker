# Contributing to ML-Checker

Thank you for considering contributing to ML-Checker! This document outlines the development workflow and standards.

## Development Setup

### Prerequisites

- uv
- Docker and Docker Compose
- Git

### Getting Started

1. **Clone the repository**
   ```bash
   git clone https://github.com/GingerBreadIdeas/ml-checker.git
   cd ml-checker
   ```

2. **Install pre-commit hooks**

   We use pre-commit hooks to ensure code quality. You can install and run them with:
   ```bash
   uv run pre-commit install
   ```

   This will automatically run black and isort on your Python code before each commit.

3. **Set up your environment**

   Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

   Edit `.env` as needed for your local development.
   
## Running the project

You can use docker-compose.yml to set up all of the services. 

```
docker compose up 
```

Alternatively you can add the `docker-compose-dev.yml` for developement setup.

```
docker compose up -f docker-compose.yml -f docker-compose-dev.yml up 
```

## Code Style Guidelines

### Python (Backend)

We follow PEP 8 and use automated tools to enforce consistency:

- **Black**: Code formatter with 88 character line limit
- **isort**: Import statement organizer (black-compatible profile)


### TypeScript/JavaScript (Frontend)

- Use ESLint for linting
- Follow React best practices
- Use camelCase for variables/functions, PascalCase for components

### Database

- Use snake_case for table and column names
- Write migrations for all schema changes


## Pull Request Process
0. **Create an issue**
   - If there is no issue regarding the thing you are going to work on, create one

1. **Create a feature branch**
   - Use github to create a branch based of an issue

2. **Make your changes**
   - Write clear, descriptive commit messages

3. **Ensure code quality**
   - Run tests locally, if there are any

4. **Push your branch**
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Open a Pull Request**
   - Open the Draft PR as soon as you have any code
   - When you are ready, change the draft to normal PR and request review from @mmajewsk


## License

By contributing, you agree that your contributions will be licensed under the same license as the project.
