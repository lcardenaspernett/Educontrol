"""
Rutas para el dashboard de Superadministrador - COMPLETO Y ACTUALIZADO
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, make_response
from flask_login import login_required, current_user
from sqlalchemy import func, and_, case, desc, or_
from datetime import datetime, timedelta
import os
import logging
from functools import wraps
import secrets
import string

from app import db
from app.models.user import User
from app.models.institution import Institution
# from app.models.course import Course  # Descomenta cuando tengas el modelo Course
from app.auth.decorators import require_role

# Configurar logging de seguridad
security_logger = logging.getLogger('security')

# Crear blueprint
superadmin_bp = Blueprint('superadmin', __name__, url_prefix='/superadmin')

# Decorador adicional de seguridad
def superadmin_required(f):
    """Decorador para verificar que el usuario sea superadmin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'superadmin':
            security_logger.warning(f'PERMISSION_DENIED - SuperAdmin access denied for user: {current_user.username if current_user.is_authenticated else "Anonymous"} - IP: {request.remote_addr}')
            flash('Acceso denegado. Se requieren permisos de SuperAdmin.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

# ================== FUNCIONES AUXILIARES ==================

def get_real_system_info():
    """Obtiene información real del sistema"""
    try:
        # Intentar importar psutil si está disponible
        try:
            import psutil
            # Información real del servidor
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Uptime del sistema
            boot_time = psutil.boot_time()
            uptime = datetime.now() - datetime.fromtimestamp(boot_time)
            
            return {
                'version': 'v1.0.2',
                'last_backup': get_last_backup_time(),
                'connected_users': get_real_connected_users(),
                'storage_usage': f"{disk.percent:.1f}%",
                'memory_usage': f"{memory.percent:.1f}%",
                'cpu_usage': f"{cpu_percent:.1f}%",
                'uptime_hours': int(uptime.total_seconds() / 3600),
                'database_status': check_database_connection(),
                'server_status': 'operational' if cpu_percent < 80 else 'warning',
                'database_size': format_bytes(get_database_size()),
                'total_files': count_uploaded_files()
            }
        except ImportError:
            # Información básica sin psutil
            return {
                'version': 'v1.0.2',
                'last_backup': get_last_backup_time(),
                'connected_users': get_real_connected_users(),
                'storage_usage': 'No disponible',
                'memory_usage': 'No disponible',
                'cpu_usage': 'No disponible',
                'uptime_hours': 'No disponible',
                'database_status': check_database_connection(),
                'server_status': 'operational',
                'database_size': format_bytes(get_database_size()),
                'total_files': count_uploaded_files()
            }
    except Exception as e:
        security_logger.error(f"Error obteniendo info del sistema: {e}")
        return {
            'version': 'v1.0.2',
            'last_backup': 'No disponible',
            'connected_users': get_real_connected_users(),
            'storage_usage': 'No disponible',
            'memory_usage': 'No disponible',
            'cpu_usage': 'No disponible',
            'uptime_hours': 'No disponible',
            'database_status': check_database_connection(),
            'server_status': 'unknown',
            'database_size': 'No disponible',
            'total_files': 0
        }

def get_last_backup_time():
    """Obtiene la hora real del último backup"""
    try:
        # Verificar directorio de backups
        backup_dirs = [
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backups'),
            '/var/backups/educontrol',
            'backups'
        ]
        
        for backup_dir in backup_dirs:
            if os.path.exists(backup_dir):
                # Buscar archivos de backup
                backup_files = []
                for ext in ['.sql', '.gz', '.zip', '.tar.gz']:
                    backup_files.extend([f for f in os.listdir(backup_dir) if f.endswith(ext)])
                
                if backup_files:
                    latest_backup = max(backup_files, key=lambda x: os.path.getctime(os.path.join(backup_dir, x)))
                    backup_time = datetime.fromtimestamp(os.path.getctime(os.path.join(backup_dir, latest_backup)))
                    return format_time_ago(backup_time)
        
        return 'No disponible'
    except Exception:
        return 'No disponible'

def get_real_connected_users():
    """Obtiene usuarios realmente conectados basado en actividad reciente"""
    try:
        # Usuarios con actividad en los últimos 15 minutos
        recent_threshold = datetime.utcnow() - timedelta(minutes=15)
        
        # Si tienes un campo last_activity en tu modelo User, úsalo
        if hasattr(User, 'last_activity'):
            active_users = User.query.filter(
                User.last_activity >= recent_threshold,
                User.is_active == True
            ).count()
        elif hasattr(User, 'last_login'):
            # Usar last_login como aproximación (últimos 30 minutos)
            recent_threshold = datetime.utcnow() - timedelta(minutes=30)
            active_users = User.query.filter(
                User.last_login >= recent_threshold,
                User.is_active == True
            ).count()
        else:
            # Si no hay campos de actividad, contar solo usuarios activos recientes
            active_users = 1  # Al menos el superadmin actual
        
        # Asegurar que al menos esté el usuario actual
        return max(active_users, 1 if current_user.is_authenticated else 0)
        
    except Exception as e:
        security_logger.error(f"Error obteniendo usuarios conectados: {e}")
        return 1 if current_user.is_authenticated else 0

def check_database_connection():
    """Verifica la conexión real a la base de datos"""
    try:
        db.session.execute('SELECT 1')
        return 'connected'
    except Exception as e:
        security_logger.error(f"Error de conexión a BD: {e}")
        return 'error'

def get_database_size():
    """Obtener tamaño de la base de datos"""
    try:
        # Para SQLite
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'educontrol.db')
        if os.path.exists(db_path):
            return os.path.getsize(db_path)
        return 0
    except:
        return 0

