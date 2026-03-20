"""app/blueprints/challenges/__init__.py"""
from flask import Blueprint

challenges_bp = Blueprint("challenges", __name__, template_folder="../../templates/challenges")

from app.blueprints.challenges import routes  # noqa: E402, F401
