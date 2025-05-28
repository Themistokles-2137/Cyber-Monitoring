import logging
import time
import random
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from app import db
from models import Source, Incident, CrawlLog
from utils.nlp_processor import extract_entities, is_relevant_to_india, classify_incident
from config import USER_AGENT, INDIA_KEYWORDS, THREAT_KEYWORDS

logger = logging.getLogger(__name__)

class PastebinScraper:
    """
    Scraper for Pastebin and similar sites that might contain leaked information
    or hacker announcements related to Indian cyber incidents
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
        Scrape pastebin-like sites for cyber incident information
        """
        try:
            logger.info(f"Starting to scrape {self.source.name} at {self.source.url}")
            self.crawl_log.status = "in_progress"
            db.session.commit()
            
            # Fetch the archive/recent page
            response = self.session.get(self.source.url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            # Parse the page
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all paste links
            paste_links = self._extract_paste_links(soup)
            logger.info(f"Found {len(paste_links)} pastes on {self.source.name}")
            self.crawl_log.items_found = len(paste_links)
            db.session.commit()
            
            # Process each paste
            processed_count = 0
            for link in paste_links[:30]:  # Limit to 30 pastes per run
                try:
                    # Add some delay to avoid overloading the server
                    time.sleep(random.uniform(1, 3))
                    
                    # Skip if already processed recently
                    if self._is_already_processed(link):
                        continue
                    
                    paste_data = self._process_paste(link)
                    if paste_data:
                        processed_count += 1
                except Exception as e:
                    logger.error(f"Error processing paste {link}: {str(e)}")
            
            # Update crawl log
            self.crawl_log.status = "success"
            self.crawl_log.end_time = datetime.utcnow()
            self.crawl_log.items_processed = processed_count
            
            # Update source last crawled time
            self.source.last_crawled = datetime.utcnow()
            
            db.session.commit()
            logger.info(f"Completed scraping {self.source.name}, processed {processed_count} pastes")
            
            return processed_count
        
        except Exception as e:
            logger.error(f"Error scraping {self.source.name}: {str(e)}")
            self.crawl_log.status = "failed"
            self.crawl_log.end_time = datetime.utcnow()
            self.crawl_log.error_message = str(e)
            db.session.commit()
            return 0
    
    def _extract_paste_links(self, soup):
        """
        Extract paste links from the page
        """
        links = []
        
        # Different selectors based on the type of paste site
        if "pastebin.com" in self.source.url:
            # Pastebin.com
            link_elements = soup.select('table.maintable tr td a')
            base_url = "https://pastebin.com"
        elif "gist.github.com" in self.source.url:
            # GitHub Gist
            link_elements = soup.select('div.gist-snippet a.link-overlay')
            base_url = "https://gist.github.com"
        else:
            # Generic approach
            link_elements = soup.find_all('a', href=True)
            base_url = self.source.url
        
        for a_tag in link_elements:
            url = a_tag.get('href')
            
            # Skip empty URLs or anchors
            if not url or url.startswith('#'):
                continue
            
            # Convert relative URLs to absolute
            if not url.startswith('http'):
                url = urljoin(base_url, url)
            
            links.append(url)
            
        return list(set(links))  # Remove duplicates
    
    def _is_already_processed(self, url):
        """
        Check if the URL has already been processed recently
        """
        existing = Incident.query.filter_by(source_url=url).first()
        return existing is not None
    
    def _process_paste(self, url):
        """
        Process a single paste to extract cyber incident information
        """
        logger.info(f"Processing paste: {url}")
        
        try:
            # Download the paste
            response = self.session.get(url, headers=self.headers, timeout=20)
            response.raise_for_status()
            
            # Parse the page
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract paste content based on the site
            content = None
            title = None
            
            if "pastebin.com" in url:
                # Pastebin.com
                content_elem = soup.select_one('div.source')
                title_elem = soup.select_one('div.info-top span.paste_box_line2')
                content = content_elem.get_text() if content_elem else None
                title = title_elem.get_text().strip() if title_elem else "Untitled Paste"
            elif "gist.github.com" in url:
                # GitHub Gist
                content_elems = soup.select('div.file-box div.blob-wrapper table')
                title_elem = soup.select_one('div.file-header span.gist-blob-name')
                
                if content_elems:
                    content = "\n".join([elem.get_text() for elem in content_elems])
                
                title = title_elem.get_text().strip() if title_elem else "Untitled Gist"
            else:
                # Generic approach
                pre_elem = soup.find('pre')
                content = pre_elem.get_text() if pre_elem else None
                title = soup.title.get_text() if soup.title else "Untitled"
            
            if not content or len(content) < 10:
                logger.info(f"No content found in paste: {url}")
                return None
            
            # Check if the paste is related to India and cybersecurity
            if not is_relevant_to_india(content) or not any(keyword.lower() in content.lower() for keyword in THREAT_KEYWORDS):
                logger.info(f"Paste not relevant to Indian cybersecurity: {url}")
                return None
            
            # Extract entities and incident details
            entities = extract_entities(content)
            incident_details = classify_incident(content)
            
            # Create a new incident
            incident = Incident(
                title=title[:255],
                description=content[:10000],  # Limit description length
                source_id=self.source.id,
                source_url=url,
                discovered_date=datetime.utcnow(),
                incident_date=datetime.utcnow(),  # Pastes usually don't have reliable dates
                sector=incident_details.get('sector'),
                severity=incident_details.get('severity', 'Medium'),  # Default to medium for pastes
                actor=entities.get('threat_actor'),
                target=entities.get('target'),
                technique=incident_details.get('technique'),
                confidence_score=incident_details.get('confidence', 0.6)
            )
            
            # Save the incident
            db.session.add(incident)
            db.session.commit()
            
            logger.info(f"Saved new incident from paste: {incident.id}")
            return {'id': incident.id, 'title': incident.title}
            
        except Exception as e:
            logger.error(f"Error processing paste {url}: {str(e)}")
            return None
