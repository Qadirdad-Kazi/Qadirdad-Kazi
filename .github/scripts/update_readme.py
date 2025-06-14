import os
import re
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

README_PATH = "README.md"

def update_section(content, tag, new_text):
    pattern = rf"(<!-- {tag} -->)(.*?)(<!-- END_{tag} -->)"
    return re.sub(pattern, rf"\1\n{new_text}\n\3", content, flags=re.DOTALL)

def get_spotify_now():
    token_url = "https://accounts.spotify.com/api/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": os.environ["SPOTIFY_REFRESH_TOKEN"],
        "client_id": os.environ["SPOTIFY_CLIENT_ID"],
        "client_secret": os.environ["SPOTIFY_CLIENT_SECRET"],
    }
    r = requests.post(token_url, data=data)
    access_token = r.json().get("access_token")
    if not access_token:
        return "🎵 Now Playing: *Unable to fetch*"
    headers = {"Authorization": f"Bearer {access_token}"}
    r = requests.get("https://api.spotify.com/v1/me/player/currently-playing", headers=headers)
    if r.status_code != 200 or not r.json():
        return "🎵 Now Playing: *Nothing playing*"
    item = r.json().get("item")
    if not item:
        return "🎵 Now Playing: *Nothing playing*"
    track = item["name"]
    artist = ", ".join([a["name"] for a in item["artists"]])
    url = item["external_urls"]["spotify"]
    return f"🎵 Now Playing: [{track} - {artist}]({url})"

def get_last_updated():
    now = datetime.now(timezone.utc)
    return f"Last Updated: {now.strftime('%B %d, %Y %H:%M UTC')}"

def get_recent_activity():
    repo_env = os.getenv("GITHUB_REPOSITORY")
    if repo_env:
        username = repo_env.split('/')[0]
    else:
        username = ""
    token = os.environ["GITHUB_TOKEN"]
    headers = {"Authorization": f"token {token}"}
    url = f"https://api.github.com/users/{username}/events/public"
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        return "- Unable to fetch activity."
    events = r.json()[:5]
    lines = []
    for e in events:
        t = e["type"]
        repo = e["repo"]["name"]
        created = e["created_at"][:10]
        if t == "PushEvent":
            lines.append(f"- 📝 Commit to **{repo}** on {created}")
        elif t == "PullRequestEvent":
            action = e["payload"]["action"]
            lines.append(f"- 🔀 PR {action} in **{repo}** on {created}")
        elif t == "IssuesEvent":
            action = e["payload"]["action"]
            lines.append(f"- ❗ Issue {action} in **{repo}** on {created}")
    return "\n".join(lines) if lines else "- No recent GitHub activity."

def get_daily_quote():
    r = requests.get("https://api.quotable.io/random")
    if r.status_code != 200:
        return "> Unable to fetch quote."
    data = r.json()
    return f'> {data["content"]}\n> — {data["author"]}'

def main():
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    content = update_section(content, "SPOTIFY_NOW", get_spotify_now())
    content = update_section(content, "LAST_UPDATED", get_last_updated())
    content = update_section(content, "RECENT_ACTIVITY", get_recent_activity())
    content = update_section(content, "DAILY_QUOTE", get_daily_quote())
    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    main()