def count_uploaded_files():
    """Contar archivos subidos"""
    try:
        uploads_dirs = [
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads'),
            'uploads',
            'static/uploads'
        ]
        
        total_files = 0
        for uploads_path in uploads_dirs:
            if os.path.exists(uploads_path):
                for root, dirs, files in os.walk(uploads_path):
                    total_files += len(files)
        
        return total_files
    except:
        return 0

def format_bytes(bytes_value):
    """Formatear bytes a formato legible"""
    try:
        bytes_value = float(bytes_value)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"
    except (TypeError, ValueError):
        return "0 B"

def format_time_ago(date):
    """Calcular tiempo transcurrido desde una fecha"""
    try:
        if not date:
            return 'Tiempo desconocido'
        
        now = datetime.utcnow() if date.tzinfo is None else datetime.now(date.tzinfo)
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

def get_real_recent_activities():
    """Obtiene SOLO actividades reales del sistema"""
    activities = []
    
    try:
        # 1. Usuarios registrados recientemente (últimos 7 días)
        recent_users = User.query.filter(
            User.created_at >= datetime.utcnow() - timedelta(days=7)
        ).order_by(User.created_at.desc()).limit(5).all()
        
        for user in recent_users:
            activities.append({
                'time': format_time_ago(user.created_at),
                'title': f'Usuario {user.role} registrado',
                'description': f'{user.full_name or user.username} se registró en el sistema',
                'icon': get_role_icon(user.role),
                'type': 'user_created',
                'real_timestamp': user.created_at
            })
        
        # 2. Instituciones creadas recientemente
        recent_institutions = Institution.query.filter(
            Institution.created_at >= datetime.utcnow() - timedelta(days=30)
        ).order_by(Institution.created_at.desc()).limit(3).all()
        
        for institution in recent_institutions:
            activities.append({
                'time': format_time_ago(institution.created_at),
                'title': 'Nueva institución registrada',
                'description': f'{institution.name} fue agregada al sistema',
                'icon': 'fas fa-building',
                'type': 'institution_created',
                'real_timestamp': institution.created_at
            })
        
        # 3. Cursos creados recientemente (solo si existe el modelo)
        try:
            from app.models.course import Course
            recent_courses = Course.query.filter(
                Course.created_at >= datetime.utcnow() - timedelta(days=7)
            ).order_by(Course.created_at.desc()).limit(3).all()
            
            for course in recent_courses:
                activities.append({
                    'time': format_time_ago(course.created_at),
                    'title': 'Nuevo curso creado',
                    'description': f'Curso "{course.name}" fue creado',
                    'icon': 'fas fa-book',
                    'type': 'course_created',
                    'real_timestamp': course.created_at
                })
        except ImportError:
            pass  # El modelo Course no existe aún
        
        # 4. Actividad actual del superadmin
        if current_user.is_authenticated and current_user.role == 'superadmin':
            activities.append({
                'time': 'Ahora',
                'title': 'Panel de administración activo',
                'description': f'{current_user.full_name or current_user.username} accedió al dashboard',
                'icon': 'fas fa-tachometer-alt',
                'type': 'dashboard_access',
                'real_timestamp': datetime.utcnow()
            })
        
        # Ordenar por timestamp real y limitar
        activities.sort(key=lambda x: x.get('real_timestamp', datetime.min), reverse=True)
        return activities[:6]
        
    except Exception as e:
        security_logger.error(f"Error obteniendo actividades reales: {e}")
        return [{
            'time': 'Ahora',
            'title': 'Panel de administración',
            'description': f'{current_user.full_name or current_user.username} accedió al dashboard',
            'icon': 'fas fa-tachometer-alt',
            'type': 'dashboard_access',
            'real_timestamp': datetime.utcnow()
        }] if current_user.is_authenticated else []

