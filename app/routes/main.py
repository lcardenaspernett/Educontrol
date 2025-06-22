"""
Rutas principales de la aplicación EduControl
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user, logout_user
from app import db
from app.models.user import User
from app.models.institution import Institution
from app.auth.decorators import login_required_custom

# Crear blueprint
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Página principal de la aplicación"""
    
    # Si el usuario está autenticado, redirigir al dashboard
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required_custom
def dashboard():
    """Dashboard principal según el rol del usuario"""
    
    # Redirigir según el rol del usuario
    if current_user.role == 'superadmin':
        return redirect(url_for('superadmin.dashboard'))
    
    # Para otros roles, mostrar dashboard general
    return render_template('dashboard.html')

@main_bp.route('/profile')
@login_required_custom
def profile():
    """Perfil del usuario"""
    return render_template('profile.html')

@main_bp.route('/settings')
@login_required_custom
def settings():
    """Configuración del usuario"""
    return render_template('settings.html')

@main_bp.route('/health')
def health_check():
    """Endpoint de verificación de salud de la aplicación"""
    try:
        # Verificar conexión a la base de datos
        db.session.execute('SELECT 1')
        
        return {
            'status': 'healthy',
            'database': 'connected',
            'timestamp': '2025-06-22T12:00:00Z'
        }, 200
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': '2025-06-22T12:00:00Z'
        }, 500

@main_bp.route('/about')
def about():
    """Información sobre la aplicación"""
    return render_template('about.html')

# Manejadores de errores
@main_bp.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@main_bp.errorhandler(403)
def forbidden_error(error):
    return render_template('errors/403.html'), 403

@main_bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500