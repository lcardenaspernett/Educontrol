"""
Rutas de autenticación para EduControl - SECURIZADO
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_user, logout_user, current_user
from datetime import datetime
import logging
from urllib.parse import urlparse
from app import db, limiter
from app.models.user import User

# Crear blueprint
auth_bp = Blueprint('auth', __name__)

# Logger de seguridad
security_logger = logging.getLogger('security')

def log_security_event(event_type, details, success=True):
    """🔒 Helper para logging de eventos de seguridad"""
    log_data = {
        'event': event_type,
        'ip': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', 'Unknown')[:200],  # Limitar longitud
        'timestamp': datetime.utcnow().isoformat(),
        'details': details,
        'success': success
    }
    
    if success:
        security_logger.info(f"SECURITY_EVENT: {log_data}")
        current_app.logger.info(f"Security: {event_type} - {details}")
    else:
        security_logger.warning(f"SECURITY_WARNING: {log_data}")
        current_app.logger.warning(f"Security: {event_type} FAILED - {details}")

def is_safe_url(target):
    """🔒 Verificar que la URL de redirección sea segura"""
    ref_url = urlparse(request.host_url)
    test_url = urlparse(target)
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")  # 🔒 CRÍTICO: Máximo 5 intentos por minuto por IP
def login():
    """Página de inicio de sesión - SECURIZADA"""
    
    # Si ya está autenticado, redirigir al dashboard
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        # 🔒 Obtener y sanitizar datos de entrada
        email_or_username = request.form.get('email_or_username', '').strip().lower()
        password = request.form.get('password', '')
        remember_me = bool(request.form.get('remember_me'))
        
        # 🔒 Validaciones básicas de entrada
        if not email_or_username or not password:
            log_security_event('LOGIN_ATTEMPT', f'Campos vacíos para entrada: {email_or_username}', False)
            flash('Por favor, completa todos los campos', 'error')
            return render_template('auth/login.html')
        
        # 🔒 Validar longitud para prevenir ataques
        if len(email_or_username) > 120 or len(password) > 200:
            log_security_event('LOGIN_ATTEMPT', f'Entrada demasiado larga: {email_or_username}', False)
            flash('Datos de entrada inválidos', 'error')
            return render_template('auth/login.html')
        
        # 🔒 Validar caracteres peligrosos básicos
        dangerous_chars = ['<', '>', '"', "'", '&', 'script', 'javascript']
        if any(char in email_or_username.lower() or char in password.lower() for char in dangerous_chars):
            log_security_event('LOGIN_ATTEMPT', f'Caracteres peligrosos detectados: {email_or_username}', False)
            flash('Caracteres no válidos detectados', 'error')
            return render_template('auth/login.html')
        
        # 🔒 Log del intento de login
        log_security_event('LOGIN_ATTEMPT', f'Usuario: {email_or_username}', True)
        
        # Buscar usuario por email o username
        try:
            user = User.query.filter(
                (User.email == email_or_username) | 
                (User.username == email_or_username)
            ).first()
        except Exception as e:
            current_app.logger.error(f"Error en consulta de usuario: {e}")
            log_security_event('LOGIN_ERROR', f'Error DB al buscar usuario: {str(e)}', False)
            flash('Error interno. Intenta de nuevo.', 'error')
            return render_template('auth/login.html')
        
        if user and user.check_password(password):
            # 🔒 Verificar si la cuenta está activa
            if not user.is_active:
                log_security_event('LOGIN_BLOCKED', f'Cuenta desactivada: {user.email}', False)
                flash('Tu cuenta está desactivada. Contacta al administrador.', 'error')
                return render_template('auth/login.html')
            
            try:
                # 🔒 Actualizar último acceso de forma segura
                user.last_login = datetime.utcnow()
                db.session.commit()
                
                # 🔒 Iniciar sesión
                login_user(user, remember=remember_me)
                
                # 🔒 Log exitoso
                log_security_event('LOGIN_SUCCESS', f'Usuario: {user.email}, Rol: {user.role}', True)
                
                flash(f'¡Bienvenido, {user.full_name}!', 'success')
                
                # Redirigir según el siguiente destino o dashboard
                next_page = request.args.get('next')
                if next_page and is_safe_url(next_page):
                    return redirect(next_page)
                
                return redirect(url_for('main.dashboard'))
                
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error al actualizar último login: {e}")
                log_security_event('LOGIN_ERROR', f'Error DB para {user.email}: {str(e)}', False)
                flash('Error interno durante el login', 'error')
                
        else:
            # 🔒 Log de credenciales incorrectas (SIN revelar si el usuario existe)
            log_security_event('LOGIN_FAILED', f'Credenciales incorrectas para: {email_or_username}', False)
            flash('Credenciales incorrectas', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    """Cerrar sesión - SECURIZADO"""
    if current_user.is_authenticated:
        # 🔒 Log del logout
        log_security_event('LOGOUT', f'Usuario: {current_user.email}', True)
        flash(f'Hasta luego, {current_user.full_name}', 'info')
    
    logout_user()
    return redirect(url_for('main.index'))

@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("3 per hour")  # 🔒 Limitar registros: máximo 3 por hora
def register():
    """Registro restringido - SOLO para desarrollo"""
    
    # 🔒 CRÍTICO: Deshabilitar en producción
    if current_app.config.get('ENV') == 'production':
        log_security_event('REGISTRATION_BLOCKED', 'Intento de registro en producción', False)
        flash('El registro público está deshabilitado', 'error')
        return redirect(url_for('auth.login'))
    
    # 🔒 CRÍTICO: Solo roles seguros por defecto
    ALLOWED_ROLES = ['student', 'parent']  # NO admin ni superadmin
    
    if request.method == 'POST':
        data = request.form
        
        # 🔒 LOGGING DE REGISTRO
        log_security_event('REGISTRATION_ATTEMPT', f'Email: {data.get("email")}, IP: {request.remote_addr}', True)
        
        # 🔒 Validaciones básicas
        required_fields = ['full_name', 'email', 'username', 'password', 'password_confirm']
        for field in required_fields:
            if not data.get(field):
                flash(f'El campo {field} es obligatorio', 'error')
                return render_template('auth/register.html', allowed_roles=ALLOWED_ROLES)
        
        # 🔒 Validar rol permitido
        role = data.get('role', 'student')
        if role not in ALLOWED_ROLES:
            log_security_event('REGISTRATION_BLOCKED', f'Rol no permitido: {role}', False)
            flash('Rol no permitido para registro público', 'error')
            return render_template('auth/register.html', allowed_roles=ALLOWED_ROLES)
        
        # 🔒 Validar confirmación de contraseña
        if data['password'] != data['password_confirm']:
            flash('Las contraseñas no coinciden', 'error')
            return render_template('auth/register.html', allowed_roles=ALLOWED_ROLES)
        
        # 🔒 Validar longitud de contraseña
        if len(data['password']) < 6:
            flash('La contraseña debe tener al menos 6 caracteres', 'error')
            return render_template('auth/register.html', allowed_roles=ALLOWED_ROLES)
        
        # Validaciones de duplicados
        email = data['email'].lower().strip()
        username = data['username'].lower().strip()
        
        if User.query.filter_by(email=email).first():
            log_security_event('REGISTRATION_FAILED', f'Email duplicado: {email}', False)
            flash('El email ya está registrado', 'error')
            return render_template('auth/register.html', allowed_roles=ALLOWED_ROLES)
        
        if User.query.filter_by(username=username).first():
            log_security_event('REGISTRATION_FAILED', f'Username duplicado: {username}', False)
            flash('El username ya está en uso', 'error')
            return render_template('auth/register.html', allowed_roles=ALLOWED_ROLES)
        
        try:
            # Crear usuario con rol restringido
            user = User(
                full_name=data['full_name'].strip(),
                email=email,
                username=username,
                role=role,  # Solo roles permitidos
                is_active=False  # 🔒 Requiere activación manual
            )
            user.set_password(data['password'])
            
            db.session.add(user)
            db.session.commit()
            
            log_security_event('REGISTRATION_SUCCESS', f'Usuario registrado: {user.email}', True)
            flash('Usuario registrado. Espera la activación del administrador.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error en registro: {str(e)}")
            log_security_event('REGISTRATION_ERROR', f'Error DB: {str(e)}', False)
            flash('Error al procesar el registro', 'error')
    
    return render_template('auth/register.html', allowed_roles=ALLOWED_ROLES)

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
@limiter.limit("3 per hour")  # 🔒 Limitar solicitudes de recuperación
def forgot_password():
    """Recuperación de contraseña - SECURIZADO"""
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        # 🔒 Log de intento de recuperación
        log_security_event('PASSWORD_RECOVERY_ATTEMPT', f'Email: {email}', True)
        
        if not email:
            flash('Por favor, ingresa tu email', 'error')
            return render_template('auth/forgot_password.html')
        
        # Buscar usuario (sin revelar si existe o no)
        user = User.query.filter_by(email=email).first()
        
        if user:
            log_security_event('PASSWORD_RECOVERY_VALID', f'Usuario encontrado: {email}', True)
            # En producción, enviar email con token de reset
            flash('Si el email existe, se ha enviado un enlace de recuperación', 'info')
        else:
            log_security_event('PASSWORD_RECOVERY_INVALID', f'Email no encontrado: {email}', False)
            # Mensaje genérico por seguridad (no revelar si el email existe)
            flash('Si el email existe, se ha enviado un enlace de recuperación', 'info')
    
    return render_template('auth/forgot_password.html')