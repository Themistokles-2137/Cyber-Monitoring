from datetime import datetime
from app import db

# Association table for many-to-many relationships
incident_tags = db.Table('incident_tags',
    db.Column('incident_id', db.Integer, db.ForeignKey('incident.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

class Source(db.Model):
    """
    Represents a source of cyber incident information
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    source_type = db.Column(db.String(50), nullable=False)  # news, twitter, pastebin, etc.
    reliability_score = db.Column(db.Float, default=0.0)  # 0-1 score of source reliability
    last_crawled = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    incidents = db.relationship('Incident', backref='source', lazy=True)
    
    def __repr__(self):
        return f"<Source {self.name}>"

class Incident(db.Model):
    """
    Represents a cyber incident
    """
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    incident_date = db.Column(db.DateTime, nullable=True)
    discovered_date = db.Column(db.DateTime, default=datetime.utcnow)
    severity = db.Column(db.String(20), nullable=True)  # critical, high, medium, low
    sector = db.Column(db.String(100), nullable=True)  # finance, healthcare, government, etc.
    actor = db.Column(db.String(100), nullable=True)  # APT group or threat actor if known
    target = db.Column(db.String(255), nullable=True)  # target organization or system
    technique = db.Column(db.String(255), nullable=True)  # MITRE ATT&CK technique if applicable
    source_id = db.Column(db.Integer, db.ForeignKey('source.id'), nullable=False)
    source_url = db.Column(db.String(255), nullable=True)  # Direct URL to the incident report
    confidence_score = db.Column(db.Float, default=0.5)  # ML confidence in classification
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tags = db.relationship('Tag', secondary=incident_tags, lazy='subquery',
                           backref=db.backref('incidents', lazy=True))
    
    def __repr__(self):
        return f"<Incident {self.title}>"

class Tag(db.Model):
    """
    Tags for categorizing incidents
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    category = db.Column(db.String(50), nullable=True)  # attack_vector, impact, etc.
    
    def __repr__(self):
        return f"<Tag {self.name}>"

class CrawlLog(db.Model):
    """
    Log of crawling activities
    """
    id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.Integer, db.ForeignKey('source.id'), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default="in_progress")  # success, failed, in_progress
    items_found = db.Column(db.Integer, default=0)
    items_processed = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text, nullable=True)
    
    # Relationships
    source = db.relationship('Source', backref='crawl_logs')
    
    def __repr__(self):
        return f"<CrawlLog {self.id} - {self.source.name}>"

class MLModel(db.Model):
    """
    Stores information about trained ML models
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    model_type = db.Column(db.String(50), nullable=False)  # source_classifier, incident_classifier, etc.
    version = db.Column(db.String(20), nullable=False)
    accuracy = db.Column(db.Float, nullable=True)
    f1_score = db.Column(db.Float, nullable=True)
    training_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f"<MLModel {self.name} v{self.version}>"
