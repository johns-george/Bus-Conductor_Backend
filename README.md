# BusMate Backend (Bus-Conductor API)

FastAPI backend for **BusMate**, a smart transit ticketing system: passengers search routes, book and pay for tickets, and show a QR code; conductors scan to validate; operators get settlement data.

- **Live app:** https://bus-conductor.netlify.app/
- **Frontend repo (Flutter):** https://github.com/johns-george/Bus-Conductor_Frontend

## Highlights

- **62 REST endpoints across 15 route modules:** auth, user, search, routes catalog, stops, buses, booking, ticket, QR, payment, payment methods, wallet, transactions, conductor and admin.
- **QR ticket validation** for conductors, with ticket state tracked server-side.
- **Payments and wallet:** payment methods, wallet balance and transaction history.
- **Auth:** email/password with bcrypt, JWT access + refresh tokens, Google sign-in, OTP and password-reset by email.
- **Operational middleware:** rate limiting, request logging and centralised error handling.
- **Route search** over a graph of stops and edges.

## Tech stack

Python 3.13 · FastAPI · SQLAlchemy 2 · Alembic · PostgreSQL · Pydantic · python-jose (JWT) · bcrypt · Google OAuth · Docker / docker-compose · Render

## Structure

```
src/
├── api/routes/     15 routers (auth, booking, ticket, qr, payment, wallet, ...)
├── services/       auth, search, stop, ticket business logic
├── dao/            data-access layer (payment methods, search, transactions, wallet)
├── models/         SQLAlchemy models (user, bus, route, stop, ticket, wallet, ...)
├── schemas/        Pydantic request/response models
├── middleware/     rate_limit, logging, error_handler
├── utility/        JWT/hash/OTP/QR/email/Google-auth helpers
└── main.py         app wiring and router registration
```

## Run locally

With Docker (API + PostgreSQL):

```bash
docker compose up --build
```

API: http://localhost:8000 · interactive docs: http://localhost:8000/docs

Without Docker:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # fill in DATABASE_URL and the JWT secrets
uvicorn src.main:app --reload
```

## Configuration

See [`.env.example`](.env.example). Key variables: `DATABASE_URL`, `SECRET_KEY`, `JWT_SECRET_KEY`, `JWT_REFRESH_SECRET_KEY`, `ALLOWED_ORIGINS`, and optionally `GOOGLE_CLIENT_ID` and the SMTP settings for email.

## Deployment

`render.yaml` and `Procfile` describe the Render web service (`uvicorn src.main:app`); the database is a hosted PostgreSQL instance (Neon).

## Author

Johns George (backend) · [LinkedIn](https://www.linkedin.com/in/johns-george-3568b8233/) · [GitHub](https://github.com/johns-george)
