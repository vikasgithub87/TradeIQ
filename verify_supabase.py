"""Verify Supabase URL and anon key by calling the REST API."""
import os
import requests
from dotenv import load_dotenv

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_ANON_KEY")

if not url or not key:
    print("ERROR: Set SUPABASE_URL and SUPABASE_ANON_KEY in .env")
    exit(1)

# Supabase REST base; a simple GET to /rest/v1/ returns 200 if keys are valid
api = f"{url.rstrip('/')}/rest/v1/"
headers = {"apikey": key, "Authorization": f"Bearer {key}"}

try:
    r = requests.get(api, headers=headers, timeout=10)
    if r.status_code in (200, 406):  # 406 = no Accept header, but auth worked
        print("OK: Supabase credentials are valid.")
    else:
        print(f"Check: Supabase returned status {r.status_code}. Response: {r.text[:200]}")
except Exception as e:
    print(f"ERROR: {e}")
