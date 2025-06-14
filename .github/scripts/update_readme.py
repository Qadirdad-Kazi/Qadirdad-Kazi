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

def update_section(content: str, section_name: str, new_content: str) -> str:
    """Update a section in the README with new content."""
    start_tag = f"<!-- {section_name} -->"
    end_tag = f"<!-- END_{section_name} -->"
    start_idx = content.find(start_tag)
    end_idx = content.find(end_tag)
    
    if start_idx == -1 or end_idx == -1:
        return content
    
    # For sections to remove completely including their headings
    sections_to_remove = ["FEATURED_PROJECTS", "RECENT_ACTIVITY", "DAILY_QUOTE"]
    if section_name in sections_to_remove:
        # Find the start of the section (including the heading)
        section_start = content.rfind('##', 0, start_idx)
        if section_start != -1:
            # Find the end of the line with the heading
            heading_end = content.find('\n', section_start)
            if heading_end != -1:
                start_idx = section_start
    
    end_idx += len(end_tag)
    # If new_content is empty, return the content without the section
    if not new_content.strip():
        return content[:start_idx] + content[end_idx:]
    return content[:start_idx] + f"{start_tag}\n{new_content}\n{end_tag}" + content[end_idx:]

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
    try:
        token = os.environ.get("GITHUB_TOKEN")
        username = os.environ.get("GITHUB_USERNAME") or os.getenv("GITHUB_REPOSITORY", "/").split('/')[0]
        cache_key = f"github_activity_{username}"
        
        # Try to get from cache first
        cached_data = get_cached_data(cache_key)
        if cached_data is not None:
            return cached_data
            
        headers = {"Authorization": f"token {token}"} if token else {}
        r = requests.get(
            f"https://api.github.com/users/{username}/events/public?per_page=5",
            headers=headers,
            timeout=10
        )
        r.raise_for_status()
        events = r.json()
        
        if not events:
            return ""
            
        result = []
        for event in events[:5]:  # Limit to 5 most recent events
            if event["type"] == "PushEvent":
                repo = event["repo"]["name"]
                branch = event["payload"]["ref"].split("/")[-1]
                commits = event["payload"]["commits"]
                commit_msgs = [commit["message"].split("\n")[0] for commit in commits[:2]]
                result.append(f"- Pushed to [{repo}](https://github.com/{repo}) on branch `{branch}`")
                for msg in commit_msgs:
                    result.append(f"  - {msg}")
            elif event["type"] == "CreateEvent":
                repo = event["repo"]["name"]
                ref_type = event["payload"]["ref_type"]
                ref = event["payload"]["ref"]
                result.append(f"- Created {ref_type} `{ref}` in [{repo}](https://github.com/{repo})")
            elif event["type"] == "PullRequestEvent":
                action = event["payload"]["action"]
                pr = event["payload"]["pull_request"]
                result.append(f"- {action.capitalize()} pull request: [{pr['title']}]({pr['html_url']}) in {pr['head']['repo']['name']}")
            elif event["type"] == "IssuesEvent":
                action = event["payload"]["action"]
                issue = event["payload"]["issue"]
                result.append(f"- {action.capitalize()} issue: [{issue['title']}]({issue['html_url']}) in {event['repo']['name']}")
                
        if not result:  # If no events were added
            return ""
            
        result = "\n".join(result)
        # Cache the result for 1 hour
        set_cached_data(cache_key, result)
        return result
        
    except Exception:
        return ""  # Return empty string on any error

def get_daily_quote():
    """Get a daily quote with error handling."""
    try:
        cache_key = "daily_quote"
        cached_quote = get_cached_data(cache_key)
        if cached_quote is not None:
            return cached_quote
            
        r = requests.get("https://api.quotable.io/random", timeout=5)
        if r.status_code != 200:
            return ""
            
        data = r.json()
        quote = f'> {data["content"]}\n> — {data["author"]}'
        
        # Cache the quote for 12 hours
        set_cached_data(cache_key, quote, ttl=43200)  # 12 hours in seconds
        return quote
    except Exception:
        return ""

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
        return ""  # Return empty string when no pinned repositories are found
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
    
    # Handle GitHub activity section
    activity = get_recent_activity()
    if not activity or "Missing configuration" in activity:
        content = update_section(content, "RECENT_ACTIVITY", "<!-- RECENT_ACTIVITY -->\n<!-- END_RECENT_ACTIVITY -->")
    else:
        content = update_section(content, "RECENT_ACTIVITY", activity)
    
    # Handle daily quote section
    quote = get_daily_quote()
    if not quote:
        content = update_section(content, "DAILY_QUOTE", "<!-- DAILY_QUOTE -->\n<!-- END_DAILY_QUOTE -->")
    else:
        content = update_section(content, "DAILY_QUOTE", quote)
    
    # Remove featured projects section completely
    content = update_section(content, "FEATURED_PROJECTS", "<!-- FEATURED_PROJECTS -->\n<!-- END_FEATURED_PROJECTS -->")
    
    # Handle achievements section
    achievements = get_achievements()
    if not achievements:
        content = update_section(content, "ACHIEVEMENTS", "<!-- ACHIEVEMENTS -->\n<!-- END_ACHIEVEMENTS -->")
    else:
        content = update_section(content, "ACHIEVEMENTS", achievements)
    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    main()
