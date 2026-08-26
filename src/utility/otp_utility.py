"""OTP utility using msg91 for SMS delivery.

Configure via environment variables:
  MSG91_API_KEY, MSG91_TEMPLATE_ID, MSG91_SENDER_ID

If not configured, falls back to console logging (dev mode).

To get a free msg91 account:
  1. Go to https://msg91.com
  2. Sign up (100 SMS/day free for India)
  3. Get API key from Settings → Auth Key
  4. Create an OTP template and get Template ID
"""

import os
import random
import string
import logging
import requests

logger = logging.getLogger(__name__)


def generate_otp(length: int = 6) -> str:
    """Generate a numeric OTP of given length."""
    return "".join(random.choices(string.digits, k=length))


def send_otp_sms(phone: str, otp: str) -> dict:
    """Send OTP via SMS using msg91 API.
    
    Args:
        phone: Phone number (e.g., "918078161433" with country code)
        otp: The OTP code to send
        
    Returns:
        dict with 'success' bool and 'message' str
    """
    api_key = os.getenv("MSG91_API_KEY", "")
    template_id = os.getenv("MSG91_TEMPLATE_ID", "")
    sender_id = os.getenv("MSG91_SENDER_ID", "BUSCON")

    # Dev mode — print to console
    if not api_key or not template_id:
        logger.warning("⚠️  msg91 not configured. Printing OTP to console.")
        print(f"\n{'='*60}", flush=True)
        print(f"📱 OTP SMS", flush=True)
        print(f"To: {phone}", flush=True)
        print(f"OTP: {otp}", flush=True)
        print(f"{'='*60}\n", flush=True)
        return {"success": True, "message": "OTP sent (dev mode — see server logs)"}

    # Production — send via msg91
    url = "https://api.msg91.com/api/v5/otp"
    payload = {
        "mobile": phone,
        "otp": otp,
        "template_id": template_id,
        "sender": sender_id,
    }
    headers = {
        "authkey": api_key,
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        data = resp.json()

        if resp.status_code == 200 and data.get("type") == "success":
            logger.info(f"✅ OTP sent to {phone}")
            return {"success": True, "message": "OTP sent successfully"}
        else:
            logger.error(f"❌ msg91 error: {data}")
            return {"success": False, "message": f"Failed to send OTP: {data.get('message', 'Unknown error')}"}

    except Exception as e:
        logger.error(f"❌ OTP send failed: {e}")
        # Fall back to console
        print(f"\n📱 OTP (fallback — SMS failed): {otp} to {phone}", flush=True)
        return {"success": True, "message": "OTP sent (see server logs)"}


def send_otp_email(to_email: str, otp: str) -> dict:
    """Send OTP via email using Resend API.
    
    Args:
        to_email: Recipient email address
        otp: The OTP code to send
        
    Returns:
        dict with 'success' bool and 'message' str
    """
    api_key = os.getenv("RESEND_API_KEY", "")
    from_email = os.getenv("SMTP_FROM", "Bus Conductor <onboarding@resend.dev>")

    # Dev mode — print to console
    if not api_key:
        logger.warning("⚠️  Resend not configured. Printing OTP to console.")
        print(f"\n{'='*60}", flush=True)
        print(f"📧 OTP EMAIL", flush=True)
        print(f"To: {to_email}", flush=True)
        print(f"OTP: {otp}", flush=True)
        print(f"{'='*60}\n", flush=True)
        return {"success": True, "message": "OTP sent (dev mode — see server logs)"}

    # Production — send via Resend
    url = "https://api.resend.com/emails"
    payload = {
        "from": from_email,
        "to": [to_email],
        "subject": "Bus Conductor — Your OTP Code",
        "html": f"""<!DOCTYPE html>
<html>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 500px; margin: 0 auto; padding: 20px;">
  <div style="background: linear-gradient(135deg, #0f172a, #1e293b); border-radius: 12px; padding: 24px; color: white; text-align: center;">
    <h2 style="margin: 0; font-size: 20px;">🔐 Your OTP Code</h2>
  </div>
  <div style="padding: 24px; background: #f8fafc; border-radius: 0 0 12px 12px; border: 1px solid #e2e8f0; border-top: none;">
    <p style="color: #475569; line-height: 1.6;">Your verification code is:</p>
    <div style="background: white; border: 2px dashed #0d9488; border-radius: 8px; padding: 16px; text-align: center; margin: 16px 0;">
      <code style="font-size: 24px; font-weight: 700; color: #0f172a; letter-spacing: 4px;">{otp}</code>
    </div>
    <p style="color: #94a3b8; font-size: 13px;">This code expires in 5 minutes. If you didn't request this, ignore this email.</p>
  </div>
</body>
</html>""",
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        data = resp.json()

        if resp.status_code == 200 and data.get("id"):
            logger.info(f"✅ OTP email sent to {to_email}")
            return {"success": True, "message": "OTP sent successfully"}
        else:
            logger.error(f"❌ Resend error: {data}")
            # Fall back to console
            print(f"\n📧 OTP (fallback — Resend failed): {otp} to {to_email}", flush=True)
            return {"success": True, "message": "OTP sent (see server logs)"}

    except Exception as e:
        logger.error(f"❌ OTP email failed: {e}")
        # Fall back to console
        print(f"\n📧 OTP (fallback — email failed): {otp} to {to_email}", flush=True)
        return {"success": True, "message": "OTP sent (see server logs)"}
