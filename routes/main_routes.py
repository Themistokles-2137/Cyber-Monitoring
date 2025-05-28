import logging
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy import func, desc

from app import db
from models import Incident, Source, Tag, CrawlLog
from scrapers.news_scraper import NewsScraper
from scrapers.twitter_scraper import TwitterScraper
from scrapers.pastebin_scraper import PastebinScraper
from config import DEFAULT_SOURCES

logger = logging.getLogger(__name__)

main = Blueprint('main', __name__)

@main.route('/')
def index():
    """
    Main landing page
    """
    # Get recent incidents
    recent_incidents = Incident.query.order_by(Incident.discovered_date.desc()).limit(5).all()
    
    # Get stats for dashboard highlights
    total_incidents = Incident.query.count()
    
    # Incidents in the last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_count = Incident.query.filter(Incident.discovered_date >= thirty_days_ago).count()
    
    # Get sector distribution for chart
    sector_counts = db.session.query(
        Incident.sector, func.count(Incident.id).label('count')
    ).group_by(Incident.sector).order_by(desc('count')).limit(5).all()
    
    sectors = [s[0] or "Unknown" for s in sector_counts]
    sector_data = [s[1] for s in sector_counts]
    
    # Get severity distribution
    severity_counts = db.session.query(
        Incident.severity, func.count(Incident.id).label('count')
    ).group_by(Incident.severity).all()
    
    severities = [s[0] or "Unknown" for s in severity_counts]
    severity_data = [s[1] for s in severity_counts]
    
    return render_template('index.html', 
                          recent_incidents=recent_incidents,
                          total_incidents=total_incidents,
                          recent_count=recent_count,
                          sectors=sectors,
                          sector_data=sector_data,
                          severities=severities,
                          severity_data=severity_data)

@main.route('/incidents')
def incidents():
    """
    List all incidents with filtering options
    """
    # Get filter parameters
    sector = request.args.get('sector')
    severity = request.args.get('severity')
    timeframe = request.args.get('timeframe', 'all')
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    
    # Start with all incidents query
    query = Incident.query
    
    # Apply filters
    if sector and sector != 'all':
        query = query.filter(Incident.sector == sector)
    
    if severity and severity != 'all':
        query = query.filter(Incident.severity == severity)
    
    if timeframe and timeframe != 'all':
        if timeframe == '7days':
            date_filter = datetime.utcnow() - timedelta(days=7)
        elif timeframe == '30days':
            date_filter = datetime.utcnow() - timedelta(days=30)
        elif timeframe == '90days':
            date_filter = datetime.utcnow() - timedelta(days=90)
        else:
            date_filter = datetime.utcnow() - timedelta(days=365)
        
        query = query.filter(Incident.discovered_date >= date_filter)
    
    # Apply search if provided
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Incident.title.ilike(search_term)) | 
            (Incident.description.ilike(search_term)) |
            (Incident.actor.ilike(search_term)) |
            (Incident.target.ilike(search_term))
        )
    
    # Get results with pagination
    incidents_per_page = 20
    paginated_incidents = query.order_by(Incident.discovered_date.desc()).paginate(
        page=page, per_page=incidents_per_page, error_out=False)
    
    # Get distinct sectors and severities for filters
    sectors = db.session.query(Incident.sector).distinct().filter(Incident.sector != None).order_by(Incident.sector).all()
    severities = db.session.query(Incident.severity).distinct().filter(Incident.severity != None).order_by(Incident.severity).all()
    
    return render_template('incidents.html',
                          incidents=paginated_incidents.items,
                          pagination=paginated_incidents,
                          sectors=[s[0] for s in sectors],
                          severities=[s[0] for s in severities],
                          current_sector=sector,
                          current_severity=severity,
                          current_timeframe=timeframe,
                          search=search)

@main.route('/incident/<int:id>')
def incident_detail(id):
    """
    Show details for a specific incident
    """
    incident = Incident.query.get_or_404(id)
    
    # Get related incidents (same sector or target)
    related = Incident.query.filter(
        (Incident.sector == incident.sector) | 
        (Incident.target == incident.target),
        Incident.id != incident.id
    ).order_by(Incident.discovered_date.desc()).limit(5).all()
    
    return render_template('incident_detail.html', incident=incident, related=related)

