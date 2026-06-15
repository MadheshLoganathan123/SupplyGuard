from typing import List, Optional

from fastapi import Depends, Header, HTTPException, status

from app.database.supabase_client import supabase_admin
from app.schemas.user import AuthUser, UserRole


def get_bearer_token(authorization: Optional[str] = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return authorization.split(" ", 1)[1].strip()


def get_current_user(token: str = Depends(get_bearer_token)) -> AuthUser:
    result = supabase_admin.auth.get_user(jwt=token)
    if not result or not getattr(result, "user", None):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = result.user
    metadata = getattr(user, "user_metadata", {}) or {}
    role_value = metadata.get("role", UserRole.FARMER.value)
    if role_value not in [role.value for role in UserRole]:
        role_value = UserRole.FARMER.value

    return AuthUser(
        id=user.id,
        email=user.email,
        full_name=metadata.get("full_name", user.email.split("@")[0]),
        role=UserRole(role_value),
    )


def require_roles(allowed_roles: List[UserRole]):
    def _require_roles(current_user: AuthUser = Depends(get_current_user)) -> AuthUser:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role privileges for this endpoint",
            )
        return current_user

    return _require_roles
