from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ratemynews import create_app
from ratemynews.extensions import db
from ratemynews.models import Article, Flag, Journalist, Rating, User

app = create_app()

# Australia + world-leading mainstream outlets only.
SEED_JOURNALISTS = [
    {
        "full_name": "Laura Tingle",
        "outlet": "ABC News",
        "beat": "Politics",
        "location": "Canberra, AU",
        "bio": "Covers federal politics and public policy for ABC News.",
        "profile_photo_url": "https://via.placeholder.com/300x200?text=Laura+Tingle",
        "article_title": "Budget pressures shape Canberra policy agenda",
    },
    {
        "full_name": "Antony Green",
        "outlet": "ABC News",
        "beat": "Elections",
        "location": "Sydney, AU",
        "bio": "Election analyst focused on voting trends and polling interpretation.",
        "profile_photo_url": "https://via.placeholder.com/300x200?text=Antony+Green",
        "article_title": "State-by-state swing analysis ahead of federal vote",
    },
    {
        "full_name": "Kumi Taguchi",
        "outlet": "SBS News",
        "beat": "Society",
        "location": "Melbourne, AU",
        "bio": "Reports on social affairs, multicultural communities, and policy impact.",
        "profile_photo_url": "https://via.placeholder.com/300x200?text=Kumi+Taguchi",
        "article_title": "Migration reforms and what they mean for employers",
    },
    {
        "full_name": "Shane Wright",
        "outlet": "The Sydney Morning Herald",
        "beat": "Economy",
        "location": "Sydney, AU",
        "bio": "Economic correspondent covering inflation, rates, and labour data.",
        "profile_photo_url": "https://via.placeholder.com/300x200?text=Shane+Wright",
        "article_title": "Reserve Bank signals caution as inflation eases",
    },
    {
        "full_name": "Nick Bonyhady",
        "outlet": "The Age",
        "beat": "Climate",
        "location": "Melbourne, AU",
        "bio": "Covers climate policy, adaptation, and environmental accountability.",
        "profile_photo_url": "https://via.placeholder.com/300x200?text=Nick+Bonyhady",
        "article_title": "Heatwave resilience plans tested across major cities",
    },
    {
        "full_name": "Paul Karp",
        "outlet": "The Guardian Australia",
        "beat": "National",
        "location": "Canberra, AU",
        "bio": "National affairs reporter focused on transparency and governance.",
        "profile_photo_url": "https://via.placeholder.com/300x200?text=Paul+Karp",
        "article_title": "Parliament scrutiny intensifies over housing package",
    },
    {
        "full_name": "Phil Coorey",
        "outlet": "AFR",
        "beat": "Business",
        "location": "Sydney, AU",
        "bio": "Business and policy reporting focused on markets and regulation.",
        "profile_photo_url": "https://via.placeholder.com/300x200?text=Phil+Coorey",
        "article_title": "ASX firms prepare for tighter disclosure requirements",
    },
    {
        "full_name": "Andrew Probyn",
        "outlet": "9News",
        "beat": "National",
        "location": "Canberra, AU",
        "bio": "Political editor reporting on federal leadership and legislation.",
        "profile_photo_url": "https://via.placeholder.com/300x200?text=Andrew+Probyn",
        "article_title": "Cabinet weighs cost-of-living relief package",
    },
    {
        "full_name": "Nakia Sargeant",
        "outlet": "7NEWS",
        "beat": "World",
        "location": "Sydney, AU",
        "bio": "World news correspondent covering international affairs for Australian audiences.",
        "profile_photo_url": "https://via.placeholder.com/300x200?text=Nakia+Sargeant",
        "article_title": "Regional security talks focus on Indo-Pacific coordination",
    },
    {
        "full_name": "Idrees Ali",
        "outlet": "Reuters",
        "beat": "International",
        "location": "Washington, US",
        "bio": "Covers global security and diplomacy for Reuters.",
        "profile_photo_url": "https://via.placeholder.com/300x200?text=Idrees+Ali",
        "article_title": "Global leaders seek agreement on shipping security",
    },
    {
        "full_name": "Lyse Doucet",
        "outlet": "BBC News",
        "beat": "World",
        "location": "London, UK",
        "bio": "International correspondent reporting from conflict and diplomatic fronts.",
        "profile_photo_url": "https://via.placeholder.com/300x200?text=Lyse+Doucet",
        "article_title": "Diplomatic push continues amid renewed ceasefire talks",
    },
    {
        "full_name": "Aamer Madhani",
        "outlet": "Associated Press",
        "beat": "Politics",
        "location": "Washington, US",
        "bio": "Covers leadership summits and international policy decisions.",
        "profile_photo_url": "https://via.placeholder.com/300x200?text=Aamer+Madhani",
        "article_title": "Leaders outline joint plan on energy and supply chains",
    },
]


with app.app_context():
    db.create_all()

    if not User.query.filter_by(email='admin@ratemynews.local').first():
        admin = User(username='admin', email='admin@ratemynews.local', is_admin=True)
        admin.set_password('adminpass123')
        db.session.add(admin)
        db.session.commit()

    # Remove old seeded/non-mainstream content to keep the DB focused.
    Flag.query.delete()
    Rating.query.delete()
    Article.query.delete()
    Journalist.query.delete()
    db.session.commit()

    for index, payload in enumerate(SEED_JOURNALISTS, start=1):
        journalist = Journalist(
            full_name=payload["full_name"],
            outlet=payload["outlet"],
            beat=payload["beat"],
            location=payload["location"],
            bio=payload["bio"],
            profile_photo_url=payload["profile_photo_url"],
        )
        db.session.add(journalist)
        db.session.flush()

        article_url = f"https://example.com/au-world-seed-article-{index}"
        db.session.add(
            Article(
                journalist_id=journalist.id,
                title=payload["article_title"],
                url=article_url,
                outlet=payload["outlet"],
            )
        )

    db.session.commit()
    print(f"Seed complete. Inserted {len(SEED_JOURNALISTS)} mainstream AU/world journalists and matching articles.")
