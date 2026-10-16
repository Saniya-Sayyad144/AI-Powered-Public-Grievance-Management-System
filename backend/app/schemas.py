from datetime import datetime
from typing import Annotated
from typing import Literal

from email_validator import EmailNotValidError, validate_email
from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr, Field, TypeAdapter, field_validator, model_validator

from app.config import settings

Role = Literal["citizen", "admin", "officer"]
ComplaintStatus = Literal["Submitted", "Under Review", "Assigned", "In Progress", "Resolved"]
Priority = Literal["Low", "Medium", "High", "Critical"]
_email_str_adapter = TypeAdapter(EmailStr)


def _validate_email(value: str) -> str:
    try:
        if settings.environment.casefold() in {"development", "test"}:
            return validate_email(value, check_deliverability=False, test_environment=True).normalized
        return str(_email_str_adapter.validate_python(value))
    except (EmailNotValidError, ValueError) as exc:
        raise ValueError("A valid email address is required") from exc


CivicEmail = Annotated[str, AfterValidator(_validate_email)]


class APIEnvelope(BaseModel):
    data: object
    message: str | None = None


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=2, max_length=120)
    email: CivicEmail
    password: str = Field(min_length=10, max_length=128)
    phone: str | None = Field(default=None, max_length=32)
    ward: str | None = Field(default=None, max_length=80)
    role: Role = "citizen"
    invitation_code: str | None = Field(default=None, min_length=16, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if len(value) < 10:
            raise ValueError("Password must be at least 10 characters long")
        if not any(ch.isupper() for ch in value):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(ch.islower() for ch in value):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(ch.isdigit() for ch in value):
            raise ValueError("Password must contain at least one number")
        if not any(not ch.isalnum() for ch in value):
            raise ValueError("Password must contain at least one symbol")
        return value


class UserInvitationCreate(BaseModel):
    role: Literal["admin", "officer"]
    department_id: int | None = None
    expires_in_minutes: int = Field(default=1440, ge=5, le=10080)

    @model_validator(mode="after")
    def validate_role_department(self):
        if self.role == "officer" and self.department_id is None:
            raise ValueError("Field Officer invitations must include a department")
        if self.role == "admin" and self.department_id is not None:
            raise ValueError("Administrator invitations cannot include a department")
        return self


class LoginRequest(BaseModel):
    email: CivicEmail
    password: str = Field(min_length=1, max_length=128)


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    phone: str | None = Field(default=None, max_length=32)
    ward: str | None = Field(default=None, max_length=80)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: CivicEmail
    phone: str | None
    ward: str | None
    role: Role
    department_id: int | None
    department: str | None = None


class AuthRead(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class ComplaintCreate(BaseModel):
    title: str = Field(min_length=5, max_length=180)
    description: str = Field(min_length=10, max_length=10000)
    category: str | None = Field(default=None, max_length=50)
    location: str = Field(min_length=2, max_length=240)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)

    @field_validator("category")
    @classmethod
    def category_not_blank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            return None
        return value.strip() if value else value


class ComplaintUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=5, max_length=180)
    description: str | None = Field(default=None, min_length=10, max_length=10000)
    location: str | None = Field(default=None, min_length=2, max_length=240)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class StatusUpdate(BaseModel):
    status: ComplaintStatus
    note: str | None = Field(default=None, max_length=500)


class AssignmentCreate(BaseModel):
    department_id: int
    officer_id: int | None = None


class CommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=5000)
    is_internal: bool = False


class CommentRead(BaseModel):
    id: int
    author: str
    body: str
    is_internal: bool
    created_at: datetime


class HistoryRead(BaseModel):
    previous_status: str | None
    new_status: str
    note: str | None
    changed_by: str
    created_at: datetime


class AssignmentRead(BaseModel):
    department: str
    officer: str | None
    assigned_by: str
    assigned_at: datetime
    is_active: bool


class AttachmentRead(BaseModel):
    id: int
    original_name: str
    content_type: str
    size_bytes: int
    url: str
    created_at: datetime


class ComplaintRead(BaseModel):
    id: str
    title: str
    description: str
    category: str
    status: ComplaintStatus
    priority: Priority
    location: str
    department: str
    citizen: str
    officer: str
    date: datetime
    latitude: float | None
    longitude: float | None
    duplicate: str | None
    ai_reason: str
    created_at: datetime
    updated_at: datetime
    history: list[HistoryRead] = []
    comments: list[CommentRead] = []
    attachments: list[AttachmentRead] = []


class NotificationRead(BaseModel):
    id: int
    complaint_id: str | None
    title: str
    message: str
    notification_type: str
    is_read: bool
    created_at: datetime


class FeedbackCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    comments: str | None = Field(default=None, max_length=2000)
    complaint_id: str | None = None


class DepartmentRead(BaseModel):
    id: int
    name: str


class DepartmentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)


class OfficerRead(BaseModel):
    id: int
    name: str
    email: CivicEmail
    department_id: int | None
    department: str | None


class AIRequest(BaseModel):
    title: str = Field(min_length=3, max_length=180)
    description: str = Field(min_length=5, max_length=10000)
    category: str | None = None
    severity: int = Field(default=2, ge=1, le=5)
    safety_impact: bool = False
    complaint_age_days: int = Field(default=0, ge=0, le=3650)


class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total: int
    pages: int


class ComplaintPage(BaseModel):
    items: list[ComplaintRead]
    pagination: PaginationMeta
