"""app/blueprints/profile/__init__.py"""
from flask import Blueprint

profile_bp = Blueprint("profile", __name__, template_folder="../../templates/profile")

from app.blueprints.profile import routes  # noqa: E402, F401
