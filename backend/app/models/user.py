import enum
from sqlalchemy import Column, String, Boolean, Enum, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import TimestampMixin
from app.core.database import Base


class UserRole(str, enum.Enum):
    owner = "owner"
    admin = "admin"
    analyst = "analyst"
    viewer = "viewer"


class User(TimestampMixin, Base):
    __tablename__ = "users"

    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    role = Column(Enum(UserRole), default=UserRole.analyst, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    mfa_enabled = Column(Boolean, default=False, nullable=False)

    organization = relationship("Organization", lazy="joined")
