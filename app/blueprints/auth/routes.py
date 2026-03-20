"""
app/blueprints/auth/routes.py — Registration, login, logout.
Rate-limited, CSRF-protected, bcrypt password verification.
"""
from datetime import datetime, timezone
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from app.blueprints.auth import auth_bp
from app.extensions import db, limiter
from app.models.user import User
from app.models.audit_log import AuditLog
from app.forms.auth_forms import RegistrationForm, LoginForm


@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per hour")
def register():
    if current_user.is_authenticated:
        return redirect(url_for("challenges.list_challenges"))

    form = RegistrationForm()
    if form.validate_on_submit():
        # Check uniqueness
        if User.query.filter_by(email=form.email.data.lower()).first():
            flash("Email address already registered.", "danger")
            return render_template("auth/register.html", form=form)
        if User.query.filter_by(username=form.username.data).first():
            flash("Username already taken.", "danger")
            return render_template("auth/register.html", form=form)

        user = User(
            username=form.username.data.strip(),
            email=form.email.data.strip().lower(),
        )
        user.set_password(form.password.data)

        # First ever user becomes admin
        if User.query.count() == 0:
            user.role = "admin"

        db.session.add(user)
        db.session.flush()  # get ID before commit

        AuditLog.log(
            action="user_register",
            user_id=user.id,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string[:512],
        )
        db.session.commit()

        flash("Account created! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("20 per 5 minutes")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("challenges.list_challenges"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()

        if user and user.banned:
            flash("Your account has been suspended.", "danger")
            return render_template("auth/login.html", form=form)

        if user and user.check_password(form.password.data):
            # Successful login
            user.failed_login_attempts = 0
            login_user(user, remember=form.remember.data)
            AuditLog.log(
                action="login_success",
                user_id=user.id,
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string[:512],
            )
            db.session.commit()
            next_page = request.args.get("next")
            flash(f"Welcome back, {user.username}! 👾", "success")
            return redirect(next_page or url_for("challenges.list_challenges"))
        else:
            # Failed login
            if user:
                user.failed_login_attempts += 1
                user.last_failed_login = datetime.now(timezone.utc)
            AuditLog.log(
                action="login_fail",
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string[:512],
                details={"email": form.email.data},
            )
            db.session.commit()
            flash("Invalid email or password.", "danger")

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    AuditLog.log(action="logout", user_id=current_user.id, ip_address=request.remote_addr)
    db.session.commit()
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
