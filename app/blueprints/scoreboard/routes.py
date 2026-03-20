"""
app/blueprints/scoreboard/routes.py — Live leaderboard with AJAX JSON endpoint.
"""
from flask import render_template, jsonify
from flask_login import login_required

from app.blueprints.scoreboard import scoreboard_bp
from app.services.scoreboard_service import get_leaderboard
from app.extensions import cache


@scoreboard_bp.route("/")
@login_required
def leaderboard():
    board = get_leaderboard(limit=100)
    return render_template("scoreboard/leaderboard.html", board=board)


@scoreboard_bp.route("/api")
@login_required
@cache.cached(timeout=10, key_prefix="scoreboard_api")
def api_leaderboard():
    """JSON endpoint polled every 30s by scoreboard.js for live updates."""
    board = get_leaderboard(limit=100)
    return jsonify(board)
