from sqlalchemy import func
from flask import Blueprint, render_template, request

from ratemynews.models import Journalist, Rating

main_bp = Blueprint("main", __name__)


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
