from sqlalchemy.orm import Session
from src.models.user import User
from src.schemas.signup import SignUpRequest
from src.utility.hash_utility import hash_password, verify_password
from src.utility.auth_utility import create_tokens
from src.utility.google_auth import verify_google_token
from fastapi import HTTPException, Response
from uuid import uuid4

_pending_otps: dict[str, dict[str, str]] = {}
_password_reset_tokens: dict[str, str] = {}


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
        print(f"🔍 DEBUG: User not found for username: {username}")
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    if not user.password_hash:
        print(f"🔍 DEBUG: User found but password_hash is None for user: {username}")
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    password_valid = verify_password(password, user.password_hash)
    print(f"🔍 DEBUG: Password verification result: {password_valid}")
    print(f"🔍 DEBUG: Input password: '{password}'")
    print(f"🔍 DEBUG: Stored hash: '{user.password_hash}'")
    
    if not password_valid:
        print(f"🔍 DEBUG: Password verification failed for user: {username}")
        raise HTTPException(status_code=401, detail="Invalid username or password")

    access_token, refresh_token = create_tokens(user.username)
    _set_auth_cookies(response, access_token, refresh_token)
    return {
        "message": "Login successful",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": _user_payload(user),
    }


def request_otp(phone: str, country: str):
    request_id = f"otp_{uuid4().hex[:12]}"
    _pending_otps[request_id] = {
        "phone": phone,
        "country": country,
        "code": "123456",
    }
    return {"message": "OTP sent", "request_id": request_id}


def verify_otp(request_id: str, code: str, db: Session, response: Response):
    payload = _pending_otps.get(request_id)
    if payload is None or payload["code"] != code:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    username = f"{payload['country']}{payload['phone']}"
    existing = db.query(User).filter(User.username == username).first()
    if existing is None:
        existing = User(
            username=username,
            email=f"{payload['phone']}@phone.local",
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
    token = f"rst_{uuid4().hex}"
    _password_reset_tokens[token] = user.username

    # Print token to console for development
    print(f"\n{'='*60}", flush=True)
    print(f"🔐 PASSWORD RESET TOKEN", flush=True)
    print(f"Email: {email}", flush=True)
    print(f"Token: {token}", flush=True)
    print(f"{'='*60}\n", flush=True)

    # Send the reset email
    from src.utility.email_utility import send_password_reset_email
    send_password_reset_email(to_email=email, reset_token=token)

    return {
        "message": "If the email exists, reset instructions are sent",
        "reset_token": token,
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
    username = _password_reset_tokens.get(token)
    if username is None:
        raise HTTPException(status_code=400, detail="Invalid reset token")
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user.password_hash = hash_password(password)
    db.commit()
    _password_reset_tokens.pop(token, None)
    return {"message": "Password reset successful"}