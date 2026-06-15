"""Authentication endpoints for Supabase-based signup, login, and current-user verification."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_user
from app.database.supabase_client import supabase
from app.schemas.user import AuthResponse, AuthTokens, AuthUser, UserSignIn, UserSignUp

router = APIRouter()


def _session_to_tokens(session: object) -> AuthTokens | None:
    if not session:
        return None
    return AuthTokens(
        access_token=session.access_token,
        refresh_token=session.refresh_token,
        expires_at=getattr(session, "expires_at", None),
        token_type="bearer",
    )


def _build_auth_user(user: object, metadata: dict) -> AuthUser:
    return AuthUser(
        id=user.id,
        email=user.email,
        full_name=metadata.get("full_name", user.email.split("@")[0]),
        role=metadata.get("role", "Farmer"),
    )


@router.post(
    "/signup",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user account",
)
async def signup(payload: UserSignUp):
    try:
        result = supabase.auth.sign_up(
            {
                "email": payload.email,
                "password": payload.password,
                "options": {
                    "data": {
                        "full_name": payload.full_name,
                        "role": payload.role,
                    }
                },
            }
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    if not getattr(result, "user", None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to register user with Supabase.",
        )

    metadata = getattr(result.user, "user_metadata", {}) or {}
    return AuthResponse(
        user=_build_auth_user(result.user, metadata),
        session=_session_to_tokens(getattr(result, "session", None)),
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Sign in with email and password",
)
async def login(payload: UserSignIn):
    try:
        result = supabase.auth.sign_in_with_password(
            {
                "email": payload.email,
                "password": payload.password,
            }
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    if not getattr(result, "session", None) or not getattr(result, "user", None):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    metadata = getattr(result.user, "user_metadata", {}) or {}
    return AuthResponse(
        user=_build_auth_user(result.user, metadata),
        session=_session_to_tokens(result.session),
    )


@router.get(
    "/me",
    response_model=AuthUser,
    summary="Get the current authenticated user",
)
async def me(current_user: AuthUser = Depends(get_current_user)) -> AuthUser:
    return current_user
