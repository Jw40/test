from functools import wraps

from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from ratemynews.extensions import db
from ratemynews.forms import JournalistForm
from ratemynews.models import AdminAuditLog, Flag, Journalist, Rating

admin_bp = Blueprint("admin", __name__)


def admin_required(func):
    @wraps(func)
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return func(*args, **kwargs)

    return wrapper


def log_action(action: str, target_type: str, target_id: int):
    entry = AdminAuditLog(
        admin_user_id=current_user.id,
        action=action,
        target_type=target_type,
        target_id=target_id,
    )
    db.session.add(entry)


@admin_bp.route("/")
@admin_required
def dashboard():
    flags = Flag.query.filter_by(resolved=False).order_by(Flag.created_at.desc()).all()
    logs = AdminAuditLog.query.order_by(AdminAuditLog.created_at.desc()).limit(30).all()
    journalists = Journalist.query.order_by(Journalist.created_at.desc()).all()
    return render_template("admin/dashboard.html", flags=flags, logs=logs, journalists=journalists)


@admin_bp.route("/journalists/new", methods=["GET", "POST"])
@admin_required
def create_journalist():
    form = JournalistForm()
    if form.validate_on_submit():
        journalist = Journalist(
            full_name=form.full_name.data,
            outlet=form.outlet.data,
            beat=form.beat.data,
            location=form.location.data,
            bio=form.bio.data,
            profile_photo_url=form.profile_photo_url.data,
        )
        db.session.add(journalist)
        db.session.flush()
        log_action("create_journalist", "journalist", journalist.id)
        db.session.commit()
        flash("Journalist created.", "success")
        return redirect(url_for("admin.dashboard"))
    return render_template("admin/journalist_form.html", form=form, title="New Journalist")


@admin_bp.route("/journalists/<int:journalist_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_journalist(journalist_id: int):
    journalist = Journalist.query.get_or_404(journalist_id)
    form = JournalistForm(obj=journalist)
    if form.validate_on_submit():
        form.populate_obj(journalist)
        log_action("edit_journalist", "journalist", journalist.id)
        db.session.commit()
        flash("Journalist updated.", "success")
        return redirect(url_for("admin.dashboard"))
    return render_template("admin/journalist_form.html", form=form, title="Edit Journalist")


@admin_bp.route("/ratings/<int:rating_id>/toggle", methods=["POST"])
@admin_required
def toggle_rating(rating_id: int):
    rating = Rating.query.get_or_404(rating_id)
    rating.is_removed = not rating.is_removed
    action = "restore_rating" if not rating.is_removed else "remove_rating"
    log_action(action, "rating", rating.id)
    db.session.commit()
    flash("Rating visibility updated.", "info")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/flags/<int:flag_id>/resolve", methods=["POST"])
@admin_required
def resolve_flag(flag_id: int):
    flag = Flag.query.get_or_404(flag_id)
    flag.resolved = True
    flag.resolved_by = current_user.id
    log_action("resolve_flag", "flag", flag.id)
    db.session.commit()
    flash("Flag resolved.", "success")
    return redirect(url_for("admin.dashboard"))
