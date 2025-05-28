import logging
import re
import string
from difflib import SequenceMatcher
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

from ml.incident_classifier import predict_incident_attributes
from config import INDIA_KEYWORDS, THREAT_KEYWORDS

logger = logging.getLogger(__name__)

# Download required NLTK resources
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
    nltk.data.find('corpora/wordnet')
    nltk.data.find('tokenizers/punkt_tab')
    nltk.data.find('taggers/averaged_perceptron_tagger')
    nltk.data.find('chunkers/maxent_ne_chunker')
    nltk.data.find('corpora/words')
except LookupError:
    # Download all required NLTK resources
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')
    nltk.download('averaged_perceptron_tagger')
    nltk.download('maxent_ne_chunker')
    nltk.download('words')

# Initialize NLTK components
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

def clean_text(text):
    """
    Clean and preprocess text for analysis
    """
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove URLs
    text = re.sub(r'http\S+', '', text)
    
    # Remove special characters and numbers
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\d+', ' ', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def is_relevant_to_india(text):
    """
    Check if the text is relevant to Indian cyberspace
    """
    if not text:
        return False
    
    # Lowercase the text for case-insensitive matching
    text_lower = text.lower()
    
    # Check for direct mentions of India-related keywords
    for keyword in INDIA_KEYWORDS:
        if keyword.lower() in text_lower:
            return True
    
    # Check for fuzzy matches of India-related terms
    words = word_tokenize(text_lower)
    india_words = ['india', 'indian', 'bharat', 'bharatiya']
    
    for word in words:
        if len(word) > 3:  # Skip very short words
            for india_word in india_words:
                # Use sequence matcher for fuzzy matching
                similarity = SequenceMatcher(None, word, india_word).ratio()
                if similarity > 0.8:  # High similarity threshold
                    return True
    
    return False

def extract_entities(text):
    """
    Extract named entities from text that are relevant to cyber incidents
    """
    entities = {
        'threat_actor': None,
        'target': None,
        'location': None,
        'date': None,
        'technique': None
    }
    
    if not text:
        return entities
    
    try:
        # Tokenize text
        sentences = sent_tokenize(text)
        
        # Common threat actor patterns
        threat_actor_patterns = [
            r'(?:attributed to|carried out by|linked to|sponsored by|conducted by)\s+([A-Z][A-Za-z0-9\s-]+)',
            r'([A-Z][A-Za-z0-9\s-]+)(?:\s+group|\s+threat\s+actor|\s+hackers|\s+attackers)'
        ]
        
        # Target organization patterns
        target_patterns = [
            r'(?:targeted|attacked|breached|compromised|affected)\s+([A-Z][A-Za-z0-9\s\-\.,]+)',
            r'([A-Z][A-Za-z0-9\s\-\.]+)(?:\s+was\s+targeted|\s+was\s+attacked|\s+was\s+breached|\s+was\s+compromised)'
        ]
        
        # Attack technique patterns
        technique_patterns = [
            r'(?:using|through|via|exploiting)\s+([a-z0-9\s\-\.]+\s+attack)',
            r'(?:using|through|via|exploiting)\s+([a-z0-9\s\-\.]+\s+vulnerability)',
            r'(?:using|through|via|exploiting)\s+([a-z0-9\s\-\.]+\s+exploit)'
        ]
        
        # Process each sentence
        for sentence in sentences:
            # Look for threat actors
            if not entities['threat_actor']:
                for pattern in threat_actor_patterns:
                    matches = re.search(pattern, sentence, re.IGNORECASE)
                    if matches:
                        entities['threat_actor'] = matches.group(1).strip()
                        break
            
            # Look for targets
            if not entities['target']:
                for pattern in target_patterns:
                    matches = re.search(pattern, sentence, re.IGNORECASE)
                    if matches:
                        entities['target'] = matches.group(1).strip()
                        break
            
            # Look for techniques
            if not entities['technique']:
                for pattern in technique_patterns:
                    matches = re.search(pattern, sentence, re.IGNORECASE)
                    if matches:
                        entities['technique'] = matches.group(1).strip()
                        break
        
        # Try using NLTK's named entity recognition as a fallback
        if not entities['target'] or not entities['threat_actor']:
            try:
                # Only use regex patterns rather than NE chunking to avoid punkt_tab resource issue
                # Look for organization patterns
                org_patterns = [
                    r'([A-Z][A-Za-z0-9\s\.,]+\b(?:Corporation|Corp|Inc|Ltd|Limited|Company|Co|Group|Technologies|Tech))',
                    r'([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){1,3})'  # Camel case multi-word names
                ]
                
                for pattern in org_patterns:
                    if not entities['target']:
                        for sentence in sentences:
                            matches = re.search(pattern, sentence)
                            if matches:
                                entities['target'] = matches.group(1).strip()
                                break
                
                # Use simple city/country detection rather than GPE NER
                if not entities['location']:
                    # Common Indian cities and states
                    locations = ['Delhi', 'Mumbai', 'Bangalore', 'Kolkata', 'Chennai', 
                                'Hyderabad', 'Pune', 'Ahmedabad', 'India', 'Maharashtra',
                                'Karnataka', 'Tamil Nadu', 'Gujarat', 'Uttar Pradesh']
                    
                    for location in locations:
                        location_pattern = r'\b' + re.escape(location) + r'\b'
                        for sentence in sentences:
                            if re.search(location_pattern, sentence, re.IGNORECASE):
                                entities['location'] = location
                                break
                        if entities['location']:
                            break
                            
            except Exception as e:
                logger.warning(f"Error in entity extraction fallback: {str(e)}")
        
    except Exception as e:
        logger.error(f"Error extracting entities: {str(e)}")
    
    return entities

def classify_incident(text):
    """
    Classify an incident based on its text
    """
    if not text:
        return {}
    
    # Use the ML model to predict attributes
    return predict_incident_attributes(text)
