from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError
from routes import router
from db import engine
import os

app = FastAPI()

app.include_router(router)

ENV = os.getenv("ENV", "development")

# Configure allowed origins
if ENV == "development":
    allowed_origins = [
        "http://localhost:5173",  # Vite dev
        "http://localhost:3000",  # Docker dev frontend
    ]
else:
    allowed_origins = [
        "https://parliametrics.bg",  # Replace with your real prod domain
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Test DB connection

@app.on_event("startup")
def test_db_connection():
    try:
        with engine.connect() as conn:
            print("✅ Connected to database.")
    except OperationalError as e:
        print("❌ Database connection failed:", e)