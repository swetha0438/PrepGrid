import httpx

from app.config import settings

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_API_URL = "https://api.github.com"


def get_authorize_url(state: str) -> str:
    params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "redirect_uri": f"{settings.BASE_URL}/auth/github/callback",
        "scope": "read:user repo",
        "state": state,
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{GITHUB_AUTHORIZE_URL}?{query}"


async def exchange_code_for_token(code: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            GITHUB_TOKEN_URL,
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": f"{settings.BASE_URL}/auth/github/callback",
            },
            headers={"Accept": "application/json"},
        )
        response.raise_for_status()
        data = response.json()
        if "access_token" not in data:
            raise ValueError(f"GitHub token exchange failed: {data}")
        return data["access_token"]


async def fetch_github_user(access_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GITHUB_API_URL}/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
            },
        )
        response.raise_for_status()
        return response.json()


async def fetch_recent_commits(access_token: str, github_username: str) -> list[dict]:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GITHUB_API_URL}/search/commits",
            params={
                "q": f"author:{github_username}",
                "sort": "author-date",
                "order": "desc",
                "per_page": 100,
            },
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github.cloak-preview+json",
            },
        )
        response.raise_for_status()
        items = response.json().get("items", [])

        commits = []
        for item in items:
            commits.append({
                "repo": item["repository"]["full_name"],
                "sha": item["sha"],
                "date": item["commit"]["author"]["date"],
                "message": item["commit"]["message"].split("\n")[0],
            })
        return commits