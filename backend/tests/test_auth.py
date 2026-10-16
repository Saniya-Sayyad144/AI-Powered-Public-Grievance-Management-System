import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.seed import seed
from tests.conftest import bearer


def test_registration_login_profile_and_logout(client: TestClient):
    registered = client.post("/api/auth/register", json={"name": "Asha Citizen", "email": "asha@example.com", "password": "ValidPassword123!", "phone": "+1 555 0100", "ward": "Ward 2"})
    assert registered.status_code == 201
    assert registered.json()["data"]["user"]["role"] == "citizen"
    headers = bearer(client, "asha@example.com")
    profile = client.get("/api/auth/me", headers=headers)
    assert profile.status_code == 200
    assert profile.json()["data"]["name"] == "Asha Citizen"
    assert "password_hash" not in profile.json()["data"]
    logout = client.post("/api/auth/logout", headers=headers)
    assert logout.status_code == 200
    assert client.get("/api/auth/me", headers=headers).status_code == 401


def test_duplicate_registration_and_bad_password_are_rejected(client: TestClient):
    body = {"name": "Asha Citizen", "email": "asha@example.com", "password": "ValidPassword123!"}
    assert client.post("/api/auth/register", json=body).status_code == 201
    assert client.post("/api/auth/register", json=body).status_code == 409
    assert client.post("/api/auth/login", json={"email": body["email"], "password": "wrong-password"}).status_code == 401
    invalid = client.post("/api/auth/register", json={**body, "email": "short@example.com", "password": "secret-short"})
    assert invalid.status_code == 422
    assert "secret-short" not in invalid.text


def test_privileged_registration_requires_admin_invitation(client: TestClient):
    body = {"name": "Unauthorized Admin", "email": "unauthorized@example.com", "password": "ValidPassword123!"}
    for role in ("officer", "admin"):
        response = client.post("/api/auth/register", json={**body, "role": role})
        assert response.status_code == 403
    unknown_role = client.post("/api/auth/register", json={**body, "role": "superuser"})
    assert unknown_role.status_code == 422
    forged_extra = client.post("/api/auth/register", json={**body, "is_admin": True})
    assert forged_extra.status_code == 422


def test_admin_invitation_creates_role_and_is_single_use(client: TestClient):
    from tests.conftest import create_account, create_department

    create_account("admin", "admin@example.com")
    admin = bearer(client, "admin@example.com")
    department_id = create_department()
    invitation = client.post(
        "/api/invitations",
        json={"role": "officer", "department_id": department_id},
        headers=admin,
    )
    assert invitation.status_code == 201, invitation.text
    code = invitation.json()["data"]["code"]
    assert code

    body = {
        "name": "Invited Officer",
        "email": "invited-officer@example.com",
        "password": "ValidPassword123!",
        "role": "officer",
        "invitation_code": code,
    }
    registered = client.post("/api/auth/register", json=body)
    assert registered.status_code == 201, registered.text
    assert registered.json()["data"]["user"]["role"] == "officer"
    assert registered.json()["data"]["user"]["department_id"] == department_id
    logged_in = client.post("/api/auth/login", json={"email": body["email"], "password": body["password"]})
    assert logged_in.status_code == 200
    assert logged_in.json()["data"]["user"]["role"] == "officer"

    reused = client.post("/api/auth/register", json={**body, "email": "second-officer@example.com"})
    assert reused.status_code == 403


def test_invitation_creation_is_admin_only(client: TestClient):
    payload = {"role": "admin"}
    assert client.post("/api/invitations", json=payload).status_code == 401
    from tests.conftest import create_account

    create_account("citizen", "citizen@example.com")
    citizen = bearer(client, "citizen@example.com")
    assert client.post("/api/invitations", json=payload, headers=citizen).status_code == 403


def test_admin_account_requires_admin_issued_invitation(client: TestClient):
    from tests.conftest import create_account

    create_account("admin", "admin@example.com")
    admin = bearer(client, "admin@example.com")
    invitation = client.post("/api/invitations", json={"role": "admin"}, headers=admin)
    assert invitation.status_code == 201, invitation.text
    registered = client.post(
        "/api/auth/register",
        json={
            "name": "Provisioned Administrator",
            "email": "provisioned-admin@example.com",
            "password": "ValidPassword123!",
            "role": "admin",
            "invitation_code": invitation.json()["data"]["code"],
        },
    )
    assert registered.status_code == 201, registered.text
    assert registered.json()["data"]["user"]["role"] == "admin"
    login = client.post(
        "/api/auth/login",
        json={"email": "provisioned-admin@example.com", "password": "ValidPassword123!"},
    )
    assert login.status_code == 200
    assert login.json()["data"]["user"]["role"] == "admin"


def test_reserved_demo_domain_is_development_only(client: TestClient, monkeypatch):
    monkeypatch.setattr(settings, "environment", "development")
    body = {
        "name": "Local Demo Citizen",
        "email": "local.demo@civicpulse.test",
        "password": "ValidPassword123!",
    }
    registered = client.post("/api/auth/register", json=body)
    assert registered.status_code == 201, registered.text
    assert registered.json()["data"]["user"]["role"] == "citizen"
    login = client.post("/api/auth/login", json={"email": body["email"], "password": body["password"]})
    assert login.status_code == 200
    assert login.json()["data"]["user"]["email"] == body["email"]

    monkeypatch.setattr(settings, "environment", "production")
    rejected = client.post(
        "/api/auth/register",
        json={**body, "email": "production.demo@civicpulse.test"},
    )
    assert rejected.status_code == 422


def test_seed_refuses_non_development_environment(monkeypatch):
    monkeypatch.setattr(settings, "environment", "production")
    with pytest.raises(RuntimeError, match="ENVIRONMENT=development"):
        seed()
