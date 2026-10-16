import os

os.environ["DATABASE_URL"] = "sqlite+pysqlite://"
os.environ["JWT_SECRET_KEY"] = "test-secret-only-never-use-in-production-123456"
os.environ["UPLOAD_DIR"] = "test-uploads"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Department, User
from app.security import hash_password

engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture(autouse=True)
def database():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def client():
    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def create_account(role="citizen", email=None, department_id=None):
    with TestingSession() as db:
        user = User(name=f"Demo {role}", email=email or f"{role}@example.com", role=role, password_hash=hash_password("ValidPassword123!"), department_id=department_id)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user.id


def bearer(client: TestClient, email: str, password: str = "ValidPassword123!"):
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


def create_department(name="Public Works"):
    with TestingSession() as db:
        department = Department(name=name)
        db.add(department)
        db.commit()
        db.refresh(department)
        return department.id
