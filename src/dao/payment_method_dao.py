from sqlalchemy.orm import Session
from src.models.payment_method import PaymentMethod


def get_all_by_user(db: Session, user_id: int) -> list[PaymentMethod]:
    return (
        db.query(PaymentMethod)
        .filter(PaymentMethod.user_id == user_id, PaymentMethod.is_active == True)
        .order_by(PaymentMethod.is_default.desc(), PaymentMethod.created_at.desc())
        .all()
    )


def get_by_id(db: Session, method_id: int) -> PaymentMethod | None:
    return db.query(PaymentMethod).filter(PaymentMethod.id == method_id).first()


def get_by_id_and_user(db: Session, method_id: int, user_id: int) -> PaymentMethod | None:
    return (
        db.query(PaymentMethod)
        .filter(PaymentMethod.id == method_id, PaymentMethod.user_id == user_id)
        .first()
    )


def create(
    db: Session,
    user_id: int,
    method_type: str,
    label: str,
    subtitle: str | None = None,
    provider: str | None = None,
    last_four: str | None = None,
    upi_id: str | None = None,
    is_default: bool = False,
) -> PaymentMethod:
    # If this is set as default, unset other defaults
    if is_default:
        _clear_defaults(db, user_id)

    method = PaymentMethod(
        user_id=user_id,
        method_type=method_type.upper(),
        label=label,
        subtitle=subtitle,
        provider=provider,
        last_four=last_four,
        upi_id=upi_id,
        is_default=is_default,
    )
    db.add(method)
    db.commit()
    db.refresh(method)
    return method


def update(
    db: Session,
    method_id: int,
    user_id: int,
    label: str | None = None,
    subtitle: str | None = None,
    is_default: bool | None = None,
) -> PaymentMethod | None:
    method = get_by_id_and_user(db, method_id, user_id)
    if method is None:
        return None

    if label is not None:
        method.label = label
    if subtitle is not None:
        method.subtitle = subtitle
    if is_default is not None:
        if is_default:
            _clear_defaults(db, user_id)
        method.is_default = is_default

    db.commit()
    db.refresh(method)
    return method


def delete(db: Session, method_id: int, user_id: int) -> bool:
    method = get_by_id_and_user(db, method_id, user_id)
    if method is None:
        return False
    method.is_active = False
    db.commit()
    return True


def set_default(db: Session, method_id: int, user_id: int) -> PaymentMethod | None:
    method = get_by_id_and_user(db, method_id, user_id)
    if method is None:
        return None
    _clear_defaults(db, user_id)
    method.is_default = True
    db.commit()
    db.refresh(method)
    return method


def _clear_defaults(db: Session, user_id: int) -> None:
    db.query(PaymentMethod).filter(
        PaymentMethod.user_id == user_id,
        PaymentMethod.is_default == True,
    ).update({"is_default": False})
