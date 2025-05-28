import logging
import time
import random
import re
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

from app import db
from models import Source, Incident, CrawlLog
from utils.nlp_processor import extract_entities, is_relevant_to_india, classify_incident
from config import USER_AGENT, INDIA_KEYWORDS, THREAT_KEYWORDS

logger = logging.getLogger(__name__)

class TwitterScraper:
    """
    Scraper for Twitter/X posts containing cyber incident information
    
    Note: This is a basic implementation using web scraping of Nitter instances
    since the Twitter API requires paid access. For a production environment,
    a more robust approach would be needed.
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
        # Use Nitter instances to access Twitter content without API
        self.nitter_instances = [
            "https://nitter.net",
            "https://nitter.42l.fr",
            "https://nitter.pussthecat.org",
            "https://nitter.esmailelbob.xyz"
        ]
        self.current_instance = self.nitter_instances[0]
        self.session = requests.Session()
        self.crawl_log = CrawlLog(source_id=source.id)
        db.session.add(self.crawl_log)
        db.session.commit()
    
    def scrape(self):
        """
        Scrape Twitter for cyber incident information
        """
        try:
            logger.info(f"Starting to scrape Twitter source: {self.source.name}")
            self.crawl_log.status = "in_progress"
            db.session.commit()
            
            processed_count = 0
            
            # Extract username from Twitter URL
            username = self._extract_username(self.source.url)
            if not username:
                raise ValueError(f"Could not extract username from {self.source.url}")
            
            # Try each Nitter instance until one works
            for instance in self.nitter_instances:
                try:
                    self.current_instance = instance
                    tweets = self._get_tweets(username)
                    if tweets:
                        break
                except Exception as e:
                    logger.warning(f"Error with Nitter instance {instance}: {str(e)}")
                    continue
            
            if not tweets:
                raise ValueError(f"Could not retrieve tweets from any Nitter instance for {username}")
            
            logger.info(f"Found {len(tweets)} tweets from {username}")
            self.crawl_log.items_found = len(tweets)
            db.session.commit()
            
            # Process each tweet
            for tweet in tweets:
                try:
                    # Skip if already processed
                    if self._is_already_processed(tweet['url']):
                        continue
                    
                    # Process tweet for incident information
                    result = self._process_tweet(tweet)
                    if result:
                        processed_count += 1
                    
                    # Add delay to avoid detection
                    time.sleep(random.uniform(1, 2))
                    
                except Exception as e:
                    logger.error(f"Error processing tweet {tweet.get('url', 'unknown')}: {str(e)}")
            
            # Update crawl log
            self.crawl_log.status = "success"
            self.crawl_log.end_time = datetime.utcnow()
            self.crawl_log.items_processed = processed_count
            
            # Update source last crawled time
            self.source.last_crawled = datetime.utcnow()
            
            db.session.commit()
            logger.info(f"Completed scraping Twitter for {username}, processed {processed_count} tweets")
            
            return processed_count
        
        except Exception as e:
            logger.error(f"Error scraping Twitter source {self.source.name}: {str(e)}")
            self.crawl_log.status = "failed"
            self.crawl_log.end_time = datetime.utcnow()
            self.crawl_log.error_message = str(e)
            db.session.commit()
            return 0
    
    def _extract_username(self, url):
        """
        Extract username from Twitter URL
        """
        # Twitter URL patterns
        patterns = [
            r'twitter\.com/([^/\?]+)',
            r'x\.com/([^/\?]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                username = match.group(1)
                # Remove @ if present
                if username.startswith('@'):
                    username = username[1:]
                return username
        
        return None
    
    def _get_tweets(self, username):
        """
        Get tweets from a user using a Nitter instance
        """
        nitter_url = f"{self.current_instance}/{username}"
        
        try:
            response = self.session.get(nitter_url, headers=self.headers, timeout=20)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            tweet_divs = soup.select('.timeline-item')
            
            tweets = []
            for div in tweet_divs:
                try:
                    # Skip pinned tweets
                    if div.select_one('.pinned'):
                        continue
                    
                    # Extract tweet content
                    content_div = div.select_one('.tweet-content')
                    if not content_div:
                        continue
                    
                    content = content_div.get_text().strip()
                    
                    # Skip if not related to cybersecurity
                    if not any(keyword.lower() in content.lower() for keyword in THREAT_KEYWORDS):
                        continue
                    
                    # Extract tweet link
                    link_elem = div.select_one('.tweet-link')
                    tweet_url = f"https://twitter.com{link_elem['href']}" if link_elem else None
                    
                    # Extract timestamp
                    time_elem = div.select_one('.tweet-date a')
                    timestamp = time_elem.get('title') if time_elem else None
                    
                    # Convert to datetime
                    tweet_time = None
                    if timestamp:
                        try:
                            tweet_time = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S %Z')
                        except:
                            tweet_time = datetime.utcnow()
                    
                    tweets.append({
                        'content': content,
                        'url': tweet_url,
                        'time': tweet_time or datetime.utcnow(),
                        'username': username
                    })
                    
                except Exception as e:
                    logger.warning(f"Error parsing tweet: {str(e)}")
            
            return tweets
            
        except Exception as e:
            logger.error(f"Error accessing {nitter_url}: {str(e)}")
            return []
    
    def _is_already_processed(self, url):
        """
        Check if the tweet URL has already been processed
        """
        existing = Incident.query.filter_by(source_url=url).first()
        return existing is not None
    
    def _process_tweet(self, tweet):
        """
        Process a tweet to extract cyber incident information
        """
        text = tweet['content']
        
        # Check if the tweet is related to India
        if not is_relevant_to_india(text):
            return None
        
        # Extract entities and incident details
        entities = extract_entities(text)
        incident_details = classify_incident(text)
        
        # Create a new incident
        incident = Incident(
            title=text[:255],  # Use tweet content as title
            description=text,
            source_id=self.source.id,
            source_url=tweet['url'],
            incident_date=tweet['time'],
            discovered_date=datetime.utcnow(),
            sector=incident_details.get('sector'),
            severity=incident_details.get('severity'),
            actor=entities.get('threat_actor'),
            target=entities.get('target'),
            technique=incident_details.get('technique'),
            confidence_score=incident_details.get('confidence', 0.4)  # Lower default confidence for tweets
        )
        
        # Save the incident
        db.session.add(incident)
        db.session.commit()
        
        logger.info(f"Saved new incident from tweet: {incident.id}")
        return {'id': incident.id, 'title': incident.title}
