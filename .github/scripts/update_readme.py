import os
import re
import json
import time
import hashlib
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional, Dict, Any, List, Tuple

# Load environment variables
load_dotenv()

# Constants
README_PATH = "README.md"
CACHE_DIR = Path(".github/cache")
CACHE_TTL = 3600  # 1 hour cache TTL

# Ensure cache directory exists
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def get_cache_key(prefix: str, *args) -> str:
    """Generate a cache key based on function name and arguments."""
    key = f"{prefix}_{'_'.join(str(arg) for arg in args)}"
    return hashlib.md5(key.encode()).hexdigest()

def get_cached_data(key: str) -> Optional[Dict[str, Any]]:
    """Get cached data if it exists and is not expired."""
    cache_file = CACHE_DIR / f"{key}.json"
    if not cache_file.exists():
        return None
        
    try:
        with open(cache_file, 'r') as f:
            data = json.load(f)
            if time.time() - data.get('timestamp', 0) < CACHE_TTL:
                return data.get('data')
    except (json.JSONDecodeError, OSError):
        pass
    return None

def set_cached_data(key: str, data: Any) -> None:
    """Cache data with a timestamp."""
    try:
        cache_file = CACHE_DIR / f"{key}.json"
        with open(cache_file, 'w') as f:
            json.dump({'timestamp': time.time(), 'data': data}, f)
    except OSError:
        pass

def update_section(content: str, tag: str, new_text: str) -> str:
    """Update a section in the README marked with HTML comments."""
    pattern = rf"(<!-- {tag} -->)(.*?)(<!-- END_{tag} -->)"
    return re.sub(pattern, rf"\1\n{new_text}\n\3", content, flags=re.DOTALL)

