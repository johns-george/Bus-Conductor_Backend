"""FastAPI dependency that verifies JWT tokens from cookies or Authorization header."""

from fastapi import Request, HTTPException, Depends
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.utility.auth_utility import decode_access_token
from src.models.user import User


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Extract and verify the current user from the request.

    Checks cookies first, then Authorization header.
    Raises 401 if not authenticated.
    """
    token = _extract_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Refresh tokens can't be used for auth
    if payload.get("type") == "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")

    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user


def require_role(*roles: str):
    """Dependency factory that restricts access to specific roles."""

    def _check(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=403,
                detail=f"Requires role: {', '.join(roles)}",
            )
        return user

    return _check


def _extract_token(request: Request) -> str | None:
    """Get JWT from cookie or Authorization header."""
    # Try cookie first
    token = request.cookies.get("access_token")
    if token:
        return token

    # Try Authorization header
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]

    return None
