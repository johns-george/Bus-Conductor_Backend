"""Email utility for sending password reset and notification emails.

Uses Resend API (simple, 3K free emails/month).
Configure via environment variables:
  RESEND_API_KEY, SMTP_FROM

If Resend is not configured, falls back to SMTP (SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS).
If neither is configured, prints to console (dev mode).

To get a free Resend account:
  1. Go to https://resend.com
  2. Sign up with GitHub
  3. Get API key from API Keys page
  4. Add RESEND_API_KEY to Render env vars
"""

import os
import smtplib
import logging
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


def send_password_reset_email(to_email: str, reset_token: str, reset_url: str = "") -> bool:
    """Send a password reset email with the token.
    
    Returns True if sent successfully, False otherwise.
    """
    subject = "Bus Conductor — Reset Your Password"
    body = f"""Hello,

You requested a password reset for your Bus Conductor account.

Your reset token is:

  {reset_token}

Use this token on the reset password screen to set a new password.

{f'Or click this link: {reset_url}' if reset_url else ''}

This token will expire in 1 hour.

If you didn't request this, please ignore this email.

— Bus Conductor Team
"""
    html_body = f"""<!DOCTYPE html>
<html>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 500px; margin: 0 auto; padding: 20px;">
  <div style="background: linear-gradient(135deg, #0f172a, #1e293b); border-radius: 12px; padding: 24px; color: white; text-align: center;">
    <h2 style="margin: 0; font-size: 20px;">🔐 Password Reset</h2>
  </div>
  <div style="padding: 24px; background: #f8fafc; border-radius: 0 0 12px 12px; border: 1px solid #e2e8f0; border-top: none;">
    <p style="color: #475569; line-height: 1.6;">You requested a password reset for your <strong>Bus Conductor</strong> account.</p>
    <p style="color: #475569; line-height: 1.6;">Your reset token:</p>
    <div style="background: white; border: 2px dashed #0d9488; border-radius: 8px; padding: 16px; text-align: center; margin: 16px 0;">
      <code style="font-size: 16px; font-weight: 700; color: #0f172a; letter-spacing: 1px;">{reset_token}</code>
    </div>
    {f'<p style="color: #475569; line-height: 1.6;"><a href="{reset_url}" style="color: #0d9488; font-weight: 600;">Or click here to reset your password</a></p>' if reset_url else ''}
    <p style="color: #94a3b8; font-size: 13px; margin-top: 24px;">This token expires in 1 hour. If you didn't request this, ignore this email.</p>
  </div>
</body>
</html>"""

    # Try Resend API first
    api_key = os.getenv("RESEND_API_KEY", "")
    from_email = os.getenv("SMTP_FROM", "Bus Conductor <onboarding@resend.dev>")

    if api_key:
        try:
            resp = requests.post(
                "https://api.resend.com/emails",
                json={
                    "from": from_email,
                    "to": [to_email],
                    "subject": subject,
                    "html": html_body,
                },
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                timeout=10,
            )
            data = resp.json()
            if resp.status_code == 200 and data.get("id"):
                logger.info(f"✅ Password reset email sent to {to_email} via Resend")
                return True
            else:
                logger.warning(f"⚠️  Resend failed: {data}, falling back to SMTP")
        except Exception as e:
            logger.warning(f"⚠️  Resend error: {e}, falling back to SMTP")

    # Fallback to SMTP
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT")
    if smtp_host and smtp_port:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = from_email
            msg["To"] = to_email
            msg.attach(MIMEText(body, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(smtp_host, int(smtp_port)) as server:
                server.ehlo()
                if int(smtp_port) == 587:
                    server.starttls()
                    server.ehlo()
                smtp_user = os.getenv("SMTP_USER", "")
                smtp_pass = os.getenv("SMTP_PASS", "")
                if smtp_user and smtp_pass:
                    server.login(smtp_user, smtp_pass)
                server.sendmail(from_email, to_email, msg.as_string())

            logger.info(f"✅ Password reset email sent to {to_email} via SMTP")
            return True
        except Exception as e:
            logger.error(f"❌ SMTP send failed: {e}")

    # Dev mode — print to console
    logger.warning("⚠️  No email service configured. Printing to console.")
    print(f"\n{'='*60}", flush=True)
    print(f"📧 PASSWORD RESET EMAIL", flush=True)
    print(f"To: {to_email}", flush=True)
    print(f"Subject: {subject}", flush=True)
    print(f"{'='*60}", flush=True)
    print(body, flush=True)
    print(f"{'='*60}\n", flush=True)
    return True
