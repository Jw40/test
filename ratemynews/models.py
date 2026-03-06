from __future__ import annotations

from datetime import datetime, timedelta, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from ratemynews.extensions import db, login_manager


class TimestampMixin:
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class User(UserMixin, TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    ratings = db.relationship("Rating", back_populates="user", lazy=True)
    votes = db.relationship("JournalistVote", back_populates="user", lazy=True, cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(user_id: str):
    return User.query.get(int(user_id))


class Journalist(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(200), nullable=False, index=True)
    outlet = db.Column(db.String(200), nullable=False, index=True)
    beat = db.Column(db.String(120), nullable=False, index=True)
    location = db.Column(db.String(120), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    profile_photo_url = db.Column(db.String(500), nullable=True)

    articles = db.relationship("Article", back_populates="journalist", lazy=True, cascade="all, delete-orphan")
    ratings = db.relationship("Rating", back_populates="journalist", lazy=True, cascade="all, delete-orphan")
    votes = db.relationship("JournalistVote", back_populates="journalist", lazy=True, cascade="all, delete-orphan")

    @property
    def thumbs_up(self) -> int:
        return sum(1 for vote in self.votes if vote.value == 1)

    @property
    def thumbs_down(self) -> int:
        return sum(1 for vote in self.votes if vote.value == -1)


class Article(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    journalist_id = db.Column(db.Integer, db.ForeignKey("journalist.id"), nullable=False)
    title = db.Column(db.String(300), nullable=False)
    url = db.Column(db.String(500), nullable=False, unique=True)
    published_at = db.Column(db.DateTime(timezone=True), nullable=True)
    outlet = db.Column(db.String(200), nullable=True)

    journalist = db.relationship("Journalist", back_populates="articles")
    ratings = db.relationship("Rating", back_populates="article", lazy=True)


class JournalistVote(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    journalist_id = db.Column(db.Integer, db.ForeignKey("journalist.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    value = db.Column(db.Integer, nullable=False)

    journalist = db.relationship("Journalist", back_populates="votes")
    user = db.relationship("User", back_populates="votes")

    __table_args__ = (
        db.CheckConstraint("value IN (-1, 1)", name="vote_value_check"),
        db.UniqueConstraint("journalist_id", "user_id", name="uq_vote_user_journalist"),
    )


class Rating(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    journalist_id = db.Column(db.Integer, db.ForeignKey("journalist.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    accuracy = db.Column(db.Integer, nullable=False)
    sourcing = db.Column(db.Integer, nullable=False)
    fairness = db.Column(db.Integer, nullable=False)
    transparency = db.Column(db.Integer, nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey("article.id"), nullable=True)
    comment = db.Column(db.String(500), nullable=True)
    is_removed = db.Column(db.Boolean, default=False, nullable=False)

    journalist = db.relationship("Journalist", back_populates="ratings")
    user = db.relationship("User", back_populates="ratings")
    article = db.relationship("Article", back_populates="ratings")
    flags = db.relationship("Flag", back_populates="rating", lazy=True, cascade="all, delete-orphan")

    __table_args__ = (
        db.CheckConstraint("score >= 1 AND score <= 5", name="score_range"),
        db.CheckConstraint("accuracy >= 1 AND accuracy <= 5", name="accuracy_range"),
        db.CheckConstraint("sourcing >= 1 AND sourcing <= 5", name="sourcing_range"),
        db.CheckConstraint("fairness >= 1 AND fairness <= 5", name="fairness_range"),
        db.CheckConstraint("transparency >= 1 AND transparency <= 5", name="transparency_range"),
    )

    @staticmethod
    def can_user_rate(user_id: int, journalist_id: int) -> bool:
        latest = (
            Rating.query.filter_by(user_id=user_id, journalist_id=journalist_id)
            .order_by(Rating.created_at.desc())
            .first()
        )
        if not latest:
            return True

        latest_created_at = latest.created_at
        if latest_created_at.tzinfo is None:
            latest_created_at = latest_created_at.replace(tzinfo=timezone.utc)

        return datetime.now(timezone.utc) - latest_created_at >= timedelta(hours=24)


class Flag(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rating_id = db.Column(db.Integer, db.ForeignKey("rating.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    reason = db.Column(db.String(500), nullable=False)
    resolved = db.Column(db.Boolean, default=False, nullable=False)
    resolved_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)

    rating = db.relationship("Rating", back_populates="flags", foreign_keys=[rating_id])
    reporter = db.relationship("User", foreign_keys=[user_id])
    resolver = db.relationship("User", foreign_keys=[resolved_by])


class AdminAuditLog(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admin_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    action = db.Column(db.String(255), nullable=False)
    target_type = db.Column(db.String(64), nullable=False)
    target_id = db.Column(db.Integer, nullable=False)
