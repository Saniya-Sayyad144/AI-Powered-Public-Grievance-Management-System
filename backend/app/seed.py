from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.config import settings
from app.database import SessionLocal
from app.models import Complaint, ComplaintAssignment, ComplaintStatusHistory, Department, User
from app.security import hash_password

DEPARTMENT_NAMES = ["Public Works", "Sanitation", "Water Works", "Drainage", "Electrical"]


def _ensure_demo_user(db, *, name: str, email: str, role: str, department_id: int | None, phone: str, ward: str, password: str) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(name=name, email=email, role=role, department_id=department_id, password_hash=hash_password(password), phone=phone, ward=ward)
        db.add(user)
        db.flush()
        return user
    user.name = name
    user.role = role
    user.department_id = department_id
    user.password_hash = hash_password(password)
    user.phone = phone
    user.ward = ward
    user.is_active = True
    return user


def seed() -> None:
    if settings.environment.casefold() != "development":
        raise RuntimeError("The seed script is restricted to ENVIRONMENT=development")
    demo_passwords = {
        "citizen.demo@civicpulse.test": settings.demo_citizen_password,
        "admin.demo@civicpulse.test": settings.demo_admin_password,
        "officer.demo@civicpulse.test": settings.demo_officer_password,
    }
    missing_passwords = [email for email, password in demo_passwords.items() if not password]
    if missing_passwords:
        raise RuntimeError("Set the three demo-account password variables in backend/.env before seeding")

    db = SessionLocal()
    try:
        departments = {}
        for name in DEPARTMENT_NAMES:
            department = db.scalar(select(Department).where(Department.name == name))
            if department is None:
                department = Department(name=name)
                db.add(department)
                db.flush()
            departments[name] = department

        demo_users = [
            ("Ananya Mehta", "ananya@example.com", "citizen", None, "+91 98765 43210", "Ward 12"),
            ("Rohan Das", "rohan@example.com", "citizen", None, "+91 98765 43211", "Ward 8"),
            ("Farah Khan", "farah@example.com", "citizen", None, "+91 98765 43212", "Ward 7"),
            ("Mihir Joshi", "mihir@example.com", "citizen", None, "+91 98765 43213", "Ward 4"),
            ("Neha Kapoor", "neha@example.com", "citizen", None, "+91 98765 43214", "Ward 15"),
            ("Civic Administrator", "admin@civicpulse.example.com", "admin", None, "+91 90000 00001", "Central Office"),
            ("Vikram Singh", "vikram@civicpulse.example.com", "officer", "Public Works", "+91 90000 00012", "Ward 12"),
            ("Priya Nair", "priya@civicpulse.example.com", "officer", "Sanitation", "+91 90000 00015", "Ward 8"),
            ("Arjun Rao", "arjun@civicpulse.example.com", "officer", "Water Works", "+91 90000 00017", "Ward 4"),
            ("Neel Shah", "neel@civicpulse.example.com", "officer", "Drainage", "+91 90000 00018", "Ward 15"),
        ]
        users = {}
        for name, email, role, department_name, phone, ward in demo_users:
            user = db.scalar(select(User).where(User.email == email))
            if user is None:
                user = User(name=name, email=email, role=role, department_id=departments[department_name].id if department_name else None, password_hash=hash_password(settings.demo_password), phone=phone, ward=ward)
                db.add(user)
                db.flush()
            users[email] = user

        demo_role_users = [
            ("Demo Citizen", "citizen.demo@civicpulse.test", "citizen", None, "+1 555 010 9101", "Ward 12", demo_passwords["citizen.demo@civicpulse.test"]),
            ("Demo Administrator", "admin.demo@civicpulse.test", "admin", None, "+1 555 010 9102", "Civic Center", demo_passwords["admin.demo@civicpulse.test"]),
            ("Demo Field Officer", "officer.demo@civicpulse.test", "officer", "Public Works", "+1 555 010 9103", "Ward 12", demo_passwords["officer.demo@civicpulse.test"]),
        ]
        for name, email, role, department_name, phone, ward, password in demo_role_users:
            users[email] = _ensure_demo_user(
                db,
                name=name,
                email=email,
                role=role,
                department_id=departments[department_name].id if department_name else None,
                phone=phone,
                ward=ward,
                password=password,
            )

        demo_complaints = [
            ("CP-2026-1842", "ananya@example.com", "Large pothole near school entrance", "Deep pothole is causing traffic congestion and is dangerous for students crossing the road.", "Roads", "In Progress", "High", "MG Road, Ward 12", "Public Works", "vikram@civicpulse.example.com", 19.076, 72.8777, "School-zone safety risk and high traffic volume."),
            ("CP-2026-1838", "rohan@example.com", "Garbage not collected for five days", "Overflowing community bins are attracting stray animals and causing a strong odor.", "Garbage", "Assigned", "Critical", "Lake View Colony, Ward 8", "Sanitation", "priya@civicpulse.example.com", 19.089, 72.865, "Public health risk with repeated service failure."),
            ("CP-2026-1824", "farah@example.com", "Streetlights not working", "Four consecutive streetlights are out, making the lane unsafe after dark.", "Streetlights", "Under Review", "Medium", "Sector 7 Market", "Electrical", None, 19.062, 72.892, "Night-time safety impact across a public market."),
            ("CP-2026-1811", "mihir@example.com", "Contaminated water supply", "Tap water appears brown and has an unusual smell since yesterday morning.", "Water Supply", "In Progress", "Critical", "Shanti Nagar, Ward 4", "Water Works", "arjun@civicpulse.example.com", 19.101, 72.881, "Potential immediate public-health hazard."),
            ("CP-2026-1796", "neha@example.com", "Blocked storm drain", "The drain is fully blocked and the street floods during moderate rain.", "Drainage", "Resolved", "High", "Station Road, Ward 15", "Drainage", "neel@civicpulse.example.com", 19.051, 72.846, "Flooding blocks emergency vehicle access."),
        ]
        status_order = ["Submitted", "Under Review", "Assigned", "In Progress", "Resolved"]
        for offset, (complaint_id, citizen_email, title, description, category, current_status, priority, location, department_name, officer_email, latitude, longitude, reason) in enumerate(demo_complaints):
            complaint = db.get(Complaint, complaint_id)
            if complaint is not None:
                continue
            created_at = datetime(2026, 10, 10 - offset, 9, 30, tzinfo=timezone.utc)
            citizen_id = users[citizen_email].id
            complaint = Complaint(id=complaint_id, citizen_id=citizen_id, title=title, description=description, category=category, status=current_status, priority=priority, location=location, latitude=latitude, longitude=longitude, department_id=departments[department_name].id, ai_reason=reason, created_at=created_at, updated_at=created_at)
            db.add(complaint)
            db.flush()
            current_index = status_order.index(current_status)
            for history_index, new_status in enumerate(status_order[:current_index + 1]):
                previous_status = status_order[history_index - 1] if history_index else None
                actor_email = citizen_email if history_index == 0 else officer_email if history_index >= 3 and officer_email else "admin@civicpulse.example.com"
                db.add(ComplaintStatusHistory(complaint_id=complaint_id, previous_status=previous_status, new_status=new_status, changed_by_id=users[actor_email].id, note="Demo complaint submitted" if history_index == 0 else "Demo status recorded", created_at=created_at.replace(minute=created_at.minute + history_index)))
            if officer_email:
                db.add(ComplaintAssignment(complaint_id=complaint_id, department_id=departments[department_name].id, officer_id=users[officer_email].id, assigned_by_id=users["admin@civicpulse.example.com"].id, is_active=True, assigned_at=created_at))

        demo_citizen_email = "citizen.demo@civicpulse.test"
        demo_admin_email = "admin.demo@civicpulse.test"
        demo_officer_email = "officer.demo@civicpulse.test"
        year = datetime.now(timezone.utc).year
        role_complaints = [
            (f"CP-{year}-9101", "Loose manhole cover near Ward 12 school", "A displaced cover creates a fall hazard on the school walking route.", "Roads", "Submitted", "High", "School Road, Ward 12", None, "A pedestrian safety hazard near a school entrance."),
            (f"CP-{year}-9102", "Damaged curb ramp outside the clinic", "The curb ramp is cracked and difficult to use for wheelchair access.", "Roads", "Assigned", "Medium", "Community Clinic, Ward 12", demo_officer_email, "An accessibility obstruction on a public route."),
            (f"CP-{year}-9103", "Large pothole beside the bus stop", "A deep pothole is forcing buses and cyclists into the same narrow lane.", "Roads", "In Progress", "Critical", "Central Bus Stop, Ward 12", demo_officer_email, "Traffic and injury risk requires prompt field review."),
        ]
        status_order = ["Submitted", "Under Review", "Assigned", "In Progress", "Resolved"]
        for index, (complaint_id, title, description, category, current_status, priority, location, officer_email, reason) in enumerate(role_complaints):
            complaint = db.get(Complaint, complaint_id)
            if complaint is not None:
                if complaint.citizen_id != users[demo_citizen_email].id:
                    raise RuntimeError(f"Refusing to overwrite unrelated complaint {complaint_id}")
                continue
            department_name = "Public Works"
            created_at = datetime.now(timezone.utc) - timedelta(days=index + 1)
            complaint = Complaint(
                id=complaint_id,
                citizen_id=users[demo_citizen_email].id,
                title=title,
                description=description,
                category=category,
                status=current_status,
                priority=priority,
                location=location,
                department_id=departments[department_name].id,
                ai_reason=reason,
                created_at=created_at,
                updated_at=created_at,
            )
            db.add(complaint)
            db.flush()
            current_index = status_order.index(current_status)
            for history_index, new_status in enumerate(status_order[:current_index + 1]):
                actor_email = demo_citizen_email if history_index == 0 else demo_officer_email if new_status == "In Progress" else demo_admin_email
                db.add(ComplaintStatusHistory(
                    complaint_id=complaint.id,
                    previous_status=status_order[history_index - 1] if history_index else None,
                    new_status=new_status,
                    changed_by_id=users[actor_email].id,
                    note="Demo complaint submitted" if history_index == 0 else "Development demo workflow",
                    created_at=created_at + timedelta(minutes=history_index),
                ))
            if officer_email:
                db.add(ComplaintAssignment(
                    complaint_id=complaint.id,
                    department_id=departments[department_name].id,
                    officer_id=users[officer_email].id,
                    assigned_by_id=users[demo_admin_email].id,
                    is_active=True,
                    assigned_at=created_at,
                ))
        db.commit()
        print("Seed complete. Ensured 3 role-specific demo accounts and 3 role-specific demo complaints.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
