import os
import sys
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # ── Database ──────────────────────────────────────────
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # ── Auth / JWT ────────────────────────────────────────
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    JWT_REFRESH_SECRET_KEY: str = str(
        os.getenv("JWT_REFRESH_SECRET_KEY") or os.getenv("JWT_SECRET_KEY", "")
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "5")
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(
        os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")
    )

    # ── CORS ──────────────────────────────────────────────
    ALLOWED_ORIGINS: list[str] = [
        o.strip()
        for o in os.getenv("ALLOWED_ORIGINS", "*").split(",")
        if o.strip()
    ]

    # ── Rate Limiting ─────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "120"))

    # ── Firebase (optional) ───────────────────────────────
    FIREBASE_PROJECT_ID: str = os.getenv("FIREBASE_PROJECT_ID", "")

    # ── OTP (msg91 for SMS, Resend for email) ────────────
    MSG91_API_KEY: str = os.getenv("MSG91_API_KEY", "")
    MSG91_TEMPLATE_ID: str = os.getenv("MSG91_TEMPLATE_ID", "")
    MSG91_SENDER_ID: str = os.getenv("MSG91_SENDER_ID", "BUSCON")
    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY", "")

    # ── Environment ───────────────────────────────────────
    ENV: str = os.getenv("ENV", "production")

    def validate(self):
        """Fail fast on missing critical config."""
        errors = []
        if not self.DATABASE_URL:
            errors.append("DATABASE_URL is not set")
        if not self.JWT_SECRET_KEY:
            errors.append("JWT_SECRET_KEY is not set")
        if errors:
            for e in errors:
                print(f"❌ FATAL: {e}", file=sys.stderr)
            sys.exit(1)


settings = Settings()
settings.validate()
