"""
extensions.py — All Flask extensions initialised here (import-safe).
Call init_app(app) on each in the application factory.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache

# --- ORM ---
db = SQLAlchemy()

# --- Migrations ---
migrate = Migrate()

# --- Auth ---
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "warning"
login_manager.session_protection = "strong"

# --- Password Hashing ---
bcrypt = Bcrypt()

# --- CSRF ---
csrf = CSRFProtect()

# --- Rate Limiting ---
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per hour", "50 per minute"],
    storage_uri="memory://",
)

# --- Caching ---
cache = Cache()
