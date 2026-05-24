import http.client
import json
import os
from dotenv import load_dotenv
from datetime import datetime
import time

load_dotenv()

# simple in-memory cache: {key: (timestamp, data)}
_cache = {}
TTL = {
    "live": 120,       # 2 minutes
    "date": 600,       # 10 minutes
    "player": 3600     # 1 hour
}

def _request(endpoint: str) -> dict:
    conn = http.client.HTTPSConnection("free-api-live-football-data.p.rapidapi.com")
    headers = {
        'x-rapidapi-key': os.getenv("RAPIDAPI_KEY"),
        'x-rapidapi-host': "free-api-live-football-data.p.rapidapi.com",
        'Content-Type': "application/json"
    }
    conn.request("GET", endpoint, headers=headers)
    res = conn.getresponse()
    return json.loads(res.read().decode("utf-8"))

def _cached_request(key: str, endpoint: str, ttl_key: str) -> dict:
    now = time.time()
    if key in _cache:
        timestamp, data = _cache[key]
        if now - timestamp < TTL[ttl_key]:
            return data
    data = _request(endpoint)
    _cache[key] = (now, data)
    return data

def get_live_matches() -> str:
    data = _cached_request("live", "/football-current-live", "live")
    matches = data.get("response", {}).get("live", [])
    if not matches:
        return "No live matches right now."
    result = []
    for m in matches:
        result.append(f"{m['home']['name']} {m['home']['score']} - {m['away']['score']} {m['away']['name']}")
    return "\n".join(result)

def get_matches_by_date(date: str = None) -> str:
    if not date:
        date = datetime.now().strftime("%Y%m%d")
    data = _cached_request(f"date_{date}", f"/football-get-matches-by-date?date={date}", "date")
    matches = data.get("response", {}).get("matches", [])
    if not matches:
        return f"No matches found for {date}."
    result = []
    for m in matches[:10]:
        status = m["status"].get("scoreStr", "vs")
        finished = "FT" if m["status"].get("finished") else "upcoming"
        result.append(f"{m['home']['name']} {status} {m['away']['name']} [{finished}]")
    return "\n".join(result)

def search_player(name: str) -> str:
    encoded_name = name.replace(" ", "%20")
    key = f"player_{name.lower()}"
    data = _cached_request(key, f"/football-players-search?search={encoded_name}", "player")
    suggestions = data.get("response", {}).get("suggestions", [])
    if not suggestions:
        return f"No players found for '{name}'."
    result = []
    for p in suggestions[:3]:
        result.append(f"{p['name']} — {p['teamName']}")
    return "\n".join(result)