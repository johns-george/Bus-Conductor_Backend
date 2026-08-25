"""
QR Token utility for Bus Conductor ticketing.

Token format: bc.ticket.<ticket_id>.<expiry_compact>.<signature>

The signature is an HMAC-SHA256 of "ticket_id:expiry" using a secret key.
This prevents forgery — only the server can generate valid tokens.

Uses '.' as separator instead of ':' to avoid conflicts with ISO time colons.
"""

import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone


# Secret key for HMAC signing — in production, load from env/secret manager
_QR_SECRET = os.getenv("QR_SECRET", "bus-conductor-qr-secret-key-change-in-prod")


def generate_qr_token(
    ticket_id: int,
    issued_at: datetime | None = None,
    valid_hours: int = 4,
) -> str:
    """
    Generate a signed QR token for a ticket.

    Token format: bc.ticket.<ticket_id>.<expiry_compact>.<signature>
    Example: bc.ticket.42.20260823T142422Z.a1b2c3d4e5f6g7h8

    Args:
        ticket_id: The database ticket ID
        issued_at: When the token is issued (defaults to now)
        valid_hours: How many hours the token is valid (default 24)

    Returns:
        Signed QR token string
    """
    if issued_at is None:
        issued_at = datetime.now(timezone.utc)

    expiry = issued_at + timedelta(hours=valid_hours)
    # Compact format: 20260823T142422Z (no colons)
    expiry_compact = expiry.strftime("%Y%m%dT%H%M%SZ")

    # Create the payload to sign
    payload = f"{ticket_id}:{expiry_compact}"

    # Generate HMAC-SHA256 signature
    signature = hmac.new(
        key=_QR_SECRET.encode("utf-8"),
        msg=payload.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()[:16]  # First 16 chars (64 bits) — enough for security

    return f"bc.ticket.{ticket_id}.{expiry_compact}.{signature}"


def validate_qr_token(token: str) -> dict:
    """
    Validate a QR token and return its details.

    Returns:
        {
            "valid": True/False,
            "ticket_id": int or None,
            "expiry": datetime or None,
            "message": str,
            "expired": bool,
        }
    """
    try:
        parts = token.split(".")
        if len(parts) != 5:
            return {"valid": False, "ticket_id": None, "expiry": None,
                    "message": "Invalid token format", "expired": False}

        prefix, kind, ticket_id_str, expiry_compact, signature = parts

        if prefix != "bc" or kind != "ticket":
            return {"valid": False, "ticket_id": None, "expiry": None,
                    "message": "Invalid token type", "expired": False}

        ticket_id = int(ticket_id_str)

        # Verify signature
        payload = f"{ticket_id_str}:{expiry_compact}"
        expected_sig = hmac.new(
            key=_QR_SECRET.encode("utf-8"),
            msg=payload.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).hexdigest()[:16]

        if not hmac.compare_digest(signature, expected_sig):
            return {"valid": False, "ticket_id": None, "expiry": None,
                    "message": "Invalid signature — token may be forged",
                    "expired": False}

        # Check expiry — compact format: 20260823T142422Z
        expiry = datetime.strptime(expiry_compact, "%Y%m%dT%H%M%SZ")
        expiry = expiry.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)

        if now > expiry:
            return {"valid": False, "ticket_id": ticket_id, "expiry": expiry,
                    "message": "Ticket expired", "expired": True}

        return {"valid": True, "ticket_id": ticket_id, "expiry": expiry,
                "message": "Ticket is valid", "expired": False}

    except (ValueError, IndexError) as e:
        return {"valid": False, "ticket_id": None, "expiry": None,
                "message": f"Malformed token: {e}", "expired": False}
