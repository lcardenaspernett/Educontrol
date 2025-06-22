"""
Inicialización de la aplicación Flask EduControl
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from config import config

# Inicializar extensiones
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
bootstrap = Bootstrap()

# Configurar Flask-Login
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Debes iniciar sesión para acceder a esta página.'
login_manager.login_message_category = 'info'

def create_app(config_name='default'):
    """Factory para crear la aplicación Flask"""
    # AQUÍ ESTÁ LA CORRECCIÓN - Especificar rutas de archivos estáticos
    app = Flask(__name__, 
                static_folder='static',           # Carpeta de archivos estáticos
                static_url_path='/static',        # URL base para archivos estáticos
                template_folder='templates')      # Carpeta de templates
    
    app.config.from_object(config[config_name])

    # Inicializar extensiones con la app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bootstrap.init_app(app)

    # Importar modelos (necesario para las migraciones)
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

    # OPCIONAL: Debug de rutas estáticas en desarrollo
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