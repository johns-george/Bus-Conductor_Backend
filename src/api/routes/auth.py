from pydantic import BaseModel
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from src.schemas.signup import SignUpRequest
from src.services import auth_service
from src.core.database import get_db
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import HTTPException, Response
from src.utility.auth_utility import create_access_token, decode_access_token

router=APIRouter(prefix="/auth")


class OtpRequest(BaseModel):
    phone: str
    country: str


class OtpVerifyRequest(BaseModel):
    request_id: str
    code: str


class PasswordResetRequest(BaseModel):
    email: str


class PasswordResetConfirm(BaseModel):
    token: str
    password: str


class ForgotEmailRequest(BaseModel):
    phone: str

@router.post("/google-login")
def google_login(token: str, db: Session = Depends(get_db), response: Response = None):
    return auth_service.google_login(token, db, response)

@router.post("/google")
def google_oauth(
    request: dict,
    db: Session = Depends(get_db),
):
    id_token = request.get("idToken")

    if not id_token:
        raise HTTPException(
            status_code=400,
            detail="Missing Google idToken"
        )

    return auth_service.google_oauth_login(
        id_token,
        db
    )

@router.post("/sign-in")
def sign_in(form_data: OAuth2PasswordRequestForm = Depends(),db: Session = Depends(get_db), response: Response = None):
    return auth_service.signin(form_data.username, form_data.password, db, response)

@router.post("/sign-up")
def sign_up(sign_up_request: SignUpRequest,db: Session = Depends(get_db), response: Response = None):
    return auth_service.signup(sign_up_request, db, response)


@router.post("/refresh")
def refresh_token(request: Request, response: Response):
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")
    
    payload = decode_access_token(refresh_token)

    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    username = payload.get("sub")

    new_access_token, new_refresh_token = __import__('src.utility.auth_utility', fromlist=['create_tokens']).create_tokens(username)

    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=False,
        samesite="Lax"
    )
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=False,
        samesite="Lax"
    )

    return {"message": "Token refreshed", "access_token": new_access_token}

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logged out"}


@router.post("/request-otp")
def request_otp(payload: OtpRequest):
    return auth_service.request_otp(payload.phone, payload.country)


@router.post("/verify-otp")
def verify_otp(payload: OtpVerifyRequest, response: Response, db: Session = Depends(get_db)):
    return auth_service.verify_otp(payload.request_id, payload.code, db, response)


@router.post("/password-reset/request")
def request_password_reset(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    return auth_service.request_password_reset(payload.email, db)


@router.post("/password-reset/confirm")
def confirm_password_reset(payload: PasswordResetConfirm, db: Session = Depends(get_db)):
    return auth_service.confirm_password_reset(payload.token, payload.password, db)


@router.post("/forgot-email")
def forgot_email(payload: ForgotEmailRequest, db: Session = Depends(get_db)):
    return auth_service.find_email_by_phone(payload.phone, db)


@router.get("/me")
def get_current_user(request: Request, response: Response, db: Session = Depends(get_db)):
    """Return the current user based on the access_token cookie.
    If access token is expired, tries to refresh using the refresh token."""
    token = request.cookies.get("access_token")
    username = None

    if token:
        payload = decode_access_token(token)
        if payload and payload.get("type") != "refresh":
            username = payload.get("sub")

    # Access token invalid/expired — try refresh
    if not username:
        refresh = request.cookies.get("refresh_token")
        if refresh:
            rpayload = decode_access_token(refresh)
            if rpayload and rpayload.get("type") == "refresh":
                username = rpayload.get("sub")
                # Issue new token pair
                from src.utility.auth_utility import create_tokens
                new_access, new_refresh = create_tokens(username)
                response.set_cookie(key="access_token", value=new_access, httponly=True, secure=False, samesite="Lax")
                response.set_cookie(key="refresh_token", value=new_refresh, httponly=True, secure=False, samesite="Lax")

    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")

    from src.models.user import User
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return {
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "mobile_number": user.mobile_number,
            "role": user.role,
        }
    }