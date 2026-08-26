import logging
import time
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from src.models.user import User
from src.schemas.signup import SignUpRequest
from src.utility.hash_utility import hash_password, verify_password
from src.utility.auth_utility import create_tokens
from src.utility.google_auth import verify_google_token
from src.utility.otp_utility import generate_otp, send_otp_sms, send_otp_email
from fastapi import HTTPException, Response
from uuid import uuid4

logger = logging.getLogger("busconductor.auth")

# OTP storage with timestamps for expiration
_pending_otps: dict[str, dict] = {}  # request_id -> {phone, code, expires_at, channel}
_password_reset_tokens: dict[str, dict] = {}  # token -> {username, expires_at}

OTP_EXPIRY_SECONDS = 300  # 5 minutes
PASSWORD_RESET_EXPIRY_SECONDS = 3600  # 1 hour


def _cleanup_expired_otps():
    """Remove expired OTPs from memory."""
    now = time.time()
    expired = [k for k, v in _pending_otps.items() if v.get("expires_at", 0) < now]
    for k in expired:
        _pending_otps.pop(k, None)


def _cleanup_expired_reset_tokens():
    """Remove expired password reset tokens from memory."""
    now = time.time()
    expired = [k for k, v in _password_reset_tokens.items() if v.get("expires_at", 0) < now]
    for k in expired:
        _password_reset_tokens.pop(k, None)


def _user_payload(user: User):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "mobile_number": user.mobile_number,
        "role": user.role,
    }


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str):
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="Lax"
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="Lax"
    )

