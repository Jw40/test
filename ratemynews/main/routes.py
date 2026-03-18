import random

from flask import Blueprint, render_template, request, session
from sqlalchemy import func

from ratemynews.models import Article, Journalist, Rating

main_bp = Blueprint("main", __name__)

# In-memory aggregate guessing stats keyed by article id.
GUESS_STATS: dict[int, dict[str, int]] = {}

# Popular mainstream publishers relevant to Australian audiences.
MAINSTREAM_AU_OUTLETS = {
    "ABC News",
    "SBS News",
    "The Sydney Morning Herald",
    "The Age",
    "The Australian",
    "The Guardian Australia",
    "AFR",
    "9News",
    "7NEWS",
}


def _article_outlet(article: Article) -> str | None:
    if article.outlet:
        return article.outlet
    if article.journalist and article.journalist.outlet:
        return article.journalist.outlet
    return None


def _is_mainstream_au_outlet(outlet: str | None) -> bool:
    return bool(outlet and outlet in MAINSTREAM_AU_OUTLETS)


def _build_guess_question() -> dict | None:
    articles = Article.query.join(Journalist).all()
    eligible_articles = [article for article in articles if _is_mainstream_au_outlet(_article_outlet(article))]
    if not eligible_articles:
        return None

    chosen_article = random.choice(eligible_articles)
    correct_outlet = _article_outlet(chosen_article)
    if not correct_outlet:
        return None

    outlet_pool = {
        _article_outlet(article)
        for article in eligible_articles
        if _article_outlet(article) and _article_outlet(article) != correct_outlet
    }
    distractors = random.sample(list(outlet_pool), k=min(3, len(outlet_pool)))
    options = distractors + [correct_outlet]
    random.shuffle(options)

    return {
        "article_id": chosen_article.id,
        "title": chosen_article.title,
        "correct_outlet": correct_outlet,
        "options": options,
    }


def _record_guess(article_id: int, is_correct: bool) -> dict[str, float | int]:
    if article_id not in GUESS_STATS:
        GUESS_STATS[article_id] = {"attempts": 0, "correct": 0}

    GUESS_STATS[article_id]["attempts"] += 1
    if is_correct:
        GUESS_STATS[article_id]["correct"] += 1

    attempts = GUESS_STATS[article_id]["attempts"]
    correct = GUESS_STATS[article_id]["correct"]

    return {
        "attempts": attempts,
        "average_correct": round((correct / attempts) * 100, 1),
    }


def _record_guess(article_id: int, is_correct: bool) -> dict[str, float | int]:
    if article_id not in GUESS_STATS:
        GUESS_STATS[article_id] = {"attempts": 0, "correct": 0}

    GUESS_STATS[article_id]["attempts"] += 1
    if is_correct:
        GUESS_STATS[article_id]["correct"] += 1

    attempts = GUESS_STATS[article_id]["attempts"]
    correct = GUESS_STATS[article_id]["correct"]

    return {
        "attempts": attempts,
        "average_correct": round((correct / attempts) * 100, 1),
    }


@main_bp.route("/", methods=["GET", "POST"])
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

    feedback = None

    if request.method == "GET" and request.args.get("new_round") == "1":
        session.pop("guess_question", None)

    question = session.get("guess_question")
    if not question:
        question = _build_guess_question()
        session["guess_question"] = question

    if request.method == "POST":
        game_action = request.form.get("game_action", "guess")
        if game_action == "new_round":
            session.pop("guess_question", None)
            question = _build_guess_question()
            session["guess_question"] = question
        elif question:
            picked_outlet = request.form.get("picked_outlet", "")
            if picked_outlet in question["options"]:
                is_correct = picked_outlet == question["correct_outlet"]
                aggregate = _record_guess(question["article_id"], is_correct=is_correct)
                feedback = {
                    "is_correct": is_correct,
                    "picked_outlet": picked_outlet,
                    "correct_outlet": question["correct_outlet"],
                    **aggregate,
                }

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
        question=question,
        feedback=feedback,
    )


@main_bp.route("/guessing-game", methods=["GET", "POST"])
def guessing_game():
    feedback = None

    if request.method == "GET" and request.args.get("new_round") == "1":
        session.pop("guess_question", None)

    question = session.get("guess_question")
    if not question:
        question = _build_guess_question()
        session["guess_question"] = question

    if request.method == "POST":
        game_action = request.form.get("game_action", "guess")
        if game_action == "new_round":
            session.pop("guess_question", None)
            question = _build_guess_question()
            session["guess_question"] = question
        elif question:
            picked_outlet = request.form.get("picked_outlet", "")
            if picked_outlet in question["options"]:
                is_correct = picked_outlet == question["correct_outlet"]
                aggregate = _record_guess(question["article_id"], is_correct=is_correct)
                feedback = {
                    "is_correct": is_correct,
                    "picked_outlet": picked_outlet,
                    "correct_outlet": question["correct_outlet"],
                    **aggregate,
                }

    return render_template(
        "main/guessing_game.html",
        question=question,
        feedback=feedback,
        mainstream_outlets=sorted(MAINSTREAM_AU_OUTLETS),
    )
