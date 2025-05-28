"""
Seed data for the Indian Cyber Incident Monitor database.
Run this script to populate the database with sample data.
"""

import sys
import logging
from datetime import datetime, timedelta
import random

from app import app, db
from models import Source, Incident, Tag, CrawlLog

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define sample data
SAMPLE_SOURCES = [
    {
        "name": "CERT-In",
        "url": "https://www.cert-in.org.in/",
        "source_type": "cert",
        "reliability_score": 0.95
    },
    {
        "name": "NCIIPC",
        "url": "https://nciipc.gov.in/",
        "source_type": "government",
        "reliability_score": 0.92
    },
    {
        "name": "The Hacker News",
        "url": "https://thehackernews.com/search/label/India",
        "source_type": "news",
        "reliability_score": 0.85
    },
    {
        "name": "CyberSecIndia Twitter",
        "url": "https://twitter.com/CyberSecIndia",
        "source_type": "twitter",
        "reliability_score": 0.75
    },
    {
        "name": "PwnDisclosures",
        "url": "https://pastebin.com/u/PwnDisclosures",
        "source_type": "pastebin",
        "reliability_score": 0.65
    }
]

SAMPLE_TAGS = [
    {"name": "phishing", "category": "attack_vector"},
    {"name": "ransomware", "category": "attack_vector"},
    {"name": "data_breach", "category": "impact"},
    {"name": "ddos", "category": "attack_vector"},
    {"name": "supply_chain", "category": "attack_vector"},
    {"name": "cve", "category": "vulnerability"},
    {"name": "zero_day", "category": "vulnerability"},
    {"name": "apt", "category": "threat_actor"},
    {"name": "critical_infrastructure", "category": "target"},
    {"name": "financial_loss", "category": "impact"}
]

SECTORS = [
    "Finance", "Healthcare", "Government", "Education", "Energy", 
    "IT/Technology", "Telecommunications", "Retail", "Manufacturing", 
    "Defense", "Transportation", "Critical Infrastructure"
]

SEVERITIES = ["Critical", "High", "Medium", "Low"]

THREAT_ACTORS = [
    "APT37", "Lazarus Group", "Confucius", "SideWinder", "Transparent Tribe", 
    "APT41", "TA456", "HAFNIUM", "Unknown Threat Actor", "DeathStalker"
]

