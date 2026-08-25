from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.dao import payment_method_dao

router = APIRouter(prefix="/payment-methods", tags=["payment-methods"])


class CreatePaymentMethodRequest(BaseModel):
    method_type: str  # UPI, CARD, NETBANKING
    label: str
    subtitle: str | None = None
    provider: str | None = None
    last_four: str | None = None
    upi_id: str | None = None
    is_default: bool = False


class UpdatePaymentMethodRequest(BaseModel):
    label: str | None = None
    subtitle: str | None = None
    is_default: bool | None = None


def _serialize(m):
    return {
        "id": m.id,
        "user_id": m.user_id,
        "method_type": m.method_type,
        "label": m.label,
        "subtitle": m.subtitle,
        "provider": m.provider,
        "last_four": m.last_four,
        "upi_id": m.upi_id,
        "is_default": m.is_default,
        "is_active": m.is_active,
        "created_at": m.created_at.isoformat() if m.created_at else None,
    }


@router.get("/{user_id}")
def list_methods(user_id: int, db: Session = Depends(get_db)):
    methods = payment_method_dao.get_all_by_user(db, user_id)
    return [_serialize(m) for m in methods]


@router.post("/{user_id}")
def create_method(user_id: int, payload: CreatePaymentMethodRequest, db: Session = Depends(get_db)):
    method = payment_method_dao.create(
        db,
        user_id=user_id,
        method_type=payload.method_type,
        label=payload.label,
        subtitle=payload.subtitle,
        provider=payload.provider,
        last_four=payload.last_four,
        upi_id=payload.upi_id,
        is_default=payload.is_default,
    )
    return _serialize(method)


@router.put("/{user_id}/{method_id}")
def update_method(user_id: int, method_id: int, payload: UpdatePaymentMethodRequest, db: Session = Depends(get_db)):
    method = payment_method_dao.update(
        db,
        method_id=method_id,
        user_id=user_id,
        label=payload.label,
        subtitle=payload.subtitle,
        is_default=payload.is_default,
    )
    if method is None:
        raise HTTPException(status_code=404, detail="Payment method not found")
    return _serialize(method)


@router.delete("/{user_id}/{method_id}")
def delete_method(user_id: int, method_id: int, db: Session = Depends(get_db)):
    ok = payment_method_dao.delete(db, method_id=method_id, user_id=user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Payment method not found")
    return {"message": "Payment method deleted", "success": True}


@router.post("/{user_id}/{method_id}/set-default")
def set_default_method(user_id: int, method_id: int, db: Session = Depends(get_db)):
    method = payment_method_dao.set_default(db, method_id=method_id, user_id=user_id)
    if method is None:
        raise HTTPException(status_code=404, detail="Payment method not found")
    return _serialize(method)
