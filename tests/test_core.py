from datetime import datetime, timedelta, timezone

from ratemynews.extensions import db
from ratemynews.models import Journalist, Rating, User
from ratemynews.utils import contains_doxxing


def create_user_and_journalist():
    user = User(username='u1', email='u1@example.com')
    user.set_password('password123')
    journalist = Journalist(full_name='Jane Doe', outlet='NewsNet', beat='Science')
    db.session.add_all([user, journalist])
    db.session.commit()
    return user, journalist


def test_create_journalist(app):
    with app.app_context():
        j = Journalist(full_name='Test Reporter', outlet='OutletX', beat='World')
        db.session.add(j)
        db.session.commit()
        assert Journalist.query.count() == 1


def test_post_rating(app):
    with app.app_context():
        user, journalist = create_user_and_journalist()
        rating = Rating(journalist_id=journalist.id, user_id=user.id, score=4, accuracy=4, sourcing=5, fairness=4, transparency=4)
        db.session.add(rating)
        db.session.commit()
        assert Rating.query.count() == 1


def test_enforce_24_hour_rule(app):
    with app.app_context():
        user, journalist = create_user_and_journalist()
        recent = Rating(journalist_id=journalist.id, user_id=user.id, score=4, accuracy=4, sourcing=4, fairness=4, transparency=4)
        recent.created_at = datetime.now(timezone.utc) - timedelta(hours=2)
        db.session.add(recent)
        db.session.commit()
        assert Rating.can_user_rate(user.id, journalist.id) is False


def test_block_doxxing_pattern():
    assert contains_doxxing('Call me at 555-123-4567') is True
    assert contains_doxxing('This reporting was balanced and sourced well.') is False
