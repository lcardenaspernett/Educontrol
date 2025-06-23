"""
Rutas para el Dashboard de Administrador Institucional
Gestión específica de cada institución por sus administradores
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func, and_, desc, or_
from datetime import datetime, timedelta
import logging
from functools import wraps

from app import db
from app.models.user import User
from app.models.institution import Institution
from app.models.course import Course
from app.auth.decorators import require_role

# Logger de seguridad
security_logger = logging.getLogger('security')

# Crear blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Decorador para verificar que el usuario sea admin y tenga institución
def admin_required(f):
    """Decorador para verificar que el usuario sea admin institucional"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        if current_user.role != 'admin':
            security_logger.warning(f'ADMIN_ACCESS_DENIED - User: {current_user.email} - Role: {current_user.role} - IP: {request.remote_addr}')
            flash('Acceso denegado. Se requieren permisos de administrador.', 'error')
            return redirect(url_for('main.index'))
        
        if not current_user.institution_id:
            security_logger.warning(f'ADMIN_NO_INSTITUTION - User: {current_user.email} - IP: {request.remote_addr}')
            flash('No tienes una institución asignada. Contacta al superadministrador.', 'error')
            return redirect(url_for('main.index'))
        
        return f(*args, **kwargs)
    return decorated_function

# ================== FUNCIONES AUXILIARES ==================

def get_institution_stats(institution_id):
    """Obtiene estadísticas específicas de la institución"""
    try:
        # Estadísticas básicas
        total_students = User.query.filter_by(
            institution_id=institution_id, 
            role='student', 
            is_active=True
        ).count()
        
        total_teachers = User.query.filter_by(
            institution_id=institution_id, 
            role='teacher', 
            is_active=True
        ).count()
        
        total_admins = User.query.filter_by(
            institution_id=institution_id, 
            role='admin', 
            is_active=True
        ).count()
        
        total_courses = Course.query.filter_by(
            institution_id=institution_id, 
            status='active'
        ).count()
        
        total_users = total_students + total_teachers + total_admins
        
        # Estadísticas de crecimiento
        current_month = datetime.utcnow().replace(day=1)
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        new_students_this_month = User.query.filter(
            User.institution_id == institution_id,
            User.role == 'student',
            User.created_at >= current_month,
            User.is_active == True
        ).count()
        
        new_teachers_this_month = User.query.filter(
            User.institution_id == institution_id,
            User.role == 'teacher', 
            User.created_at >= current_month,
            User.is_active == True
        ).count()
        
        # Usuarios activos (con actividad reciente)
        users_online = get_active_users_count(institution_id)
        
        return {
            'total_students': total_students,
            'total_teachers': total_teachers,
            'total_admins': total_admins,
            'total_courses': total_courses,
            'total_users': total_users,
            'new_students_this_month': new_students_this_month,
            'new_teachers_this_month': new_teachers_this_month,
            'active_teachers': total_teachers,  # Por ahora todos los activos
            'active_courses': total_courses,
            'users_online': users_online
        }
        
    except Exception as e:
        security_logger.error(f"Error getting institution stats: {e}")
        return {
            'total_students': 0,
            'total_teachers': 0, 
            'total_admins': 0,
            'total_courses': 0,
            'total_users': 0,
            'new_students_this_month': 0,
            'new_teachers_this_month': 0,
            'active_teachers': 0,
            'active_courses': 0,
            'users_online': 0
        }

def get_active_users_count(institution_id):
    """Obtiene usuarios activos de la institución en las últimas 2 horas"""
    try:
        recent_threshold = datetime.utcnow() - timedelta(hours=2)
        
        if hasattr(User, 'last_activity'):
            return User.query.filter(
                User.institution_id == institution_id,
                User.last_activity >= recent_threshold,
                User.is_active == True
            ).count()
        elif hasattr(User, 'last_login'):
            return User.query.filter(
                User.institution_id == institution_id,
                User.last_login >= recent_threshold,
                User.is_active == True
            ).count()
        else:
            return 1  # Al menos el admin actual
            
    except Exception:
        return 1

