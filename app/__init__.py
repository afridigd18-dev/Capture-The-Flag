"""
app/__init__.py — Application Factory.
Creates and configures the Flask application with all extensions and blueprints.
"""
import os
from flask import Flask, render_template
from config import config_map
from app.extensions import db, migrate, login_manager, bcrypt, csrf, limiter, cache


def create_app(env: str = "development") -> Flask:
    """Flask application factory.

    Args:
        env: One of 'development', 'production', 'testing'.
    Returns:
        Configured Flask application instance.
    """
    app = Flask(__name__, instance_relative_config=True)

    # ------------------------------------------------------------------ #
    # Configuration                                                        #
    # ------------------------------------------------------------------ #
    cfg = config_map.get(env, config_map["default"])
    app.config.from_object(cfg)

    # Ensure instance folder exists (for SQLite)
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config.get("UPLOAD_FOLDER", "uploads"), exist_ok=True)

    # ------------------------------------------------------------------ #
    # Extensions                                                           #
    # ------------------------------------------------------------------ #
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    cache.init_app(app, config={"CACHE_TYPE": "SimpleCache"})

    # ------------------------------------------------------------------ #
    # Flask-Login user loader                                              #
    # ------------------------------------------------------------------ #
    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id: str):
        return db.session.get(User, int(user_id))

    # ------------------------------------------------------------------ #
    # Blueprints                                                           #
    # ------------------------------------------------------------------ #
    from app.blueprints.auth import auth_bp
    from app.blueprints.challenges import challenges_bp
    from app.blueprints.scoreboard import scoreboard_bp
    from app.blueprints.admin import admin_bp
    from app.blueprints.profile import profile_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(challenges_bp, url_prefix="/challenges")
    app.register_blueprint(scoreboard_bp, url_prefix="/scoreboard")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(profile_bp, url_prefix="/profile")

    # ------------------------------------------------------------------ #
    # Root redirect                                                        #
    # ------------------------------------------------------------------ #
    from flask import redirect, url_for

    @app.route("/")
    def index():
        return redirect(url_for("challenges.list_challenges"))

    # ------------------------------------------------------------------ #
    # Security headers                                                     #
    # ------------------------------------------------------------------ #
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:;"
        )
        return response

    # ------------------------------------------------------------------ #
    # Error handlers                                                       #
    # ------------------------------------------------------------------ #
    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(429)
    def rate_limited(e):
        return render_template("errors/429.html"), 429

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    # ------------------------------------------------------------------ #
    # Jinja2 globals                                                       #
    # ------------------------------------------------------------------ #
    from app.utils.markdown import render_markdown

    app.jinja_env.globals["render_markdown"] = render_markdown

    return app
