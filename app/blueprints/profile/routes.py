"""
app/blueprints/profile/routes.py — User profile page.
Shows score, solved challenges, and submission history.
"""
from flask import render_template, abort
from flask_login import login_required, current_user

from app.blueprints.profile import profile_bp
from app.models.user import User
from app.models.submission import Submission
from app.models.challenge import Challenge


@profile_bp.route("/")
@login_required
def my_profile():
    return redirect_to_profile(current_user.username)


@profile_bp.route("/<username>")
@login_required
def view_profile(username: str):
    return redirect_to_profile(username)


def redirect_to_profile(username: str):
    from flask import redirect, url_for
    user = User.query.filter_by(username=username).first_or_404()

    # Solved challenges (correct submissions)
    solved_subs = (
        Submission.query
        .filter_by(user_id=user.id, is_correct=True)
        .order_by(Submission.created_at.desc())
        .all()
    )
    challenge_ids = [s.challenge_id for s in solved_subs]
    solved_challenges = Challenge.query.filter(Challenge.id.in_(challenge_ids)).all()
    solved_map = {c.id: c for c in solved_challenges}

    # All recent submissions (last 50)
    recent_subs = (
        Submission.query
        .filter_by(user_id=user.id)
        .order_by(Submission.created_at.desc())
        .limit(50)
        .all()
    )

    # Category breakdown
    category_stats = {}
    for sub in solved_subs:
        ch = solved_map.get(sub.challenge_id)
        if ch:
            category_stats[ch.category] = category_stats.get(ch.category, 0) + 1

    return render_template(
        "profile/profile.html",
        profile_user=user,
        solved_subs=solved_subs,
        solved_map=solved_map,
        recent_subs=recent_subs,
        category_stats=category_stats,
    )
