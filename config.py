import os
import secrets
from datetime import timedelta

def validate_environment():
    """Validate required environment variables"""
    warnings = []
    
    if not os.environ.get('SECRET_KEY'):
        warnings.append("SECRET_KEY not set - using generated key")
    
    if not os.environ.get('DATABASE_URL'):
        warnings.append("DATABASE_URL not set - using SQLite")
        
    if os.environ.get('FLASK_ENV') == 'production' and not os.environ.get('SECRET_KEY'):
        raise RuntimeError("SECRET_KEY must be set in production!")
        
    return warnings

class Config:
    """Base configuration."""
    # Validate environment
    warnings = validate_environment()
    for warning in warnings:
        print(f"WARNING: {warning}")
    
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///rubiks_cube.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Upload configuration
    UPLOAD_FOLDER = 'static/uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    
class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
