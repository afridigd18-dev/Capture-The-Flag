"""
config.py — Application Configuration
Loads settings from .env file via python-dotenv.
Supports Development, Production, and Testing environments.
"""
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration shared across all environments."""

    # --- Core ---
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-change-in-prod"
    FLASK_ENV = os.environ.get("FLASK_ENV", "development")

    # --- Database ---
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or \
        f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'ctf.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Uploads ---
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "app", "static", "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size
    ALLOWED_EXTENSIONS = {"zip", "txt", "png", "jpg", "pdf", "bin", "tar", "gz"}

    # --- Security ---
    WTF_CSRF_ENABLED = os.environ.get("WTF_CSRF_ENABLED", "True").lower() == "true"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "False").lower() == "true"

    # --- Rate Limiting ---
    RATELIMIT_STORAGE_URL = os.environ.get("RATELIMIT_STORAGE_URL", "memory://")
    RATELIMIT_DEFAULT = "200 per day;50 per hour"

    # --- Admin Bootstrap ---
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@ctf.local")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Admin@CTF2024!")


class DevelopmentConfig(Config):
    """Development — debug mode, SQLite, relaxed security."""
    DEBUG = True
    SQLALCHEMY_ECHO = False  # Set True to log SQL queries


class ProductionConfig(Config):
    """Production — strict security, PostgreSQL, no debug."""
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    WTF_CSRF_ENABLED = True


class TestingConfig(Config):
    """Testing — in-memory SQLite, CSRF disabled."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
