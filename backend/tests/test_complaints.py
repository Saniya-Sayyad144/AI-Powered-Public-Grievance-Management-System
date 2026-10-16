from fastapi.testclient import TestClient

from tests.conftest import TestingSession, bearer, create_account, create_department


def complaint_payload():
    return {"title": "Pothole outside the library", "description": "A deep pothole is causing dangerous traffic near the public library.", "category": "Roads", "location": "Ward 4 main road", "latitude": 19.07, "longitude": 72.87}


def test_citizen_complaint_crud_and_private_scope(client: TestClient):
    create_account("citizen", "citizen@example.com")
    create_account("citizen", "other@example.com")
    citizen = bearer(client, "citizen@example.com")
    other = bearer(client, "other@example.com")
    created = client.post("/api/complaints", json=complaint_payload(), headers=citizen)
    assert created.status_code == 201, created.text
    complaint_id = created.json()["data"]["id"]
    assert complaint_id.startswith("CP-")
    assert client.get("/api/complaints", headers=citizen).json()["meta"]["total"] == 1
    assert client.get(f"/api/complaints/{complaint_id}", headers=other).status_code == 404
    assert client.patch(f"/api/complaints/{complaint_id}", json={"location": "Ward 4"}, headers=citizen).status_code == 200
    assert client.get(f"/api/complaints/{complaint_id}/track", headers=citizen).json()["data"]["id"] == complaint_id


def test_admin_assignment_and_officer_status_updates(client: TestClient):
    department_id = create_department()
    create_account("admin", "admin@example.com")
    officer_id = create_account("officer", "officer@example.com", department_id)
    create_account("citizen", "citizen@example.com")
    citizen = bearer(client, "citizen@example.com")
    admin = bearer(client, "admin@example.com")
    officer = bearer(client, "officer@example.com")
    created = client.post("/api/complaints", json=complaint_payload(), headers=citizen)
    complaint_id = created.json()["data"]["id"]
    assignment = client.post(f"/api/complaints/{complaint_id}/assign", json={"department_id": department_id, "officer_id": officer_id}, headers=admin)
    assert assignment.status_code == 200, assignment.text
    assert assignment.json()["data"]["status"] == "Assigned"
    rows = client.get("/api/complaints", headers=officer).json()["data"]
    assert [item["id"] for item in rows] == [complaint_id]
    changed = client.patch(f"/api/complaints/{complaint_id}/status", json={"status": "In Progress"}, headers=officer)
    assert changed.status_code == 200, changed.text
    assert changed.json()["data"]["status"] == "In Progress"
    assert len(changed.json()["data"]["history"]) == 4


def test_permissions_and_invalid_status_transitions(client: TestClient):
    create_account("citizen", "citizen@example.com")
    create_account("officer", "officer@example.com")
    citizen = bearer(client, "citizen@example.com")
    officer = bearer(client, "officer@example.com")
    created = client.post("/api/complaints", json=complaint_payload(), headers=citizen)
    complaint_id = created.json()["data"]["id"]
    assert client.patch(f"/api/complaints/{complaint_id}/status", json={"status": "Resolved"}, headers=citizen).status_code == 403
    assert client.patch(f"/api/complaints/{complaint_id}/status", json={"status": "Resolved"}, headers=officer).status_code == 404
    assert client.post("/api/complaints", json={**complaint_payload(), "title": "no"}, headers=citizen).status_code == 422
    assert client.get("/api/complaints").status_code == 401


def test_invalid_officer_assignment_is_rejected(client: TestClient):
    department_id = create_department()
    create_account("admin", "admin@example.com")
    create_account("citizen", "citizen@example.com")
    create_account("officer", "wrong-department@example.com")
    citizen = bearer(client, "citizen@example.com")
    admin = bearer(client, "admin@example.com")
    complaint_id = client.post("/api/complaints", json=complaint_payload(), headers=citizen).json()["data"]["id"]
    response = client.post(f"/api/complaints/{complaint_id}/assign", json={"department_id": department_id, "officer_id": 3}, headers=admin)
    assert response.status_code == 422


def test_duplicate_matches_do_not_disclose_other_citizen_records(client: TestClient):
    create_account("citizen", "first@example.com")
    create_account("citizen", "second@example.com")
    first_headers = bearer(client, "first@example.com")
    second_headers = bearer(client, "second@example.com")
    first = client.post("/api/complaints", json=complaint_payload(), headers=first_headers).json()["data"]
    second = client.post("/api/complaints", json=complaint_payload(), headers=second_headers).json()["data"]
    assert first["id"] not in second["duplicate"]
    analysis = client.post("/api/ai/analyze", json={"title": complaint_payload()["title"], "description": complaint_payload()["description"]}, headers=second_headers)
    assert analysis.status_code == 200
    assert all("complaint_id" not in item for item in analysis.json()["data"]["possible_duplicates"])


def test_new_complaint_notifies_citizen_and_administrators(client: TestClient):
    create_account("citizen", "citizen@example.com")
    create_account("admin", "admin@example.com")
    citizen = bearer(client, "citizen@example.com")
    admin = bearer(client, "admin@example.com")
    created = client.post("/api/complaints", json=complaint_payload(), headers=citizen)
    assert created.status_code == 201, created.text
    complaint_id = created.json()["data"]["id"]

    citizen_notifications = client.get("/api/notifications", headers=citizen).json()
    admin_notifications = client.get("/api/notifications", headers=admin).json()
    assert citizen_notifications["meta"]["unread"] == 1
    assert citizen_notifications["data"][0]["notification_type"] == "complaint_submitted"
    assert admin_notifications["data"][0]["complaint_id"] == complaint_id
    assert admin_notifications["data"][0]["title"] == "New complaint"
    assert client.get("/api/complaints", headers=admin).json()["data"][0]["id"] == complaint_id


