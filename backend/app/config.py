import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-change-me")
    BASE_URL: str = os.getenv("BASE_URL", "http://localhost:8000")

    GITHUB_CLIENT_ID: str = os.getenv("GITHUB_CLIENT_ID", "")
    GITHUB_CLIENT_SECRET: str = os.getenv("GITHUB_CLIENT_SECRET", "")

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./prepgrid.db")


settings = Settings()