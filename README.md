# RateMyNews

RateMyNews is a Flask web app for constructive, evidence-based journalist ratings.

## Stack
- Python 3.10+
- Flask + SQLAlchemy + Flask-Migrate
- Flask-Login, WTForms, Bootstrap 5
- SQLite (dev), Postgres-ready via `DATABASE_URL`

## Correct project structure
```
.
├── ratemynews/
│   ├── __init__.py
│   ├── config.py
│   ├── extensions.py
│   ├── models.py
│   ├── forms.py
│   ├── utils.py
│   ├── auth/routes.py
│   ├── main/routes.py
│   ├── journalists/routes.py
│   ├── admin/routes.py
│   ├── templates/
│   └── static/
├── scripts/seed.py
├── tests/test_core.py
├── conftest.py
├── run.py
└── requirements.txt
```

## Features
- News page (`/news`) that aggregates free public RSS feeds (BBC, NPR, Reuters)
- Auth: register/login/logout + user profile history
- Home: search journalists, filter by outlet/beat, top-rated and most-reviewed
- Journalist profile: dimension stats, ratings distribution, sortable/paginated ratings
- Rating rules: 1 rating per user per journalist per 24h, profanity filter, doxxing detection, rate limiting
- Flagging: report ratings for admin review
- Admin: journalist CRUD, flag resolution, remove/restore ratings, audit log

## Setup
```bash
git clone <repo-url>
cd test
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Database & migrations
```bash
export FLASK_APP=run.py
# Optional Postgres:
# export DATABASE_URL=postgresql+psycopg://user:pass@localhost/ratemynews
flask db init
flask db migrate -m "initial schema"
flask db upgrade
```

## Run
```bash
flask run
# or
python run.py
```

After starting, open:
- Ratings app: `http://127.0.0.1:5000/`
- News feed: `http://127.0.0.1:5000/news`


## Seed sample data
```bash
python scripts/seed.py
```

Creates sample journalists, articles, and an admin user:
- email: `admin@ratemynews.local`
- password: `adminpass123`

## Tests
```bash
pytest -q
```

## Screenshot placeholders
- Home page: `docs/screenshots/home.png`
- Journalist profile: `docs/screenshots/journalist-profile.png`
- Admin dashboard: `docs/screenshots/admin-dashboard.png`