def get_role_icon(role):
    """Retorna el icono según el rol"""
    icons = {
        'superadmin': 'fas fa-crown',
        'admin': 'fas fa-user-shield',
        'teacher': 'fas fa-chalkboard-teacher',
        'student': 'fas fa-graduation-cap',
        'parent': 'fas fa-users'
    }
    return icons.get(role, 'fas fa-user')

def get_dashboard_chart_data():
    """Obtiene datos reales para los gráficos del dashboard"""
    try:
        # Usuarios por institución - DATOS REALES
        institution_data = db.session.query(
            Institution.name,
            func.count(User.id).label('total_users'),
            func.sum(
                case(
                    (User.role == 'student', 1),
                    else_=0
                )
            ).label('students'),
            func.sum(
                case(
                    (User.role == 'teacher', 1),
                    else_=0
                )
            ).label('teachers')
        ).outerjoin(User).filter(Institution.is_active == True).group_by(Institution.id, Institution.name).all()
        
        # Si no hay datos, retornar estructura vacía
        if not institution_data:
            return {
                'institution_names': [],
                'students_per_institution': [],
                'teachers_per_institution': []
            }
        
        return {
            'institution_names': [row.name for row in institution_data],
            'students_per_institution': [int(row.students or 0) for row in institution_data],
            'teachers_per_institution': [int(row.teachers or 0) for row in institution_data]
        }
    except Exception as e:
        security_logger.error(f"Error en get_dashboard_chart_data: {e}")
        return {
            'institution_names': [],
            'students_per_institution': [],
            'teachers_per_institution': []
        }

