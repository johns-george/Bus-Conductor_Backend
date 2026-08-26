"""Legacy booking route — DEPRECATED.

Use /tickets/* endpoints instead. This router returns 410 Gone for all requests.
"""

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("")
@router.get("/{booking_id}")
@router.get("/user/{user_id}")
@router.patch("/{booking_id}/cancel")
@router.patch("/{booking_id}/validate")
async def deprecated_booking():
    raise HTTPException(
        status_code=410,
        detail="This endpoint is deprecated. Use /tickets/* endpoints instead.",
    )
