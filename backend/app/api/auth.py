"""Authentication endpoints backed by Supabase Auth."""

from fastapi import APIRouter, Depends, status
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from app.services.auth.auth_dependency import get_current_user
from app.services.auth.auth_service import AuthenticatedUser, login_user, register_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


class AuthRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: str
    email: str | None = None
    role: str


class AuthResponse(BaseModel):
    access_token: str | None = None
    token_type: str = "bearer"
    user: UserResponse


def _user_response(user: AuthenticatedUser) -> UserResponse:
    return UserResponse(id=user.id, email=user.email, role=user.role)


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a user",
    description="Create a Supabase Auth user and an application profile.",
)
async def register(request: AuthRequest) -> AuthResponse:
    user, token = await run_in_threadpool(register_user, request.email, request.password)
    return AuthResponse(access_token=token, user=_user_response(user))


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Sign in a user",
    description="Sign in with Supabase Auth and return a bearer access token.",
)
async def login(request: AuthRequest) -> AuthResponse:
    user, token = await run_in_threadpool(login_user, request.email, request.password)
    return AuthResponse(access_token=token, user=_user_response(user))


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the current user",
    description="Return the identity represented by the supplied Supabase token.",
)
async def me(current_user: AuthenticatedUser = Depends(get_current_user)) -> UserResponse:
    return _user_response(current_user)