def get_spotify_now() -> str:
    """Get currently playing track from Spotify with caching and error handling."""
    cache_key = get_cache_key("spotify_now")
    cached = get_cached_data(cache_key)
    if cached:
        return cached

    try:
        # Get access token
        token_url = "https://accounts.spotify.com/api/token"
        data = {
            "grant_type": "refresh_token",
            "refresh_token": os.environ["SPOTIFY_REFRESH_TOKEN"],
            "client_id": os.environ["SPOTIFY_CLIENT_ID"],
            "client_secret": os.environ["SPOTIFY_CLIENT_SECRET"],
        }
        
        response = requests.post(token_url, data=data, timeout=10)
        response.raise_for_status()
        
        access_token = response.json().get("access_token")
        if not access_token:
            raise ValueError("No access token received")

        # Get currently playing track
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(
            "https://api.spotify.com/v1/me/player/currently-playing",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 204:  # No content
            result = "🎵 Now Playing: *Nothing playing*"
        elif response.status_code == 200:
            data = response.json()
            item = data.get("item", {})
            if not item:
                result = "🎵 Now Playing: *Nothing playing*"
            else:
                track = item.get("name", "Unknown Track")
                artists = ", ".join(a.get("name", "Unknown Artist") for a in item.get("artists", []))
                url = item.get("external_urls", {}).get("spotify", "#")
                result = f"🎵 Now Playing: [{track} - {artists}]({url})"
        else:
            result = f"🎵 Now Playing: *Status {response.status_code}*"
            
        # Cache the result for 1 minute
        set_cached_data(cache_key, result)
        return result
        
    except requests.RequestException as e:
        return f"🎵 Now Playing: *Error: {str(e)}*"
    except Exception as e:
        return "🎵 Now Playing: *Temporarily unavailable*"

def get_last_updated() -> str:
    """Get the current timestamp in a readable format."""
    now = datetime.now(timezone.utc)
    return f"Last Updated: {now.strftime('%B %d, %Y %H:%M UTC')} (updates every 4 hours)"

def get_recent_activity() -> str:
    """Get recent GitHub activity with caching and error handling."""
    cache_key = get_cache_key("github_activity")
    cached = get_cached_data(cache_key)
    if cached:
        return cached

    try:
        # Get username from environment
        repo_env = os.getenv("GITHUB_REPOSITORY")
        username = repo_env.split('/')[0] if repo_env else os.environ.get("GITHUB_USERNAME", "")
        token = os.environ.get("PERSONAL_ACCESS_TOKEN")
        
        if not username or not token:
            return "- GitHub activity: Missing configuration"

        # Prepare request
        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
        url = f"https://api.github.com/users/{username}/events/public?per_page=5"
        
        # Make request with timeout
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        events = response.json()
        if not isinstance(events, list):
            return "- GitHub activity: Unexpected response format"
            
        lines = []
        for event in events[:5]:  # Limit to 5 most recent events
            try:
                event_type = event.get("type")
                repo_name = event.get("repo", {}).get("name", "unknown/repo")
                created = event.get("created_at", "")[:10]
                
                if event_type == "PushEvent":
                    lines.append(f"- 📝 Pushed to **{repo_name}** on {created}")
                elif event_type == "PullRequestEvent":
                    action = event.get("payload", {}).get("action", "")
                    pr_num = event.get("payload", {}).get("number", "")
                    lines.append(f"- 🔀 PR #{pr_num} {action} in **{repo_name}** on {created}")
                elif event_type == "IssuesEvent":
                    action = event.get("payload", {}).get("action", "")
                    issue_num = event.get("payload", {}).get("issue", {}).get("number", "")
                    lines.append(f"- ❗ Issue #{issue_num} {action} in **{repo_name}** on {created}")
                elif event_type == "CreateEvent":
                    ref_type = event.get("payload", {}).get("ref_type", "")
                    lines.append(f"- 🆕 Created {ref_type} in **{repo_name}** on {created}")
                    
            except (KeyError, AttributeError):
                continue
                
        result = "\n".join(lines) if lines else "- No recent GitHub activity"
        
        # Cache for 1 hour
        set_cached_data(cache_key, result)
        return result
        
    except Exception:
        # Return empty string instead of error message
        return ""

def get_daily_quote():
    try:
        r = requests.get("https://api.quotable.io/random", timeout=5)
        if r.status_code != 200:
            return ""  # Return empty string instead of error
        data = r.json()
        return f'> {data["content"]}\n> — {data["author"]}'
    except Exception:
        return ""  # Return empty string on error

def get_featured_projects():
    token = os.environ.get("GITHUB_TOKEN")
    username = os.environ.get("GITHUB_USERNAME") or os.getenv("GITHUB_REPOSITORY", "/").split('/')[0]
    headers = {"Authorization": f"token {token}"}
    query = '''
    query($login: String!) {
      user(login: $login) {
        pinnedItems(first: 4, types: REPOSITORY) {
          nodes {
            ... on Repository {
              name
              description
              url
              stargazerCount
              forkCount
              primaryLanguage { name color }
            }
          }
        }
      }
    }
    '''
    variables = {"login": username}
    r = requests.post(
        "https://api.github.com/graphql",
        json={"query": query, "variables": variables},
        headers=headers
    )
    data = r.json().get("data")
    if not data or not data.get("user") or not data["user"].get("pinnedItems"):
        return ""  # Return empty string on error
    nodes = data["user"]["pinnedItems"]["nodes"]
    if not nodes:
        return "- No featured projects found. Pin repositories on your GitHub profile to feature them here."
    lines = []
    for repo in nodes:
        lang = repo["primaryLanguage"]["name"] if repo["primaryLanguage"] else ""
        color = repo["primaryLanguage"]["color"] if repo["primaryLanguage"] else "#ccc"
        lines.append(f"- [{repo['name']}]({repo['url']}): {repo['description'] or ''} ⭐{repo['stargazerCount']} 🍴{repo['forkCount']} <span style='color:{color}'>● {lang}</span>")
    return '\n'.join(lines)

def get_achievements():
    token = os.environ.get("GITHUB_TOKEN")
    username = os.environ.get("GITHUB_USERNAME") or os.getenv("GITHUB_REPOSITORY", "/").split('/')[0]
    headers = {"Authorization": f"token {token}"}
    url = f"https://api.github.com/users/{username}"
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        return ""  # Return empty string on error
    user = r.json()
    lines = [
        f"- 🏆 **Public Repos:** {user.get('public_repos', 0)}",
        f"- 👥 **Followers:** {user.get('followers', 0)}",
        f"- ⭐ **GitHub Stars:** {user.get('public_gists', 0)}",
        f"- 🗓️ **GitHub Since:** {user.get('created_at', '')[:10]}"
    ]
    return '\n'.join(lines)

def main():
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    content = update_section(content, "SPOTIFY_NOW", get_spotify_now())
    content = update_section(content, "LAST_UPDATED", get_last_updated())
    content = update_section(content, "RECENT_ACTIVITY", get_recent_activity())
    content = update_section(content, "DAILY_QUOTE", get_daily_quote())
    content = update_section(content, "FEATURED_PROJECTS", get_featured_projects())
    content = update_section(content, "ACHIEVEMENTS", get_achievements())
    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    main()
