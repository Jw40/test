from ratemynews import create_app
from ratemynews.extensions import db
from ratemynews.models import Article, Journalist, User

app = create_app()

with app.app_context():
    db.create_all()

    if not User.query.filter_by(email='admin@ratemynews.local').first():
        admin = User(username='admin', email='admin@ratemynews.local', is_admin=True)
        admin.set_password('adminpass123')
        db.session.add(admin)

    if Journalist.query.count() == 0:
        j1 = Journalist(
            full_name='Aisha Khan',
            outlet='Global Daily',
            beat='Politics',
            location='New York',
            bio='Covers public policy and elections with a focus on verification practices.',
            profile_photo_url='https://via.placeholder.com/300x200?text=Aisha+Khan',
        )
        j2 = Journalist(
            full_name='Daniel Ortega',
            outlet='City Herald',
            beat='Investigations',
            location='Chicago',
            bio='Investigative reporter focused on local accountability and public records.',
            profile_photo_url='https://via.placeholder.com/300x200?text=Daniel+Ortega',
        )
        db.session.add_all([j1, j2])
        db.session.flush()
        db.session.add_all(
            [
                Article(journalist_id=j1.id, title='Election data deep dive', url='https://example.com/article-1', outlet='Global Daily'),
                Article(journalist_id=j2.id, title='Public contracts explained', url='https://example.com/article-2', outlet='City Herald'),
            ]
        )

    db.session.commit()
    print('Seed complete.')
