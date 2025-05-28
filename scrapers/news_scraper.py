import logging
import time
import random
import requests
from datetime import datetime
import trafilatura
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

from app import db
from models import Source, Incident, CrawlLog
from utils.nlp_processor import extract_entities, is_relevant_to_india, classify_incident
from utils.text_extractor import clean_text
from config import USER_AGENT, INDIA_KEYWORDS, THREAT_KEYWORDS

logger = logging.getLogger(__name__)

class NewsScraper:
    """
    Scraper for news websites containing cyber incident information
    """
    
    def __init__(self, source):
        """
        Initialize with a source object from the database
        """
        self.source = source
        self.headers = {
            'User-Agent': USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        self.session = requests.Session()
        self.crawl_log = CrawlLog(source_id=source.id)
        db.session.add(self.crawl_log)
        db.session.commit()
    
    def scrape(self):
        """
        Scrape the news source for cyber incident information
        """
        try:
            logger.info(f"Starting to scrape {self.source.name} at {self.source.url}")
            self.crawl_log.status = "in_progress"
            db.session.commit()
            
            # Fetch the main page
            response = self.session.get(self.source.url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            # Parse the page
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all links
            links = self._extract_article_links(soup)
            logger.info(f"Found {len(links)} links on {self.source.name}")
            self.crawl_log.items_found = len(links)
            db.session.commit()
            
            # Process each link
            processed_count = 0
            for link in links:
                try:
                    # Add some delay to avoid overloading the server
                    time.sleep(random.uniform(1, 3))
                    
                    # Skip if already processed recently
                    if self._is_already_processed(link):
                        continue
                    
                    article_data = self._process_article(link)
                    if article_data:
                        processed_count += 1
                except Exception as e:
                    logger.error(f"Error processing article {link}: {str(e)}")
            
            # Update crawl log
            self.crawl_log.status = "success"
            self.crawl_log.end_time = datetime.utcnow()
            self.crawl_log.items_processed = processed_count
            
            # Update source last crawled time
            self.source.last_crawled = datetime.utcnow()
            
            db.session.commit()
            logger.info(f"Completed scraping {self.source.name}, processed {processed_count} articles")
            
            return processed_count
        
        except Exception as e:
            logger.error(f"Error scraping {self.source.name}: {str(e)}")
            self.crawl_log.status = "failed"
            self.crawl_log.end_time = datetime.utcnow()
            self.crawl_log.error_message = str(e)
            db.session.commit()
            return 0
    
    def _extract_article_links(self, soup):
        """
        Extract article links from the page that might contain cyber incident information
        """
        links = []
        try:
            for a_tag in soup.find_all('a', href=True):
                try:
                    url = a_tag.get('href')
                    
                    # Skip empty URLs or anchors
                    if not url or url.startswith('#'):
                        continue
                    
                    # Convert relative URLs to absolute
                    if not url.startswith('http'):
                        base_url = urlparse(self.source.url)
                        url = urljoin(f"{base_url.scheme}://{base_url.netloc}", url)
                    
                    # Skip URLs that point to other domains
                    parsed_url = urlparse(url)
                    source_domain = urlparse(self.source.url).netloc
                    if parsed_url.netloc != source_domain:
                        continue
                    
                    # Check if the link text or URL contains any cybersecurity keywords
                    try:
                        text = a_tag.get_text().lower()
                        if any(keyword.lower() in text or keyword.lower() in url.lower() for keyword in THREAT_KEYWORDS):
                            links.append(url)
                    except Exception as e:
                        logger.warning(f"Error getting text from link: {str(e)}")
                        # If text extraction fails, just check URL
                        if any(keyword.lower() in url.lower() for keyword in THREAT_KEYWORDS):
                            links.append(url)
                except Exception as e:
                    logger.warning(f"Error processing link: {str(e)}")
                    continue
                    
            # Limit to a reasonable number of links
            if len(links) > 10:
                links = links[:10]
                
        except Exception as e:
            logger.error(f"Error extracting links: {str(e)}")
            
        return list(set(links))  # Remove duplicates
    
    def _is_already_processed(self, url):
        """
        Check if the URL has already been processed recently
        """
        existing = Incident.query.filter_by(source_url=url).first()
        return existing is not None
    
    def _process_article(self, url):
        """
        Process a single article to extract cyber incident information
        """
        logger.info(f"Processing article: {url}")
        
        try:
            # Validate URL
            if not url or not isinstance(url, str):
                logger.warning(f"Invalid URL: {url}")
                return None
                
            # Limit URL length
            if len(url) > 500:
                url = url[:500]
            
            # Download the article
            try:
                downloaded = trafilatura.fetch_url(url)
                if not downloaded:
                    logger.warning(f"Could not download content from: {url}")
                    return None
            except Exception as e:
                logger.error(f"Error downloading URL {url}: {str(e)}")
                return None
            
            # Extract the main text content
            try:
                text = trafilatura.extract(downloaded, include_comments=False, 
                                          include_tables=False, no_fallback=False)
                
                if not text or len(text) < 100:  # Skip very short articles
                    logger.info(f"Content too short or empty: {url}")
                    return None
            except Exception as e:
                logger.error(f"Error extracting text from {url}: {str(e)}")
                return None
            
            # Clean and process the text
            try:
                text = clean_text(text)
            except Exception as e:
                logger.error(f"Error cleaning text from {url}: {str(e)}")
                # Continue with original text if cleaning fails
                pass
                
            # Check if the article is related to India
            try:
                if not is_relevant_to_india(text):
                    logger.info(f"Article not relevant to India: {url}")
                    return None
            except Exception as e:
                logger.error(f"Error checking relevance to India for {url}: {str(e)}")
                # Continue processing anyway
            
            # Extract title - try from trafilatura or BeautifulSoup as fallback
            title = "Untitled Article"  # Default title
            try:
                soup = BeautifulSoup(downloaded, 'html.parser')
                title_tag = soup.find('h1') or soup.find('title')
                if title_tag:
                    title = title_tag.get_text().strip()
                if not title or len(title) < 3:  # If title extraction fails
                    title = text.split('\n')[0][:255]
            except Exception as e:
                logger.warning(f"Error extracting title: {str(e)}")
                # Use first line of text as fallback
                try:
                    title = text.split('\n')[0][:255]
                except:
                    # Keep default title if all else fails
                    pass
            
            # Set a default sector and severity if classification fails
            default_sector = "Information Technology"
            default_severity = "Medium"
            
            # Extract entities and incident details with error handling
            try:
                entities = extract_entities(text)
            except Exception as e:
                logger.error(f"Error extracting entities: {str(e)}")
                entities = {'threat_actor': None, 'target': None, 'technique': None}
                
            try:
                incident_details = classify_incident(text)
            except Exception as e:
                logger.error(f"Error classifying incident: {str(e)}")
                incident_details = {'sector': default_sector, 'severity': default_severity, 'confidence': 0.5}
            
            # Create a new incident
            try:
                incident = Incident(
                    title=title[:255],
                    description=text[:5000],  # Limit description length
                    source_id=self.source.id,
                    source_url=url[:500],  # Limit URL length
                    discovered_date=datetime.utcnow(),
                    sector=incident_details.get('sector', default_sector),
                    severity=incident_details.get('severity', default_severity),
                    actor=entities.get('threat_actor'),
                    target=entities.get('target'),
                    technique=incident_details.get('technique'),
                    confidence_score=incident_details.get('confidence', 0.5)
                )
                
                # Try to extract incident date
                try:
                    article_date = None
                    # Try to extract from meta tags
                    if 'html' in downloaded:
                        soup = BeautifulSoup(downloaded, 'html.parser')
                        date_meta = soup.find('meta', {'property': 'article:published_time'}) or \
                                    soup.find('meta', {'name': 'date'}) or \
                                    soup.find('meta', {'itemprop': 'datePublished'})
                        if date_meta and date_meta.get('content'):
                            try:
                                article_date = datetime.fromisoformat(date_meta['content'].replace('Z', '+00:00'))
                            except:
                                pass
                    
                    incident.incident_date = article_date or datetime.utcnow()
                except Exception as e:
                    logger.warning(f"Error extracting article date: {str(e)}")
                    incident.incident_date = datetime.utcnow()
                
                # Save the incident with transaction handling
                try:
                    db.session.add(incident)
                    db.session.commit()
                    logger.info(f"Saved new incident: {incident.title} from {url}")
                    return {'id': incident.id, 'title': incident.title}
                except Exception as e:
                    logger.error(f"Database error saving incident from {url}: {str(e)}")
                    db.session.rollback()
                    return None
            
            except Exception as e:
                logger.error(f"Error creating incident object from {url}: {str(e)}")
                return None
                
        except Exception as e:
            logger.error(f"Error processing article {url}: {str(e)}")
            return None
