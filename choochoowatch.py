import requests
from bs4 import BeautifulSoup
import time
import os
import math
from geopy.geocoders import Nominatim
import logging

# Config
POSTCODE = "CV1 4AR"
MARGIN_SEC = 90
POLL_INTERVAL = 20
SIGNALBOX_API = "https://map-api.production.signalbox.io//api/locations"
RENTRY_SECRET_FILE = "rentry_secret.txt"

# Logging
class FlushFileHandler(logging.FileHandler):
    def emit(self, record):
        super().emit(record)
        self.flush()

logger = logging.getLogger("choochoowatch")
logger.setLevel(logging.INFO)
file_handler = FlushFileHandler("choochoowatch.log", mode='a', encoding='utf-8')
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def log(msg):
    print(msg)
    logger.info(msg)

# --- Rentry ---
def create_rentry_spoofed(content="🚦 ChooChoo Log"):
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://rentry.co/"
    }
    resp = session.get("https://rentry.co", headers=headers)
    log(f"Fetched Rentry homepage: {resp.status_code}")
    soup = BeautifulSoup(resp.text, "html.parser")
    token_tag = soup.find("input", {"name": "csrf-token"})
    csrf = token_tag["value"].strip() if token_tag and token_tag.has_attr("value") else ""
    if not csrf:
        raise Exception("Failed to retrieve CSRF token from Rentry")
    if not csrf:
        raise Exception("Failed to retrieve CSRF token from Rentry")

    data = {
        "csrf-token": csrf,
        "edit_code": "",
        "text": content,
        "lang": "plain_text"
    }
    post_headers = headers.copy()
    post_headers["Content-Type"] = "application/x-www-form-urlencoded"
    post = session.post("https://rentry.co", data=data, headers=post_headers, allow_redirects=False)
    if post.status_code == 302 and "Location" in post.headers:
        slug = post.headers["Location"].lstrip("/")
        edit_resp = session.get(f"https://rentry.co/{slug}/edit", headers=headers)
        soup = BeautifulSoup(edit_resp.text, "html.parser")
        edit_code = soup.find("input", {"name": "edit_code"})["value"]
        with open(RENTRY_SECRET_FILE, "w", encoding="utf-8") as f:
            f.write(f"{slug}\n{edit_code}")
        return slug, edit_code
    else:
        raise Exception(f"Failed to create paste: {post.status_code}")

def read_rentry_credentials():
    if os.path.exists(RENTRY_SECRET_FILE):
        with open(RENTRY_SECRET_FILE, "r", encoding="utf-8") as f:
            lines = f.read().strip().splitlines()
            if len(lines) == 2:
                return lines[0], lines[1]
    return create_rentry_spoofed()

def update_rentry_log():
    try:
        slug, edit_code = read_rentry_credentials()
        with open("choochoowatch.log", "r", encoding="utf-8") as f:
            last_lines = f.readlines()[-10:]
        content = "### 🚦 ChooChoo Watch Log\n\n```\n" + "".join(last_lines).strip() + "\n```"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
            "Referer": f"https://rentry.co/{slug}"
        }
        data = {
            "edit_code": edit_code,
            "content": content
        }
        resp = requests.post(f"https://rentry.co/api/edit/{slug}", data=data, headers=headers)
        if resp.status_code == 200:
            log(f"🔁 Rentry updated: https://rentry.co/{slug}")
        else:
            log(f"❌ Failed to update Rentry: {resp.status_code} {resp.text[:200]}")
    except Exception as e:
        log(f"Rentry update error: {e}")

# --- Geolocation ---
def get_crossing_coords(postcode):
    geo = Nominatim(user_agent="train-warn")
    loc = geo.geocode(postcode + ", UK")
    if loc is None:
        raise ValueError("Could not locate postcode")
    return (loc.latitude, loc.longitude)

# --- Train Data ---
def fetch_trains():
    try:
        log(f"Fetching train data from: {SIGNALBOX_API}")
        resp = requests.get(SIGNALBOX_API)
        log(f"Train data response code: {resp.status_code}")
        resp.raise_for_status()
        content_snippet = resp.text[:300].replace('', ' ').replace('', '')
        log(f"Response snippet: {content_snippet}...")
        data = resp.json()
        train_locs = data.get("train_locations", [])
        log(f"Retrieved {len(train_locs)} train location entries")
        return train_locs
    except Exception as e:
        log(f"Error fetching train data: {e}")
        return []
    except Exception as e:
        log(f"Error fetching train data: {e}")
        return []

def estimate_time_to_crossing(train, crossing_coord):
    loc = train.get("location", {})
    tx, ty = loc.get("lat"), loc.get("lon")
    if tx is None or ty is None:
        raise ValueError("Missing train location data")
    dist = haversine(tx, ty, crossing_coord[0], crossing_coord[1])
    speed = train.get('speed', 80)
    eta = (dist / speed) * 3600
    log(f"Train {train.get('rid', 'N/A')} at ({tx}, {ty}) is {dist:.2f} km from crossing, est ETA: {eta:.1f}s")
    return eta

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# --- Main Loop ---
def main():
    crossing = get_crossing_coords(POSTCODE)
    log(f"📍 Monitoring crossing at {crossing} (margin {MARGIN_SEC}s)")
    while True:
        trains = fetch_trains()
        for t in trains:
            if not isinstance(t, dict):
                continue
            try:
                eta = estimate_time_to_crossing(t, crossing)
                if eta < MARGIN_SEC + POLL_INTERVAL:
                    log(f"⚠️ Train approaching in ~{int(eta)}s")
            except Exception as e:
                log(f"Skipping train due to error: {e}")
        update_rentry_log()
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
