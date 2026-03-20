"""
app/models/challenge.py — Challenge, Hint, and HintUnlock models.
"""
from datetime import datetime, timezone
from app.extensions import db


CATEGORIES = ["web", "crypto", "forensics", "reverse", "pwn", "misc", "network"]
DIFFICULTIES = ["easy", "medium", "hard", "insane"]


class Challenge(db.Model):
    """A CTF challenge with flag (SHA-256 hashed), hints, and file support."""

    __tablename__ = "challenges"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(220), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)  # Markdown source
    category = db.Column(db.String(30), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False, default="easy")
    points = db.Column(db.Integer, nullable=False, default=100)

    # Security: only the SHA-256 hex-digest is stored — never the raw flag
    flag_hash = db.Column(db.String(64), nullable=False)

    # Optional downloadable file (relative path under static/uploads/)
    file_path = db.Column(db.String(500), nullable=True)
    file_name = db.Column(db.String(255), nullable=True)

    # Visibility
    active = db.Column(db.Boolean, default=True)

    # Aggregated stats (updated on each solve for fast display)
    solve_count = db.Column(db.Integer, default=0)

    # Author / meta
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    hints = db.relationship(
        "Hint", back_populates="challenge", lazy="dynamic", cascade="all, delete-orphan"
    )
    submissions = db.relationship(
        "Submission", back_populates="challenge", lazy="dynamic", cascade="all, delete-orphan"
    )
    author = db.relationship("User", foreign_keys=[author_id])

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    @property
    def difficulty_color(self) -> str:
        return {
            "easy": "neon-green",
            "medium": "neon-yellow",
            "hard": "neon-orange",
            "insane": "neon-red",
        }.get(self.difficulty, "neon-gray")

    @property
    def category_icon(self) -> str:
        return {
            "web": "🌐",
            "crypto": "🔐",
            "forensics": "🔍",
            "reverse": "⚙️",
            "pwn": "💣",
            "misc": "🎲",
            "network": "📡",
        }.get(self.category, "🏴")

    def has_file(self) -> bool:
        return bool(self.file_path)

    def __repr__(self) -> str:
        return f"<Challenge {self.title!r} {self.difficulty}/{self.points}pts>"


class Hint(db.Model):
    """A point-penalising hint attached to a challenge."""

    __tablename__ = "hints"

    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(
        db.Integer, db.ForeignKey("challenges.id"), nullable=False, index=True
    )
    text = db.Column(db.Text, nullable=False)  # Markdown
    penalty_points = db.Column(db.Integer, default=25)  # % or absolute

    challenge = db.relationship("Challenge", back_populates="hints")
    unlocks = db.relationship(
        "HintUnlock", back_populates="hint", lazy="dynamic", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Hint challenge={self.challenge_id} penalty={self.penalty_points}>"


class HintUnlock(db.Model):
    """Records which user unlocked which hint (prevents double-penalty)."""

    __tablename__ = "hint_unlocks"
    __table_args__ = (db.UniqueConstraint("user_id", "hint_id", name="uq_user_hint"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    hint_id = db.Column(db.Integer, db.ForeignKey("hints.id"), nullable=False)
    unlocked_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", back_populates="hint_unlocks")
    hint = db.relationship("Hint", back_populates="unlocks")
