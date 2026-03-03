# Flask Free News Aggregator

A simple Python Flask web portal that aggregates headlines from free public RSS feeds (no API key required).

## Features
- Aggregates from BBC, Reuters, and NPR RSS feeds.
- Filter by source.
- Adjust headline count (5-100).
- Sorts items by most recent publication date.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then open: <http://localhost:5000>