def generate_random_password(length=12):
    """Generar contraseña aleatoria segura"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for i in range(length))

# ================== RUTAS PRINCIPALES ==================

@superadmin_bp.route('/')
@login_required
@superadmin_required
def dashboard():
    """Dashboard principal del superadministrador con SOLO datos reales"""
    try:
        # Estadísticas generales REALES
        stats = {
            'total_institutions': Institution.query.filter_by(is_active=True).count(),
            'total_users': User.query.filter_by(is_active=True).count(),
            'total_admins': User.query.filter_by(role='admin', is_active=True).count(),
            'total_teachers': User.query.filter_by(role='teacher', is_active=True).count(),
            'total_students': User.query.filter_by(role='student', is_active=True).count(),
        }
        
        # Intentar obtener estadísticas de cursos si existe el modelo
        try:
            from app.models.course import Course
            stats['total_courses'] = Course.query.filter_by(status='active').count()
            stats['active_courses'] = Course.query.filter_by(status='active').count()
        except ImportError:
            stats['total_courses'] = 0
            stats['active_courses'] = 0
        
        # Estadísticas de crecimiento REALES
        current_month = datetime.utcnow().replace(day=1)
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        stats.update({
            'new_institutions_this_month': Institution.query.filter(
                Institution.created_at >= current_month,
                Institution.is_active == True
            ).count(),
            'new_users_this_week': User.query.filter(
                User.created_at >= week_ago,
                User.is_active == True
            ).count(),
            'new_teachers_this_month': User.query.filter(
                User.created_at >= current_month,
                User.role == 'teacher',
                User.is_active == True
            ).count(),
            'new_students_this_month': User.query.filter(
                User.created_at >= current_month,
                User.role == 'student',
                User.is_active == True
            ).count(),
            'active_admins': User.query.filter_by(role='admin', is_active=True).count(),
        })
        
        # Datos REALES para gráficos
        chart_data = get_dashboard_chart_data()
        
        # Información REAL del sistema
        system_info = get_real_system_info()
        
        # Actividades REALES únicamente
        recent_activities = get_real_recent_activities()
        
        # Log del acceso
        security_logger.info(f'SUPERADMIN_DASHBOARD_ACCESS - User: {current_user.username} - IP: {request.remote_addr}')
        
        return render_template('superadmin/dashboard.html',
                             stats=stats,
                             chart_data=chart_data,
                             system_info=system_info,
                             recent_activities=recent_activities)
        
    except Exception as e:
        security_logger.error(f'SUPERADMIN_DASHBOARD_ERROR - User: {current_user.username} - Error: {str(e)}')
        flash('Error al cargar el dashboard', 'error')
        return redirect(url_for('main.index'))

@superadmin_bp.route('/users')
@login_required
@superadmin_required
def users():
    """Gestión de usuarios del sistema"""
    try:
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '', type=str)
        role_filter = request.args.get('role', '', type=str)
        status_filter = request.args.get('status', '', type=str)
        
        query = User.query
        
        # Aplicar filtros de búsqueda
        if search:
            query = query.filter(
                or_(
                    User.username.contains(search),
                    User.email.contains(search),
                    User.first_name.contains(search) if hasattr(User, 'first_name') else False,
                    User.last_name.contains(search) if hasattr(User, 'last_name') else False,
                    User.full_name.contains(search) if hasattr(User, 'full_name') else False
                )
            )
        
        if role_filter:
            query = query.filter(User.role == role_filter)
        
        if status_filter:
            if status_filter == 'active':
                query = query.filter(User.is_active == True)
            elif status_filter == 'inactive':
                query = query.filter(User.is_active == False)
        
        # Paginación
        users = query.order_by(desc(User.created_at)).paginate(
            page=page, per_page=20, error_out=False
        )
        
        # Obtener roles únicos para el filtro
        roles = db.session.query(User.role).distinct().all()
        roles = [role[0] for role in roles if role[0]]
        
        security_logger.info(f'USER_MANAGEMENT_ACCESS - User: {current_user.username} - IP: {request.remote_addr}')
        
        return render_template('superadmin/users.html', 
                             users=users, 
                             search=search, 
                             role_filter=role_filter,
                             status_filter=status_filter,
                             roles=roles)
    
    except Exception as e:
        security_logger.error(f'USERS_MANAGEMENT_ERROR - User: {current_user.username} - Error: {str(e)}')
        flash('Error al cargar usuarios', 'error')
        return redirect(url_for('superadmin.dashboard'))

@superadmin_bp.route('/users/<int:user_id>/toggle_status', methods=['POST'])
@login_required
@superadmin_required
def toggle_user_status(user_id):
    """Activar/Desactivar usuario"""
    try:
        user = User.query.get_or_404(user_id)
        
        # No permitir desactivar al propio superadmin
        if user.id == current_user.id:
            return jsonify({'success': False, 'message': 'No puedes desactivar tu propia cuenta'})
        
        # No permitir desactivar a otros superadmins
        if user.role == 'superadmin' and user.id != current_user.id:
            return jsonify({'success': False, 'message': 'No se puede desactivar a otros SuperAdmins'})
        
        user.is_active = not user.is_active
        db.session.commit()
        
        action = 'ACTIVATED' if user.is_active else 'DEACTIVATED'
        security_logger.warning(f'USER_{action} - Target: {user.username} - By: {current_user.username} - IP: {request.remote_addr}')
        
        status = 'activado' if user.is_active else 'desactivado'
        return jsonify({'success': True, 'message': f'Usuario {status} correctamente'})
        
    except Exception as e:
        db.session.rollback()
        security_logger.error(f'USER_STATUS_TOGGLE_ERROR - User: {current_user.username} - Error: {str(e)}')
        return jsonify({'success': False, 'message': 'Error interno del servidor'})

@superadmin_bp.route('/institutions')
@login_required
@superadmin_required
def institutions():
    """Gestión de instituciones"""
    try:
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '', type=str)
        status_filter = request.args.get('status', '', type=str)
        type_filter = request.args.get('type', '', type=str)
        
        query = Institution.query
        
        # Aplicar filtros
        if search:
            query = query.filter(
                or_(
                    Institution.name.contains(search),
                    Institution.code.contains(search),
                    Institution.city.contains(search)
                )
            )
        
        if status_filter:
            if hasattr(Institution, 'status'):
                query = query.filter(Institution.status == status_filter)
            elif status_filter == 'active':
                query = query.filter(Institution.is_active == True)
            elif status_filter == 'inactive':
                query = query.filter(Institution.is_active == False)
        
        if type_filter and hasattr(Institution, 'type'):
            query = query.filter(Institution.type == type_filter)
        
        # Paginación
        institutions = query.order_by(desc(Institution.created_at)).paginate(
            page=page, per_page=12, error_out=False
        )
        
        # Agregar conteos de usuarios por institución
        for institution in institutions.items:
            user_counts = db.session.query(
                func.count(User.id),
                User.role
            ).filter(
                User.institution_id == institution.id
            ).group_by(User.role).all()
            
            # Inicializar conteos
            institution.user_count = 0
            institution.admin_count = 0
            institution.teacher_count = 0
            institution.student_count = 0
            
            # Asignar conteos reales
            for count, role in user_counts:
                institution.user_count += count
                if role == 'admin':
                    institution.admin_count = count
                elif role == 'teacher':
                    institution.teacher_count = count
                elif role == 'student':
                    institution.student_count = count
        
        security_logger.info(f'INSTITUTIONS_MANAGEMENT_ACCESS - User: {current_user.username} - IP: {request.remote_addr}')
        
        return render_template('superadmin/institutions.html', 
                             institutions=institutions,
                             search=search,
                             status_filter=status_filter,
                             type_filter=type_filter)
    
    except Exception as e:
        security_logger.error(f'INSTITUTIONS_MANAGEMENT_ERROR - User: {current_user.username} - Error: {str(e)}')
        flash('Error al cargar instituciones', 'error')
        return redirect(url_for('superadmin.dashboard'))

@superadmin_bp.route('/institutions/create', methods=['GET', 'POST'])
@login_required
@superadmin_required
def create_institution():
    """Crear nueva institución"""
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            name = request.form.get('name', '').strip()
            code = request.form.get('code', '').strip().upper()
            description = request.form.get('description', '').strip()
            
            # Ubicación
            city = request.form.get('city', '').strip()
            state = request.form.get('state', '').strip()
            address = request.form.get('address', '').strip()
            
            # Contacto
            phone = request.form.get('phone', '').strip()
            email = request.form.get('email', '').strip()
            website = request.form.get('website', '').strip()
            
            # Configuración
            institution_type = request.form.get('type', '').strip()
            status = request.form.get('status', 'active').strip()
            create_admin = request.form.get('create_admin') == 'on'
            
            # Validaciones básicas
            if not name or not code or not city:
                flash('Los campos Nombre, Código y Ciudad son obligatorios', 'error')
                return render_template('superadmin/create_institution.html')
            
            # Verificar que el código no exista
            if Institution.query.filter_by(code=code).first():
                flash(f'Ya existe una institución con el código "{code}"', 'error')
                return render_template('superadmin/create_institution.html')
            
            # Crear institución
            institution_data = {
                'name': name,
                'code': code,
                'city': city,
                'is_active': status == 'active'
            }
            
            # Agregar campos opcionales si no están vacíos
            if description:
                institution_data['description'] = description
            if state:
                institution_data['state'] = state
            if address:
                institution_data['address'] = address
            if phone:
                institution_data['phone'] = phone
            if email:
                institution_data['email'] = email
            if website:
                institution_data['website'] = website
            
            # Agregar campos adicionales si existen en el modelo
            if hasattr(Institution, 'type') and institution_type:
                institution_data['type'] = institution_type
            if hasattr(Institution, 'status'):
                institution_data['status'] = status
            
            institution = Institution(**institution_data)
            db.session.add(institution)
            db.session.flush()  # Para obtener el ID
            
            # Crear usuario administrador si se solicita
            if create_admin and email:
                admin_username = f"admin_{code.lower()}"
                admin_password = generate_random_password()
                
                admin_data = {
                    'username': admin_username,
                    'email': email,
                    'role': 'admin',
                    'institution_id': institution.id,
                    'is_active': True
                }
                
                # Agregar nombres según el modelo
                if hasattr(User, 'first_name'):
                    admin_data['first_name'] = "Administrador"
                    admin_data['last_name'] = name
                elif hasattr(User, 'full_name'):
                    admin_data['full_name'] = f"Administrador {name}"
                
                admin_user = User(**admin_data)
                admin_user.set_password(admin_password)
                
                db.session.add(admin_user)
                
                # Mostrar credenciales (en producción, enviar por email)
                flash(f'Usuario administrador creado: {admin_username} / {admin_password}', 'info')
            
            db.session.commit()
            
            security_logger.info(f'INSTITUTION_CREATED - Institution: {name} ({code}) - By: {current_user.username} - IP: {request.remote_addr}')
            flash(f'Institución "{name}" creada exitosamente', 'success')
            
            return redirect(url_for('superadmin.institutions'))
            
        except Exception as e:
            db.session.rollback()
            security_logger.error(f'INSTITUTION_CREATE_ERROR - User: {current_user.username} - Error: {str(e)}')
            flash('Error al crear la institución. Intente nuevamente.', 'error')
            return render_template('superadmin/create_institution.html')
    
    return render_template('superadmin/create_institution.html')

@superadmin_bp.route('/institutions/<int:institution_id>/toggle_status', methods=['POST'])
@login_required
@superadmin_required
def toggle_institution_status(institution_id):
    """Activar/Desactivar institución"""
    try:
        institution = Institution.query.get_or_404(institution_id)
        
        institution.is_active = not institution.is_active
        db.session.commit()
        
        action = 'ACTIVATED' if institution.is_active else 'DEACTIVATED'
        security_logger.warning(f'INSTITUTION_{action} - Target: {institution.name} - By: {current_user.username} - IP: {request.remote_addr}')
        
        status = 'activada' if institution.is_active else 'desactivada'
        return jsonify({'success': True, 'message': f'Institución {status} correctamente'})
        
    except Exception as e:
        db.session.rollback()
        security_logger.error(f'INSTITUTION_STATUS_TOGGLE_ERROR - User: {current_user.username} - Error: {str(e)}')
        return jsonify({'success': False, 'message': 'Error interno del servidor'})

@superadmin_bp.route('/settings')
@login_required
@superadmin_required
def settings():
    """Configuración del sistema"""
    try:
        security_logger.info(f'SYSTEM_SETTINGS_ACCESS - User: {current_user.username} - IP: {request.remote_addr}')
        
        # Información del sistema
        system_info = get_real_system_info()
        
        return render_template('superadmin/settings.html', system_info=system_info)
    
    except Exception as e:
        security_logger.error(f'SETTINGS_ERROR - User: {current_user.username} - Error: {str(e)}')
        flash('Error al cargar configuración', 'error')
        return redirect(url_for('superadmin.dashboard'))

@superadmin_bp.route('/api/stats')
@login_required
@superadmin_required
def api_stats():
    """API para obtener estadísticas en tiempo real con SOLO datos reales"""
    try:
        system_info = get_real_system_info()
        
        stats = {
            'users_online': system_info['connected_users'],
            'total_institutions': Institution.query.filter_by(is_active=True).count(),
            'total_users': User.query.filter_by(is_active=True).count(),
            'system_status': system_info['server_status'],
            'database_status': system_info['database_status'],
            'cpu_usage': system_info.get('cpu_usage', 'No disponible'),
            'memory_usage': system_info.get('memory_usage', 'No disponible'),
            'storage_usage': system_info.get('storage_usage', 'No disponible'),
            'last_updated': datetime.utcnow().isoformat()
        }
        
        return jsonify(stats)
    
    except Exception as e:
        security_logger.error(f'API_STATS_ERROR - User: {current_user.username} - Error: {str(e)}')
        return jsonify({'error': 'Error interno del servidor'}), 500

# ================== RUTAS DE EXPORTACIÓN ==================

@superadmin_bp.route('/export/users')
@login_required
@superadmin_required
def export_users():
    """Exportar usuarios a CSV"""
    try:
        users = User.query.all()
        
        # Crear CSV
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Encabezados
        headers = ['ID', 'Username', 'Email', 'Rol', 'Estado', 'Institución', 'Fecha Registro']
        
        # Agregar campos adicionales según el modelo
        if hasattr(User, 'full_name'):
            headers.insert(3, 'Nombre Completo')
        elif hasattr(User, 'first_name'):
            headers.insert(3, 'Nombre')
            headers.insert(4, 'Apellido')
        
        writer.writerow(headers)
        
        # Datos
        for user in users:
            row = [
                user.id,
                user.username,
                user.email
            ]
            
            # Agregar nombre según el modelo
            if hasattr(User, 'full_name'):
                row.append(user.full_name or '')
            elif hasattr(User, 'first_name'):
                row.append(user.first_name or '')
                row.append(user.last_name or '')
            
            row.extend([
                user.role,
                'Activo' if user.is_active else 'Inactivo',
                user.institution.name if user.institution else 'Sin asignar',
                user.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
            
            writer.writerow(row)
        
        # Generar respuesta
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename=usuarios_educontrol_{datetime.utcnow().strftime("%Y%m%d")}.csv'
        
        security_logger.info(f'USERS_EXPORT - User: {current_user.username} - Count: {len(users)}')
        
        return response
        
    except Exception as e:
        security_logger.error(f'USERS_EXPORT_ERROR - User: {current_user.username} - Error: {str(e)}')
        flash('Error al exportar usuarios', 'error')
        return redirect(url_for('superadmin.users'))

@superadmin_bp.route('/export/institutions')
@login_required
@superadmin_required
def export_institutions():
    """Exportar instituciones a CSV"""
    try:
        institutions = Institution.query.all()
        
        # Crear CSV
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Encabezados
        headers = ['ID', 'Nombre', 'Código', 'Ciudad', 'Departamento', 'Estado', 'Total Usuarios', 'Fecha Registro']
        
        # Agregar campos adicionales según el modelo
        if hasattr(Institution, 'type'):
            headers.insert(5, 'Tipo')
        
        writer.writerow(headers)
        
        # Datos
        for institution in institutions:
            user_count = User.query.filter_by(institution_id=institution.id).count()
            
            row = [
                institution.id,
                institution.name,
                institution.code,
                institution.city,
                getattr(institution, 'state', '') or ''
            ]
            
            # Agregar tipo si existe
            if hasattr(Institution, 'type'):
                row.append(getattr(institution, 'type', '') or 'No especificado')
            
            row.extend([
                'Activa' if institution.is_active else 'Inactiva',
                user_count,
                institution.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
            
            writer.writerow(row)
        
        # Generar respuesta
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename=instituciones_educontrol_{datetime.utcnow().strftime("%Y%m%d")}.csv'
        
        security_logger.info(f'INSTITUTIONS_EXPORT - User: {current_user.username} - Count: {len(institutions)}')
        
        return response
        
    except Exception as e:
        security_logger.error(f'INSTITUTIONS_EXPORT_ERROR - User: {current_user.username} - Error: {str(e)}')
        flash('Error al exportar instituciones', 'error')
        return redirect(url_for('superadmin.institutions'))

# ================== RUTAS DE MANTENIMIENTO ==================

@superadmin_bp.route('/maintenance/optimize-db', methods=['POST'])
@login_required
@superadmin_required
def optimize_database():
    """Optimizar base de datos"""
    try:
        # Para SQLite
        db.session.execute('VACUUM;')
        db.session.execute('ANALYZE;')
        db.session.commit()
        
        security_logger.info(f'DATABASE_OPTIMIZED - User: {current_user.username}')
        
        return jsonify({
            'success': True,
            'message': 'Base de datos optimizada correctamente'
        })
        
    except Exception as e:
        db.session.rollback()
        security_logger.error(f'DATABASE_OPTIMIZE_ERROR - User: {current_user.username} - Error: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error al optimizar la base de datos'
        }), 500

@superadmin_bp.route('/maintenance/clear-logs', methods=['POST'])
@login_required
@superadmin_required
def clear_logs():
    """Limpiar logs antiguos"""
    try:
        logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        
        if os.path.exists(logs_dir):
            files_cleared = 0
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            for filename in os.listdir(logs_dir):
                filepath = os.path.join(logs_dir, filename)
                if os.path.isfile(filepath):
                    # Verificar edad del archivo
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                    if file_mtime < cutoff_date:
                        os.remove(filepath)
                        files_cleared += 1
            
            security_logger.info(f'LOGS_CLEARED - User: {current_user.username} - Files: {files_cleared}')
            
            return jsonify({
                'success': True,
                'message': f'Se limpiaron {files_cleared} archivos de log antiguos'
            })
        else:
            return jsonify({
                'success': True,
                'message': 'No hay directorio de logs para limpiar'
            })
            
    except Exception as e:
        security_logger.error(f'CLEAR_LOGS_ERROR - User: {current_user.username} - Error: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error al limpiar logs'
        }), 500

@superadmin_bp.route('/backup/create', methods=['POST'])
@login_required
@superadmin_required
def create_backup():
    """Crear backup del sistema"""
    try:
        import shutil
        import zipfile
        
        # Crear directorio de backups si no existe
        backup_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        # Nombre del backup
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        backup_name = f'educontrol_backup_{timestamp}'
        backup_path = os.path.join(backup_dir, backup_name)
        
        # Crear directorio temporal del backup
        os.makedirs(backup_path, exist_ok=True)
        
        # Copiar base de datos
        db_source = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'educontrol.db')
        if os.path.exists(db_source):
            shutil.copy2(db_source, os.path.join(backup_path, 'educontrol.db'))
        
        # Copiar archivos de configuración importantes
        config_files = ['.env', 'config.py']
        for config_file in config_files:
            config_source = os.path.join(os.path.dirname(os.path.dirname(__file__)), config_file)
            if os.path.exists(config_source):
                shutil.copy2(config_source, os.path.join(backup_path, config_file))
        
        # Crear archivo de información del backup
        info_content = f"""EduControl Backup Information
