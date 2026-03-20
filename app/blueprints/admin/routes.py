"""
app/blueprints/admin/routes.py — Full admin panel: challenge CRUD, user management, audit logs.
Protected by @admin_required decorator.
"""
import os
from flask import (
    render_template, redirect, url_for, flash, request, abort, jsonify
)
from flask_login import login_required, current_user

from app.blueprints.admin import admin_bp
from app.extensions import db
from app.models.user import User
from app.models.challenge import Challenge, Hint
from app.models.submission import Submission
from app.models.audit_log import AuditLog
from app.forms.admin_forms import ChallengeForm
from app.utils.decorators import admin_required
from app.utils.file_utils import save_challenge_file, delete_challenge_file
from app.utils.flag_crypto import hash_flag
from app.utils.markdown import slugify


# ------------------------------------------------------------------ #
# Dashboard                                                            #
# ------------------------------------------------------------------ #

@admin_bp.route("/")
@login_required
@admin_required
def dashboard():
    stats = {
        "total_users": User.query.count(),
        "total_challenges": Challenge.query.count(),
        "total_submissions": Submission.query.count(),
        "correct_submissions": Submission.query.filter_by(is_correct=True).count(),
    }
    recent_logs = (
        AuditLog.query
        .order_by(AuditLog.created_at.desc())
        .limit(20)
        .all()
    )
    return render_template("admin/dashboard.html", stats=stats, recent_logs=recent_logs)


# ------------------------------------------------------------------ #
# Challenges CRUD                                                      #
# ------------------------------------------------------------------ #

@admin_bp.route("/challenges")
@login_required
@admin_required
def challenges_list():
    challenges = Challenge.query.order_by(Challenge.created_at.desc()).all()
    return render_template("admin/challenges.html", challenges=challenges)


