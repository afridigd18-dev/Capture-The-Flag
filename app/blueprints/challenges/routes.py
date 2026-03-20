"""
app/blueprints/challenges/routes.py — Challenge list, detail, flag submit, hint unlock.
Rate-limited flag submissions with SHA-256 verification and duplicate-solve prevention.
"""
from datetime import datetime, timezone
from flask import (
    render_template, redirect, url_for, flash, request, abort
)
from flask_login import login_required, current_user
from sqlalchemy import func

from app.blueprints.challenges import challenges_bp
from app.extensions import db, limiter
from app.models.challenge import Challenge, Hint, HintUnlock
from app.models.submission import Submission
from app.models.audit_log import AuditLog
from app.forms.challenge_forms import FlagSubmitForm, HintUnlockForm
from app.utils.flag_crypto import verify_flag, hash_flag


@challenges_bp.route("/")
@login_required
def list_challenges():
    """Show all active challenges grouped by category."""
    challenges = Challenge.query.filter_by(active=True).order_by(
        Challenge.category, Challenge.points
    ).all()

    # Build set of solved challenge IDs for the current user
    solved_ids = set()
    if current_user.is_authenticated:
        solved = (
            Submission.query
            .filter_by(user_id=current_user.id, is_correct=True)
            .with_entities(Submission.challenge_id)
            .all()
        )
        solved_ids = {row[0] for row in solved}

    # Group by category
    categories = {}
    for ch in challenges:
        categories.setdefault(ch.category, []).append(ch)

    return render_template(
        "challenges/list.html",
        categories=categories,
        solved_ids=solved_ids,
    )


@challenges_bp.route("/<slug>")
@login_required
def challenge_detail(slug: str):
    """Show a single challenge detail page."""
    challenge = Challenge.query.filter_by(slug=slug, active=True).first_or_404()

    # Check if user already solved this
    already_solved = Submission.query.filter_by(
        user_id=current_user.id,
        challenge_id=challenge.id,
        is_correct=True,
    ).first()

    # Unlocked hints for this user
    unlocked_hint_ids = set(
        row[0] for row in
        HintUnlock.query
        .filter_by(user_id=current_user.id)
        .join(Hint)
        .filter(Hint.challenge_id == challenge.id)
        .with_entities(HintUnlock.hint_id)
        .all()
    )

    form = FlagSubmitForm()
    hint_form = HintUnlockForm()

    return render_template(
        "challenges/detail.html",
        challenge=challenge,
        already_solved=already_solved,
        unlocked_hint_ids=unlocked_hint_ids,
        form=form,
        hint_form=hint_form,
    )


@challenges_bp.route("/<slug>/submit", methods=["POST"])
@login_required
@limiter.limit("5 per minute; 30 per hour")
def submit_flag(slug: str):
    """Validate a flag submission. Rate-limited to 5/min per user per challenge."""
    challenge = Challenge.query.filter_by(slug=slug, active=True).first_or_404()

    # Prevent duplicate correct solve
    existing_solve = Submission.query.filter_by(
        user_id=current_user.id,
        challenge_id=challenge.id,
        is_correct=True,
    ).first()
    if existing_solve:
        flash("You have already solved this challenge!", "info")
        return redirect(url_for("challenges.challenge_detail", slug=slug))

    form = FlagSubmitForm()
    if not form.validate_on_submit():
        flash("Invalid form submission.", "danger")
        return redirect(url_for("challenges.challenge_detail", slug=slug))

    submitted = form.flag.data.strip()
    is_correct = verify_flag(submitted, challenge.flag_hash)
    submitted_hash = hash_flag(submitted)

    # Log the submission
    sub = Submission(
        user_id=current_user.id,
        challenge_id=challenge.id,
        submitted_flag_hash=submitted_hash,
        is_correct=is_correct,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string[:512],
        points_earned=challenge.points if is_correct else 0,
    )
    db.session.add(sub)

    if is_correct:
        current_user.add_score(challenge.points)
        challenge.solve_count += 1
        AuditLog.log(
            action="flag_submit_correct",
            user_id=current_user.id,
            target_id=challenge.id,
            target_type="challenge",
            ip_address=request.remote_addr,
            details={"challenge": challenge.title, "points": challenge.points},
        )
        db.session.commit()
        flash(
            f"🎉 Correct! You earned {challenge.points} points!",
            "success",
        )
    else:
        AuditLog.log(
            action="flag_submit_wrong",
            user_id=current_user.id,
            target_id=challenge.id,
            target_type="challenge",
            ip_address=request.remote_addr,
        )
        db.session.commit()
        flash("❌ Wrong flag. Keep trying!", "danger")

    return redirect(url_for("challenges.challenge_detail", slug=slug))


@challenges_bp.route("/<slug>/hint/<int:hint_id>", methods=["POST"])
@login_required
@limiter.limit("10 per hour")
def unlock_hint(slug: str, hint_id: int):
    """Unlock a hint, applying score penalty once per user per hint."""
    challenge = Challenge.query.filter_by(slug=slug, active=True).first_or_404()
    hint = Hint.query.filter_by(id=hint_id, challenge_id=challenge.id).first_or_404()

    # Already unlocked?
    existing = HintUnlock.query.filter_by(
        user_id=current_user.id, hint_id=hint.id
    ).first()
    if existing:
        flash("Hint already unlocked.", "info")
        return redirect(url_for("challenges.challenge_detail", slug=slug))

    # Deduct points (floor at 0)
    penalty = min(hint.penalty_points, current_user.score)
    current_user.score = max(0, current_user.score - penalty)

    unlock = HintUnlock(user_id=current_user.id, hint_id=hint.id)
    db.session.add(unlock)
    AuditLog.log(
        action="hint_unlock",
        user_id=current_user.id,
        target_id=hint.id,
        target_type="hint",
        ip_address=request.remote_addr,
        details={"penalty": penalty},
    )
    db.session.commit()
    flash(f"Hint unlocked! -{penalty} points.", "warning")
    return redirect(url_for("challenges.challenge_detail", slug=slug))
