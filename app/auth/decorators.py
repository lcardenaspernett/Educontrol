"""
Decoradores para control de acceso y autorización
"""

from functools import wraps
from flask import abort, redirect, url_for, flash
from flask_login import current_user, login_required

def require_role(*roles):
    """
    Decorador que requiere que el usuario tenga uno de los roles especificados
    Uso: @require_role('superadmin', 'admin')
    """
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            
            if not current_user.is_active:
                flash('Tu cuenta está desactivada. Contacta al administrador.', 'error')
                return redirect(url_for('auth.login'))
            
            if current_user.role not in roles:  # Corregido: rol -> role
                abort(403)  # Forbidden
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def superadmin_required(f):
    """
    Decorador que requiere rol de superadministrador
    """
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        if not current_user.is_active:
            flash('Tu cuenta está desactivada. Contacta al administrador.', 'error')
            return redirect(url_for('auth.login'))
        
        if current_user.role != 'superadmin':  # Simplificado
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """
    Decorador que requiere rol de administrador (superadmin o admin)
    """
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        if not current_user.is_active:
            flash('Tu cuenta está desactivada. Contacta al administrador.', 'error')
            return redirect(url_for('auth.login'))
        
        if current_user.role not in ['superadmin', 'admin']:  # Simplificado
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function

def same_institution_required(f):
    """
    Decorador que requiere que el usuario pertenezca a la misma institución
    o sea superadministrador
    """
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        if not current_user.is_active:
            flash('Tu cuenta está desactivada. Contacta al administrador.', 'error')
            return redirect(url_for('auth.login'))
        
        # Los superadmin pueden acceder a todo
        if current_user.role == 'superadmin':  # Simplificado
            return f(*args, **kwargs)
        
        # Verificar institución si se proporciona en los argumentos
        institucion_id = kwargs.get('institucion_id')
        if institucion_id and not current_user.can_access_institution(institucion_id):
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function

def login_required_custom(f):
    """
    Decorador personalizado para login que incluye verificación de cuenta activa
    """
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        if not current_user.is_active:
            flash('Tu cuenta está desactivada. Contacta al administrador.', 'error')
            return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    return decorated_function