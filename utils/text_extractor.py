import logging
import re
import trafilatura
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

def extract_text_from_url(url):
    """
    Extract the main text content from a URL using trafilatura
    """
    try:
        # Download the content
        downloaded = trafilatura.fetch_url(url)
        
        if not downloaded:
            logger.warning(f"Failed to download content from {url}")
            return None
        
        # Extract main text content
        text = trafilatura.extract(downloaded, include_comments=False, 
                                  include_tables=False, no_fallback=False)
        
        if not text or len(text.strip()) < 100:  # Skip very short content
            # Fallback to BeautifulSoup
            try:
                soup = BeautifulSoup(downloaded, 'html.parser')
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # Get text
                text = soup.get_text(separator=" ")
                
                # Clean the text
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = '\n'.join(chunk for chunk in chunks if chunk)
            except Exception as e:
                logger.error(f"Error using BeautifulSoup fallback: {str(e)}")
        
        return clean_text(text) if text else None
    
    except Exception as e:
        logger.error(f"Error extracting text from {url}: {str(e)}")
        return None

def clean_text(text):
    """
    Clean and normalize extracted text
    """
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove redundant newlines while preserving paragraph structure
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Trim extra spaces
    text = text.strip()
    
    return text

def extract_title_from_html(html_content):
    """
    Extract the title from HTML content
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Try to get the title from various elements in order of preference
        # 1. First h1 element
        h1 = soup.find('h1')
        if h1:
            return h1.get_text().strip()
        
        # 2. HTML title tag
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()
        
        # 3. Meta title
        meta_title = soup.find('meta', {'property': 'og:title'})
        if meta_title and meta_title.get('content'):
            return meta_title['content'].strip()
        
        return None
    
    except Exception as e:
        logger.error(f"Error extracting title: {str(e)}")
        return None
