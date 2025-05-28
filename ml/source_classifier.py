import os
import logging
import pickle
import numpy as np
from datetime import datetime
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score

from app import db
from models import Source, MLModel
from config import MODEL_PATH, SOURCE_CLASSIFIER_MODEL, INDIA_KEYWORDS, THREAT_KEYWORDS

logger = logging.getLogger(__name__)

# Create models directory if it doesn't exist
os.makedirs(MODEL_PATH, exist_ok=True)

def initialize_model():
    """
    Initialize or load the source classifier model
    """
    model_path = os.path.join(MODEL_PATH, SOURCE_CLASSIFIER_MODEL)
    
    # Check if model exists
    if os.path.exists(model_path):
        logger.info(f"Loading existing source classifier model from {model_path}")
        try:
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            return model
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
    
    # If model doesn't exist or loading failed, create a new one
    logger.info("Creating new source classifier model")
    return create_initial_model()

def create_initial_model():
    """
    Create an initial model with some basic training data
    """
    # Initial training data - URLs and their page titles/descriptions
    training_data = [
        # Cybersecurity news sites
        {
            "url": "https://thehackernews.com/",
            "text": "The Hacker News is a trusted cybersecurity news platform covering hacking news, cyber attacks, data breaches, malware, vulnerabilities",
            "is_relevant": 1
        },
        {
            "url": "https://www.bleepingcomputer.com/",
            "text": "BleepingComputer cybersecurity technology news and support. Covering ransomware, malware, data breaches, vulnerabilities, exploits, hacking news.",
            "is_relevant": 1
        },
        {
            "url": "https://krebsonsecurity.com/",
            "text": "Security news and investigation on cybercrime, data breaches, vulnerability reports covering banking, financial security, privacy concerns",
            "is_relevant": 1
        },
        {
            "url": "https://www.thehindu.com/sci-tech/technology/",
            "text": "Technology News: Get the latest tech news, views and updates from the technology industry in India. Read latest gadgets launches, mobile phones",
            "is_relevant": 1
        },
        {
            "url": "https://cert-in.org.in/",
            "text": "CERT-In Indian Computer Emergency Response Team. Vulnerability alerts, advisories, security incidents, intrusions affecting Indian cyberspace",
            "is_relevant": 1
        },
        # Non-relevant sites
        {
            "url": "https://www.espn.com/",
            "text": "Sports news, scores, fantasy games and highlights from ESPN. Covering NFL, MLB, NBA, NHL, college sports, FIFA World Cup, Olympics.",
            "is_relevant": 0
        },
        {
            "url": "https://www.foodnetwork.com/",
            "text": "Food Network recipes, healthy eating ideas, cooking techniques, party food, restaurant reviews, celebrity chefs, kitchen tips",
            "is_relevant": 0
        },
        {
            "url": "https://www.travelchannel.com/",
            "text": "Travel destinations, videos, vacation ideas, travel guides, tips for planning trips, flight deals, hotels, cruises, vacation packages",
            "is_relevant": 0
        },
        {
            "url": "https://www.history.com/",
            "text": "History articles, shows, facts about historical events, figures, wars, conflicts, discoveries, civilizations throughout the ages",
            "is_relevant": 0
        }
    ]
    
    # Add more examples with Indian keywords
    for keyword in INDIA_KEYWORDS[:10]:  # Use first 10 keywords
        training_data.append({
            "url": f"https://example.com/{keyword.lower().replace(' ', '-')}",
            "text": f"Cybersecurity news related to {keyword}. Covering data breaches, hacking incidents, and cyberthreats in Indian context.",
            "is_relevant": 1
        })
    
    # Add more examples with threat keywords
    for keyword in THREAT_KEYWORDS[:10]:  # Use first 10 keywords
        training_data.append({
            "url": f"https://example.com/{keyword.lower().replace(' ', '-')}",
            "text": f"News about {keyword} incidents affecting Indian organizations. Critical infrastructure security updates.",
            "is_relevant": 1
        })
    
    # Create DataFrame
    df = pd.DataFrame(training_data)
    
    # Split into features and target
    X = df['text']
    y = df['is_relevant']
    
    # Split into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Create pipeline with TF-IDF and Random Forest
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(max_features=5000, ngram_range=(1, 2))),
        ('classifier', RandomForestClassifier(n_estimators=100, random_state=42))
    ])
    
    # Train the model
    pipeline.fit(X_train, y_train)
    
    # Evaluate the model
    y_pred = pipeline.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    
    logger.info(f"Initial source classifier model trained with accuracy: {accuracy:.4f}, F1 score: {f1:.4f}")
    
    # Save the model
    model_path = os.path.join(MODEL_PATH, SOURCE_CLASSIFIER_MODEL)
    with open(model_path, 'wb') as f:
        pickle.dump(pipeline, f)
    
    # Save model metadata to database
    model_record = MLModel(
        name="Source Classifier",
        model_type="source_classifier",
        version="1.0.0",
        accuracy=float(accuracy),
        f1_score=float(f1),
        training_date=datetime.utcnow(),
        is_active=True
    )
    
    db.session.add(model_record)
    db.session.commit()
    
    return pipeline

