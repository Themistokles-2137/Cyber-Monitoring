"""
Route modules for the Flask application.
"""

# Import all route blueprints to make them available when the package is imported
from .main_routes import main
from .dashboard_routes import dashboard
from .api_routes import api

__all__ = ['main', 'dashboard', 'api']
