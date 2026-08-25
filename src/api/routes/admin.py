from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from src.core.database import get_db
from src.models.user import User
from src.models.ticket import Ticket
from src.models.wallet import Wallet
from src.models.bus_route import BusRoute
from src.models.bus import Bus
from src.models.route import Route
from src.dao.transaction_dao import get_transactions_by_user

router = APIRouter(prefix="/admin", tags=["admin"])


class SetRoleRequest(BaseModel):
    role: str  # USER, CONDUCTOR, ADMIN


class CreateConductorRequest(BaseModel):
    username: str
    email: str
    password: str
    full_name: str


@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get overall stats for admin dashboard."""
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_conductors = db.query(func.count(User.id)).filter(User.role == "CONDUCTOR").scalar() or 0
    total_admins = db.query(func.count(User.id)).filter(User.role == "ADMIN").scalar() or 0
    total_tickets = db.query(func.count(Ticket.id)).scalar() or 0
    active_tickets = db.query(func.count(Ticket.id)).filter(Ticket.status.in_(["ACTIVE", "PENDING_VALIDATION", "CONFIRMED"])).scalar() or 0
    validated_tickets = db.query(func.count(Ticket.id)).filter(Ticket.status == "VALIDATED").scalar() or 0
    expired_tickets = db.query(func.count(Ticket.id)).filter(Ticket.status == "EXPIRED").scalar() or 0
    cancelled_tickets = db.query(func.count(Ticket.id)).filter(Ticket.status == "CANCELLED").scalar() or 0
    total_revenue = db.query(func.sum(Ticket.price)).filter(Ticket.status.in_(["VALIDATED", "ACTIVE", "CONFIRMED"])).scalar() or 0
    total_wallet_balance = db.query(func.sum(Wallet.balance)).scalar() or 0
    total_bus_routes = db.query(func.count(BusRoute.id)).scalar() or 0
    total_buses = db.query(func.count(Bus.id)).scalar() or 0
    total_routes = db.query(func.count(Route.id)).scalar() or 0

    return {
        "users": {"total": total_users, "conductors": total_conductors, "admins": total_admins},
        "tickets": {"total": total_tickets, "active": active_tickets, "validated": validated_tickets, "expired": expired_tickets, "cancelled": cancelled_tickets},
        "revenue": float(total_revenue),
        "wallet_balance": float(total_wallet_balance),
        "fleet": {"buses": total_buses, "routes": total_routes, "schedules": total_bus_routes},
    }


@router.get("/users")
def list_users(db: Session = Depends(get_db)):
    """List all users."""
    users = db.query(User).order_by(User.id.desc()).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "full_name": u.full_name,
            "mobile_number": u.mobile_number,
            "role": u.role,
        }
        for u in users
    ]


@router.put("/users/{user_id}/role")
def set_user_role(user_id: int, payload: SetRoleRequest, db: Session = Depends(get_db)):
    """Set a user's role."""
    if payload.role not in ("USER", "CONDUCTOR", "ADMIN"):
        raise HTTPException(status_code=400, detail="Invalid role")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = payload.role
    db.commit()
    return {"message": f"Role set to {payload.role}", "user_id": user_id, "role": payload.role}


@router.post("/conductors")
def create_conductor(payload: CreateConductorRequest, db: Session = Depends(get_db)):
    """Create a new conductor account."""
    from src.utility.hash_utility import hash_password
    existing = db.query(User).filter(
        (User.username == payload.username) | (User.email == payload.email)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already exists")
    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        role="CONDUCTOR",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "Conductor created", "user_id": user.id, "role": user.role}


@router.get("/routes")
def list_all_routes(db: Session = Depends(get_db)):
    """List all routes with bus counts."""
    routes = db.query(Route).all()
    result = []
    for r in routes:
        bus_count = db.query(func.count(BusRoute.id)).filter(BusRoute.route_id == r.id).scalar() or 0
        result.append({
            "id": r.id,
            "name": r.name,
            "bus_count": bus_count,
        })
    return result


@router.get("/buses")
def list_all_buses(db: Session = Depends(get_db)):
    """List all buses."""
    buses = db.query(Bus).all()
    return [
        {
            "id": b.id,
            "name": b.name,
            "bus_number": b.bus_number,
            "bus_type": b.bus_type,
            "operator_name": b.operator_name,
            "capacity": b.capacity,
        }
        for b in buses
    ]


@router.get("/schedules")
def list_all_schedules(db: Session = Depends(get_db)):
    """List all bus schedules."""
    rows = db.query(BusRoute).all()
    result = []
    for br in rows:
        bus = db.query(Bus).filter(Bus.id == br.bus_id).first()
        route = db.query(Route).filter(Route.id == br.route_id).first()
        result.append({
            "id": br.id,
            "bus_id": br.bus_id,
            "bus_name": bus.name if bus else "Unknown",
            "bus_number": bus.bus_number if bus else "",
            "route_id": br.route_id,
            "route_name": route.name if route else "Unknown",
            "start_time": br.start_time.strftime("%H:%M:%S") if br.start_time else None,
            "platform": br.platform,
            "days_of_week": br.days_of_week,
        })
    return result


@router.get("/transactions")
def list_all_transactions(db: Session = Depends(get_db)):
    """List all recent transactions."""
    from src.models.transaction import Transaction
    txns = db.query(Transaction).order_by(Transaction.created_at.desc()).limit(100).all()
    return [
        {
            "id": t.id,
            "user_id": t.user_id,
            "amount": t.amount,
            "type": t.type,
            "status": t.status,
            "payment_method": t.payment_method,
            "note": t.note,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in txns
    ]
