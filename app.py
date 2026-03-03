from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any
import xml.etree.ElementTree as ET

import requests
from flask import Flask, render_template, request

app = Flask(__name__)

# Free public RSS feeds (no API key required)
FEEDS: dict[str, str] = {
    "BBC World": "https://feeds.bbci.co.uk/news/world/rss.xml",
    "Reuters World": "https://feeds.reuters.com/Reuters/worldNews",
    "NPR": "https://feeds.npr.org/1004/rss.xml",
}


def parse_date(raw_date: str | None) -> datetime | None:
    """Parse common RSS date formats into timezone-aware datetime."""
    if not raw_date:
        return None

    try:
        dt = parsedate_to_datetime(raw_date)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (TypeError, ValueError):
        return None


def extract_items(xml_content: str, source_name: str) -> list[dict[str, Any]]:
    """Extract RSS items from both RSS and Atom formats."""
    root = ET.fromstring(xml_content)
    items: list[dict[str, Any]] = []

    # RSS format
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "Untitled").strip()
        link = (item.findtext("link") or "#").strip()
        description = (item.findtext("description") or "").strip()
        pub_raw = item.findtext("pubDate")
        published_at = parse_date(pub_raw)
        items.append(
            {
                "title": title,
                "url": link,
                "summary": description,
                "published_at": published_at,
                "published_raw": pub_raw,
                "source": source_name,
            }
        )

    # Atom format (fallback)
    atom_ns = "{http://www.w3.org/2005/Atom}"
    for entry in root.findall(f".//{atom_ns}entry"):
        title = (entry.findtext(f"{atom_ns}title") or "Untitled").strip()
        link_el = entry.find(f"{atom_ns}link")
        link = link_el.attrib.get("href", "#") if link_el is not None else "#"
        summary = (
            (entry.findtext(f"{atom_ns}summary") or entry.findtext(f"{atom_ns}content") or "")
            .strip()
        )
        pub_raw = entry.findtext(f"{atom_ns}updated") or entry.findtext(f"{atom_ns}published")
        published_at = parse_date(pub_raw)
        items.append(
            {
                "title": title,
                "url": link,
                "summary": summary,
                "published_at": published_at,
                "published_raw": pub_raw,
                "source": source_name,
            }
        )

    return items


def fetch_news(selected_sources: list[str], limit: int = 30) -> list[dict[str, Any]]:
    """Fetch and merge news items from selected RSS feeds."""
    all_items: list[dict[str, Any]] = []

    for source in selected_sources:
        feed_url = FEEDS.get(source)
        if not feed_url:
            continue

        try:
            response = requests.get(feed_url, timeout=12)
            response.raise_for_status()
            all_items.extend(extract_items(response.text, source))
        except (requests.RequestException, ET.ParseError):
            # Ignore unreachable or malformed feeds to keep portal responsive
            continue

    all_items.sort(
        key=lambda item: item["published_at"] or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )

    return all_items[:limit]


@app.route("/")
def index() -> str:
    selected_sources = request.args.getlist("source") or list(FEEDS.keys())
    limit = request.args.get("limit", default=30, type=int)
    limit = max(5, min(limit, 100))

    news_items = fetch_news(selected_sources=selected_sources, limit=limit)
    now = datetime.now(timezone.utc)

    return render_template(
        "index.html",
        feeds=FEEDS,
        selected_sources=selected_sources,
        limit=limit,
        news_items=news_items,
        now=now,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