SAMPLE_INCIDENTS = [
    {
        "title": "Major Ransomware Attack on Indian Healthcare Provider",
        "description": """A large healthcare provider in Delhi reported a sophisticated ransomware attack that compromised patient data and temporarily disabled critical systems. The attackers demanded a 50 BTC ransom payment and threatened to publish sensitive patient information. Hospital operations were severely impacted for 3 days.
        
        The attack vector appears to have been a phishing email with a malicious document that exploited a vulnerability in the hospital's outdated Windows systems. Security researchers have attributed this attack to a known ransomware group.
        
        This incident highlights ongoing vulnerabilities in India's healthcare sector and the need for improved cybersecurity measures and regular system updates.""",
        "severity": "Critical",
        "sector": "Healthcare",
        "actor": "DeathStalker",
        "target": "Metro Hospital Systems",
        "technique": "Phishing email leading to ransomware payload",
        "tags": ["ransomware", "phishing", "data_breach", "healthcare"]
    },
    {
        "title": "Data Breach at Major Indian Financial Institution",
        "description": """One of India's largest banks reported a significant data breach affecting approximately 3.7 million customers. The breach exposed personal information including names, account numbers, phone numbers, and in some cases, transaction histories.
        
        The breach was discovered during a routine security audit and is believed to have been ongoing for at least 3 months. Initial investigation suggests the attackers gained access through compromised employee credentials and a vulnerable API endpoint.
        
        This incident is one of the largest financial data breaches in India's history and has prompted the RBI to issue new security guidelines for the banking sector.""",
        "severity": "High",
        "sector": "Finance",
        "actor": "Unknown Threat Actor",
        "target": "National Banking Corporation",
        "technique": "Credential theft and API exploitation",
        "tags": ["data_breach", "financial_loss", "api_vulnerability"]
    },
    {
        "title": "DDoS Attack on Indian Government Websites",
        "description": """Multiple Indian government websites experienced a coordinated distributed denial-of-service (DDoS) attack, making them inaccessible for several hours. The attack targeted primarily Ministry of Defence and Home Affairs related domains.
        
        The attack peaked at approximately 2.5 Tbps, making it one of the largest DDoS attacks recorded against Indian government infrastructure. A threat actor group claimed responsibility on social media, citing political motivations.
        
        Government IT teams mitigated the attack by implementing traffic filtering and leveraging anti-DDoS services from their cloud providers.""",
        "severity": "High",
        "sector": "Government",
        "actor": "APT37",
        "target": "Government of India Websites",
        "technique": "Distributed Denial of Service (botnet)",
        "tags": ["ddos", "government", "critical_infrastructure"]
    },
    {
        "title": "Supply Chain Attack Targeting Indian IT Service Providers",
        "description": """A sophisticated supply chain attack was discovered affecting multiple Indian IT service providers that manage outsourced IT operations for various sectors. The attackers implanted backdoors in software updates that were then distributed to clients.
        
        The attack potentially affected hundreds of downstream customers across various industries. The malware was designed to exfiltrate specific data and establish persistent access for future exploitation.
        
        Security researchers attribute this campaign to a state-sponsored APT group known for targeting strategic commercial and government entities.""",
        "severity": "Critical",
        "sector": "IT/Technology",
        "actor": "APT41",
        "target": "Multiple IT Service Providers",
        "technique": "Software supply chain compromise",
        "tags": ["supply_chain", "apt", "backdoor"]
    },
    {
        "title": "Critical Vulnerability in Indian Payment Processing Systems",
        "description": """A critical vulnerability was discovered in a widely used payment processing system implemented across multiple Indian financial institutions. The vulnerability could allow attackers to manipulate transaction data or perform unauthorized transactions.
        
        The vulnerability (CVE-2024-34567) was reported responsibly through a bug bounty program and has been patched by the vendor. There is no evidence of exploitation in the wild, but the vulnerability affected approximately 70% of domestic payment processors.
        
        Financial regulatory authorities have issued an advisory requiring all affected institutions to apply the security patch within 48 hours.""",
        "severity": "High",
        "sector": "Finance",
        "actor": None,
        "target": "Payment Processing Infrastructure",
        "technique": "Application vulnerability exploitation",
        "tags": ["cve", "financial_loss", "zero_day"]
    },
    {
        "title": "Targeted Phishing Campaign Against Indian Energy Sector",
        "description": """A sophisticated spear-phishing campaign targeted senior executives and engineers at several Indian energy companies. The emails contained malicious documents that appeared to be regulatory compliance requirements from the Ministry of Power.
        
        The malware deployed in this campaign was designed to establish persistence, capture credentials, and exfiltrate sensitive documents related to power grid operations and infrastructure designs.
        
        This campaign shows similarities to previous operations attributed to threat actors targeting critical infrastructure in the region. Several organizations were compromised before the campaign was detected.""",
        "severity": "Critical",
        "sector": "Energy",
        "actor": "SideWinder",
        "target": "Energy Grid Operators",
        "technique": "Spear phishing with malicious attachments",
        "tags": ["phishing", "critical_infrastructure", "apt"]
    },
    {
        "title": "Data Exposure from Unsecured Cloud Database of Indian Telecom",
        "description": """An unsecured MongoDB database belonging to a major Indian telecommunications provider was discovered exposed on the internet. The database contained over 350 million customer records including names, addresses, phone numbers, and call detail records.
        
        The exposure was discovered by a security researcher who responsibly disclosed the issue. The database was secured within 24 hours of notification, but it had been exposed for approximately 14 days.
        
        This incident underscores the need for proper security configurations and regular audits of cloud resources, especially those containing sensitive customer data.""",
        "severity": "Medium",
        "sector": "Telecommunications",
        "actor": None,
        "target": "Major Telecom Provider",
        "technique": "Unsecured database exposure",
        "tags": ["data_breach", "misconfiguration", "cloud_security"]
    },
    {
        "title": "Website Defacement of Multiple Educational Institutions",
        "description": """Several prominent Indian universities and educational institutions had their websites defaced in a coordinated campaign. The attackers replaced the homepages with political messages and claimed to have exfiltrated internal data.
        
        The attacks exploited vulnerable Content Management Systems (CMS) that had not been updated with the latest security patches. While website defacement was the visible impact, investigators are examining whether the attackers gained access to internal systems or data.
        
        This campaign affected over 15 educational websites in a 48-hour period.""",
        "severity": "Medium",
        "sector": "Education",
        "actor": "Transparent Tribe",
        "target": "University Websites",
        "technique": "CMS vulnerability exploitation",
        "tags": ["website_defacement", "data_breach", "education"]
    },
    {
        "title": "Mobile Banking Trojan Targeting Indian Financial Apps",
        "description": """A new Android banking trojan specifically targeting Indian financial applications has been discovered in multiple apps on the Google Play Store. The malware, dubbed 'FinStealer', overlays fake login screens to steal credentials and can intercept SMS messages to bypass two-factor authentication.
        
        The malware-infected apps had been downloaded over 500,000 times before being removed from the Play Store. The trojan specifically targets 27 Indian banking and financial applications.
        
        Financial institutions have issued warnings to customers and recommended security measures including app verification and enabling additional authentication factors.""",
        "severity": "High",
        "sector": "Finance",
        "actor": "TA456",
        "target": "Mobile Banking Users",
        "technique": "Trojanized Android applications",
        "tags": ["malware", "mobile", "financial_loss"]
    },
    {
        "title": "Insider Threat at Indian Technology Company",
        "description": """A major Indian technology company reported an insider threat incident where a former employee exfiltrated proprietary source code and customer data before leaving the organization. The individual allegedly sold this information to competitors.
        
        The breach was discovered when portions of the source code appeared in a competitor's product. Forensic investigation revealed the exfiltration occurred over several months using personal cloud storage accounts.
        
        This incident highlights the importance of monitoring data movement and implementing proper offboarding procedures for employees with access to sensitive information.""",
        "severity": "Medium",
        "sector": "IT/Technology",
        "actor": None,
        "target": "Proprietary Technology",
        "technique": "Insider data exfiltration",
        "tags": ["insider_threat", "data_breach", "intellectual_property"]
    }
]


