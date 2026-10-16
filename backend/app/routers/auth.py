import logging
import hashlib
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import joinedload

from app.dependencies import CurrentAuth, DbSession
from app.models import RevokedToken, User, UserInvitation
from app.schemas import AuthRead, LoginRequest, UserCreate, UserRead, UserUpdate
from app.security import create_access_token, hash_password, verify_password
from app.serializers import user_data

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = logging.getLogger(__name__)


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: DbSession):
    email = str(payload.email).casefold()
    if db.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    department_id = None
    if payload.role == "citizen":
        if payload.invitation_code:
            raise HTTPException(status_code=422, detail="Invitation codes are only used for privileged accounts")
    else:
        if not payload.invitation_code:
            role_name = "Field Officer" if payload.role == "officer" else "Administrator"
            raise HTTPException(status_code=403, detail=f"{role_name} registration requires an administrator-issued invitation code")
        code_hash = hashlib.sha256(payload.invitation_code.strip().encode("utf-8")).hexdigest()
        invitation = db.scalar(select(UserInvitation).where(UserInvitation.code_hash == code_hash))
        if invitation is None or invitation.role != payload.role:
            raise HTTPException(status_code=403, detail="Invitation code is invalid, expired, or for a different user type")
        now = datetime.now(timezone.utc)
        claimed = db.execute(
            update(UserInvitation)
            .where(
                UserInvitation.id == invitation.id,
                UserInvitation.used_at.is_(None),
                UserInvitation.expires_at > now,
            )
            .values(used_at=now)
            .returning(UserInvitation.department_id)
            .execution_options(synchronize_session=False)
        ).first()
        if claimed is None:
            raise HTTPException(status_code=403, detail="Invitation code is invalid, expired, or already used")
        department_id = claimed.department_id
    user = User(
        name=payload.name.strip(), email=email, password_hash=hash_password(payload.password),
        phone=payload.phone, ward=payload.ward, role=payload.role, department_id=department_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("Citizen account registered: user_id=%s", user.id)
    token, _, _ = create_access_token(user.id)
    response = AuthRead(access_token=token, user=UserRead.model_validate(user_data(user)))
    return {"data": response.model_dump(mode="json")}


@router.post("/login", response_model=dict)
def login(payload: LoginRequest, db: DbSession):
    user = db.scalar(select(User).options(joinedload(User.department)).where(User.email == str(payload.email).casefold()))
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email or password is incorrect")
    token, _, _ = create_access_token(user.id)
    logger.info("User signed in: user_id=%s", user.id)
    return {"data": AuthRead(access_token=token, user=UserRead.model_validate(user_data(user))).model_dump(mode="json")}


@router.post("/logout", response_model=dict)
def logout(auth: CurrentAuth, db: DbSession):
    db.add(RevokedToken(jti=auth.token_id, expires_at=auth.expires_at))
    db.commit()
    return {"data": {"logged_out": True}}


@router.get("/me", response_model=dict)
def read_profile(auth: CurrentAuth):
    return {"data": user_data(auth.user)}


@router.patch("/me", response_model=dict)
def update_profile(payload: UserUpdate, auth: CurrentAuth, db: DbSession):
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(auth.user, key, value.strip() if isinstance(value, str) else value)
    db.commit()
    db.refresh(auth.user)
    return {"data": user_data(auth.user)}
