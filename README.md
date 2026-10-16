# CivicPulse AI
### AI-Powered Public Grievance Management System

CivicPulse AI is a full-stack web application designed to streamline public grievance management through centralized complaint tracking, role-based access control, officer assignment, and AI-assisted complaint analysis. The platform connects citizens, administrators, and field officers through a structured workflow that improves complaint visibility, accountability, and resolution tracking.

## Key Features

- **Complaint Management:** Submit, review, track, and manage civic complaints through a centralized platform.
- **Role-Based Dashboards:** Dedicated interfaces for Citizens, Administrators, and Field Officers.
- **Officer Assignment:** Assign and reassign complaints to specific field officers.
- **Complaint Tracking:** Monitor complaint status, progress, and resolution history.
- **AI-Assisted Analysis:** Support complaint categorization, priority recommendations, and duplicate-report detection.
- **Notification System:** Keep users informed about complaint submissions, assignments, and status updates.
- **Administrative Analytics:** Monitor complaint statistics, workload, and resolution trends.
- **Feedback Management:** Collect citizen feedback on complaint resolution.
- **Data Export:** Export complaint records for reporting and analysis.

## User Roles

| Role | Responsibilities |
|---|---|
| Citizen | Submit complaints, track progress, receive notifications, and provide feedback. |
| Administrator | Manage complaints, assign field officers, monitor operations, and review analytics. |
| Field Officer | Access assigned complaints, update progress, and record resolutions. |

## Technology Stack

| Layer | Technologies |
|---|---|
| Frontend | React, TypeScript, TanStack Start, Tailwind CSS |
| Backend | Python, FastAPI |
| Database | PostgreSQL |
| ORM & Migrations | SQLAlchemy, Alembic |
| Authentication | JWT, Argon2 password hashing |
| AI/ML | Complaint categorization and prioritization recommendations, subject to the implemented models |

## Architecture

```text
Citizen / Administrator / Field Officer
                  |
                  v
        React + TypeScript UI
                  |
                  v
            FastAPI REST API
                  |
          +-------+-------+
          |               |
          v               v
     PostgreSQL        AI Analysis
          |
          v
 Complaints, Assignments,
 Notifications and History
```

## Project Structure

```text
CivicPulse-AI/
├── backend/
│   ├── app/
│   ├── migrations/
│   ├── tests/
│   └── requirements.txt
├── src/
├── public/
├── package.json
├── .env.example
├── .gitignore
└── README.md
```

*The directory structure may vary based on the current implementation.*

## Getting Started

### Prerequisites

- Node.js and npm
- Python 3.10+
- PostgreSQL
- Git

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd CivicPulse-AI
```

### 2. Configure the database

Create a PostgreSQL database and a dedicated local development user. Configure the connection string in `backend/.env`.

### 3. Set up the backend

From the project root, run:

```powershell
Copy-Item backend/.env.example backend/.env
py -3.10 -m venv backend/.venv
backend/.venv/Scripts/Activate.ps1
python -m pip install -r backend/requirements.txt
Set-Location backend
alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Configure all required environment variables and generate a secure JWT secret before running the application.

API documentation: http://127.0.0.1:8000/docs

### 4. Set up the frontend

Open a second terminal in the project root:

```powershell
Copy-Item .env.example .env
npm install
npm run dev
```

Configure the frontend API URL to point to the running backend. Open the local URL displayed in the terminal.

## Testing

Backend tests:

```powershell
Set-Location backend
python -m pytest -q
```

Frontend checks:

```powershell
npm run lint
npm run build
```

Run these commands from the appropriate directories and verify the results against the project's configured scripts.

## Security

- Role-based authorization for protected operations.
- Secure password hashing.
- Environment-based configuration for credentials and secrets.
- Server-side authorization for complaint access and assignment.
- Separate permissions for citizens, administrators, and field officers.

## Project Objective

The objective of CivicPulse AI is to provide a transparent and structured approach to public grievance handling by connecting complaint reporting, administrative assignment, field-level action, and resolution tracking in one application.

## License

Specify an appropriate license before distributing this project as open-source software.