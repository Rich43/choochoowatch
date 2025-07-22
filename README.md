# ChooChoo Watch

ChooChoo Watch is a small Python script that monitors trains approaching a UK rail crossing. It polls the [Signalbox](https://map.production.signalbox.io) API for live train positions, calculates how far each train is from your chosen crossing and logs when a train is about to pass. The most recent log entries can be uploaded to [Rentry](https://rentry.co/) for quick sharing.

## Features

- Finds crossing coordinates from a postcode using Nominatim.
- Polls the Signalbox API at a configurable interval.
- Estimates train arrival times using the haversine formula.
- Alerts when a train is within the configured margin.
- Writes a log file and optionally updates a Rentry paste.

## Requirements

- Python 3.8 or newer
- `requests`
- `beautifulsoup4`
- `geopy`

Install the dependencies with:

```bash
pip install requests beautifulsoup4 geopy
```

## Usage

Edit the constants at the top of `choochoowatch.py` to suit your location:

```python
POSTCODE = "CV1 4AR"      # Crossing postcode
MARGIN_SEC = 90            # Alert window in seconds
POLL_INTERVAL = 20         # How often to poll the API
```

Then run the script:

```bash
python choochoowatch.py
```

A short snippet of the output looks like:

```
📍 Monitoring crossing at (52.41217, -1.52129) (margin 90s)
Fetching train data from: https://map-api.production.signalbox.io/api/locations
Train data response code: 200
Retrieved 10 train location entries
⚠️ Train approaching in ~30s
```

The latest entries are stored in `choochoowatch.log`. If a Rentry paste is configured, the log is uploaded automatically.

## Disclaimer

This project is for demonstration purposes only. It is **not** intended for safety-critical use. Always observe proper railway safety guidelines.

