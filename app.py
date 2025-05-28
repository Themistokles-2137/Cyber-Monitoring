import os
import logging
from markupsafe import Markup, escape

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix


# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key_for_development")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# configure the database, relative to the app instance folder
# Use SQLite for now to avoid PostgreSQL connectivity issues
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///cyber_incidents.db"
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# initialize the app with the extension
db.init_app(app)

# Import routes after app is created
from routes import main, dashboard, api

# Custom Jinja2 filters
@app.template_filter('nl2br')
def nl2br(value):
    """Convert newlines to HTML line breaks."""
    if value:
        value = str(value)
        return Markup(escape(value).replace('\n', '<br>\n'))
    return ''

# Register blueprints
app.register_blueprint(main)
app.register_blueprint(dashboard)
app.register_blueprint(api)

with app.app_context():
    # Import models
    import models  # noqa: F401
    
    # Create all tables
    db.create_all()
    
    # Initialize ML models if needed
    from ml.source_classifier import initialize_model as init_source_model
    from ml.incident_classifier import initialize_model as init_incident_model
    
    init_source_model()
    init_incident_model()
