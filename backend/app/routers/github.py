import datetime as dt

from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session

from app.auth import github_oauth
from app.database import get_db
from app.models import User, Activity

router = APIRouter(prefix="/github", tags=["github"])


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Reads user_id from the session (set during OAuth callback) and
    loads the User row. Reused by any route that needs 'who's logged in'."""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not logged in")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.post("/sync-commits")
async def sync_commits(request: Request, db: Session = Depends(get_db)):
    """Pulls recent commits from GitHub and inserts new ones as
    Activity rows. Safe to call repeatedly - skips commits already saved."""
    user = get_current_user(request, db)

    commits = await github_oauth.fetch_recent_commits(
        user.github_access_token, user.github_username
    )

    new_count = 0
    for commit in commits:
        # avoid duplicate rows if this endpoint gets called again
        exists = db.query(Activity).filter(
            Activity.user_id == user.id,
            Activity.source == "github",
            Activity.label == commit["sha"],
        ).first()
        if exists:
            continue

        commit_date = dt.datetime.fromisoformat(
            commit["date"].replace("Z", "+00:00")
        ).date()

        db.add(Activity(
            user_id=user.id,
            source="github",
            activity_type="commit",
            label=commit["sha"],
            occurred_on=commit_date,
        ))
        new_count += 1

    db.commit()
    return {"synced": new_count, "total_fetched": len(commits)}