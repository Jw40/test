from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ratemynews import create_app
from ratemynews.extensions import db
from ratemynews.models import Article, Journalist, User

app = create_app()

JOURNALISTS = [
    {
        "full_name": "Aisha Khan",
        "outlet": "Global Daily",
        "beat": "Politics",
        "location": "New York, NY",
        "bio": "Covers public policy and elections with a focus on verification practices.",
        "profile_photo_url": "https://via.placeholder.com/300x200?text=Aisha+Khan",
        "article_title": "Election data deep dive",
    },
    {
        "full_name": "Daniel Ortega",
        "outlet": "City Herald",
        "beat": "Investigations",
        "location": "Chicago, IL",
        "bio": "Investigative reporter focused on local accountability and public records.",
        "profile_photo_url": "https://via.placeholder.com/300x200?text=Daniel+Ortega",
        "article_title": "Public contracts explained",
    },
    {
        "full_name": "Mei Lin",
        "outlet": "Pacific Ledger",
        "beat": "Technology",
        "location": "San Francisco, CA",
        "bio": "Reports on AI, privacy, and platform policy with source-first explainers.",
        "profile_photo_url": "https://via.placeholder.com/300x200?text=Mei+Lin",
        "article_title": "How states regulate AI procurement",
    },
    {
        "full_name": "Jordan Price",
        "outlet": "Metro Tribune",
        "beat": "Education",
        "location": "Austin, TX",
        "bio": "Follows K-12 funding and classroom outcomes across urban districts.",
        "profile_photo_url": "https://via.placeholder.com/300x200?text=Jordan+Price",
        "article_title": "Tracking literacy gains district by district",
    },
    {
        "full_name": "Elena Petrova",
        "outlet": "World Dispatch",
        "beat": "International",
        "location": "Washington, DC",
        "bio": "Analyzes diplomacy and conflict with open-source evidence and timelines.",
        "profile_photo_url": "https://via.placeholder.com/300x200?text=Elena+Petrova",
        "article_title": "Inside the latest ceasefire framework",
    },
    {
        "full_name": "Noah Bennett",
        "outlet": "Great Lakes Post",
        "beat": "Environment",
        "location": "Detroit, MI",
        "bio": "Covers water quality, climate adaptation, and regional infrastructure risk.",
        "profile_photo_url": "https://via.placeholder.com/300x200?text=Noah+Bennett",
        "article_title": "Mapping flood risk across the lakeshore",
    },
    {
        "full_name": "Priya Raman",
        "outlet": "Capital Journal",
        "beat": "Healthcare",
        "location": "Boston, MA",
        "bio": "Reports on hospital systems, public health metrics, and medical policy.",
        "profile_photo_url": "https://via.placeholder.com/300x200?text=Priya+Raman",
        "article_title": "Why ER wait times keep climbing",
    },
    {
        "full_name": "Marcus Reed",
        "outlet": "Southern Sentinel",
        "beat": "Justice",
        "location": "Atlanta, GA",
        "bio": "Focuses on courts, prosecution data, and sentencing disparities.",
        "profile_photo_url": "https://via.placeholder.com/300x200?text=Marcus+Reed",
        "article_title": "What new bail rules changed this year",
    },
    {
        "full_name": "Sofia Alvarez",
        "outlet": "Sunline News",
        "beat": "Housing",
        "location": "Miami, FL",
        "bio": "Tracks rent trends, zoning debates, and housing affordability.",
        "profile_photo_url": "https://via.placeholder.com/300x200?text=Sofia+Alvarez",
        "article_title": "Condo market correction explained",
    },
    {
        "full_name": "Ethan Wallace",
        "outlet": "Mountain Press",
        "beat": "Energy",
        "location": "Denver, CO",
        "bio": "Covers utilities, transmission projects, and the economics of renewables.",
        "profile_photo_url": "https://via.placeholder.com/300x200?text=Ethan+Wallace",
        "article_title": "Can battery storage stabilize summer demand?",
    },
    {
        "full_name": "Layla Hassan",
        "outlet": "National Wire",
        "beat": "Economy",
        "location": "New York, NY",
        "bio": "Explains inflation, labor data, and household economic pressures.",
        "profile_photo_url": "https://via.placeholder.com/300x200?text=Layla+Hassan",
        "article_title": "Small business hiring after rate changes",
    },
    {
        "full_name": "Gabe Thompson",
        "outlet": "Heartland Record",
        "beat": "Agriculture",
        "location": "Des Moines, IA",
        "bio": "Reports on crop markets, farm policy, and rural broadband access.",
        "profile_photo_url": "https://via.placeholder.com/300x200?text=Gabe+Thompson",
        "article_title": "How drought planning is changing corn yields",
    },
    {
        "full_name": "Naomi Sato",
        "outlet": "Harbor Review",
        "beat": "Transportation",
        "location": "Seattle, WA",
        "bio": "Covers ports, freight bottlenecks, and major transit projects.",
        "profile_photo_url": "https://via.placeholder.com/300x200?text=Naomi+Sato",
        "article_title": "Transit reliability after schedule redesign",
    },
    {
        "full_name": "Rafael Costa",
        "outlet": "Desert Times",
        "beat": "Water",
        "location": "Phoenix, AZ",
        "bio": "Investigates groundwater policy and long-term drought resilience.",
        "profile_photo_url": "https://via.placeholder.com/300x200?text=Rafael+Costa",
        "article_title": "Who controls groundwater in fast-growing suburbs?",
    },
    {
        "full_name": "Claire Dubois",
        "outlet": "North Star News",
        "beat": "Public Safety",
        "location": "Minneapolis, MN",
        "bio": "Tracks emergency response metrics and community safety initiatives.",
        "profile_photo_url": "https://via.placeholder.com/300x200?text=Claire+Dubois",
        "article_title": "Response-time disparities across neighborhoods",
    },
]

with app.app_context():
    db.create_all()

    if not User.query.filter_by(email='admin@ratemynews.local').first():
        admin = User(username='admin', email='admin@ratemynews.local', is_admin=True)
        admin.set_password('adminpass123')
        db.session.add(admin)

    existing = {j.full_name: j for j in Journalist.query.all()}
    created_count = 0

    for index, payload in enumerate(JOURNALISTS, start=1):
        journalist = existing.get(payload["full_name"])
        if not journalist:
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
            existing[payload["full_name"]] = journalist
            created_count += 1

        article_url = f"https://example.com/seed-article-{index}"
        if not Article.query.filter_by(url=article_url).first():
            db.session.add(
                Article(
                    journalist_id=journalist.id,
                    title=payload["article_title"],
                    url=article_url,
                    outlet=payload["outlet"],
                )
            )

    db.session.commit()
    print(f"Seed complete. Added {created_count} journalists. Total journalists: {Journalist.query.count()}.")