@main.route('/sources')
def sources():
    """
    List all data sources
    """
    sources = Source.query.order_by(Source.name).all()
    
    # Get source types for filtering
    source_types = db.session.query(Source.source_type).distinct().order_by(Source.source_type).all()
    
    # Get the most recently crawled sources
    recent_crawls = CrawlLog.query.order_by(CrawlLog.start_time.desc()).limit(5).all()
    
    return render_template('sources.html', 
                          sources=sources, 
                          source_types=[t[0] for t in source_types],
                          recent_crawls=recent_crawls)

@main.route('/search')
def search():
    """
    Advanced search page
    """
    # Get search parameters
    query = request.args.get('query', '')
    sector = request.args.get('sector')
    severity = request.args.get('severity')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Start with all incidents
    search_query = Incident.query
    
    # Apply filters
    if query:
        search_term = f"%{query}%"
        search_query = search_query.filter(
            (Incident.title.ilike(search_term)) | 
            (Incident.description.ilike(search_term)) |
            (Incident.actor.ilike(search_term)) |
            (Incident.target.ilike(search_term))
        )
    
    if sector and sector != 'all':
        search_query = search_query.filter(Incident.sector == sector)
    
    if severity and severity != 'all':
        search_query = search_query.filter(Incident.severity == severity)
    
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            search_query = search_query.filter(Incident.incident_date >= start)
        except ValueError:
            pass
    
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d')
            search_query = search_query.filter(Incident.incident_date <= end)
        except ValueError:
            pass
    
    # Execute the query
    results = []
    if any([query, sector, severity, start_date, end_date]):
        results = search_query.order_by(Incident.discovered_date.desc()).all()
    
    # Get distinct sectors and severities for filters
    sectors = db.session.query(Incident.sector).distinct().filter(Incident.sector != None).order_by(Incident.sector).all()
    severities = db.session.query(Incident.severity).distinct().filter(Incident.severity != None).order_by(Incident.severity).all()
    
    return render_template('search.html',
                          results=results,
                          query=query,
                          sectors=[s[0] for s in sectors],
                          severities=[s[0] for s in severities],
                          current_sector=sector,
                          current_severity=severity,
                          start_date=start_date,
                          end_date=end_date)

@main.route('/initialize_sources', methods=['POST'])
def initialize_sources():
    """
    Initialize the database with default sources
    """
    try:
        # Check if we already have sources
        existing_count = Source.query.count()
        if existing_count > 0:
            flash('Sources have already been initialized.', 'info')
            return redirect(url_for('main.sources'))
        
        # Add default sources
        for source_data in DEFAULT_SOURCES:
            source = Source(
                name=source_data['name'],
                url=source_data['url'],
                source_type=source_data['source_type'],
                reliability_score=0.7,  # Default reliability score
                created_at=datetime.utcnow(),
                is_active=True
            )
            db.session.add(source)
        
        db.session.commit()
        flash(f'Successfully initialized {len(DEFAULT_SOURCES)} sources.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error initializing sources: {str(e)}")
        flash(f'Error initializing sources: {str(e)}', 'error')
    
    return redirect(url_for('main.sources'))

@main.route('/crawl_source/<int:id>', methods=['GET', 'POST'])
def crawl_source(id):
    """
    Manually trigger a crawl for a specific source
    """
    source = Source.query.get_or_404(id)
    
    try:
        # Create the appropriate scraper based on source type
        scraper = None
        if source.source_type == 'news':
            scraper = NewsScraper(source)
        elif source.source_type == 'twitter':
            scraper = TwitterScraper(source)
        elif source.source_type in ['pastesite', 'pastebin']:
            scraper = PastebinScraper(source)
        else:
            # Default to news scraper
            scraper = NewsScraper(source)
        
        # Run the scraper
        if scraper:
            processed_count = scraper.scrape()
            flash(f'Successfully crawled {source.name}. Processed {processed_count} items.', 'success')
        else:
            flash(f'No appropriate scraper found for source type: {source.source_type}', 'warning')
    
    except Exception as e:
        logger.error(f"Error crawling source {source.name}: {str(e)}")
        flash(f'Error crawling source: {str(e)}', 'error')
    
    return redirect(url_for('main.sources'))
