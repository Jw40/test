from urllib.parse import urlparse

from flask import Blueprint, current_app, flash, redirect, request, url_for, render_template
from flask_login import current_user, login_required
from sqlalchemy import func

from ratemynews import limiter
from ratemynews.extensions import db
from ratemynews.forms import FlagForm, RatingForm
from ratemynews.models import Article, Flag, Journalist, JournalistVote, Rating
from ratemynews.utils import contains_doxxing, contains_profanity

journalists_bp = Blueprint("journalists", __name__)


@journalists_bp.route("/<int:journalist_id>", methods=["GET", "POST"])
def profile(journalist_id: int):
    journalist = Journalist.query.get_or_404(journalist_id)
    form = RatingForm()
    sort = request.args.get("sort", "newest")
    page = request.args.get("page", 1, type=int)

    ratings_query = Rating.query.filter_by(journalist_id=journalist.id, is_removed=False)
    if sort == "highest":
        ratings_query = ratings_query.order_by(Rating.score.desc(), Rating.created_at.desc())
    elif sort == "lowest":
        ratings_query = ratings_query.order_by(Rating.score.asc(), Rating.created_at.desc())
    else:
        ratings_query = ratings_query.order_by(Rating.created_at.desc())

    ratings = ratings_query.paginate(page=page, per_page=10, error_out=False)

    averages = db.session.query(
        func.avg(Rating.score),
        func.avg(Rating.accuracy),
        func.avg(Rating.sourcing),
        func.avg(Rating.fairness),
        func.avg(Rating.transparency),
        func.count(Rating.id),
    ).filter_by(journalist_id=journalist.id, is_removed=False).first()

    distribution = {
        score: Rating.query.filter_by(journalist_id=journalist.id, score=score, is_removed=False).count()
        for score in range(1, 6)
    }

    return render_template(
        "journalists/profile.html",
        journalist=journalist,
        ratings=ratings,
        form=form,
        sort=sort,
        averages=averages,
        distribution=distribution,
        flag_form=FlagForm(),
    )


@journalists_bp.route("/from-news", methods=["POST"])
@login_required
def create_from_news():
    full_name = (request.form.get("author") or "").strip()
    article_title = (request.form.get("title") or "Untitled article").strip()
    article_url = (request.form.get("url") or "").strip()
    outlet = (request.form.get("outlet") or "Unknown Outlet").strip()

    if not full_name or full_name.lower() in {"unknown", "staff", "admin"}:
        flash("This article has no clear journalist author to create a profile from.", "warning")
        return redirect(url_for("main.news_portal"))

    journalist = Journalist.query.filter_by(full_name=full_name, outlet=outlet).first()
    if not journalist:
        journalist = Journalist(
            full_name=full_name,
            outlet=outlet,
            beat="General",
            bio="Profile auto-created from a news article. Please update details.",
        )
        db.session.add(journalist)
        db.session.flush()

    if article_url:
        existing = Article.query.filter_by(url=article_url).first()
        if not existing:
            parsed = urlparse(article_url)
            article = Article(
                journalist_id=journalist.id,
                title=article_title,
                url=article_url,
                outlet=parsed.netloc or outlet,
            )
            db.session.add(article)

    db.session.commit()
    flash(f"Journalist profile ready: {journalist.full_name}", "success")
    return redirect(url_for("journalists.profile", journalist_id=journalist.id))


@journalists_bp.route("/<int:journalist_id>/thumb/<string:direction>", methods=["POST"])
@login_required
def thumb_vote(journalist_id: int, direction: str):
    journalist = Journalist.query.get_or_404(journalist_id)
    if direction not in {"up", "down"}:
        flash("Invalid vote type.", "danger")
        return redirect(url_for("journalists.profile", journalist_id=journalist.id))

    value = 1 if direction == "up" else -1
    vote = JournalistVote.query.filter_by(journalist_id=journalist.id, user_id=current_user.id).first()
    if vote:
        vote.value = value
    else:
        vote = JournalistVote(journalist_id=journalist.id, user_id=current_user.id, value=value)
        db.session.add(vote)

    db.session.commit()
    flash("Your thumbs vote was saved.", "success")
    return redirect(url_for("journalists.profile", journalist_id=journalist.id))


@journalists_bp.route("/<int:journalist_id>/rate", methods=["POST"])
@login_required
@limiter.limit(lambda: str(current_app.config.get("RATINGS_PER_MINUTE", "5/minute")))
def add_rating(journalist_id: int):
    journalist = Journalist.query.get_or_404(journalist_id)
    form = RatingForm()
    if not form.validate_on_submit():
        flash("Please correct form errors.", "danger")
        return redirect(url_for("journalists.profile", journalist_id=journalist.id))

    if not Rating.can_user_rate(current_user.id, journalist.id):
        flash("You can rate this journalist only once every 24 hours.", "warning")
        return redirect(url_for("journalists.profile", journalist_id=journalist.id))

    comment = (form.comment.data or "").strip()
    if comment and contains_profanity(comment):
        flash("Comment rejected: please avoid abusive language.", "danger")
        return redirect(url_for("journalists.profile", journalist_id=journalist.id))
    if comment and contains_doxxing(comment):
        flash("Comment rejected: personal identifying information is not allowed.", "danger")
        return redirect(url_for("journalists.profile", journalist_id=journalist.id))

    article = None
    article_url = (form.article_url.data or "").strip()
    if article_url:
        parsed = urlparse(article_url)
        outlet = parsed.netloc or None
        article = Article.query.filter_by(url=article_url).first()
        if not article:
            article = Article(
                journalist_id=journalist.id,
                title=(form.article_title.data or "Linked article").strip(),
                url=article_url,
                outlet=outlet,
            )
            db.session.add(article)
            db.session.flush()

    rating = Rating(
        journalist_id=journalist.id,
        user_id=current_user.id,
        score=form.score.data,
        accuracy=form.accuracy.data,
        sourcing=form.sourcing.data,
        fairness=form.fairness.data,
        transparency=form.transparency.data,
        article_id=article.id if article else None,
        comment=comment or None,
    )
    db.session.add(rating)
    db.session.commit()

    flash("Thanks for your evidence-based feedback.", "success")
    return redirect(url_for("journalists.profile", journalist_id=journalist.id))


@journalists_bp.route("/ratings/<int:rating_id>/flag", methods=["POST"])
@login_required
def flag_rating(rating_id: int):
    rating = Rating.query.get_or_404(rating_id)
    form = FlagForm()
    if not form.validate_on_submit():
        flash("Flag reason is required.", "danger")
        return redirect(url_for("journalists.profile", journalist_id=rating.journalist_id))

    flag = Flag(rating_id=rating.id, user_id=current_user.id, reason=form.reason.data)
    db.session.add(flag)
    db.session.commit()

    flash("Rating reported for moderator review.", "info")
    return redirect(url_for("journalists.profile", journalist_id=rating.journalist_id))
