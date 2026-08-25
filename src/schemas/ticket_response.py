from pydantic import BaseModel
from datetime import datetime

class TicketResponse(BaseModel):
    id: int
    user_id: int
    trip_id: int
    source_stop_id: int
    destination_stop_id: int
    booking_time: datetime
    expires_at: datetime | None = None
    status: str
    time_of_travel: datetime
    price: float
    qr_token: str | None = None
    passenger_name: str | None = None
    passenger_phone: str | None = None
    passenger_count: int = 1
    validated_by: int | None = None
    validated_at: datetime | None = None

    class Config:
        orm_mode = True
