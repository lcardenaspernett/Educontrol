import os
from dotenv import load_dotenv

# Cargar variables de entorno
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    """Configuración base del sistema"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'clave-super-secreta-para-desarrollo'
    
    # Base de datos - SQLite por defecto
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'educontrol.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuración de aplicación
    APP_NAME = os.environ.get('APP_NAME') or 'EduControl'
    APP_VERSION = os.environ.get('APP_VERSION') or '1.0.0'
    
    # Configuración de formularios
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    
    # Configuración de Bootstrap
    BOOTSTRAP_SERVE_LOCAL = True
    
class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False
    TESTING = False

class TestingConfig(Config):
    """Configuración para pruebas"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# Diccionario de configuraciones
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
