from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any
import os
import random
import xml.etree.ElementTree as ET

import requests
from flask import Flask, render_template, request, session

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-guessing-game-secret")

# Free public RSS feeds (no API key required)
FEEDS: dict[str, str] = {
    "BBC World": "https://feeds.bbci.co.uk/news/world/rss.xml",
    "Reuters World": "https://feeds.reuters.com/Reuters/worldNews",
    "NPR": "https://feeds.npr.org/1004/rss.xml",
}

# In-memory aggregate guessing stats shared by all visitors.
GUESS_STATS: dict[str, dict[str, int]] = {}


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


def _build_question(selected_sources: list[str]) -> dict[str, Any] | None:
    """Create one guessing-game round from live headlines."""
    usable_sources = [source for source in selected_sources if source in FEEDS]
    if len(usable_sources) < 2:
        usable_sources = list(FEEDS.keys())

    news_items = fetch_news(selected_sources=usable_sources, limit=40)
    candidate_items = [item for item in news_items if item.get("source") in usable_sources]
    if not candidate_items:
        return None

    chosen_item = random.choice(candidate_items)
    return {
        "title": chosen_item["title"],
        "url": chosen_item["url"],
        "published_at": chosen_item["published_at"],
        "published_raw": chosen_item["published_raw"],
        "correct_source": chosen_item["source"],
        "options": sorted(usable_sources),
    }


def _stats_key(question: dict[str, Any]) -> str:
    return f"{question['title']}::{question['correct_source']}"


def _record_guess(question: dict[str, Any], selected_source: str) -> dict[str, Any]:
    """Record a guess and return result payload for UI feedback."""
    stats_key = _stats_key(question)
    is_correct = selected_source == question["correct_source"]

    if stats_key not in GUESS_STATS:
        GUESS_STATS[stats_key] = {"attempts": 0, "correct": 0}

    GUESS_STATS[stats_key]["attempts"] += 1
    if is_correct:
        GUESS_STATS[stats_key]["correct"] += 1

    attempts = GUESS_STATS[stats_key]["attempts"]
    correct = GUESS_STATS[stats_key]["correct"]
    average_correct = round((correct / attempts) * 100, 1)

    return {
        "is_correct": is_correct,
        "selected_source": selected_source,
        "correct_source": question["correct_source"],
        "average_correct": average_correct,
        "attempts": attempts,
    }


@app.route("/", methods=["GET", "POST"])
def index() -> str:
    selected_sources = request.values.getlist("source") or list(FEEDS.keys())
    selected_sources = [source for source in selected_sources if source in FEEDS]
    if len(selected_sources) < 2:
        selected_sources = list(FEEDS.keys())

    feedback = None

    if request.method == "GET" and request.args.get("next") == "1":
        session.pop("current_question", None)

    question = session.get("current_question")
    if not question:
        question = _build_question(selected_sources)
        session["current_question"] = question

    if request.method == "POST" and question:
        picked_source = request.form.get("picked_source", "")
        if picked_source in question["options"]:
            feedback = _record_guess(question, picked_source)

    now = datetime.now(timezone.utc)

    return render_template(
        "index.html",
        feeds=FEEDS,
        selected_sources=selected_sources,
        question=question,
        feedback=feedback,
        now=now,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
