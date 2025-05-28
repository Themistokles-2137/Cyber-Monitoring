import os
import logging
import pickle
import numpy as np
from datetime import datetime
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.multioutput import MultiOutputClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score

from app import db
from models import Incident, MLModel
from config import MODEL_PATH, INCIDENT_CLASSIFIER_MODEL, INCIDENT_SECTORS, INCIDENT_SEVERITY

logger = logging.getLogger(__name__)

# Create models directory if it doesn't exist
os.makedirs(MODEL_PATH, exist_ok=True)

def initialize_model():
    """
    Initialize or load the incident classifier model
    """
    model_path = os.path.join(MODEL_PATH, INCIDENT_CLASSIFIER_MODEL)
    
    # Check if model exists
    if os.path.exists(model_path):
        logger.info(f"Loading existing incident classifier model from {model_path}")
        try:
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            return model
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
    
    # If model doesn't exist or loading failed, create a new one
    logger.info("Creating new incident classifier model")
    return create_initial_model()

def create_initial_model():
    """
    Create an initial model with some basic training data
    """
    # Initial training data with sector and severity classification
    training_data = [
        {
            "text": "Indian power grid under cyberattack from Chinese state-sponsored hackers. Critical infrastructure systems compromised.",
            "sector": "Energy",
            "severity": "Critical"
        },
        {
            "text": "Bank of India reports data breach affecting customer accounts. Personal information of thousands of customers exposed.",
            "sector": "Finance",
            "severity": "High"
        },
        {
            "text": "Healthcare records of patients from major Delhi hospital leaked online. Medical histories and personal details compromised.",
            "sector": "Healthcare",
            "severity": "High"
        },
        {
            "text": "Indian government websites defaced by Pakistani hacker group. No sensitive data reported stolen.",
            "sector": "Government",
            "severity": "Medium"
        },
        {
            "text": "IT systems of major Indian tech company hit by ransomware. Services disrupted for several hours.",
            "sector": "Information Technology",
            "severity": "High"
        },
        {
            "text": "Minor data leak from educational institution in Mumbai. Student email addresses exposed.",
            "sector": "Education",
            "severity": "Low"
        },
        {
            "text": "E-commerce platform faces temporary outage due to DDoS attack. Customer data safe.",
            "sector": "E-commerce",
            "severity": "Medium"
        },
        {
            "text": "Vulnerability found in Indian banking app. No evidence of exploitation yet.",
            "sector": "Finance",
            "severity": "Medium"
        },
        {
            "text": "Critical vulnerability in Aadhaar authentication system discovered and patched. No known breaches reported.",
            "sector": "Government",
            "severity": "High"
        },
        {
            "text": "Defense contractor's systems breached, classified documents stolen by state-sponsored actors.",
            "sector": "Defense",
            "severity": "Critical"
        },
        {
            "text": "Telecom provider reports SIM swapping attacks affecting hundreds of customers in India.",
            "sector": "Telecom",
            "severity": "High"
        },
        {
            "text": "Manufacturing plant's industrial control systems infected with malware, production halted.",
            "sector": "Manufacturing",
            "severity": "High"
        },
        {
            "text": "Indian media organization's website compromised to distribute fake news.",
            "sector": "Media",
            "severity": "Medium"
        },
        {
            "text": "Transport authority's ticketing system breached, minor disruption to services.",
            "sector": "Transportation",
            "severity": "Low"
        },
        {
            "text": "UPI payment vulnerability discovered allowing potential transaction manipulation.",
            "sector": "Finance",
            "severity": "High"
        }
    ]
    
    # Convert sectors and severities to numeric values
    sector_mapping = {sector: i for i, sector in enumerate(INCIDENT_SECTORS)}
    severity_mapping = {severity: i for i, severity in enumerate(INCIDENT_SEVERITY)}
    
    # Create DataFrame
    df = pd.DataFrame(training_data)
    
    # Convert text labels to numeric
    df['sector_id'] = df['sector'].map(sector_mapping)
    df['severity_id'] = df['severity'].map(severity_mapping)
    
    # Split into features and targets
    X = df['text']
    y = df[['sector_id', 'severity_id']]
    
    # Split into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Create pipeline with TF-IDF and Multi-output Random Forest
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(max_features=5000, ngram_range=(1, 2))),
        ('classifier', MultiOutputClassifier(RandomForestClassifier(n_estimators=100, random_state=42)))
    ])
    
    # Train the model
    pipeline.fit(X_train, y_train)
    
    # Evaluate the model
    y_pred = pipeline.predict(X_test)
    
    # Calculate metrics
    accuracy_sector = accuracy_score(y_test['sector_id'], y_pred[:, 0])
    accuracy_severity = accuracy_score(y_test['severity_id'], y_pred[:, 1])
    
    logger.info(f"Initial incident classifier trained with accuracy: sector={accuracy_sector:.4f}, severity={accuracy_severity:.4f}")
    
    # Save the model
    model_path = os.path.join(MODEL_PATH, INCIDENT_CLASSIFIER_MODEL)
    
    # Also save the mappings with the model for later use
    model_data = {
        'pipeline': pipeline,
        'sector_mapping': sector_mapping,
        'severity_mapping': severity_mapping
    }
    
    with open(model_path, 'wb') as f:
        pickle.dump(model_data, f)
    
    # Save model metadata to database
    model_record = MLModel(
        name="Incident Classifier",
        model_type="incident_classifier",
        version="1.0.0",
        accuracy=float((accuracy_sector + accuracy_severity) / 2),  # Average accuracy
        f1_score=0.0,  # Not calculated for this initial model
        training_date=datetime.utcnow(),
        is_active=True
    )
    
    db.session.add(model_record)
    db.session.commit()
    
    return model_data

