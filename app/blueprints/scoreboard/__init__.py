"""app/blueprints/scoreboard/__init__.py"""
from flask import Blueprint

scoreboard_bp = Blueprint("scoreboard", __name__, template_folder="../../templates/scoreboard")

from app.blueprints.scoreboard import routes  # noqa: E402, F401
