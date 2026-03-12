from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=255)
    org_name: str = Field(min_length=1, max_length=255)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserInvite(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    role: Literal["admin", "analyst", "viewer"] = "analyst"


class OrganizationResponse(BaseModel):
    id: str
    name: str
    slug: str
    domain: Optional[str] = None
    plan: str
    llm_provider: str
    llm_model: str
    max_verifications_per_month: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    last_login: Optional[datetime] = None
    mfa_enabled: bool
    organization: OrganizationResponse
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    user_id: str
    org_id: str
    role: str


class LLMConfigUpdate(BaseModel):
    llm_provider: str
    llm_model: str


class OrgUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    settings: Optional[dict] = None