def predict_incident_attributes(text):
    """
    Predict sector and severity for an incident based on its text
    
    Args:
        text (str): The incident text content
    
    Returns:
        dict: Predicted attributes and confidence scores
    """
    model_data = initialize_model()
    
    # Extract components
    pipeline = model_data['pipeline']
    sector_mapping = model_data['sector_mapping']
    severity_mapping = model_data['severity_mapping']
    
    # Reverse the mappings for lookup
    sector_reverse = {v: k for k, v in sector_mapping.items()}
    severity_reverse = {v: k for k, v in severity_mapping.items()}
    
    # Make prediction
    prediction = pipeline.predict([text])[0]
    prediction_proba = pipeline.predict_proba([text])
    
    # Get sector and severity predictions
    sector_id = prediction[0]
    severity_id = prediction[1]
    
    # Get confidence scores
    sector_confidence = max(prediction_proba[0][0])
    severity_confidence = max(prediction_proba[1][0])
    
    # Map back to text labels
    sector = sector_reverse.get(sector_id, "Other")
    severity = severity_reverse.get(severity_id, "Medium")
    
    # Overall confidence is average of sector and severity confidence
    confidence = (sector_confidence + severity_confidence) / 2
    
    return {
        'sector': sector,
        'severity': severity,
        'confidence': float(confidence),
        'sector_confidence': float(sector_confidence),
        'severity_confidence': float(severity_confidence)
    }

def retrain_model_with_incidents():
    """
    Retrain the model with new data from the database
    """
    logger.info("Retraining incident classifier model with new data")
    
    # Get incidents that have verified sector and severity
    incidents = Incident.query.filter_by(is_verified=True).all()
    
    if not incidents or len(incidents) < 10:
        logger.warning("Not enough verified incidents for retraining")
        return initialize_model()
    
    # Create training data
    training_data = []
    
    for incident in incidents:
        if incident.sector and incident.severity:
            training_data.append({
                "text": f"{incident.title} {incident.description}",
                "sector": incident.sector,
                "severity": incident.severity
            })
    
    # If we don't have enough data, add the initial training data
    if len(training_data) < 20:
        # Add some synthetic examples
        initial_data = create_initial_model()
        
        # Use the initial training data from create_initial_model
        synthetic_examples = [
            {
                "text": "Indian power grid under cyberattack from Chinese state-sponsored hackers. Critical infrastructure systems compromised.",
                "sector": "Energy",
                "severity": "Critical"
            },
            {
                "text": "Bank of India reports data breach affecting customer accounts. Personal information of thousands of customers exposed.",
                "sector": "Finance",
                "severity": "High"
            },
            # Add more from the initial examples
            {
                "text": "Healthcare records of patients from major Delhi hospital leaked online. Medical histories and personal details compromised.",
                "sector": "Healthcare",
                "severity": "High"
            },
            {
                "text": "Indian government websites defaced by Pakistani hacker group. No sensitive data reported stolen.",
                "sector": "Government",
                "severity": "Medium"
            }
        ]
        
        training_data.extend(synthetic_examples)
    
    # Convert sectors and severities to numeric values
    sector_mapping = {sector: i for i, sector in enumerate(INCIDENT_SECTORS)}
    severity_mapping = {severity: i for i, severity in enumerate(INCIDENT_SEVERITY)}
    
    # Create DataFrame
    df = pd.DataFrame(training_data)
    
    # Convert text labels to numeric
    df['sector_id'] = df['sector'].map(sector_mapping)
    df['severity_id'] = df['severity'].map(severity_mapping)
    
    # Handle missing values
    df['sector_id'].fillna(sector_mapping.get('Other', 0), inplace=True)
    df['severity_id'].fillna(severity_mapping.get('Medium', 2), inplace=True)
    
    # Split into features and targets
    X = df['text']
    y = df[['sector_id', 'severity_id']]
    
    # Split into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Create pipeline with TF-IDF and Multi-output Random Forest
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(max_features=5000, ngram_range=(1, 2))),
        ('classifier', MultiOutputClassifier(RandomForestClassifier(n_estimators=100, random_state=42)))
    ])
    
    # Train the model
    pipeline.fit(X_train, y_train)
    
    # Evaluate the model
    y_pred = pipeline.predict(X_test)
    
    # Calculate metrics
    accuracy_sector = accuracy_score(y_test['sector_id'], y_pred[:, 0])
    accuracy_severity = accuracy_score(y_test['severity_id'], y_pred[:, 1])
    
    avg_accuracy = (accuracy_sector + accuracy_severity) / 2
    
    logger.info(f"Retrained incident classifier with accuracy: sector={accuracy_sector:.4f}, severity={accuracy_severity:.4f}")
    
    # Save the model
    model_path = os.path.join(MODEL_PATH, INCIDENT_CLASSIFIER_MODEL)
    
    # Also save the mappings with the model for later use
    model_data = {
        'pipeline': pipeline,
        'sector_mapping': sector_mapping,
        'severity_mapping': severity_mapping
    }
    
    with open(model_path, 'wb') as f:
        pickle.dump(model_data, f)
    
    # Get the current version from the database
    current_model = MLModel.query.filter_by(model_type="incident_classifier", is_active=True).first()
    
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
        name="Incident Classifier",
        model_type="incident_classifier",
        version=version,
        accuracy=float(avg_accuracy),
        f1_score=0.0,  # Not calculated for this model
        training_date=datetime.utcnow(),
        is_active=True
    )
    
    db.session.add(model_record)
    db.session.commit()
    
    return model_data
