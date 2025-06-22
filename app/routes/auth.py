"""
Rutas de autenticación para EduControl
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, logout_user, current_user
from datetime import datetime
from app import db
from app.models.user import User

# Crear blueprint
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Página de inicio de sesión"""
    
    # Si ya está autenticado, redirigir al dashboard
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        email_or_username = request.form.get('email_or_username', '').strip()
        password = request.form.get('password', '')
        remember_me = bool(request.form.get('remember_me'))
        
        if not email_or_username or not password:
            flash('Por favor, completa todos los campos', 'error')
            return render_template('auth/login.html')
        
        # Buscar usuario por email o username
        user = User.query.filter(
            (User.email == email_or_username) | 
            (User.username == email_or_username)
        ).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Tu cuenta está desactivada. Contacta al administrador.', 'error')
                return render_template('auth/login.html')
            
            # Actualizar último acceso
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Iniciar sesión
            login_user(user, remember=remember_me)
            
            flash(f'¡Bienvenido, {user.full_name}!', 'success')
            
            # Redirigir según el rol
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            
            return redirect(url_for('main.dashboard'))
        else:
            flash('Credenciales incorrectas', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    """Cerrar sesión"""
    if current_user.is_authenticated:
        flash(f'Hasta luego, {current_user.full_name}', 'info')
    
    logout_user()
    return redirect(url_for('main.index'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Registro de nuevos usuarios (solo para desarrollo)"""
    
    # En producción, deshabilitar o restringir este endpoint
    if request.method == 'POST':
        data = request.form
        
        # Validaciones básicas
        if User.query.filter_by(email=data['email']).first():
            flash('El email ya está registrado', 'error')
            return render_template('auth/register.html')
        
        if User.query.filter_by(username=data['username']).first():
            flash('El username ya está en uso', 'error')
            return render_template('auth/register.html')
        
        # Crear usuario
        user = User(
            full_name=data['full_name'],
            email=data['email'],
            username=data['username'],
            role=data.get('role', 'student'),
            is_active=True
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        flash('Usuario registrado exitosamente', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Recuperación de contraseña"""
    
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            # En producción, enviar email con token de reset
            flash('Se ha enviado un enlace de recuperación a tu email', 'info')
        else:
            flash('No se encontró un usuario con ese email', 'error')
    
    return render_template('auth/forgot_password.html')