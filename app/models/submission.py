"""
app/models/submission.py — Flag submission tracking.
Unique constraint prevents duplicate solves per user/challenge.
"""
from datetime import datetime, timezone
from app.extensions import db


class Submission(db.Model):
    """Every flag attempt (correct or wrong) is logged here."""

    __tablename__ = "submissions"
    __table_args__ = (
        # Core security constraint: one correct solve per user per challenge
        db.UniqueConstraint("user_id", "challenge_id", "is_correct",
                            name="uq_user_challenge_correct"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    challenge_id = db.Column(
        db.Integer, db.ForeignKey("challenges.id"), nullable=False, index=True
    )

    # Never store the raw flag — only enough to detect duplicates
    submitted_flag_hash = db.Column(db.String(64), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False, default=False)

    # Metadata for audit
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(512), nullable=True)
    hint_used = db.Column(db.Boolean, default=False)
    points_earned = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    user = db.relationship("User", back_populates="submissions")
    challenge = db.relationship("Challenge", back_populates="submissions")

    def __repr__(self) -> str:
        status = "✓" if self.is_correct else "✗"
        return f"<Submission user={self.user_id} chall={self.challenge_id} {status}>"