def create_sources():
    """Create sample sources"""
    logger.info("Creating sample sources...")
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
    logger.info(f"Created {len(sources)} sample sources")
    return sources


def create_tags():
    """Create sample tags"""
    logger.info("Creating sample tags...")
    tags = {}
    for tag_data in SAMPLE_TAGS:
        tag = Tag(
            name=tag_data["name"],
            category=tag_data["category"]
        )
        db.session.add(tag)
        tags[tag_data["name"]] = tag
    
    db.session.commit()
    logger.info(f"Created {len(tags)} sample tags")
    return tags


def create_incidents(sources, tags):
    """Create sample incidents"""
    logger.info("Creating sample incidents...")
    
    now = datetime.utcnow()
    incidents = []
    
    for i, incident_data in enumerate(SAMPLE_INCIDENTS):
        # Assign random discovery dates within the last 60 days
        days_ago = random.randint(1, 60)
        discovered_date = now - timedelta(days=days_ago)
        
        # Incident date is typically before discovery date
        incident_date = discovered_date - timedelta(days=random.randint(1, 5))
        
        # Pick a random source for this incident
        source = random.choice(sources)
        
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
        
        # Add tags to the incident
        incident_tag_names = incident_data.get("tags", [])
        for tag_name in incident_tag_names:
            if tag_name in tags:
                incident.tags.append(tags[tag_name])
        
        db.session.add(incident)
        incidents.append(incident)
    
    db.session.commit()
    logger.info(f"Created {len(incidents)} sample incidents")
    return incidents


def create_crawl_logs(sources):
    """Create sample crawl logs"""
    logger.info("Creating sample crawl logs...")
    
    now = datetime.utcnow()
    logs = []
    
    for source in sources:
        # Create 2-3 crawl logs for each source
        for _ in range(random.randint(2, 3)):
            # Random date within the last 15 days
            days_ago = random.randint(0, 15)
            start_time = now - timedelta(days=days_ago, 
                                        hours=random.randint(0, 23),
                                        minutes=random.randint(0, 59))
            
            # Crawl typically takes a few minutes
            end_time = start_time + timedelta(minutes=random.randint(3, 15))
            
            # Most crawls are successful
            status = random.choices(
                ["success", "failed", "in_progress"],
                weights=[0.8, 0.15, 0.05],
                k=1
            )[0]
            
            items_found = random.randint(5, 30)
            items_processed = items_found if status == "success" else random.randint(0, items_found)
            
            error_message = None
            if status == "failed":
                error_messages = [
                    "Connection timeout",
                    "Access denied (403)",
                    "Internal server error (500)",
                    "Rate limited by server",
                    "Network connection interrupted"
                ]
                error_message = random.choice(error_messages)
            
            log = CrawlLog(
                source_id=source.id,
                start_time=start_time,
                end_time=end_time if status != "in_progress" else None,
                status=status,
                items_found=items_found,
                items_processed=items_processed,
                error_message=error_message
            )
            
            db.session.add(log)
            logs.append(log)
    
    db.session.commit()
    logger.info(f"Created {len(logs)} sample crawl logs")
    return logs


def seed_database():
    """Main function to seed the database with sample data"""
    logger.info("Starting database seeding process...")
    
    try:
        # Check if we already have data
        existing_sources = Source.query.count()
        if existing_sources > 0:
            logger.info(f"Found {existing_sources} existing sources in the database.")
            logger.info("Deleting existing data...")
            # Delete in proper order to respect foreign keys
            CrawlLog.query.delete()
            Incident.query.delete()
            Source.query.delete()
            Tag.query.delete()
            db.session.commit()
        
        # Create sample data
        sources = create_sources()
        tags = create_tags()
        incidents = create_incidents(sources, tags)
        logs = create_crawl_logs(sources)
        
        logger.info("Database seeding completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error seeding database: {str(e)}")
        db.session.rollback()
        return False


if __name__ == "__main__":
    with app.app_context():
        success = seed_database()
        sys.exit(0 if success else 1)