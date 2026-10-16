import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.dependencies import AuthContext, DbSession, require_roles
from app.models import Department, User, UserInvitation
from app.schemas import DepartmentCreate, DepartmentRead, OfficerRead, UserInvitationCreate

router = APIRouter(tags=["Administration"])
AdminAuth = require_roles("admin")


@router.get("/departments", response_model=dict)
def list_departments(db: DbSession, _auth: Annotated[AuthContext, Depends(require_roles("admin", "officer"))]):
    departments = db.scalars(select(Department).order_by(Department.name)).all()
    return {"data": [DepartmentRead(id=item.id, name=item.name).model_dump() for item in departments]}


@router.post("/departments", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_department(payload: DepartmentCreate, db: DbSession, _auth: Annotated[AuthContext, Depends(AdminAuth)]):
    name = payload.name.strip()
    if db.scalar(select(Department.id).where(Department.name == name)):
        raise HTTPException(status_code=409, detail="Department already exists")
    department = Department(name=name)
    db.add(department)
    db.commit()
    db.refresh(department)
    return {"data": DepartmentRead(id=department.id, name=department.name).model_dump()}


@router.get("/officers", response_model=dict)
def list_officers(db: DbSession, _auth: Annotated[AuthContext, Depends(AdminAuth)]):
    officers = db.scalars(select(User).where(User.role == "officer", User.is_active.is_(True)).order_by(User.name)).all()
    return {"data": [OfficerRead(id=item.id, name=item.name, email=item.email, department_id=item.department_id, department=item.department.name if item.department else None).model_dump() for item in officers]}


@router.post("/invitations", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_user_invitation(
    payload: UserInvitationCreate,
    db: DbSession,
    auth: Annotated[AuthContext, Depends(AdminAuth)],
):
    if payload.department_id is not None and db.get(Department, payload.department_id) is None:
        raise HTTPException(status_code=404, detail="Department not found")
    code = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=payload.expires_in_minutes)
    invitation = UserInvitation(
        code_hash=hashlib.sha256(code.encode("utf-8")).hexdigest(),
        role=payload.role,
        department_id=payload.department_id,
        created_by_id=auth.user.id,
        expires_at=expires_at,
    )
    db.add(invitation)
    db.commit()
    return {"data": {"code": code, "role": invitation.role, "department_id": invitation.department_id, "expires_at": expires_at}}


@router.patch("/users/{user_id}/role", response_model=dict)
def update_user_role(
    user_id: int,
    role: Literal["citizen", "admin", "officer"],
    db: DbSession,
    auth: Annotated[AuthContext, Depends(AdminAuth)],
    department_id: int | None = None,
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == auth.user.id and role != "admin":
        raise HTTPException(status_code=400, detail="Administrators cannot remove their own administrator role")
    if role == "officer" and department_id is None:
        raise HTTPException(status_code=422, detail="Officers must belong to a department")
    if department_id is not None and db.get(Department, department_id) is None:
        raise HTTPException(status_code=404, detail="Department not found")
    user.role = role
    user.department_id = department_id if role == "officer" else None
    db.commit()
    return {"data": {"id": user.id, "role": user.role, "department_id": user.department_id}}