Created: {datetime.utcnow().isoformat()}
Created by: {current_user.username}
Version: 1.0.2
Database size: {format_bytes(get_database_size())}
Total users: {User.query.count()}
Total institutions: {Institution.query.count()}
"""
        
        with open(os.path.join(backup_path, 'backup_info.txt'), 'w', encoding='utf-8') as f:
            f.write(info_content)
        
        # Comprimir backup
        zip_path = f'{backup_path}.zip'
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(backup_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, backup_path)
                    zipf.write(file_path, arcname)
        
        # Limpiar directorio temporal
        shutil.rmtree(backup_path)
        
        security_logger.info(f'BACKUP_CREATED - User: {current_user.username} - File: {backup_name}.zip')
        
        return jsonify({
            'success': True,
            'message': 'Backup creado exitosamente',
            'backup_file': f'{backup_name}.zip',
            'backup_size': format_bytes(os.path.getsize(zip_path))
        })
        
    except Exception as e:
        security_logger.error(f'BACKUP_CREATE_ERROR - User: {current_user.username} - Error: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Error al crear backup: {str(e)}'
        }), 500

# ================== RUTAS DE ANÁLISIS ==================

@superadmin_bp.route('/analytics')
@login_required
@superadmin_required
def analytics():
    """Analytics y reportes del sistema"""
    try:
        # Datos para gráficos avanzados
        analytics_data = {
            'users_growth': get_users_growth_data(),
            'institutions_growth': get_institutions_growth_data(),
            'activity_by_month': get_activity_by_month(),
            'top_institutions': get_top_institutions_by_users()
        }
        
        security_logger.info(f'ANALYTICS_ACCESS - User: {current_user.username} - IP: {request.remote_addr}')
        
        return render_template('superadmin/analytics.html', analytics_data=analytics_data)
        
    except Exception as e:
        security_logger.error(f'ANALYTICS_ERROR - User: {current_user.username} - Error: {str(e)}')
        flash('Error al cargar analytics', 'error')
        return redirect(url_for('superadmin.dashboard'))

def get_users_growth_data():
    """Obtener datos de crecimiento de usuarios por mes"""
    try:
        # Últimos 12 meses
        months_data = []
        for i in range(12):
            month_start = (datetime.utcnow().replace(day=1) - timedelta(days=30*i)).replace(day=1)
            next_month = (month_start + timedelta(days=32)).replace(day=1)
            
            users_count = User.query.filter(
                User.created_at >= month_start,
                User.created_at < next_month
            ).count()
            
            months_data.append({
                'month': month_start.strftime('%B %Y'),
                'users': users_count
            })
        
        return list(reversed(months_data))
    except Exception:
        return []

def get_institutions_growth_data():
    """Obtener datos de crecimiento de instituciones"""
    try:
        months_data = []
        for i in range(12):
            month_start = (datetime.utcnow().replace(day=1) - timedelta(days=30*i)).replace(day=1)
            next_month = (month_start + timedelta(days=32)).replace(day=1)
            
            institutions_count = Institution.query.filter(
                Institution.created_at >= month_start,
                Institution.created_at < next_month
            ).count()
            
            months_data.append({
                'month': month_start.strftime('%B %Y'),
                'institutions': institutions_count
            })
        
        return list(reversed(months_data))
    except Exception:
        return []

def get_activity_by_month():
    """Obtener actividad general por mes"""
    try:
        # Combinar datos de usuarios e instituciones
        activity_data = []
        for i in range(6):  # Últimos 6 meses
            month_start = (datetime.utcnow().replace(day=1) - timedelta(days=30*i)).replace(day=1)
            next_month = (month_start + timedelta(days=32)).replace(day=1)
            
            new_users = User.query.filter(
                User.created_at >= month_start,
                User.created_at < next_month
            ).count()
            
            new_institutions = Institution.query.filter(
                Institution.created_at >= month_start,
                Institution.created_at < next_month
            ).count()
            
            activity_data.append({
                'month': month_start.strftime('%b %Y'),
                'total_activity': new_users + new_institutions,
                'users': new_users,
                'institutions': new_institutions
            })
        
        return list(reversed(activity_data))
    except Exception:
        return []

def get_top_institutions_by_users():
    """Obtener instituciones con más usuarios"""
    try:
        top_institutions = db.session.query(
            Institution.name,
            func.count(User.id).label('user_count')
        ).join(User).filter(
            Institution.is_active == True
        ).group_by(Institution.id, Institution.name).order_by(
            desc('user_count')
        ).limit(10).all()
        
        return [{'name': inst.name, 'users': inst.user_count} for inst in top_institutions]
    except Exception:
        return []

# ================== ERROR HANDLERS ==================

@superadmin_bp.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@superadmin_bp.errorhandler(403)
def forbidden_error(error):
    return render_template('errors/403.html'), 403

@superadmin_bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500