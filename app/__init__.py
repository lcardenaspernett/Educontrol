"""
Inicialización de la aplicación Flask EduControl - SECURIZADO CON TALISMAN
"""

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
import logging
from logging.handlers import RotatingFileHandler
import os
from config import config

# Inicializar extensiones
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
bootstrap = Bootstrap()

# 🔒 Rate Limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Configurar Flask-Login
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Debes iniciar sesión para acceder a esta página.'
login_manager.login_message_category = 'info'

def create_app(config_name='default'):
    """Factory para crear la aplicación Flask"""
    app = Flask(__name__, 
                static_folder='static',
                static_url_path='/static',
                template_folder='templates')
    
    app.config.from_object(config[config_name])

    # Inicializar extensiones
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bootstrap.init_app(app)
    limiter.init_app(app)

    # 🔒 NUEVO: Configurar Flask-Talisman para headers de seguridad
    configure_security_headers(app)

    # Configurar logging
    configure_logging(app)

    # Importar modelos
    from app.models import user, institution

    # Registrar blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.superadmin import superadmin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(superadmin_bp, url_prefix='/superadmin')

    # User loader para Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))

    # Context processors globales
    @app.context_processor
    def inject_config():
        return {
            'APP_NAME': app.config.get('APP_NAME'),
            'APP_VERSION': app.config.get('APP_VERSION')
        }

    # Manejadores de errores
    register_error_handlers(app)

    # Debug en desarrollo
    if app.debug:
        @app.route('/debug/static')
        def debug_static():
            import os
            static_path = os.path.join(app.root_path, 'static')
            files = []
            for root, dirs, filenames in os.walk(static_path):
                for filename in filenames:
                    rel_path = os.path.relpath(os.path.join(root, filename), static_path)
                    files.append(rel_path)
            return f"<h3>Archivos estáticos encontrados:</h3><ul>{''.join([f'<li>{f}</li>' for f in files])}</ul>"

    return app

def configure_security_headers(app):
    """🔒 Configurar headers de seguridad con Flask-Talisman"""
    
    # Solo aplicar en producción o si se especifica
    if not app.debug or os.environ.get('FORCE_HTTPS_HEADERS') == 'true':
        # Configuración ESTRICTA para producción
        csp = {
            'default-src': "'self'",
            'script-src': [
                "'self'",
                "'unsafe-inline'",  # Necesario para Bootstrap
                "https://cdn.jsdelivr.net",
                "https://cdnjs.cloudflare.com"
            ],
            'style-src': [
                "'self'",
                "'unsafe-inline'",  # Necesario para estilos inline
                "https://cdn.jsdelivr.net",
                "https://cdnjs.cloudflare.com",
                "https://fonts.googleapis.com"
            ],
            'img-src': [
                "'self'",
                "data:",
                "https:"
            ],
            'font-src': [
                "'self'",
                "https://cdnjs.cloudflare.com",
                "https://fonts.gstatic.com"
            ],
            'connect-src': "'self'",
            'frame-ancestors': "'none'",
            'base-uri': "'self'"
        }
        
        # Sintaxis simplificada para Talisman
        Talisman(app, content_security_policy=csp)
        
        app.logger.info('Headers de seguridad ESTRICTOS aplicados (Produccion)')
        
    else:
        # Configuración RELAJADA para desarrollo
        csp = {
            'default-src': "'self'",
            'script-src': [
                "'self'",
                "'unsafe-inline'",
                "'unsafe-eval'",  # Para desarrollo
                "https://cdn.jsdelivr.net",
                "https://cdnjs.cloudflare.com"
            ],
            'style-src': [
                "'self'",
                "'unsafe-inline'",
                "https://cdn.jsdelivr.net",
                "https://cdnjs.cloudflare.com",
                "https://fonts.googleapis.com"
            ],
            'img-src': [
                "'self'",
                "data:",
                "https:",
                "http:"  # Para desarrollo
            ],
            'font-src': [
                "'self'",
                "https://cdnjs.cloudflare.com",
                "https://fonts.gstatic.com"
            ],
            'connect-src': "'self'"
        }
        
        # Sintaxis simplificada para desarrollo
        Talisman(app, content_security_policy=csp, force_https=False)
        
        app.logger.info('Headers de seguridad RELAJADOS aplicados (Desarrollo)')

def configure_logging(app):
    """🔒 Configurar sistema de logging"""
    # Crear directorio de logs si no existe
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    if not app.debug and not app.testing:
        # PRODUCCIÓN: Logging completo a archivos
        file_handler = RotatingFileHandler(
            'logs/educontrol.log', maxBytes=10240000, backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        
        # Logger de seguridad
        security_handler = RotatingFileHandler(
            'logs/security.log', maxBytes=10240000, backupCount=20
        )
        security_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s'
        ))
        security_handler.setLevel(logging.INFO)
        
        security_logger = logging.getLogger('security')
        security_logger.addHandler(security_handler)
        security_logger.setLevel(logging.INFO)
        security_logger.propagate = False
        
        app.logger.info('EduControl startup - Security logging enabled (PRODUCTION)')
    else:
        # DESARROLLO: Log a consola Y archivos para testing
        app.logger.setLevel(logging.INFO)
        
        # Handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s'
        ))
        app.logger.addHandler(console_handler)
        
        # Logs de seguridad en desarrollo
        security_handler = RotatingFileHandler(
            'logs/security.log', maxBytes=10240000, backupCount=20
        )
        security_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s'
        ))
        security_handler.setLevel(logging.INFO)
        
        security_logger = logging.getLogger('security')
        security_logger.addHandler(security_handler)
        security_logger.setLevel(logging.INFO)
        security_logger.propagate = False
        
        # Logger general también a archivo en desarrollo
        file_handler = RotatingFileHandler(
            'logs/educontrol.log', maxBytes=10240000, backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.info('EduControl startup - Security logging enabled (DEBUG mode)')

def register_error_handlers(app):
    """🔒 Registrar manejadores de errores globales"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.warning(f'404 - Página no encontrada: {error}')
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden_error(error):
        app.logger.warning(f'403 - Acceso denegado: {error}')
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.error(f'500 - Error interno: {error}')
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(429)
    def ratelimit_handler(e):
        app.logger.warning(f'429 - Rate limit excedido: {e.description}')
        return render_template('errors/429.html'), 429