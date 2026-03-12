import enum
from sqlalchemy import Column, String, Boolean, Integer, Enum, JSON
from app.models.base import TimestampMixin
from app.core.database import Base


class OrgPlan(str, enum.Enum):
    starter = "starter"
    professional = "professional"
    enterprise = "enterprise"


class Organization(TimestampMixin, Base):
    __tablename__ = "organizations"

    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    domain = Column(String(255), nullable=True)
    plan = Column(Enum(OrgPlan), default=OrgPlan.starter, nullable=False)
    stripe_customer_id = Column(String(255), nullable=True)
    stripe_subscription_id = Column(String(255), nullable=True)
    settings = Column(JSON, default=dict, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    llm_provider = Column(String(50), default="deepseek", nullable=False)
    llm_model = Column(String(100), default="deepseek-chat", nullable=False)
    max_verifications_per_month = Column(Integer, default=10, nullable=False)
