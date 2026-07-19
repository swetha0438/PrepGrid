import secrets

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.auth import github_oauth
from app.database import get_db
from app.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/github/login")
async def github_login(request: Request):
    """
    Step 1: user clicks "Login with GitHub" -> we generate a random
    `state` value (CSRF protection), stash it in their session, and
    redirect them to GitHub's authorize page.
    """
    state = secrets.token_urlsafe(16)
    request.session["oauth_state"] = state
    return RedirectResponse(github_oauth.get_authorize_url(state))


@router.get("/github/callback")
async def github_callback(request: Request, code: str, state: str, db: Session = Depends(get_db)):
    """
    Step 2: GitHub redirects back here with a `code` (to exchange for
    a token) and the `state` we sent earlier. We check `state` matches
    what we stored - if it doesn't, someone may be trying to forge a
    login, so we reject it.
    """
    expected_state = request.session.get("oauth_state")
    if not expected_state or expected_state != state:
        return RedirectResponse("/login-error?reason=state_mismatch")

    # Exchange the one-time code for a real access token
    access_token = await github_oauth.exchange_code_for_token(code)

    # Use the token to fetch who this actually is
    profile = await github_oauth.fetch_github_user(access_token)

    # Find existing user by github_id, or create a new one
    user = db.query(User).filter(User.github_id == str(profile["id"])).first()
    if user is None:
        user = User(
            github_id=str(profile["id"]),
            github_username=profile["login"],
            github_access_token=access_token,
        )
        db.add(user)
    else:
        # Refresh username/token in case they changed
        user.github_username = profile["login"]
        user.github_access_token = access_token

    db.commit()
    db.refresh(user)

    # Log them into our own session (not GitHub's) so future requests
    # know who they are without re-doing OAuth every time
    request.session["user_id"] = user.id

    return RedirectResponse("/dashboard")