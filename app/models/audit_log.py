"""
app/models/audit_log.py — Security audit trail for compliance.
Tracks logins, flag submissions, admin actions, and ban events.
"""
from datetime import datetime, timezone
from app.extensions import db


class AuditLog(db.Model):
    """Immutable security event log. Never update rows — only insert."""

    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=True, index=True
    )

    # Action codes (keep short, snake_case)
    action = db.Column(db.String(50), nullable=False)  # e.g. 'flag_submit_correct'
    target_id = db.Column(db.Integer, nullable=True)
    target_type = db.Column(db.String(30), nullable=True)  # 'challenge', 'user'

    # Network context
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(512), nullable=True)

    # Arbitrary JSON details (SQLite stores as TEXT)
    details = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # Relationship
    user = db.relationship("User", back_populates="audit_logs")

    @classmethod
    def log(cls, action: str, user_id=None, target_id=None,
            target_type=None, ip_address=None, user_agent=None, details=None):
        """Convenience factory — create and add to session."""
        import json
        entry = cls(
            action=action,
            user_id=user_id,
            target_id=target_id,
            target_type=target_type,
            ip_address=ip_address,
            user_agent=user_agent,
            details=json.dumps(details) if details else None,
        )
        db.session.add(entry)
        return entry

    def __repr__(self) -> str:
        return f"<AuditLog {self.action!r} user={self.user_id}>"
