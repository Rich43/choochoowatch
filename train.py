import math
from typing import Iterable, Dict, Any, List

import requests

from log_utils import log


def fetch_trains(api_url: str) -> List[Dict[str, Any]]:
    try:
        log(f"Fetching train data from: {api_url}")
        resp = requests.get(api_url)
        log(f"Train data response code: {resp.status_code}")
        resp.raise_for_status()
        content_snippet = resp.text[:300].replace('\n', ' ')
        log(f"Response snippet: {content_snippet}...")
        data = resp.json()
        train_locs = data.get("train_locations", [])
        log(f"Retrieved {len(train_locs)} train location entries")
        return train_locs
    except Exception as e:
        log(f"Error fetching train data: {e}")
        return []


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def estimate_time_to_crossing(train: Dict[str, Any], crossing_coord: Iterable[float]) -> float:
    loc = train.get("location", {})
    tx, ty = loc.get("lat"), loc.get("lon")
    if tx is None or ty is None:
        raise ValueError("Missing train location data")
    dist = haversine(tx, ty, crossing_coord[0], crossing_coord[1])
    speed = train.get("speed", 80)
    eta = (dist / speed) * 3600
    log(
        f"Train {train.get('rid', 'N/A')} at ({tx}, {ty}) is {dist:.2f} km from crossing, est ETA: {eta:.1f}s"
    )
    return eta
