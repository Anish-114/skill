import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_current_student_profile
from app.core.security import get_password_hash, verify_password, create_access_token
from app.db.session import get_db
from app.models import User, StudentProfile
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    TokenResponse,
)
from app.api.v1.profiles import _format_profile_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _build_user_response(user: User, db: Session) -> UserResponse:
    profile_response = None
    if user.profile:
        profile_response = _format_profile_response(user.profile, user)
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        created_at=user.created_at,
        profile=profile_response
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def register_user(payload: UserRegisterRequest, db: Session = Depends(get_db)):
    """
    Registers a new user account with an attached baseline StudentProfile
    and returns a signed JWT access token.
    """
    clean_email = payload.email.strip().lower()
    existing_user = db.query(User).filter(User.email == clean_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists. Please log in."
        )

    hashed_pw = get_password_hash(payload.password)
    user = User(
        email=clean_email,
        full_name=payload.full_name.strip(),
        hashed_password=hashed_pw,
        is_active=True,
        is_superuser=False
    )
    db.add(user)
    db.flush()

    # Create associated student profile
    profile = StudentProfile(
        user_id=user.id,
        degree=payload.degree or "B.Tech",
        branch=payload.branch or "Computer Science",
        year=payload.year or 1,
        college_name=payload.college_name,
        experience_level=payload.experience_level or "Beginner",
        raw_bio=f"Student pursuing {payload.degree or 'B.Tech'} in {payload.branch or 'Computer Science'}."
    )
    db.add(profile)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.email, "user_id": user.id})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=_build_user_response(user, db)
    )


@router.post("/login", response_model=TokenResponse)
def login_user(payload: UserLoginRequest, db: Session = Depends(get_db)):
    """
    Authenticates an existing user via email and password and returns a signed JWT token.
    """
    clean_email = payload.email.strip().lower()
    user = db.query(User).filter(User.email == clean_email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This user account is inactive. Please contact support."
        )

    # Ensure profile exists
    if not user.profile:
        profile = StudentProfile(
            user_id=user.id,
            degree="B.Tech",
            branch="Computer Science",
            year=1,
            experience_level="Beginner",
            raw_bio=""
        )
        db.add(profile)
        db.commit()
        db.refresh(user)

    token = create_access_token({"sub": user.email, "user_id": user.id})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=_build_user_response(user, db)
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns the currently authenticated user's account details and profile.
    """
    return _build_user_response(current_user, db)


# Users router for /users/me endpoint
users_router = APIRouter(prefix="/users", tags=["Users"])


@users_router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint for fetching the active authenticated user and profile (/api/users/me).
    """
    return _build_user_response(current_user, db)
