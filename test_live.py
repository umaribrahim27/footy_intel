import http.client
import json
from dotenv import load_dotenv
import os

load_dotenv()

conn = http.client.HTTPSConnection("free-api-live-football-data.p.rapidapi.com")

headers = {
    'x-rapidapi-key': os.getenv("RAPIDAPI_KEY"),
    'x-rapidapi-host': "free-api-live-football-data.p.rapidapi.com",
    'Content-Type': "application/json"
}

# test live scores
conn.request("GET", "/football-get-all-matches-by-league?leagueid=42", headers=headers)
res = conn.getresponse()
data = res.read()
print("PL:")
print(json.dumps(json.loads(data.decode("utf-8")), indent=2)[:1000])