def test_assignment_is_idempotent_and_reassignment_updates_visibility(client: TestClient):
    public_works_id = create_department("Public Works")
    sanitation_id = create_department("Sanitation")
    create_account("admin", "admin@example.com")
    first_officer_id = create_account("officer", "first-officer@example.com", public_works_id)
    second_officer_id = create_account("officer", "second-officer@example.com", sanitation_id)
    create_account("citizen", "citizen@example.com")
    citizen = bearer(client, "citizen@example.com")
    admin = bearer(client, "admin@example.com")
    first_officer = bearer(client, "first-officer@example.com")
    second_officer = bearer(client, "second-officer@example.com")
    complaint_id = client.post("/api/complaints", json=complaint_payload(), headers=citizen).json()["data"]["id"]

    payload = {"department_id": public_works_id, "officer_id": first_officer_id}
    initial = client.post(f"/api/complaints/{complaint_id}/assign", json=payload, headers=admin)
    assert initial.status_code == 200, initial.text
    initial_history_count = len(initial.json()["data"]["assignments"])
    initial_officer_notifications = client.get("/api/notifications", headers=first_officer).json()["meta"]["unread"]
    repeated = client.post(f"/api/complaints/{complaint_id}/assign", json=payload, headers=admin)
    assert repeated.status_code == 200
    assert len(repeated.json()["data"]["assignments"]) == initial_history_count
    assert client.get("/api/notifications", headers=first_officer).json()["meta"]["unread"] == initial_officer_notifications

    reassigned = client.post(
        f"/api/complaints/{complaint_id}/assign",
        json={"department_id": sanitation_id, "officer_id": second_officer_id},
        headers=admin,
    )
    assert reassigned.status_code == 200, reassigned.text
    assert client.get("/api/complaints", headers=first_officer).json()["meta"]["total"] == 0
    assert client.get("/api/complaints", headers=second_officer).json()["meta"]["total"] == 1
    previous_officer_notifications = client.get("/api/notifications", headers=first_officer).json()["data"]
    assert any(item["notification_type"] == "complaint_reassigned" for item in previous_officer_notifications)
    assert client.get("/api/notifications", headers=second_officer).json()["data"][0]["notification_type"] == "complaint_assigned"
    assert client.get("/api/notifications", headers=citizen).json()["meta"]["unread"] == 3

    with TestingSession() as db:
        active = db.query(__import__("app.models", fromlist=["ComplaintAssignment"]).ComplaintAssignment).filter_by(complaint_id=complaint_id, is_active=True).one()
        assert active.officer_id == second_officer_id


def test_only_administrators_can_assign_complaints(client: TestClient):
    department_id = create_department()
    create_account("citizen", "citizen@example.com")
    create_account("officer", "officer@example.com", department_id)
    citizen = bearer(client, "citizen@example.com")
    officer = bearer(client, "officer@example.com")
    complaint_id = client.post("/api/complaints", json=complaint_payload(), headers=citizen).json()["data"]["id"]
    payload = {"department_id": department_id, "officer_id": 2}
    assert client.post(f"/api/complaints/{complaint_id}/assign", json=payload, headers=citizen).status_code == 403
    assert client.post(f"/api/complaints/{complaint_id}/assign", json=payload, headers=officer).status_code == 403


def test_notification_read_is_private_and_updates_unread_count(client: TestClient):
    create_account("citizen", "citizen@example.com")
    create_account("citizen", "other@example.com")
    citizen = bearer(client, "citizen@example.com")
    other = bearer(client, "other@example.com")
    created = client.post("/api/complaints", json=complaint_payload(), headers=citizen)
    complaint_id = created.json()["data"]["id"]
    notification = client.get("/api/notifications", headers=citizen).json()["data"][0]
    assert notification["title"] == "Complaint received"
    assert notification["notification_type"] == "complaint_submitted"
    assert notification["complaint_id"] == complaint_id
    assert client.patch(f"/api/notifications/{notification['id']}/read", headers=other).status_code == 404
    read = client.patch(f"/api/notifications/{notification['id']}/read", headers=citizen)
    assert read.status_code == 200
    assert read.json()["data"]["is_read"] is True
    assert client.get("/api/notifications", headers=citizen).json()["meta"]["unread"] == 0


def test_officer_filter_is_admin_only_and_limits_active_assignments(client: TestClient):
    department_id = create_department()
    create_account("admin", "admin@example.com")
    officer_id = create_account("officer", "officer@example.com", department_id)
    create_account("citizen", "citizen@example.com")
    admin = bearer(client, "admin@example.com")
    officer = bearer(client, "officer@example.com")
    citizen = bearer(client, "citizen@example.com")
    complaint_id = client.post("/api/complaints", json=complaint_payload(), headers=citizen).json()["data"]["id"]
    assert client.get(f"/api/complaints?officer_id={officer_id}", headers=citizen).status_code == 403
    assigned = client.post(
        f"/api/complaints/{complaint_id}/assign",
        json={"department_id": department_id, "officer_id": officer_id},
        headers=admin,
    )
    assert assigned.status_code == 200
    filtered = client.get(f"/api/complaints?officer_id={officer_id}", headers=admin)
    assert filtered.status_code == 200
    assert [row["id"] for row in filtered.json()["data"]] == [complaint_id]
    assert client.get(f"/api/complaints?officer_id={officer_id}", headers=officer).status_code == 403
