"""
app/models/user.py — Complete User model with role-based access,
score tracking, login security, and Flask-Login integration.
"""
import re
from datetime import datetime, timezone
from flask_login import UserMixin
from app.extensions import db, bcrypt


class User(UserMixin, db.Model):
    """Platform user with full authentication and scoring support."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    # Role: 'user', 'moderator', 'admin'
    role = db.Column(db.String(20), nullable=False, default="user")

    # Scoring
    score = db.Column(db.Integer, default=0, nullable=False)
    first_solve_timestamp = db.Column(db.DateTime, nullable=True)

    # Account status
    email_verified = db.Column(db.Boolean, default=False)
    banned = db.Column(db.Boolean, default=False)

    # Security: track failed logins
    failed_login_attempts = db.Column(db.Integer, default=0)
    last_failed_login = db.Column(db.DateTime, nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    submissions = db.relationship(
        "Submission", back_populates="user", lazy="dynamic", cascade="all, delete-orphan"
    )
    hint_unlocks = db.relationship(
        "HintUnlock", back_populates="user", lazy="dynamic", cascade="all, delete-orphan"
    )
    audit_logs = db.relationship(
        "AuditLog", back_populates="user", lazy="dynamic", cascade="all, delete-orphan"
    )

    # ------------------------------------------------------------------ #
    # Password management                                                  #
    # ------------------------------------------------------------------ #

    def set_password(self, password: str) -> None:
        """Hash and store password using bcrypt (14 rounds)."""
        self.password_hash = bcrypt.generate_password_hash(
            password, rounds=14
        ).decode("utf-8")

    def check_password(self, password: str) -> bool:
        """Timing-safe password verification."""
        return bcrypt.check_password_hash(self.password_hash, password)

    # ------------------------------------------------------------------ #
    # Role helpers                                                         #
    # ------------------------------------------------------------------ #

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def is_moderator(self) -> bool:
        return self.role in ("admin", "moderator")

    def promote_to_admin(self) -> None:
        self.role = "admin"

    # ------------------------------------------------------------------ #
    # Score helpers                                                        #
    # ------------------------------------------------------------------ #

    def add_score(self, points: int) -> None:
        """Increase score; track timestamp of first ever solve."""
        self.score += points
        if self.first_solve_timestamp is None:
            self.first_solve_timestamp = datetime.now(timezone.utc)

    # ------------------------------------------------------------------ #
    # Properties                                                           #
    # ------------------------------------------------------------------ #

    @property
    def solved_challenges(self):
        """Return list of challenges this user solved correctly."""
        from app.models.submission import Submission

        return (
            self.submissions.filter_by(is_correct=True)
            .with_entities(Submission.challenge_id)
            .all()
        )

    @property
    def solve_count(self) -> int:
        return self.submissions.filter_by(is_correct=True).count()

    @property
    def is_active(self) -> bool:  # Flask-Login interface
        return not self.banned

    @staticmethod
    def validate_username(username: str) -> bool:
        """Only alphanumeric + underscores, 3–32 chars."""
        return bool(re.match(r"^[a-zA-Z0-9_]{3,32}$", username))

    def __repr__(self) -> str:
        return f"<User {self.username!r} score={self.score}>"
