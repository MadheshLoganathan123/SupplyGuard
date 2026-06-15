"""
Pydantic schemas for user authentication and role-based access.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRole(str, Enum):
    ADMIN = "Admin"
    FARMER = "Farmer"
    DRIVER = "Driver"
    STORE_OWNER = "Store Owner"
    PANTRY_MANAGER = "Pantry Manager"


class UserSignUp(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2)
    role: UserRole = UserRole.FARMER


class UserSignIn(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class AuthTokens(BaseModel):
    access_token: str
    refresh_token: str
    expires_at: Optional[int] = None
    token_type: str = "bearer"


class AuthUser(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: UserRole


class AuthResponse(BaseModel):
    user: AuthUser
    session: Optional[AuthTokens] = None
