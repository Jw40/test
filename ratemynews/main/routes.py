from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

from flask import Blueprint, render_template, request
from sqlalchemy import func

from ratemynews.models import Journalist, Rating

main_bp = Blueprint("main", __name__)

NEWS_FEEDS = {
    "BBC World": "https://feeds.bbci.co.uk/news/world/rss.xml",
    "NPR News": "https://feeds.npr.org/1001/rss.xml",
    "Reuters World": "https://feeds.reuters.com/Reuters/worldNews",
    "CBS World": "https://www.cbsnews.com/latest/rss/world",
    "AP Top News": "https://feeds.apnews.com/apf-topnews",
    "NYTimes World": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
}


def parse_pub_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = parsedate_to_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (TypeError, ValueError):
        return None


def _get_creator(item: ET.Element) -> str:
    # Try RSS dc:creator first
    for child in list(item):
        if child.tag.endswith("creator") and child.text:
            return child.text.strip()
    return (item.findtext("author") or "").strip()


def extract_feed_items(xml_text: str, source: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    items: list[dict] = []

    for item in root.findall(".//item"):
        title = (item.findtext("title") or "Untitled").strip()
        link = (item.findtext("link") or "#").strip()
        summary = (item.findtext("description") or "").strip()
        raw_date = item.findtext("pubDate")
        author = _get_creator(item)
        items.append(
            {
                "title": title,
                "url": link,
                "summary": summary,
                "source": source,
                "author": author,
                "published_at": parse_pub_date(raw_date),
                "published_raw": raw_date,
            }
        )

    atom_ns = "{http://www.w3.org/2005/Atom}"
    for entry in root.findall(f".//{atom_ns}entry"):
        title = (entry.findtext(f"{atom_ns}title") or "Untitled").strip()
        link_el = entry.find(f"{atom_ns}link")
        link = link_el.attrib.get("href", "#") if link_el is not None else "#"
        summary = (entry.findtext(f"{atom_ns}summary") or "").strip()
        raw_date = entry.findtext(f"{atom_ns}updated") or entry.findtext(f"{atom_ns}published")
        author = (entry.findtext(f"{atom_ns}author/{atom_ns}name") or "").strip()
        items.append(
            {
                "title": title,
                "url": link,
                "summary": summary,
                "source": source,
                "author": author,
                "published_at": parse_pub_date(raw_date),
                "published_raw": raw_date,
            }
        )

    return items


def fetch_news(selected_sources: list[str], limit: int = 30) -> list[dict]:
    items: list[dict] = []
    for source in selected_sources:
        feed_url = NEWS_FEEDS.get(source)
        if not feed_url:
            continue
        try:
            req = Request(feed_url, headers={"User-Agent": "RateMyNews/1.0"})
            with urlopen(req, timeout=12) as response:
                xml_text = response.read().decode("utf-8", errors="ignore")
            items.extend(extract_feed_items(xml_text, source))
        except Exception:
            continue

    items.sort(
        key=lambda i: i["published_at"] or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    return items[:limit]


@main_bp.route("/")
def home():
    q = request.args.get("q", "").strip()
    outlet = request.args.get("outlet", "").strip()
    beat = request.args.get("beat", "").strip()

    query = Journalist.query
    if q:
        query = query.filter(Journalist.full_name.ilike(f"%{q}%"))
    if outlet:
        query = query.filter(Journalist.outlet == outlet)
    if beat:
        query = query.filter(Journalist.beat == beat)

    journalists = query.order_by(Journalist.full_name.asc()).all()

    top_rated = (
        Journalist.query.join(Rating)
        .group_by(Journalist.id)
        .order_by(func.avg(Rating.score).desc())
        .limit(5)
        .all()
    )
    most_reviewed = (
        Journalist.query.join(Rating)
        .group_by(Journalist.id)
        .order_by(func.count(Rating.id).desc())
        .limit(5)
        .all()
    )

    outlets = [x[0] for x in Journalist.query.with_entities(Journalist.outlet).distinct().order_by(Journalist.outlet).all()]
    beats = [x[0] for x in Journalist.query.with_entities(Journalist.beat).distinct().order_by(Journalist.beat).all()]

    return render_template(
        "main/home.html",
        journalists=journalists,
        top_rated=top_rated,
        most_reviewed=most_reviewed,
        outlets=outlets,
        beats=beats,
        q=q,
        outlet=outlet,
        beat=beat,
    )


@main_bp.route("/news")
def news_portal():
    selected_sources = request.args.getlist("source") or list(NEWS_FEEDS.keys())
    limit = request.args.get("limit", default=30, type=int)
    limit = max(5, min(100, limit))
    items = fetch_news(selected_sources, limit=limit)

    return render_template(
        "main/news.html",
        items=items,
        feeds=NEWS_FEEDS,
        selected_sources=selected_sources,
        limit=limit,
    )
