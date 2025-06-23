"""
Inicialización de la aplicación Flask EduControl - SECURIZADO CON TALISMAN
ACTUALIZADO para compatibilidad completa con SuperAdmin
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
    """Factory para crear la aplicación Flask - VERSIÓN COMPATIBLE WINDOWS"""
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

    # Configurar Flask-Talisman para headers de seguridad
    configure_security_headers(app)

    # Configurar logging (SIN EMOJIS)
    configure_logging(app)

    # Importar modelos ANTES de registrar blueprints
    from app.models import user, institution
    # Importar modelo course si existe
    try:
        from app.models import course
        app.logger.info('Modelo Course cargado correctamente')
    except ImportError:
        app.logger.info('Modelo Course no encontrado - Algunas funciones estarán limitadas')

    # Registrar blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.superadmin import superadmin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(superadmin_bp, url_prefix='/superadmin')

    # Crear directorio de uploads si no existe
    uploads_dir = os.path.join(app.root_path, 'uploads')
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)
        app.logger.info('Directorio uploads creado')

    # Crear directorio de backups si no existe
    backups_dir = os.path.join(os.path.dirname(app.root_path), 'backups')
    if not os.path.exists(backups_dir):
        os.makedirs(backups_dir)
        app.logger.info('Directorio backups creado')

    # User loader para Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))

    # Context processors globales
    @app.context_processor
    def inject_config():
        return {
            'APP_NAME': app.config.get('APP_NAME', 'EduControl'),
            'APP_VERSION': app.config.get('APP_VERSION', '1.0.2')
        }

    # Context processor para utilidades
    @app.context_processor
    def utility_processor():
        """Inyectar funciones útiles en templates"""
        from datetime import datetime
        return {
            'now': datetime.utcnow(),
            'moment': lambda: datetime.utcnow()  # Para usar en templates como {{ moment() }}
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
        
        @app.route('/debug/routes')
        def debug_routes():
            """Mostrar todas las rutas registradas"""
            import urllib
            output = []
            for rule in app.url_map.iter_rules():
                methods = ','.join(rule.methods - {'HEAD', 'OPTIONS'})
                line = urllib.parse.unquote(f"{rule.endpoint:50s} {methods:20s} {rule}")
                output.append(line)
            
            return f"<h3>Rutas registradas:</h3><pre>{'<br>'.join(sorted(output))}</pre>"

    return app

def configure_security_headers(app):
    """Configurar headers de seguridad con Flask-Talisman - SIN EMOJIS"""
    
    # Solo aplicar en producción o si se especifica
    if not app.debug or os.environ.get('FORCE_HTTPS_HEADERS') == 'true':
        # Configuración ESTRICTA para producción
        csp = {
            'default-src': "'self'",
            'script-src': [
                "'self'",
                "'unsafe-inline'",  # Necesario para el dashboard
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
        
        Talisman(app, content_security_policy=csp)
        app.logger.info('Headers de seguridad ESTRICTOS aplicados (Produccion)')
        
    else:
        # Configuración RELAJADA para desarrollo
        csp = {
            'default-src': "'self'",
            'script-src': [
                "'self'",
                "'unsafe-inline'",
                "'unsafe-eval'",  # Para desarrollo y Chart.js
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
        
        Talisman(app, content_security_policy=csp, force_https=False)
        app.logger.info('Headers de seguridad RELAJADOS aplicados (Desarrollo)')

def configure_logging(app):
    """Configurar sistema de logging compatible con Windows"""
    # Crear directorio de logs si no existe
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    if not app.debug and not app.testing:
        # PRODUCCIÓN: Logging completo a archivos
        file_handler = RotatingFileHandler(
            'logs/educontrol.log', maxBytes=10240000, backupCount=10, encoding='utf-8'
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
        
        # Handler para consola SIN EMOJIS (compatible con Windows)
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
    """Registrar manejadores de errores globales - COMPATIBLE WINDOWS"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.warning(f'404 - Página no encontrada: {error} - URL: {request.url if "request" in globals() else "unknown"}')
        try:
            return render_template('errors/404.html'), 404
        except:
            return '<h1>404 - Página no encontrada</h1>', 404

    @app.errorhandler(403)
    def forbidden_error(error):
        app.logger.warning(f'403 - Acceso denegado: {error}')
        try:
            return render_template('errors/403.html'), 403
        except:
            return '<h1>403 - Acceso denegado</h1>', 403

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.error(f'500 - Error interno: {error}')
        try:
            return render_template('errors/500.html'), 500
        except:
            return '<h1>500 - Error interno del servidor</h1>', 500
    
    @app.errorhandler(429)
    def ratelimit_handler(e):
        # Logging de seguridad para rate limiting
        security_logger = logging.getLogger('security')
        security_logger.warning(f'RATE_LIMIT_EXCEEDED - IP: {get_remote_address()} - Description: {e.description}')
        
        try:
            return render_template('errors/429.html'), 429
        except:
            return '<h1>429 - Demasiadas solicitudes</h1><p>Has excedido el límite de solicitudes. Intenta más tarde.</p>', 429

    @app.errorhandler(413)
    def file_too_large(error):
        """Manejo de archivos demasiado grandes"""
        app.logger.warning(f'413 - Archivo demasiado grande: {error}')
        try:
            return render_template('errors/413.html'), 413
        except:
            return '<h1>413 - Archivo demasiado grande</h1>', 413