def get_institution_recent_activities(institution_id):
    """Obtiene actividades recientes de la institución"""
    activities = []
    
    try:
        # Usuarios registrados recientemente (últimos 7 días)
        recent_users = User.query.filter(
            User.institution_id == institution_id,
            User.created_at >= datetime.utcnow() - timedelta(days=7)
        ).order_by(User.created_at.desc()).limit(5).all()
        
        for user in recent_users:
            activities.append({
                'user_name': user.full_name or user.email,
                'title': f'Nuevo {user.role} registrado',
                'description': f'{user.full_name or user.email} se unió a la institución',
                'time': format_time_ago(user.created_at),
                'timestamp': user.created_at
            })
        
        # Cursos creados recientemente
        recent_courses = Course.query.filter(
            Course.institution_id == institution_id,
            Course.created_at >= datetime.utcnow() - timedelta(days=7)
        ).order_by(Course.created_at.desc()).limit(3).all()
        
        for course in recent_courses:
            activities.append({
                'user_name': course.teacher.full_name if course.teacher else 'Sistema',
                'title': 'Nuevo curso creado',
                'description': f'Curso "{course.name}" fue agregado',
                'time': format_time_ago(course.created_at),
                'timestamp': course.created_at
            })
        
        # Actividad actual del admin
        activities.append({
            'user_name': current_user.full_name or current_user.email,
            'title': 'Panel de administración accedido',
            'description': f'{current_user.full_name or current_user.email} ingresó al dashboard',
            'time': 'Ahora',
            'timestamp': datetime.utcnow()
        })
        
        # Ordenar por timestamp
        activities.sort(key=lambda x: x.get('timestamp', datetime.min), reverse=True)
        return activities[:6]
        
    except Exception as e:
        security_logger.error(f"Error getting recent activities: {e}")
        return [{
            'user_name': current_user.full_name or current_user.email,
            'title': 'Panel de administración accedido',
            'description': f'{current_user.full_name or current_user.email} ingresó al dashboard',
            'time': 'Ahora',
            'timestamp': datetime.utcnow()
        }]

def get_recent_users(institution_id, limit=5):
    """Obtiene usuarios recientes de la institución"""
    try:
        return User.query.filter(
            User.institution_id == institution_id,
            User.is_active == True
        ).order_by(User.created_at.desc()).limit(limit).all()
    except Exception:
        return []

def get_available_teachers(institution_id):
    """Obtiene profesores disponibles para asignar a cursos"""
    try:
        return User.query.filter(
            User.institution_id == institution_id,
            User.role == 'teacher',
            User.is_active == True
        ).order_by(User.full_name).all()
    except Exception:
        return []

def format_time_ago(date):
    """Calcular tiempo transcurrido desde una fecha"""
    try:
        if not date:
            return 'Tiempo desconocido'
        
        now = datetime.utcnow()
        diff = now - date
        
        if diff.days > 0:
            return f'Hace {diff.days} día{"s" if diff.days > 1 else ""}'
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f'Hace {hours} hora{"s" if hours > 1 else ""}'
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f'Hace {minutes} minuto{"s" if minutes > 1 else ""}'
        else:
            return 'Hace unos segundos'
    except Exception:
        return 'Tiempo desconocido'

def generate_random_password(length=8):
    """Generar contraseña temporal aleatoria"""
    import secrets
    import string
    
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(length))

