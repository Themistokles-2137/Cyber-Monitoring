import os

# Flask configuration
DEBUG = True
SECRET_KEY = os.environ.get("SESSION_SECRET", "default_secret_key_for_development")
DB_PATH = os.environ.get("DATABASE_URL", "sqlite:///cyber_incidents.db")

# Scraping configuration
SCRAPE_INTERVAL_MINUTES = 60  # How often to scrape sources
MAX_SOURCES_PER_RUN = 20  # Maximum number of sources to process in one run
USER_AGENT = "CyberIncidentMonitor/1.0 (Research Project for NCIIPC India)"

# ML model configuration
MODEL_PATH = "ml/models"
SOURCE_CLASSIFIER_MODEL = "source_classifier.pkl"
INCIDENT_CLASSIFIER_MODEL = "incident_classifier.pkl"
RETRAIN_INTERVAL_DAYS = 7  # How often to retrain models

# NLP configuration
MAX_TEXT_LENGTH = 10000  # Maximum text length to process
LANGUAGE = "en"  # Default language for NLP processing
STOP_WORDS_FILE = "utils/data/stop_words.txt"

# India-specific keywords to look for in content
INDIA_KEYWORDS = [
    "India", "Indian", "भारत", "भारतीय", "Bharat", "Bharatiya", 
    "New Delhi", "Mumbai", "Bangalore", "Bengaluru", "Chennai", "Kolkata", 
    "Hyderabad", "Ahmedabad", "Pune", "CERT-In", "NCIIPC", "NIC", "CDAC",
    "Indian government", "Indian ministry", "Indian cybersecurity",
    "Aadhaar", "UPI", "BHIM", "DigiLocker", "MyGov", "UMANG", "IRCTC",
    "Indian critical infrastructure", "Indian banking", "Indian telecom",
    "Indian energy sector", "Indian power grid"
]

# Cybersecurity threat keywords
THREAT_KEYWORDS = [
    "cyber attack", "data breach", "malware", "ransomware", "phishing",
    "vulnerability", "exploit", "zero-day", "backdoor", "DDoS", "APT",
    "hack", "leaked", "compromise", "threat actor", "CVE", "cyber espionage",
    "cyber crime", "information theft", "data leak", "security incident",
    "intrusion", "botnet", "trojan", "spyware", "wiper", "credential theft"
]

# Source platforms to monitor
DEFAULT_SOURCES = [
    # News sources
    {"name": "The Hindu Tech", "url": "https://www.thehindu.com/sci-tech/technology/", "source_type": "news"},
    {"name": "Times of India Tech", "url": "https://timesofindia.indiatimes.com/technology", "source_type": "news"},
    {"name": "Economic Times Tech", "url": "https://economictimes.indiatimes.com/tech", "source_type": "news"},
    {"name": "NDTV Tech", "url": "https://www.ndtv.com/technology", "source_type": "news"},
    {"name": "India Today Tech", "url": "https://www.indiatoday.in/technology", "source_type": "news"},
    
    # Cybersecurity news
    {"name": "The Hacker News", "url": "https://thehackernews.com/", "source_type": "news"},
    {"name": "Bleeping Computer", "url": "https://www.bleepingcomputer.com/", "source_type": "news"},
    {"name": "Krebs on Security", "url": "https://krebsonsecurity.com/", "source_type": "news"},
    {"name": "Security Affairs", "url": "https://securityaffairs.co/", "source_type": "news"},
    
    # CERT and government sources
    {"name": "CERT-In", "url": "https://www.cert-in.org.in/", "source_type": "cert"},
    {"name": "NCIIPC", "url": "https://nciipc.gov.in/", "source_type": "government"},
    
    # Pastebin-like sites
    {"name": "Pastebin", "url": "https://pastebin.com/archive", "source_type": "pastesite"},
    {"name": "Github Gist", "url": "https://gist.github.com/discover", "source_type": "pastesite"},
]

# Categories for incidents
INCIDENT_SECTORS = [
    "Government", "Finance", "Healthcare", "Energy", "Transportation",
    "Telecom", "Information Technology", "Manufacturing", "Defense",
    "Education", "E-commerce", "Media", "Other"
]

INCIDENT_SEVERITY = [
    "Critical", "High", "Medium", "Low", "Informational"
]
