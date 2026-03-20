"""
app/services/scoreboard_service.py — Complex leaderboard ranking logic.
Ranks by score DESC, then first_solve_timestamp ASC as tiebreaker.
"""
from app.models.user import User


def get_leaderboard(limit: int = 100) -> list[dict]:
    """Return ranked list of users for the scoreboard.

    Users with score 0 are excluded.
    """
    users = (
        User.query
        .filter(User.score > 0, User.banned.is_(False))
        .order_by(User.score.desc(), User.first_solve_timestamp.asc())
        .limit(limit)
        .all()
    )

    board = []
    for rank, user in enumerate(users, start=1):
        board.append({
            "rank": rank,
            "username": user.username,
            "score": user.score,
            "solve_count": user.solve_count,
            "first_solve": (
                user.first_solve_timestamp.isoformat()
                if user.first_solve_timestamp else None
            ),
        })
    return board