# ================== RUTAS PRINCIPALES ==================

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    """Dashboard principal del administrador institucional"""
    try:
        institution_id = current_user.institution_id
        
        # Obtener estadísticas de la institución
        institution_stats = get_institution_stats(institution_id)
        
        # Obtener actividades recientes
        recent_activities = get_institution_recent_activities(institution_id)
        
        # Obtener usuarios recientes
        recent_users = get_recent_users(institution_id)
        
        # Obtener profesores disponibles para los modales
        available_teachers = get_available_teachers(institution_id)
        
        # Log del acceso
        security_logger.info(f'ADMIN_DASHBOARD_ACCESS - User: {current_user.email} - Institution: {current_user.institution.name} - IP: {request.remote_addr}')
        
        return render_template('admin/dashboard.html',
                             institution_stats=institution_stats,
                             recent_activities=recent_activities,
                             recent_users=recent_users,
                             available_teachers=available_teachers)
        
    except Exception as e:
        security_logger.error(f'ADMIN_DASHBOARD_ERROR - User: {current_user.email} - Error: {str(e)}')
        flash('Error al cargar el dashboard', 'error')
        return redirect(url_for('main.index'))

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """Gestión de usuarios de la institución"""
    try:
        institution_id = current_user.institution_id
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '', type=str)
        role_filter = request.args.get('role', '', type=str)
        
        # Query base: solo usuarios de la institución
        query = User.query.filter(User.institution_id == institution_id)
        
        # Aplicar filtros
        if search:
            query = query.filter(
                or_(
                    User.full_name.contains(search),
                    User.email.contains(search)
                )
            )
        
        if role_filter:
            query = query.filter(User.role == role_filter)
        
        # Paginación
        users = query.order_by(desc(User.created_at)).paginate(
            page=page, per_page=20, error_out=False
        )
        
        # Roles disponibles en la institución
        roles = db.session.query(User.role).filter(
            User.institution_id == institution_id
        ).distinct().all()
        roles = [role[0] for role in roles if role[0]]
        
        security_logger.info(f'ADMIN_USERS_ACCESS - User: {current_user.email} - Institution: {current_user.institution.name}')
        
        return render_template('admin/users.html',
                             users=users,
                             search=search,
                             role_filter=role_filter,
                             roles=roles)
        
    except Exception as e:
        security_logger.error(f'ADMIN_USERS_ERROR - User: {current_user.email} - Error: {str(e)}')
        flash('Error al cargar usuarios', 'error')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/users/create', methods=['POST'])
