from fastapi import Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.models.user import User
from src.utility.auth_utility import decode_access_token, create_access_token


def get_current_user(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    token = request.cookies.get("access_token")
    if token is None:
        raise HTTPException(status_code=401, detail="Invalid token")

    payload = decode_access_token(token)
    username = payload.get("sub")

    # If username claim is missing, try refresh flow.
    if not username:
        refresh_token = request.cookies.get("refresh_token")
        if not refresh_token:
            raise HTTPException(status_code=401, detail="Session expired")

        refresh_payload = decode_access_token(refresh_token)
        if refresh_payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        username = refresh_payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        new_access_token = create_access_token({"sub": username})
        response.set_cookie(
            key="access_token",
            value=new_access_token,
            httponly=True,
            secure=False,
            samesite="Lax"
        )

    user = db.query(User).filter(User.username == username).first()

    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user