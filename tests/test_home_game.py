from ratemynews.extensions import db
from ratemynews.models import Article, Journalist


def _seed_articles():
    j1 = Journalist(full_name='A One', outlet='Outlet One', beat='World')
    j2 = Journalist(full_name='B Two', outlet='Outlet Two', beat='Politics')
    db.session.add_all([j1, j2])
    db.session.flush()

    a1 = Article(journalist_id=j1.id, title='Headline One', url='https://example.com/one', outlet='Outlet One')
    a2 = Article(journalist_id=j2.id, title='Headline Two', url='https://example.com/two', outlet='Outlet Two')
    db.session.add_all([a1, a2])
    db.session.commit()


def test_home_shows_guessing_game(app):
    with app.app_context():
        _seed_articles()

    client = app.test_client()
    response = client.get('/')

    assert response.status_code == 200
    assert b'Headline Guessing Game' in response.data


def test_home_guess_submission_returns_feedback(app):
    with app.app_context():
        _seed_articles()

    client = app.test_client()
    client.get('/')

    with client.session_transaction() as sess:
        question = sess.get('guess_question')

    assert question is not None
    picked_outlet = question['options'][0]

    response = client.post('/', data={'game_action': 'guess', 'picked_outlet': picked_outlet})

    assert response.status_code == 200
    assert b'Crowd average for this headline' in response.data
