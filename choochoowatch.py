import time

from geo import get_crossing_coords
from train import fetch_trains, estimate_time_to_crossing
from rentry import update_rentry_log
from log_utils import log

# Config
POSTCODE = "CV1 4AR"
MARGIN_SEC = 90
POLL_INTERVAL = 20
SIGNALBOX_API = "https://map-api.production.signalbox.io/api/locations"
RENTRY_SECRET_FILE = "rentry_secret.txt"


# --- Main Loop ---
def main():
    crossing = get_crossing_coords(POSTCODE)
    log(f"\ud83d\udccd Monitoring crossing at {crossing} (margin {MARGIN_SEC}s)")
    try:
        while True:
            trains = fetch_trains(SIGNALBOX_API)
            for t in trains:
                if not isinstance(t, dict):
                    continue
                try:
                    eta = estimate_time_to_crossing(t, crossing)
                    if eta < MARGIN_SEC + POLL_INTERVAL:
                        log(f"\u26a0\ufe0f Train approaching in ~{int(eta)}s")
                except Exception as e:
                    log(f"Skipping train due to error: {e}")
            update_rentry_log(log_path="choochoowatch.log", secret_file=RENTRY_SECRET_FILE)
            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        log("Shutdown requested, exiting...")


if __name__ == "__main__":
    main()
