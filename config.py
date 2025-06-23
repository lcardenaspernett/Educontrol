import os
from datetime import timedelta
from dotenv import load_dotenv

# Cargar variables de entorno
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    """Configuración base del sistema - SECURIZADA"""
    
    # 🔒 CRÍTICO: Secret key obligatoria desde entorno
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("❌ CRÍTICO: SECRET_KEY debe estar definida en .env")
    
    # Verificar longitud mínima de SECRET_KEY
    if len(SECRET_KEY) < 32:
        raise ValueError("❌ CRÍTICO: SECRET_KEY debe tener al menos 32 caracteres")
    
    # Base de datos - SQLite por defecto
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'educontrol.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 🔒 Configuración de seguridad de sesiones
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(seconds=int(os.environ.get('PERMANENT_SESSION_LIFETIME', 28800)))  # 8 horas por defecto
    
    # Configuración de aplicación
    APP_NAME = os.environ.get('APP_NAME') or 'EduControl'
    APP_VERSION = os.environ.get('APP_VERSION') or '1.0.0'
    
    # 🔒 Configuración de formularios CSRF
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hora
    
    # Configuración de Bootstrap
    BOOTSTRAP_SERVE_LOCAL = True
    
    # 🔒 Configuración de Rate Limiting
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL') or 'memory://'
    RATELIMIT_DEFAULT = "200 per day;50 per hour"

class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True
    TESTING = False
    
    # En desarrollo, cookies pueden ser menos estrictas
    SESSION_COOKIE_SECURE = False

class ProductionConfig(Config):
    """Configuración para producción - MÁXIMA SEGURIDAD"""
    DEBUG = False
    TESTING = False
    
    # 🔒 Configuraciones estrictas de seguridad para producción
    SESSION_COOKIE_SECURE = True  # Solo HTTPS
    SESSION_COOKIE_SAMESITE = 'Strict'  # Más estricto
    
    # 🔒 Headers de seguridad adicionales
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000  # 1 año
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    
    # Rate limiting más estricto en producción
    RATELIMIT_DEFAULT = "100 per day;20 per hour"

class TestingConfig(Config):
    """Configuración para pruebas"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    
    # Rate limiting más permisivo para tests
    RATELIMIT_ENABLED = False

# Diccionario de configuraciones
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

# 🔒 Validación de configuración al importar
def validate_config():
    """Valida que la configuración sea segura"""
    required_vars = ['SECRET_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        raise ValueError(f"❌ Variables de entorno faltantes: {', '.join(missing_vars)}")

# Ejecutar validación
try:
    validate_config()
    print("✅ Configuración validada correctamente")
except ValueError as e:
    print(f"🚨 Error de configuración: {e}")
    print("💡 Asegúrate de tener un archivo .env con todas las variables necesarias")