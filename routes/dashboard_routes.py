import logging
from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify
from sqlalchemy import func, desc, cast, Date, extract

from app import db
from models import Incident, Source, CrawlLog

logger = logging.getLogger(__name__)

dashboard = Blueprint('dashboard', __name__)

@dashboard.route('/dashboard')
def index():
    """
    Main dashboard page
    """
    # Get basic stats
    total_incidents = Incident.query.count()
    
    # Incidents in the last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_count = Incident.query.filter(Incident.discovered_date >= thirty_days_ago).count()
    
    # Count by severity
    severity_counts = db.session.query(
        Incident.severity, func.count(Incident.id).label('count')
    ).group_by(Incident.severity).all()
    
    # Count by sector
    sector_counts = db.session.query(
        Incident.sector, func.count(Incident.id).label('count')
    ).group_by(Incident.sector).order_by(desc('count')).all()
    
    # Get source stats
    source_counts = db.session.query(
        Source.name, func.count(Incident.id).label('count')
    ).join(Incident, Incident.source_id == Source.id
    ).group_by(Source.name).order_by(desc('count')).limit(10).all()
    
    # Get trend data for the last 90 days - Fixed for SQLite compatibility
    ninety_days_ago = datetime.utcnow() - timedelta(days=90)
    try:
        daily_counts = db.session.query(
            func.date(Incident.discovered_date).label('date'),
            func.count(Incident.id).label('count')
        ).filter(Incident.discovered_date >= ninety_days_ago
        ).group_by(func.date(Incident.discovered_date)).order_by(func.date(Incident.discovered_date)).all()
    except Exception as e:
        # Fallback if date functions don't work
        daily_counts = []
    
    # Format the trend data for Chart.js
    trend_dates = []
    trend_counts = []
    
    for d in daily_counts:
        try:
            if isinstance(d[0], str):
                trend_dates.append(d[0])
            else:
                trend_dates.append(d[0].strftime('%Y-%m-%d'))
            trend_counts.append(d[1])
        except:
            continue
    
    # Recent high severity incidents
    high_severity_incidents = Incident.query.filter(
        Incident.severity.in_(['Critical', 'High'])
    ).order_by(Incident.discovered_date.desc()).limit(5).all()
    
    return render_template('dashboard.html',
                          total_incidents=total_incidents,
                          recent_count=recent_count,
                          severity_counts=severity_counts,
                          sector_counts=sector_counts,
                          source_counts=source_counts,
                          trend_dates=trend_dates,
                          trend_counts=trend_counts,
                          high_severity_incidents=high_severity_incidents)

@dashboard.route('/dashboard/sector_distribution')
def sector_distribution():
    """
    Get sector distribution data for charts
    """
    # Count by sector
    sector_counts = db.session.query(
        Incident.sector, func.count(Incident.id).label('count')
    ).group_by(Incident.sector).order_by(desc('count')).all()
    
    # Format for Chart.js
    sectors = [s[0] or "Unknown" for s in sector_counts]
    counts = [s[1] for s in sector_counts]
    
    return jsonify({
        'labels': sectors,
        'data': counts
    })

@dashboard.route('/dashboard/severity_distribution')
def severity_distribution():
    """
    Get severity distribution data for charts
    """
    # Count by severity
    severity_counts = db.session.query(
        Incident.severity, func.count(Incident.id).label('count')
    ).group_by(Incident.severity).all()
    
    # Format for Chart.js
    severities = [s[0] or "Unknown" for s in severity_counts]
    counts = [s[1] for s in severity_counts]
    
    return jsonify({
        'labels': severities,
        'data': counts
    })

@dashboard.route('/dashboard/time_trend')
def time_trend():
    """
    Get time trend data for charts
    """
    # Default to 90 days
    days = int(request.args.get('days', 90))
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get daily counts
    daily_counts = db.session.query(
        cast(Incident.discovered_date, Date).label('date'),
        func.count(Incident.id).label('count')
    ).filter(Incident.discovered_date >= start_date
    ).group_by('date').order_by('date').all()
    
    # Format for Chart.js
    dates = [d[0].strftime('%Y-%m-%d') for d in daily_counts]
    counts = [d[1] for d in daily_counts]
    
    return jsonify({
        'labels': dates,
        'data': counts
    })

@dashboard.route('/dashboard/monthly_trend')
def monthly_trend():
    """
    Get monthly trend data for charts
    """
    # Get data for the last 12 months
    # SQLite doesn't have good date functions, so we'll do this in Python
    
    # Get all incidents in the last year
    one_year_ago = datetime.utcnow() - timedelta(days=365)
    incidents = Incident.query.filter(
        Incident.discovered_date >= one_year_ago
    ).all()
    
    # Group by month
    monthly_data = {}
    for incident in incidents:
        month_key = incident.discovered_date.strftime('%Y-%m')
        if month_key not in monthly_data:
            monthly_data[month_key] = 0
        monthly_data[month_key] += 1
    
    # Sort by month
    sorted_months = sorted(monthly_data.keys())
    
    return jsonify({
        'labels': sorted_months,
        'data': [monthly_data[month] for month in sorted_months]
    })

@dashboard.route('/dashboard/actor_distribution')
def actor_distribution():
    """
    Get threat actor distribution data for charts
    """
    # Count incidents by actor where actor is not null
    actor_counts = db.session.query(
        Incident.actor, func.count(Incident.id).label('count')
    ).filter(Incident.actor != None
    ).group_by(Incident.actor).order_by(desc('count')).limit(10).all()
    
    # Format for Chart.js
    actors = [a[0] for a in actor_counts]
    counts = [a[1] for a in actor_counts]
    
    return jsonify({
        'labels': actors,
        'data': counts
    })