@admin_bp.route("/challenges/new", methods=["GET", "POST"])
@login_required
@admin_required
def challenge_new():
    form = ChallengeForm()
    if form.validate_on_submit():
        slug = slugify(form.title.data)
        # Ensure slug uniqueness
        base_slug, counter = slug, 1
        while Challenge.query.filter_by(slug=slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1

        ch = Challenge(
            title=form.title.data.strip(),
            slug=slug,
            description=form.description.data,
            category=form.category.data,
            difficulty=form.difficulty.data,
            points=form.points.data,
            flag_hash=hash_flag(form.flag.data.strip()),
            active=form.active.data,
            author_id=current_user.id,
        )

        # Handle file upload
        if form.challenge_file.data and form.challenge_file.data.filename:
            try:
                rel_path, orig_name = save_challenge_file(form.challenge_file.data)
                ch.file_path = rel_path
                ch.file_name = orig_name
            except ValueError as e:
                flash(str(e), "danger")
                return render_template("admin/challenge_form.html", form=form, title="New Challenge")

        db.session.add(ch)
        db.session.flush()

        # Optional hint
        if form.hint_text.data and form.hint_text.data.strip():
            hint = Hint(
                challenge_id=ch.id,
                text=form.hint_text.data.strip(),
                penalty_points=form.hint_penalty.data or 25,
            )
            db.session.add(hint)

        AuditLog.log(
            action="challenge_create",
            user_id=current_user.id,
            target_id=ch.id,
            target_type="challenge",
            ip_address=request.remote_addr,
            details={"title": ch.title},
        )
        db.session.commit()
        flash(f"Challenge '{ch.title}' created!", "success")
        return redirect(url_for("admin.challenges_list"))

    return render_template("admin/challenge_form.html", form=form, title="New Challenge")


@admin_bp.route("/challenges/<int:challenge_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def challenge_edit(challenge_id: int):
    ch = Challenge.query.get_or_404(challenge_id)
    form = ChallengeForm(obj=ch)

    if form.validate_on_submit():
        ch.title = form.title.data.strip()
        ch.description = form.description.data
        ch.category = form.category.data
        ch.difficulty = form.difficulty.data
        ch.points = form.points.data
        ch.active = form.active.data

        # Only rehash if a new flag provided (non-empty field)
        if form.flag.data and form.flag.data.strip():
            ch.flag_hash = hash_flag(form.flag.data.strip())

        # File replacement
        if form.challenge_file.data and form.challenge_file.data.filename:
            try:
                # Delete old file
                if ch.file_path:
                    delete_challenge_file(ch.file_path)
                rel_path, orig_name = save_challenge_file(form.challenge_file.data)
                ch.file_path = rel_path
                ch.file_name = orig_name
            except ValueError as e:
                flash(str(e), "danger")
                return render_template("admin/challenge_form.html", form=form, challenge=ch, title="Edit")

        # Update hint
        existing_hint = ch.hints.first()
        if form.hint_text.data and form.hint_text.data.strip():
            if existing_hint:
                existing_hint.text = form.hint_text.data.strip()
                existing_hint.penalty_points = form.hint_penalty.data or 25
            else:
                hint = Hint(
                    challenge_id=ch.id,
                    text=form.hint_text.data.strip(),
                    penalty_points=form.hint_penalty.data or 25,
                )
                db.session.add(hint)

        AuditLog.log(
            action="challenge_edit",
            user_id=current_user.id,
            target_id=ch.id,
            target_type="challenge",
            ip_address=request.remote_addr,
        )
        db.session.commit()
        flash(f"Challenge '{ch.title}' updated!", "success")
        return redirect(url_for("admin.challenges_list"))

    # Pre-fill flag field hint (never show hash)
    form.flag.data = ""
    # Pre-fill hint
    existing_hint = ch.hints.first()
    if existing_hint:
        form.hint_text.data = existing_hint.text
        form.hint_penalty.data = existing_hint.penalty_points

    return render_template("admin/challenge_form.html", form=form, challenge=ch, title="Edit Challenge")


@admin_bp.route("/challenges/<int:challenge_id>/delete", methods=["POST"])
@login_required
@admin_required
def challenge_delete(challenge_id: int):
    ch = Challenge.query.get_or_404(challenge_id)
    if ch.file_path:
        delete_challenge_file(ch.file_path)
    title = ch.title
    AuditLog.log(
        action="challenge_delete",
        user_id=current_user.id,
        target_id=ch.id,
        target_type="challenge",
        ip_address=request.remote_addr,
        details={"title": title},
    )
    db.session.delete(ch)
    db.session.commit()
    flash(f"Challenge '{title}' deleted.", "success")
    return redirect(url_for("admin.challenges_list"))


# ------------------------------------------------------------------ #
# Users                                                                #
# ------------------------------------------------------------------ #

@admin_bp.route("/users")
@login_required
@admin_required
def users_list():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=users)


@admin_bp.route("/users/<int:user_id>/promote", methods=["POST"])
@login_required
@admin_required
def promote_user(user_id: int):
    user = User.query.get_or_404(user_id)
    user.role = "admin"
    AuditLog.log(action="user_promote", user_id=current_user.id, target_id=user.id, target_type="user")
    db.session.commit()
    flash(f"{user.username} promoted to Admin.", "success")
    return redirect(url_for("admin.users_list"))


@admin_bp.route("/users/<int:user_id>/ban", methods=["POST"])
@login_required
@admin_required
def ban_user(user_id: int):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("Cannot ban yourself.", "danger")
        return redirect(url_for("admin.users_list"))
    user.banned = not user.banned
    action = "user_ban" if user.banned else "user_unban"
    AuditLog.log(action=action, user_id=current_user.id, target_id=user.id, target_type="user")
    db.session.commit()
    state = "banned" if user.banned else "unbanned"
    flash(f"{user.username} {state}.", "success")
    return redirect(url_for("admin.users_list"))


# ------------------------------------------------------------------ #
# Audit Logs                                                           #
# ------------------------------------------------------------------ #

@admin_bp.route("/logs")
@login_required
@admin_required
def audit_logs():
    page = request.args.get("page", 1, type=int)
    logs = (
        AuditLog.query
        .order_by(AuditLog.created_at.desc())
        .paginate(page=page, per_page=50, error_out=False)
    )
    return render_template("admin/logs.html", logs=logs)