def google_login(token: str, db: Session, response: Response):
    google_user = verify_google_token(token, db)

    if not google_user:
        raise HTTPException(status_code=401, detail="Invalid Google token")

    email = google_user.get("email")
    name = google_user.get("name")

    # Check if user exists
    user = db.query(User).filter(User.email == email).first()

    # Create user if not exists
    if not user:
        user = User(
            username=email,   # or generate username
            email=email,
            password_hash=None,
            full_name=name,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    access_token, refresh_token = create_tokens(user.username)
    _set_auth_cookies(response, access_token, refresh_token)
    return {
        "message": "Login successful",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": _user_payload(user),
    }

def signup(signup_request: SignUpRequest,db: Session, response: Response):
    user_data = signup_request.dict()
    existing_user = db.query(User).filter(User.username == user_data["username"]).first()
    existing_email = db.query(User).filter(User.email == user_data["email"]).first()

    if existing_user or existing_email:
        raise HTTPException(status_code=400, detail="Username or email already exists")
    
    role = user_data.get("role", "USER").upper()
    if role not in ("USER", "CONDUCTOR", "ADMIN"):
        role = "USER"

    new_user = User(
        username=user_data["username"],
        email=user_data["email"],
        password_hash=hash_password(user_data["password"]),
        full_name=user_data.get("full_name"),
        mobile_number=user_data.get("mobile_number"),
        role=role,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    access_token, refresh_token = create_tokens(new_user.username)

    _set_auth_cookies(response, access_token, refresh_token)
    return {
        "message": "Signup successful",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": _user_payload(new_user),
    }

def signin(username: str, password: str, db: Session, response: Response):
    # First try to find by username
    user = db.query(User).filter(User.username == username).first()
    
    # If not found by username, try by email (handle email-based signins)
    if user is None:
        user = db.query(User).filter(User.email == username).first()
    
    if not user:
        logger.debug("User not found: %s", username)
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if not user.password_hash:
        logger.debug("User has no password: %s", username)
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if not verify_password(password, user.password_hash):
        logger.debug("Password mismatch: %s", username)
        raise HTTPException(status_code=401, detail="Invalid username or password")

    access_token, refresh_token = create_tokens(user.username)
    _set_auth_cookies(response, access_token, refresh_token)
    return {
        "message": "Login successful",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": _user_payload(user),
    }


def request_otp(phone: str, country: str, channel: str = "sms"):
    """Request OTP via SMS or email.
    
    Args:
        phone: Phone number or email address
        country: Country code (for phone) or 'email'
        channel: 'sms' or 'email'
    """
    _cleanup_expired_otps()
    
    # Check rate limiting — max 3 OTPs per phone/email in 10 minutes
    recent_otps = [
        v for v in _pending_otps.values()
        if v.get("phone") == phone and v.get("expires_at", 0) > time.time() - 600
    ]
    if len(recent_otps) >= 3:
        raise HTTPException(status_code=429, detail="Too many OTP requests. Please wait 10 minutes.")
    
    request_id = f"otp_{uuid4().hex[:12]}"
    otp_code = generate_otp()
    
    _pending_otps[request_id] = {
        "phone": phone,
        "country": country,
        "code": otp_code,
        "channel": channel,
        "expires_at": time.time() + OTP_EXPIRY_SECONDS,
        "attempts": 0,
    }
    
    # Send OTP via selected channel
    if channel == "email":
        result = send_otp_email(to_email=phone, otp=otp_code)
    else:
        # Format phone with country code for SMS
        formatted_phone = f"{country}{phone}" if country and not phone.startswith(country) else phone
        result = send_otp_sms(phone=formatted_phone, otp=otp_code)
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail="Failed to send OTP")
    
    return {
        "message": f"OTP sent to {phone}",
        "request_id": request_id,
        "channel": channel,
    }


def verify_otp(request_id: str, code: str, db: Session, response: Response):
    """Verify OTP and authenticate user."""
    _cleanup_expired_otps()
    
    payload = _pending_otps.get(request_id)
    if payload is None:
        raise HTTPException(status_code=400, detail="OTP expired or invalid request")
    
    # Check expiration
    if time.time() > payload.get("expires_at", 0):
        _pending_otps.pop(request_id, None)
        raise HTTPException(status_code=400, detail="OTP expired. Please request a new one.")
    
    # Check attempts (max 5)
    if payload.get("attempts", 0) >= 5:
        _pending_otps.pop(request_id, None)
        raise HTTPException(status_code=429, detail="Too many failed attempts. Please request a new OTP.")
    
    payload["attempts"] = payload.get("attempts", 0) + 1
    
    # Verify code
    if payload["code"] != code:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    # OTP verified — find or create user
    phone = payload["phone"]
    country = payload.get("country", "")
    
    if payload.get("channel") == "email":
        # Email-based login
        existing = db.query(User).filter(User.email == phone).first()
        if existing is None:
            username = phone.split("@")[0]
            # Ensure unique username
            if db.query(User).filter(User.username == username).first():
                username = f"{username}_{uuid4().hex[:6]}"
            existing = User(
                username=username,
                email=phone,
                password_hash=None,
                full_name="Email User",
            )
            db.add(existing)
            db.commit()
            db.refresh(existing)
    else:
        # Phone-based login
        username = f"{country}{phone}" if country and not phone.startswith(country) else phone
        existing = db.query(User).filter(User.username == username).first()
        if existing is None:
            existing = User(
                username=username,
                email=f"{phone}@phone.local",
                mobile_number=username,
                full_name="Phone User",
                password_hash=None,
            )
            db.add(existing)
            db.commit()
            db.refresh(existing)
    
    _pending_otps.pop(request_id, None)
    access_token, refresh_token = create_tokens(existing.username)
    _set_auth_cookies(response, access_token, refresh_token)
    return {
        "message": "OTP verified",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": _user_payload(existing),
    }


def firebase_phone_login(id_token: str, db: Session, response: Response):
    """Verify a Firebase ID token and create/return our app's JWT tokens."""
    from google.auth.transport import requests as google_requests
    from google.oauth2 import id_token as google_id_token
    import os

    try:
        # Verify the Firebase ID token using Google's public keys
        # This works without firebase-admin SDK
        project_id = os.getenv("FIREBASE_PROJECT_ID", "")
        claims = google_id_token.verify_firebase_token(
            id_token,
            google_requests.Request(),
            audience=project_id if project_id else None,
        )
    except Exception as e:
        logger.error("Firebase token verification failed: %s", e)
        raise HTTPException(status_code=401, detail=f"Invalid Firebase token: {e}")

    phone = claims.get("phone_number", "")
    email = claims.get("email", "")
    firebase_uid = claims.get("sub", "")
    name = claims.get("name", "")

    # Find or create user
    username = phone or f"fb_{firebase_uid[:12]}"
    user = db.query(User).filter(User.username == username).first()

    if user is None:
        user = User(
            username=username,
            email=email or f"{phone}@phone.local" if phone else f"{firebase_uid}@firebase.local",
            password_hash=None,
            full_name=name or "Phone User",
            mobile_number=phone or None,
            google_id=firebase_uid,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    elif not user.google_id:
        user.google_id = firebase_uid
        db.commit()

    access_token, refresh_token = create_tokens(user.username)
    _set_auth_cookies(response, access_token, refresh_token)
    return {
        "message": "Phone login successful",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": _user_payload(user),
    }


def find_email_by_phone(phone: str, db: Session):
    """Find email by phone number."""
    user = db.query(User).filter(User.mobile_number == phone).first()
    if user is None or user.email is None:
        return {"found": False, "message": "No account found with this phone number"}
    return {
        "found": True,
        "email": user.email,
        "message": f"Account found: {user.email}",
    }


def request_password_reset(email: str, db: Session):
    user = db.query(User).filter(User.email == email).first()
    # Always return the same message to prevent email enumeration
    if user is None:
        return {"message": "If the email exists, reset instructions are sent"}
    
    _cleanup_expired_reset_tokens()
    
    token = f"rst_{uuid4().hex}"
    _password_reset_tokens[token] = {
        "username": user.username,
        "expires_at": time.time() + PASSWORD_RESET_EXPIRY_SECONDS,
    }

    logger.info("Password reset requested for %s", email)

    # Send the reset email
    from src.utility.email_utility import send_password_reset_email
    send_password_reset_email(to_email=email, reset_token=token)

    return {
        "message": "If the email exists, reset instructions are sent",
    }

def google_oauth_login(id_token: str, db: Session):

    google_user = verify_google_token(id_token, db)

    if not google_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid Google token"
        )

    email = google_user.get("email")
    name = google_user.get("name")
    google_id = google_user.get("sub")

    if not email:
        raise HTTPException(
            status_code=400,
            detail="Google account email not available"
        )

    # Find existing user
    user = db.query(User).filter(
        (User.google_id == google_id) |
        (User.email == email)
    ).first()

    # Create new user
    if not user:

        username = email.split("@")[0]

        # ensure username uniqueness
        existing = db.query(User).filter(
            User.username == username
        ).first()

        if existing:
            username = f"{username}_{google_id[:5]}"

        user = User(
            username=username,
            email=email,
            password_hash=None,
            full_name=name,
            google_id=google_id,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

    # Link Google ID if existing email account
    elif not user.google_id:
        user.google_id = google_id
        db.commit()

    access_token, refresh_token = create_tokens(
        user.username
    )

    return {
        "success": True,
        "message": "Google login successful",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": 3600,
        "user": _user_payload(user),
    }

def confirm_password_reset(token: str, password: str, db: Session):
    _cleanup_expired_reset_tokens()
    
    token_data = _password_reset_tokens.get(token)
    if token_data is None:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    # Check expiration
    if time.time() > token_data.get("expires_at", 0):
        _password_reset_tokens.pop(token, None)
        raise HTTPException(status_code=400, detail="Reset token expired. Please request a new one.")
    
    username = token_data["username"]
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user.password_hash = hash_password(password)
    db.commit()
    _password_reset_tokens.pop(token, None)
    logger.info("Password reset completed for %s", username)
    return {"message": "Password reset successful"}