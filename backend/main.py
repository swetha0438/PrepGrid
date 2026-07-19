from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers import auth

# Create all tables (User, etc.) in the SQLite DB if they don't exist yet
Base.metadata.create_all(bind=engine)

app = FastAPI(title="PrepGrid")

# Enables `request.session` used in auth.py - signs the session cookie
# with SECRET_KEY so it can't be tampered with client-side
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

app.include_router(auth.router)


@app.get("/")
async def root():
    return {"message": "PrepGrid backend is running"}


@app.get("/dashboard")
async def dashboard():
    # Placeholder - replace with real dashboard once login is confirmed working
    return {"message": "You're logged in! Dashboard coming soon."}