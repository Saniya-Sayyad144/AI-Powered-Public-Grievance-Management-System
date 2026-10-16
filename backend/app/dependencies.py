from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.database import get_db
from app.models import RevokedToken, User

bearer_scheme = HTTPBearer(auto_error=False)
DbSession = Annotated[Session, Depends(get_db)]


@dataclass
class AuthContext:
    user: User
    token_id: str
    expires_at: datetime


def get_current_auth(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: DbSession,
) -> AuthContext:
    unauthorized = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required", headers={"WWW-Authenticate": "Bearer"})
    if credentials is None:
        raise unauthorized
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id = int(payload["sub"])
        token_id = str(payload["jti"])
        expires_at = datetime.fromtimestamp(float(payload["exp"]), tz=timezone.utc)
    except (jwt.PyJWTError, KeyError, TypeError, ValueError):
        raise unauthorized from None
    if db.get(RevokedToken, token_id):
        raise unauthorized
    user = db.query(User).options(joinedload(User.department)).filter(User.id == user_id, User.is_active.is_(True)).one_or_none()
    if user is None:
        raise unauthorized
    return AuthContext(user=user, token_id=token_id, expires_at=expires_at)


def require_roles(*roles: str):
    def check(auth: Annotated[AuthContext, Depends(get_current_auth)]) -> AuthContext:
        if auth.user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to perform this action")
        return auth

    return check


CurrentAuth = Annotated[AuthContext, Depends(get_current_auth)]
