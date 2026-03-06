from datetime import datetime, timedelta, timezone

from ratemynews.extensions import db
from ratemynews.main.routes import extract_feed_items
from ratemynews.models import Journalist, JournalistVote, Rating, User
from ratemynews.utils import contains_doxxing


def create_user_and_journalist(email='u1@example.com', username='u1'):
    user = User(username=username, email=email)
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


def test_extract_feed_items_from_rss_with_author():
    xml = """
    <rss xmlns:dc="http://purl.org/dc/elements/1.1/"><channel>
      <item>
        <title>Headline A</title>
        <link>https://example.com/a</link>
        <description>Summary A</description>
        <dc:creator>Reporter A</dc:creator>
        <pubDate>Mon, 03 Mar 2025 10:00:00 GMT</pubDate>
      </item>
    </channel></rss>
    """
    items = extract_feed_items(xml, "Example")
    assert len(items) == 1
    assert items[0]["title"] == "Headline A"
    assert items[0]["author"] == "Reporter A"


def test_upsert_thumb_vote(app):
    with app.app_context():
        user, journalist = create_user_and_journalist()
        vote = JournalistVote(journalist_id=journalist.id, user_id=user.id, value=1)
        db.session.add(vote)
        db.session.commit()

        existing = JournalistVote.query.filter_by(journalist_id=journalist.id, user_id=user.id).first()
        existing.value = -1
        db.session.commit()

        assert JournalistVote.query.count() == 1
        assert JournalistVote.query.first().value == -1
