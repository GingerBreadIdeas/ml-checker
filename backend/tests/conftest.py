import os

# Set environment variables for test environment BEFORE any imports
os.environ["TEST_ENV"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app as fastapi_app
from app.database import get_db, Base
from app.models import User, Project, UserRole, RoleType, ProjectToken
from app.core.security import create_access_token, generate_project_token

# Import and patch the database module to use our test engine
import app.database
import app.admin


SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    future=True,#!
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Patch the app's database module to use our test engine
app.database.engine = engine
app.database.SessionLocal = TestingSessionLocal

@pytest.fixture(scope="function")
def db(tmp_path):
    """
    Fresh SQLite DB file for each test. Build schema, yield a Session,
    then drop schema and dispose the engine.
    """
    db_path = tmp_path / "test.db"
    url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(url, connect_args={"check_same_thread": False}, future=True)

    # Build schema from models
    Base.metadata.create_all(engine)

    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        future=True,
    )

    # If your app code imports a shared SessionLocal/engine, patch them here:
    # (Only if you actually have app.database.SessionLocal / engine globals)
    try:
        import app.database as dbmod
        dbmod.engine = engine
        dbmod.SessionLocal = TestingSessionLocal
    except Exception:
        pass  # if you don't expose these, it's fine

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        # teardown: close and nuke schema
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()
        # tmp_path cleanup handled by pytest

@pytest.fixture(scope="function")
def client(db):
    """
    Route all app DB usage through the same test Session by overriding get_db.
    """
    def override_get_db():
        yield db

    fastapi_app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(fastapi_app) as c:
            yield c
    finally:
        fastapi_app.dependency_overrides.clear()

@pytest.fixture
def test_user(db):
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_project(db, test_user):
    project = Project(
        name="test_project",
        description="Test project for testing",
        is_default=True,
        is_active=True
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    # Create user role to link user to project
    user_role = UserRole(
        user_id=test_user.id,
        project_id=project.id,
        role=RoleType.ADMIN
    )
    db.add(user_role)
    db.commit()

    return project


@pytest.fixture
def test_user2(db):
    user = User(
        username="testuser2",
        email="test2@example.com",
        hashed_password="hashed_password",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_project2(db, test_user2):
    project = Project(
        name="test_project2",
        description="Second test project",
        is_default=False,  # Only test_project should be default
        is_active=True
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    # Create user role to link user2 to project2
    user_role = UserRole(
        user_id=test_user2.id,
        project_id=project.id,
        role=RoleType.ADMIN
    )
    db.add(user_role)
    db.commit()

    return project


@pytest.fixture
def auth_headers(test_user):
    access_token = create_access_token(subject=test_user.id)
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def auth_headers2(test_user2):
    access_token = create_access_token(subject=test_user2.id)
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def project_token_headers(project_token):
    """Headers with project token for API testing."""
    return {"Authorization": f"Bearer {project_token}"}


@pytest.fixture
def project_token(db, test_project, test_user):
    """Create a project token for testing API access."""
    raw_token, token_hash = generate_project_token()

    project_token = ProjectToken(
        project_id=test_project.id,
        token_hash=token_hash,
        created_by_user_id=test_user.id,
        is_active=True
    )
    db.add(project_token)
    db.commit()
    db.refresh(project_token)

    # Return the raw token for use in tests
    return raw_token


@pytest.fixture
def project_token2(db, test_project2, test_user2):
    """Create a project token for second project."""
    raw_token, token_hash = generate_project_token()

    project_token = ProjectToken(
        project_id=test_project2.id,
        token_hash=token_hash,
        created_by_user_id=test_user2.id,
        is_active=True
    )
    db.add(project_token)
    db.commit()
    db.refresh(project_token)

    return raw_token


@pytest.fixture
def project_token_headers2(project_token2):
    """Headers with second project token for API testing."""
    return {"Authorization": f"Bearer {project_token2}"}
