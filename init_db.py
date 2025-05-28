"""
Simple script to initialize the database with minimal data
"""

from datetime import datetime, timedelta
import random
from app import app, db
from models import Source, Incident, Tag, CrawlLog

# Define minimal sample data
SAMPLE_SOURCES = [
    {
        "name": "CERT-In",
        "url": "https://www.cert-in.org.in/",
        "source_type": "cert",
        "reliability_score": 0.95
    },
    {
        "name": "The Hacker News",
        "url": "https://thehackernews.com/search/label/India",
        "source_type": "news",
        "reliability_score": 0.85
    }
]

SAMPLE_TAGS = [
    {"name": "ransomware", "category": "attack_vector"},
    {"name": "data_breach", "category": "impact"},
    {"name": "ddos", "category": "attack_vector"}
]

SAMPLE_INCIDENTS = [
    {
        "title": "Major Ransomware Attack on Indian Healthcare Provider",
        "description": "A large healthcare provider reported a ransomware attack that compromised patient data.",
        "severity": "Critical",
        "sector": "Healthcare",
        "actor": "Unknown",
        "target": "Healthcare Systems",
        "technique": "Phishing email",
        "tags": ["ransomware"]
    },
    {
        "title": "Data Breach at Major Indian Financial Institution",
        "description": "A bank reported a significant data breach affecting approximately 3.7 million customers.",
        "severity": "High",
        "sector": "Finance",
        "actor": "Unknown",
        "target": "National Banking Corporation",
        "technique": "API exploitation",
        "tags": ["data_breach"]
    },
    {
        "title": "DDoS Attack on Indian Government Websites",
        "description": "Multiple government websites experienced a coordinated DDoS attack.",
        "severity": "High",
        "sector": "Government",
        "actor": "Unknown",
        "target": "Government Websites",
        "technique": "Distributed Denial of Service",
        "tags": ["ddos"]
    }
]

def init_db():
    """Initialize the database with sample data"""
    print("Initializing database...")
    
    # Clear existing data
    print("Clearing existing data...")
    CrawlLog.query.delete()
    Incident.query.delete()
    Tag.query.delete()
    Source.query.delete()
    db.session.commit()
    
    # Create sources
    print("Creating sources...")
    sources = []
    for source_data in SAMPLE_SOURCES:
        source = Source(
            name=source_data["name"],
            url=source_data["url"],
            source_type=source_data["source_type"],
            reliability_score=source_data["reliability_score"],
            is_active=True
        )
        db.session.add(source)
        sources.append(source)
    
    db.session.commit()
    
    # Create tags
    print("Creating tags...")
    tags = {}
    for tag_data in SAMPLE_TAGS:
        tag = Tag(
            name=tag_data["name"],
            category=tag_data["category"]
        )
        db.session.add(tag)
        tags[tag_data["name"]] = tag
    
    db.session.commit()
    
    # Create incidents
    print("Creating incidents...")
    now = datetime.utcnow()
    incidents = []
    
    for i, incident_data in enumerate(SAMPLE_INCIDENTS):
        # Assign discovery dates within the last 30 days
        days_ago = random.randint(1, 30)
        discovered_date = now - timedelta(days=days_ago)
        
        # Incident date is before discovery date
        incident_date = discovered_date - timedelta(days=random.randint(1, 5))
        
        # Pick a source
        source = sources[i % len(sources)]
        
        # Create the incident
        incident = Incident(
            title=incident_data["title"],
            description=incident_data["description"],
            incident_date=incident_date,
            discovered_date=discovered_date,
            severity=incident_data["severity"],
            sector=incident_data["sector"],
            actor=incident_data["actor"],
            target=incident_data["target"],
            technique=incident_data["technique"],
            source_id=source.id,
            source_url=f"{source.url}incident{i}",
            confidence_score=random.uniform(0.65, 0.95),
            is_verified=random.choice([True, False])
        )
        
        # Add tags
        for tag_name in incident_data.get("tags", []):
            if tag_name in tags:
                incident.tags.append(tags[tag_name])
        
        db.session.add(incident)
        incidents.append(incident)
    
    db.session.commit()
    
    print(f"Database initialized with {len(sources)} sources, {len(tags)} tags, and {len(incidents)} incidents.")

if __name__ == "__main__":
    with app.app_context():
        init_db()