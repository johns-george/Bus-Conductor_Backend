from datetime import datetime, timedelta
from itertools import count


_booking_counter = count(1)
_transaction_counter = count(1)
_notification_counter = count(1)

bookings_by_id: dict[str, dict] = {}
wallets_by_user: dict[int, dict] = {}
transactions_by_id: dict[str, dict] = {}
notifications_by_user: dict[int, list[dict]] = {}


def create_booking(data: dict) -> dict:
    booking_id = f"bk_{next(_booking_counter)}"
    now = datetime.utcnow()
    booking = {
        "id": booking_id,
        "user_id": data["user_id"],
        "route_id": data["route_id"],
        "from_stop_id": data["from_stop_id"],
        "to_stop_id": data["to_stop_id"],
        "fare": data.get("fare") or 0,
        "seat_labels": data.get("seat_labels", []),
        "passenger_name": data.get("passenger_name"),
        "passenger_phone": data.get("passenger_phone"),
        "booked_at": now.isoformat(),
        "expires_at": (now + timedelta(hours=3)).isoformat(),
        "status": "PENDING_VALIDATION",
    }
    bookings_by_id[booking_id] = booking
    return booking


def wallet_for_user(user_id: int) -> dict:
    wallet = wallets_by_user.get(user_id)
    if wallet is None:
        wallet = {
            "user_id": user_id,
            "balance": 0.0,
            "passes": [],
            "last_updated": datetime.utcnow().isoformat(),
        }
        wallets_by_user[user_id] = wallet
    return wallet


def create_transaction(data: dict) -> dict:
    tx_id = f"tx_{next(_transaction_counter)}"
    tx = {
        "id": tx_id,
        "user_id": data["user_id"],
        "amount": data["amount"],
        "status": data.get("status", "SUCCESSFUL"),
        "method_type": data.get("method_type", "UPI"),
        "booking_id": data.get("booking_id"),
        "ticket_id": data.get("ticket_id"),
        "note": data.get("note"),
        "method_label": data.get("method_label"),
        "created_at": datetime.utcnow().isoformat(),
    }
    transactions_by_id[tx_id] = tx
    return tx


def seed_notification(user_id: int, title: str, body: str, kind: str = "generic") -> dict:
    entry = {
        "id": f"n_{next(_notification_counter)}",
        "title": title,
        "body": body,
        "kind": kind,
        "read": False,
        "created_at": datetime.utcnow().isoformat(),
    }
    notifications_by_user.setdefault(user_id, []).insert(0, entry)
    return entry