# Función auxiliar para verificar dependencias opcionales
def check_optional_dependencies(app):
    """Verificar dependencias opcionales y registrar estado"""
    dependencies = {}
    
    # Verificar psutil para monitoreo del sistema
    try:
        import psutil
        dependencies['psutil'] = True
        app.logger.info('psutil disponible - Monitoreo del sistema habilitado')
    except ImportError:
        dependencies['psutil'] = False
        app.logger.info('psutil no disponible - Monitoreo del sistema limitado')
    
    # Verificar otras dependencias
    optional_deps = ['redis', 'celery', 'pillow']
    for dep in optional_deps:
        try:
            __import__(dep)
            dependencies[dep] = True
            app.logger.info(f'{dep} disponible')
        except ImportError:
            dependencies[dep] = False
            app.logger.info(f'{dep} no disponible')
    
    return dependencies

# Función para validar configuración
def validate_config(app):
    """Validar configuración crítica"""
    required_configs = ['SECRET_KEY', 'DATABASE_URL']
    missing_configs = []
    
    for config_key in required_configs:
        if not app.config.get(config_key):
            missing_configs.append(config_key)
    
    if missing_configs:
        app.logger.error(f'❌ Configuraciones faltantes: {", ".join(missing_configs)}')
        raise RuntimeError(f'Configuraciones requeridas faltantes: {missing_configs}')
    else:
        app.logger.info('✅ Configuración validada correctamente')

# Función para inicializar datos de prueba (solo en desarrollo)
def init_development_data(app):
    """Inicializar datos de desarrollo si es necesario"""
    if app.debug and app.config.get('INIT_SAMPLE_DATA', False):
        with app.app_context():
            from app.models.user import User
            from app.models.institution import Institution
            
            # Verificar si ya existen datos
            if User.query.count() == 0:
                app.logger.info('🔧 Inicializando datos de desarrollo...')
                # Aquí puedes agregar lógica para crear datos de prueba
                # create_sample_institutions()
                # create_sample_users()
                pass
            else:
                app.logger.info('📊 Datos de desarrollo ya existentes')

def create_app_with_validation(config_name='default'):
    """Crear aplicación con validaciones completas - COMPATIBLE WINDOWS"""
    app = create_app(config_name)
    
    with app.app_context():
        # Validar configuración
        validate_config(app)
        
        # Verificar dependencias opcionales
        dependencies = check_optional_dependencies(app)
        
        # Inicializar datos de desarrollo si es necesario
        if app.debug:
            init_development_data(app)
        
        app.logger.info('🎉 EduControl inicializado correctamente')
        app.logger.info(f'🔧 Modo: {"Desarrollo" if app.debug else "Producción"}')
        app.logger.info(f'📊 Base de datos: {app.config.get("DATABASE_URL", "No configurada")[:50]}...')
    
    return app