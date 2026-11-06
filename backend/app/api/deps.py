import logging
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models import User, StudentProfile

logger = logging.getLogger(__name__)

# Optional HTTPBearer so unauthenticated requests in dev mode can use seeded test profile
security_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency that resolves the current authenticated user.
    - If a valid Bearer JWT is supplied, decodes email and fetches user.
    - If in development mode and no token is passed, falls back to the seeded student user.
    """
    token = auth.credentials if auth else None

    if token:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            email: Optional[str] = payload.get("sub")
            if email:
                user = db.query(User).filter(User.email == email).first()
                if user and user.is_active:
                    return user
        except JWTError:
            pass  # Fall through to dev fallback or 401

    # Development fallback to primary seeded student
    if settings.DEBUG or settings.ENVIRONMENT == "development":
        user = db.query(User).filter(User.email == "student@skillbridge.ai").first()
        if not user:
            user = db.query(User).first()
        if user and user.is_active:
            return user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or active session",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_student_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> StudentProfile:
    """
    Ensures the current user has an attached StudentProfile.
    Creates a baseline profile if one does not exist yet.
    """
    profile = current_user.profile
    if not profile:
        profile = StudentProfile(
            user_id=current_user.id,
            degree="B.Tech",
            branch="Computer Science",
            year=1,
            experience_level="Beginner",
            raw_bio=""
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)

    return profile
