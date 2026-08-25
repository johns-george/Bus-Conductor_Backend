from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.models.user import User
from src.services import app_state

router = APIRouter(prefix="/users", tags=["users"])


class UpdateUserRequest(BaseModel):
    full_name: str | None = None
    email: str | None = None
    mobile_number: str | None = None
    avatar_url: str | None = None


@router.get("/{user_id}")
def user_by_id(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "email": user.email,
        "mobile_number": user.mobile_number,
        "avatar_url": None,
        "role": user.role,
        "message": "User detail",
    }


@router.put("/{user_id}")
def update_user(user_id: int, payload: UpdateUserRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.email is not None:
        user.email = payload.email
    if payload.mobile_number is not None:
        user.mobile_number = payload.mobile_number
    db.commit()
    db.refresh(user)
    return {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "email": user.email,
        "mobile_number": user.mobile_number,
        "avatar_url": payload.avatar_url,
        "role": user.role,
        "message": "User updated",
    }


@router.get("/{user_id}/notifications")
def user_notifications(user_id: int):
    app_state.notifications_by_user.setdefault(user_id, [])
    return {
        "user_id": user_id,
        "items": app_state.notifications_by_user[user_id],
        "message": "User notifications",
    }


@router.patch("/{user_id}/notifications/{notification_id}/read")
def mark_notification_read(user_id: int, notification_id: str):
    items = app_state.notifications_by_user.setdefault(user_id, [])
    target = next((item for item in items if item["id"] == notification_id), None)
    if target is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    target["read"] = True
    return {"user_id": user_id, "notification_id": notification_id, "read": True, "message": "Notification marked read"}
