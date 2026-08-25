from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from src.api.routes import auth
from src.api.routes import booking
from src.api.routes import bus
from src.api.routes import routes_catalog
from src.api.routes import stop
from src.api.routes import search
from src.api.routes import ticket
from src.api.routes import transaction
from src.api.routes import payment
from src.api.routes import user
from src.api.routes import wallet
from src.api.routes import qr
from src.api.routes import payment_method
from src.api.routes import admin
from src.api.routes import conductor
from src.core.database import Base, engine

app = FastAPI()

# Debugging middleware to track requests
@app.middleware("http")
async def debug_requests(request, call_next):
    print(f"🔍 Incoming request: {request.method} {request.url}")
    print(f"🔍 Origin: {request.headers.get('origin')}")
    print(f"🔍 Headers: {dict(request.headers)}")
    response = await call_next(request)
    print(f"🔍 Response status: {response.status_code}")
    return response

# More permissive CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"message": "API running 🚀"}


@app.get("/test-db")
def test_db():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        return {
            "status": "connected",
            "result": [row[0] for row in result]
        }


# Including Routes
app.include_router(stop.router)
app.include_router(search.router)
app.include_router(auth.router)
app.include_router(routes_catalog.router)
app.include_router(bus.router)
app.include_router(booking.router)
app.include_router(ticket.router)
app.include_router(wallet.router)
app.include_router(transaction.router)
app.include_router(payment.router)
app.include_router(user.router)
app.include_router(qr.router)
app.include_router(payment_method.router)
app.include_router(admin.router)
app.include_router(conductor.router)
