# RateMyNews

RateMyNews is a Flask web app for constructive journalist profiles and ratings, now with a built-in free news portal.

## Keep it simple (DB)
- Default DB is SQLite (`ratemynews.db`).
- App auto-creates tables on startup via `db.create_all()` (no migration step required for local use).
- You can still switch DB using `DATABASE_URL` if needed.

## Core features
- Live `/news` page aggregating free feeds from **6 sources** (BBC, NPR, Reuters, CBS, AP, NYTimes).
- Create journalist profiles directly from news articles when an author is present.
- Thumbs up / thumbs down rating on each journalist profile.
- Optional detailed 1-5 rating dimensions with comments.

## Setup and run (main mode)
```bash
git clone <repo-url>
cd test
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Open:
- Home: `http://127.0.0.1:5000/`
- News: `http://127.0.0.1:5000/news`

## Optional seed
```bash
python scripts/seed.py
```

Admin created by seed:
- email: `admin@ratemynews.local`
- password: `adminpass123`

## Tests
```bash
pytest -q
```

## Project structure
```
.
├── ratemynews/
│   ├── __init__.py
│   ├── models.py
│   ├── main/routes.py
│   ├── journalists/routes.py
│   ├── auth/routes.py
│   ├── admin/routes.py
│   ├── templates/
│   └── static/
├── tests/
├── scripts/seed.py
├── run.py
└── requirements.txt
```