@login_required
@admin_required
def create_user():
    """Crear nuevo usuario en la institución"""
    try:
        data = request.get_json()
        
        # Validar datos requeridos
        required_fields = ['full_name', 'email', 'role', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'Campo {field} es requerido'})
        
        # Verificar que el email no exista
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'success': False, 'message': 'El email ya está registrado'})
        
        # Crear usuario
        user = User(
            full_name=data['full_name'],
            email=data['email'],
            role=data['role'],
            institution_id=current_user.institution_id,
            is_active=True
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        security_logger.info(f'USER_CREATED_BY_ADMIN - Admin: {current_user.email} - New User: {user.email} - Role: {user.role}')
        
        return jsonify({
            'success': True,
            'message': f'Usuario {user.role} creado exitosamente',
            'user': user.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        security_logger.error(f'USER_CREATE_ERROR - Admin: {current_user.email} - Error: {str(e)}')
        return jsonify({'success': False, 'message': 'Error interno del servidor'})

@admin_bp.route('/courses')
@login_required
@admin_required
def courses():
    """Gestión de cursos de la institución"""
    try:
        institution_id = current_user.institution_id
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '', type=str)
        
        # Query base: solo cursos de la institución
        query = Course.query.filter(Course.institution_id == institution_id)
        
        # Aplicar filtros
        if search:
            query = query.filter(
                or_(
                    Course.name.contains(search),
                    Course.code.contains(search)
                )
            )
        
        # Paginación
        courses = query.order_by(desc(Course.created_at)).paginate(
            page=page, per_page=15, error_out=False
        )
        
        security_logger.info(f'ADMIN_COURSES_ACCESS - User: {current_user.email}')
        
        return render_template('admin/courses.html',
                             courses=courses,
                             search=search)
        
    except Exception as e:
        security_logger.error(f'ADMIN_COURSES_ERROR - User: {current_user.email} - Error: {str(e)}')
        flash('Error al cargar cursos', 'error')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/courses/create', methods=['POST'])
@login_required
@admin_required
def create_course():
    """Crear nuevo curso en la institución"""
    try:
        data = request.get_json()
        
        # Validar datos requeridos
        if not data.get('name') or not data.get('code'):
            return jsonify({'success': False, 'message': 'Nombre y código son requeridos'})
        
        # Verificar que el código no exista en la institución
        existing_course = Course.query.filter_by(
            code=data['code'],
            institution_id=current_user.institution_id
        ).first()
        
        if existing_course:
            return jsonify({'success': False, 'message': 'Ya existe un curso con ese código'})
        
        # Crear curso
        course = Course(
            name=data['name'],
            code=data['code'],
            description=data.get('description', ''),
            institution_id=current_user.institution_id,
            teacher_id=data.get('teacher_id') if data.get('teacher_id') else None,
            status=data.get('status', 'active')
        )
        
        db.session.add(course)
        db.session.commit()
        
        security_logger.info(f'COURSE_CREATED_BY_ADMIN - Admin: {current_user.email} - Course: {course.name} ({course.code})')
        
        return jsonify({
            'success': True,
            'message': 'Curso creado exitosamente',
            'course': course.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        security_logger.error(f'COURSE_CREATE_ERROR - Admin: {current_user.email} - Error: {str(e)}')
        return jsonify({'success': False, 'message': 'Error interno del servidor'})

@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    """Reportes y analytics de la institución"""
    try:
        institution_id = current_user.institution_id
        
        # Datos para reportes
        report_data = {
            'users_by_role': get_users_by_role_data(institution_id),
            'registration_trends': get_registration_trends(institution_id),
            'course_statistics': get_course_statistics(institution_id)
        }
        
        security_logger.info(f'ADMIN_REPORTS_ACCESS - User: {current_user.email}')
        
        return render_template('admin/reports.html', report_data=report_data)
        
    except Exception as e:
        security_logger.error(f'ADMIN_REPORTS_ERROR - User: {current_user.email} - Error: {str(e)}')
        flash('Error al cargar reportes', 'error')
        return redirect(url_for('admin.dashboard'))

def get_users_by_role_data(institution_id):
    """Obtener datos de usuarios por rol para gráficos"""
    try:
        data = db.session.query(
            User.role,
            func.count(User.id)
        ).filter(
            User.institution_id == institution_id,
            User.is_active == True
        ).group_by(User.role).all()
        
        return {role: count for role, count in data}
    except Exception:
        return {}

def get_registration_trends(institution_id):
    """Obtener tendencias de registro por mes"""
    try:
        # Últimos 6 meses
        trends = []
        for i in range(6):
            month_start = (datetime.utcnow().replace(day=1) - timedelta(days=30*i)).replace(day=1)
            next_month = (month_start + timedelta(days=32)).replace(day=1)
            
            count = User.query.filter(
                User.institution_id == institution_id,
                User.created_at >= month_start,
                User.created_at < next_month
            ).count()
            
            trends.append({
                'month': month_start.strftime('%b %Y'),
                'registrations': count
            })
        
        return list(reversed(trends))
    except Exception:
        return []

def get_course_statistics(institution_id):
    """Obtener estadísticas de cursos"""
    try:
        total_courses = Course.query.filter_by(institution_id=institution_id).count()
        active_courses = Course.query.filter_by(institution_id=institution_id, status='active').count()
        courses_with_teacher = Course.query.filter(
            Course.institution_id == institution_id,
            Course.teacher_id.isnot(None)
        ).count()
        
        return {
            'total': total_courses,
            'active': active_courses,
            'with_teacher': courses_with_teacher,
            'without_teacher': total_courses - courses_with_teacher
        }
    except Exception:
        return {'total': 0, 'active': 0, 'with_teacher': 0, 'without_teacher': 0}

# ================== API ENDPOINTS ==================

@admin_bp.route('/api/stats')
@login_required
@admin_required
def api_stats():
    """API para obtener estadísticas en tiempo real"""
    try:
        institution_id = current_user.institution_id
        stats = get_institution_stats(institution_id)
        
        return jsonify({
            'success': True,
            'stats': stats,
            'last_updated': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        security_logger.error(f'ADMIN_API_STATS_ERROR - User: {current_user.email} - Error: {str(e)}')
        return jsonify({'success': False, 'error': 'Error interno del servidor'}), 500