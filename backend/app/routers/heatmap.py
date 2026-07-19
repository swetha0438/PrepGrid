import datetime as dt
from collections import defaultdict

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Activity
from app.routers.github import get_current_user

router = APIRouter(prefix="/heatmap", tags=["heatmap"])


@router.get("")
async def get_heatmap(request: Request, db: Session = Depends(get_db)):
    """
    Returns activity counts per day for the last 365 days, in the shape
    a heatmap component wants: [{"date": "2026-07-19", "count": 3}, ...]
    Days with zero activity aren't included - frontend fills gaps as 0.
    """
    user = get_current_user(request, db)

    one_year_ago = dt.date.today() - dt.timedelta(days=365)

    activities = db.query(Activity).filter(
        Activity.user_id == user.id,
        Activity.occurred_on >= one_year_ago,
    ).all()

    counts = defaultdict(int)
    for activity in activities:
        counts[activity.occurred_on.isoformat()] += 1

    return {
        "current_streak": _calculate_streak(counts),
        "days": [{"date": d, "count": c} for d, c in sorted(counts.items())],
    }


def _calculate_streak(counts: dict) -> int:
    """Counts consecutive active days ending today (or yesterday, so a
    streak doesn't look broken before today's activity is even logged)."""
    streak = 0
    day = dt.date.today()

    # if today has nothing yet, start checking from yesterday instead
    if counts.get(day.isoformat(), 0) == 0:
        day -= dt.timedelta(days=1)

    while counts.get(day.isoformat(), 0) > 0:
        streak += 1
        day -= dt.timedelta(days=1)

    return streak