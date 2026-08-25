from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from src.services import app_state

router = APIRouter(prefix="/bookings", tags=["bookings"])


class CreateBookingRequest(BaseModel):
    user_id: int
    route_id: int
    from_stop_id: int
    to_stop_id: int
    seat_labels: list[str] = []
    fare: float | None = None
    passenger_name: str | None = None
    passenger_phone: str | None = None


@router.post("")
def create_booking(payload: CreateBookingRequest):
    booking = app_state.create_booking(payload.model_dump())
    app_state.seed_notification(
        payload.user_id,
        title="Booking created",
        body=f"Booking {booking['id']} is awaiting validation",
        kind="booking",
    )
    booking["message"] = "Booking created"
    return booking


@router.get("/{booking_id}")
def booking_by_id(booking_id: str):
    booking = app_state.bookings_by_id.get(booking_id)
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


@router.get("/user/{user_id}")
def bookings_by_user(user_id: int):
    items = [
        value for value in app_state.bookings_by_id.values()
        if value["user_id"] == user_id
    ]
    items.sort(key=lambda b: b["booked_at"], reverse=True)
    return {"user_id": user_id, "items": items, "message": "Bookings list"}


@router.patch("/{booking_id}/cancel")
def cancel_booking(booking_id: str):
    booking = app_state.bookings_by_id.get(booking_id)
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    booking["status"] = "CANCELLED"
    app_state.seed_notification(
        booking["user_id"],
        title="Booking cancelled",
        body=f"Booking {booking_id} was cancelled",
        kind="booking",
    )
    return {**booking, "message": "Booking cancelled"}


@router.patch("/{booking_id}/validate")
def validate_booking(booking_id: str):
    booking = app_state.bookings_by_id.get(booking_id)
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    booking["status"] = "CONFIRMED"
    app_state.seed_notification(
        booking["user_id"],
        title="Booking validated",
        body=f"Booking {booking_id} is confirmed",
        kind="booking",
    )
    return {**booking, "message": "Booking validated"}