def predict_source_relevance(url, text):
    """
    Predict if a source is relevant for cyber incidents in Indian context
    
    Args:
        url (str): The URL of the source
        text (str): Text content or description of the source
    
    Returns:
        tuple: (is_relevant, confidence)
    """
    model = initialize_model()
    
    # Combine URL and text for prediction
    combined_text = f"{url} {text}"
    
    # Make prediction
    prediction_proba = model.predict_proba([combined_text])[0]
    is_relevant = int(prediction_proba[1] >= 0.5)  # Class 1 probability >= 0.5
    confidence = prediction_proba[1] if is_relevant else prediction_proba[0]
    
    return is_relevant, float(confidence)

def retrain_model_with_new_data(sources=None):
    """
    Retrain the model with new data from the database
    
    Args:
        sources (list): Optional list of Source objects to use for training
    """
    logger.info("Retraining source classifier model with new data")
    
    if sources is None:
        # Get all sources from the database
        sources = Source.query.all()
    
    if not sources:
        logger.warning("No sources available for retraining")
        return initialize_model()
    
    # Create training data
    training_data = []
    
    for source in sources:
        # Create a text description from the source data
        text = f"{source.name} {source.url} {source.source_type}"
        
        # Determine if the source is relevant based on its reliability score
        # and if it has produced any incidents
        is_relevant = 1 if source.reliability_score > 0.3 or len(source.incidents) > 0 else 0
        
        training_data.append({
            "url": source.url,
            "text": text,
            "is_relevant": is_relevant
        })
    
    # If we don't have enough data, add the initial training data
    if len(training_data) < 20:
        # Get initial model
        initial_model = create_initial_model()
        
        # Extract some of the training data from the initial model
        try:
            # Get the vectorizer
            tfidf = initial_model.named_steps['tfidf']
            # Get the feature names
            feature_names = tfidf.get_feature_names_out()
            # Get some of the most important features
            for feature in feature_names[:30]:
                if len(feature) > 3:  # Skip short words
                    training_data.append({
                        "url": f"https://example.com/{feature.replace(' ', '-')}",
                        "text": f"Cybersecurity news related to {feature}. Data breaches and security incidents.",
                        "is_relevant": 1 if any(keyword.lower() in feature.lower() for keyword in INDIA_KEYWORDS + THREAT_KEYWORDS) else 0
                    })
        except:
            logger.warning("Could not extract features from initial model")
    
    # Create DataFrame
    df = pd.DataFrame(training_data)
    
    # Split into features and target
    X = df['text']
    y = df['is_relevant']
    
    # Split into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Create pipeline with TF-IDF and Random Forest
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(max_features=5000, ngram_range=(1, 2))),
        ('classifier', RandomForestClassifier(n_estimators=100, random_state=42))
    ])
    
    # Train the model
    pipeline.fit(X_train, y_train)
    
    # Evaluate the model
    y_pred = pipeline.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    
    logger.info(f"Retrained source classifier model with accuracy: {accuracy:.4f}, F1 score: {f1:.4f}")
    
    # Save the model
    model_path = os.path.join(MODEL_PATH, SOURCE_CLASSIFIER_MODEL)
    with open(model_path, 'wb') as f:
        pickle.dump(pipeline, f)
    
    # Get the current version from the database
    current_model = MLModel.query.filter_by(model_type="source_classifier", is_active=True).first()
    
    # Create a new version
    version = "1.0.0"
    if current_model:
        # Deactivate the current model
        current_model.is_active = False
        
        # Parse the version and increment
        parts = current_model.version.split('.')
        if len(parts) == 3:
            try:
                major, minor, patch = map(int, parts)
                patch += 1
                version = f"{major}.{minor}.{patch}"
            except:
                pass
    
    # Save model metadata to database
    model_record = MLModel(
        name="Source Classifier",
        model_type="source_classifier",
        version=version,
        accuracy=float(accuracy),
        f1_score=float(f1),
        training_date=datetime.utcnow(),
        is_active=True
    )
    
    db.session.add(model_record)
    db.session.commit()
    
    return pipeline
