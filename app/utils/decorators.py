"""
app/utils/decorators.py — Custom access-control decorators.
"""
from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user


def admin_required(f):
    """Restrict a view to admin users only."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated


def moderator_required(f):
    """Restrict a view to moderator/admin users."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        if not current_user.is_moderator:
            abort(403)
        return f(*args, **kwargs)
    return decorated


def not_banned(f):
    """Block banned users from accessing views."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.is_authenticated and current_user.banned:
            flash("Your account has been suspended.", "danger")
            return redirect(url_for("auth.logout"))
        return f(*args, **kwargs)
    return decorated
