import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from sqlalchemy import func, desc

from app import db
from models import Incident, Source, Tag
from utils.nlp_processor import is_relevant_to_india, extract_entities, classify_incident
from ml.source_classifier import predict_source_relevance

logger = logging.getLogger(__name__)

api = Blueprint('api', __name__)

@api.route('/api/incidents')
def get_incidents():
    """
    API endpoint to get incidents
    """
    # Get filter parameters
    sector = request.args.get('sector')
    severity = request.args.get('severity')
    days = request.args.get('days', type=int)
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    # Start with all incidents query
    query = Incident.query
    
    # Apply filters
    if sector:
        query = query.filter(Incident.sector == sector)
    
    if severity:
        query = query.filter(Incident.severity == severity)
    
    if days:
        date_filter = datetime.utcnow() - timedelta(days=days)
        query = query.filter(Incident.discovered_date >= date_filter)
    
    # Get total count for pagination
    total = query.count()
    
    # Apply pagination
    incidents = query.order_by(Incident.discovered_date.desc()).limit(limit).offset(offset).all()
    
    # Format the response
    result = {
        'total': total,
        'limit': limit,
        'offset': offset,
        'incidents': []
    }
    
    for incident in incidents:
        result['incidents'].append({
            'id': incident.id,
            'title': incident.title,
            'description': incident.description[:200] + '...' if incident.description and len(incident.description) > 200 else incident.description,
            'sector': incident.sector,
            'severity': incident.severity,
            'actor': incident.actor,
            'target': incident.target,
            'incident_date': incident.incident_date.isoformat() if incident.incident_date else None,
            'discovered_date': incident.discovered_date.isoformat() if incident.discovered_date else None,
            'confidence_score': incident.confidence_score
        })
    
    return jsonify(result)

@api.route('/api/incident/<int:id>')
def get_incident(id):
    """
    API endpoint to get a specific incident
    """
    incident = Incident.query.get_or_404(id)
    
    result = {
        'id': incident.id,
        'title': incident.title,
        'description': incident.description,
        'sector': incident.sector,
        'severity': incident.severity,
        'actor': incident.actor,
        'target': incident.target,
        'technique': incident.technique,
        'incident_date': incident.incident_date.isoformat() if incident.incident_date else None,
        'discovered_date': incident.discovered_date.isoformat() if incident.discovered_date else None,
        'source_url': incident.source_url,
        'confidence_score': incident.confidence_score,
        'is_verified': incident.is_verified,
        'source': {
            'id': incident.source.id,
            'name': incident.source.name,
            'type': incident.source.source_type
        } if incident.source else None,
        'tags': [{'id': tag.id, 'name': tag.name} for tag in incident.tags]
    }
    
    return jsonify(result)

@api.route('/api/sectors')
def get_sectors():
    """
    API endpoint to get all sectors with incident counts
    """
    sector_counts = db.session.query(
        Incident.sector, func.count(Incident.id).label('count')
    ).group_by(Incident.sector).order_by(desc('count')).all()
    
    result = [{
        'sector': sector[0] or 'Unknown',
        'count': sector[1]
    } for sector in sector_counts]
    
    return jsonify(result)

@api.route('/api/severities')
def get_severities():
    """
    API endpoint to get all severities with incident counts
    """
    severity_counts = db.session.query(
        Incident.severity, func.count(Incident.id).label('count')
    ).group_by(Incident.severity).all()
    
    result = [{
        'severity': severity[0] or 'Unknown',
        'count': severity[1]
    } for severity in severity_counts]
    
    return jsonify(result)

@api.route('/api/analyze_text', methods=['POST'])
def analyze_text():
    """
    API endpoint to analyze text for Indian cybersecurity relevance
    """
    if not request.json or 'text' not in request.json:
        return jsonify({'error': 'Text is required'}), 400
    
    text = request.json['text']
    
    # Check if the text is relevant to India
    is_relevant = is_relevant_to_india(text)
    
    # If not relevant, return early
    if not is_relevant:
        return jsonify({
            'is_relevant_to_india': False,
            'message': 'Text does not appear to be related to Indian cyberspace'
        })
    
    # Extract entities
    entities = extract_entities(text)
    
    # Classify the incident
    classification = classify_incident(text)
    
    # Combine the results
    result = {
        'is_relevant_to_india': True,
        'entities': entities,
        'classification': classification
    }
    
    return jsonify(result)

@api.route('/api/check_source', methods=['POST'])
def check_source():
    """
    API endpoint to check if a source is relevant for Indian cybersecurity
    """
    if not request.json or 'url' not in request.json:
        return jsonify({'error': 'URL is required'}), 400
    
    url = request.json['url']
    text = request.json.get('text', '')
    
    # Predict source relevance
    is_relevant, confidence = predict_source_relevance(url, text)
    
    result = {
        'is_relevant': bool(is_relevant),
        'confidence': confidence,
        'message': 'This source appears to be relevant for Indian cybersecurity monitoring' if is_relevant else 'This source does not appear to be focused on Indian cybersecurity'
    }
    
    return jsonify(result)
