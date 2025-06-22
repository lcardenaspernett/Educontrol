"""
Rutas para el dashboard de Superadministrador - SOLO DATOS REALES
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func, and_, case
from datetime import datetime, timedelta
import os

from app import db
from app.models.user import User
from app.models.institution import Institution
from app.models.course import Course
from app.auth.decorators import require_role

# Crear blueprint al principio
superadmin_bp = Blueprint('superadmin', __name__)

# Funciones auxiliares - SOLO DATOS REALES
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
                'server_status': 'operational' if cpu_percent < 80 else 'warning'
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
                'server_status': 'operational'
            }
    except Exception as e:
        print(f"Error obteniendo info del sistema: {e}")
        return {
            'version': 'v1.0.2',
            'last_backup': 'No disponible',
            'connected_users': get_real_connected_users(),
            'storage_usage': 'No disponible',
            'memory_usage': 'No disponible',
            'cpu_usage': 'No disponible',
            'uptime_hours': 'No disponible',
            'database_status': check_database_connection(),
            'server_status': 'unknown'
        }

def get_last_backup_time():
    """Obtiene la hora real del último backup"""
    try:
        # Aquí deberías implementar la lógica real de tu sistema de backups
        # Por ejemplo, verificar archivos de backup o consultar un log
        backup_dir = '/path/to/backups'  # Ajusta esta ruta
        if os.path.exists(backup_dir):
            # Buscar el archivo de backup más reciente
            backup_files = [f for f in os.listdir(backup_dir) if f.endswith('.sql') or f.endswith('.gz')]
            if backup_files:
                latest_backup = max(backup_files, key=lambda x: os.path.getctime(os.path.join(backup_dir, x)))
                backup_time = datetime.fromtimestamp(os.path.getctime(os.path.join(backup_dir, latest_backup)))
                time_diff = datetime.now() - backup_time
                
                if time_diff.days > 0:
                    return f"Hace {time_diff.days} día{'s' if time_diff.days > 1 else ''}"
                elif time_diff.seconds > 3600:
                    hours = time_diff.seconds // 3600
                    return f"Hace {hours} hora{'s' if hours > 1 else ''}"
                else:
                    minutes = max(1, time_diff.seconds // 60)
                    return f"Hace {minutes} minuto{'s' if minutes > 1 else ''}"
        
        return 'No disponible'
    except Exception:
        return 'No disponible'

def get_real_connected_users():
    """Obtiene usuarios realmente conectados basado en actividad reciente"""
    try:
        # Usuarios con actividad en los últimos 15 minutos
        recent_threshold = datetime.now() - timedelta(minutes=15)
        
        # Si tienes un campo last_activity en tu modelo User, úsalo
        # Si no, usar last_login como aproximación
        active_users = User.query.filter(
            User.last_login >= recent_threshold,
            User.is_active == True
        ).count()
        
        # Asegurar que al menos esté el usuario actual
        return max(active_users, 1 if current_user.is_authenticated else 0)
        
    except Exception as e:
        print(f"Error obteniendo usuarios conectados: {e}")
        return 1 if current_user.is_authenticated else 0

def check_database_connection():
    """Verifica la conexión real a la base de datos"""
    try:
        db.session.execute('SELECT 1')
        return 'connected'
    except Exception as e:
        print(f"Error de conexión a BD: {e}")
        return 'error'

def get_real_recent_activities():
    """Obtiene SOLO actividades reales del sistema - Sin datos simulados"""
    activities = []
    
    try:
        # 1. Usuarios registrados recientemente (últimos 7 días para más actividad)
        recent_users = User.query.filter(
            User.created_at >= datetime.now() - timedelta(days=7)
        ).order_by(User.created_at.desc()).limit(5).all()
        
        for user in recent_users:
            time_diff = datetime.now() - user.created_at
            
            # Calcular tiempo transcurrido
            if time_diff.days > 0:
                time_str = f"Hace {time_diff.days} día{'s' if time_diff.days > 1 else ''}"
            elif time_diff.seconds > 3600:
                hours = time_diff.seconds // 3600
                time_str = f"Hace {hours} hora{'s' if hours > 1 else ''}"
            else:
                minutes = max(1, time_diff.seconds // 60)  # Mínimo 1 minuto
                time_str = f"Hace {minutes} minuto{'s' if minutes > 1 else ''}"
            
            activities.append({
                'time': time_str,
                'title': f'Usuario {user.role} registrado',
                'description': f'{user.full_name} se registró en el sistema',
                'icon': get_role_icon(user.role),
                'type': 'user_created',
                'real_timestamp': user.created_at
            })
        
        # 2. Instituciones creadas recientemente (últimos 30 días)
        recent_institutions = Institution.query.filter(
            Institution.created_at >= datetime.now() - timedelta(days=30)
        ).order_by(Institution.created_at.desc()).limit(3).all()
        
        for institution in recent_institutions:
            time_diff = datetime.now() - institution.created_at
            
            if time_diff.days > 0:
                time_str = f"Hace {time_diff.days} día{'s' if time_diff.days > 1 else ''}"
            elif time_diff.seconds > 3600:
                hours = time_diff.seconds // 3600
                time_str = f"Hace {hours} hora{'s' if hours > 1 else ''}"
            else:
                minutes = max(1, time_diff.seconds // 60)
                time_str = f"Hace {minutes} minuto{'s' if minutes > 1 else ''}"
            
            activities.append({
                'time': time_str,
                'title': 'Nueva institución registrada',
                'description': f'{institution.name} fue agregada al sistema',
                'icon': 'fas fa-building',
                'type': 'institution_created',
                'real_timestamp': institution.created_at
            })
        
        # 3. Cursos creados recientemente (últimos 7 días)
        recent_courses = Course.query.filter(
            Course.created_at >= datetime.now() - timedelta(days=7)
        ).order_by(Course.created_at.desc()).limit(3).all()
        
        for course in recent_courses:
            time_diff = datetime.now() - course.created_at
            
            if time_diff.days > 0:
                time_str = f"Hace {time_diff.days} día{'s' if time_diff.days > 1 else ''}"
            elif time_diff.seconds > 3600:
                hours = time_diff.seconds // 3600
                time_str = f"Hace {hours} hora{'s' if hours > 1 else ''}"
            else:
                minutes = max(1, time_diff.seconds // 60)
                time_str = f"Hace {minutes} minuto{'s' if minutes > 1 else ''}"
            
            activities.append({
                'time': time_str,
                'title': 'Nuevo curso creado',
                'description': f'Curso "{course.name}" fue creado',
                'icon': 'fas fa-book',
                'type': 'course_created',
                'real_timestamp': course.created_at
            })
        
        # 4. Logins recientes SOLO SI EXISTEN (últimas 24 horas)
        if hasattr(User, 'last_login'):
            recent_logins = User.query.filter(
                User.last_login >= datetime.now() - timedelta(hours=24),
                User.last_login.isnot(None)
            ).order_by(User.last_login.desc()).limit(3).all()
            
            for user in recent_logins:
                if user.last_login:
                    time_diff = datetime.now() - user.last_login
                    
                    if time_diff.seconds > 3600:
                        hours = time_diff.seconds // 3600
                        time_str = f"Hace {hours} hora{'s' if hours > 1 else ''}"
                    else:
                        minutes = max(1, time_diff.seconds // 60)
                        time_str = f"Hace {minutes} minuto{'s' if minutes > 1 else ''}"
                    
                    activities.append({
                        'time': time_str,
                        'title': f'Acceso de {user.role}',
                        'description': f'{user.full_name} inició sesión',
                        'icon': 'fas fa-sign-in-alt',
                        'type': 'user_login',
                        'real_timestamp': user.last_login
                    })
        
        # 5. Actividad actual SOLO del superadmin logueado
        if current_user.is_authenticated and current_user.role == 'superadmin':
            activities.append({
                'time': 'Ahora',
                'title': 'Panel de administración activo',
                'description': f'{current_user.full_name} accedió al dashboard',
                'icon': 'fas fa-tachometer-alt',
                'type': 'dashboard_access',
                'real_timestamp': datetime.now()
            })
        
        # Ordenar por timestamp real (más reciente primero)
        activities.sort(key=lambda x: x.get('real_timestamp', datetime.min), reverse=True)
        
        # Eliminar duplicados y limitar a 6 actividades
        seen = set()
        unique_activities = []
        for activity in activities:
            key = (activity['title'], activity['description'])
            if key not in seen:
                seen.add(key)
                unique_activities.append(activity)
                if len(unique_activities) >= 6:
                    break
        
        return unique_activities
        
    except Exception as e:
        print(f"Error obteniendo actividades reales: {e}")
        # Si hay error, retornar solo la actividad actual si existe
        if current_user.is_authenticated and current_user.role == 'superadmin':
            return [{
                'time': 'Ahora',
                'title': 'Panel de administración',
                'description': f'{current_user.full_name} accedió al dashboard',
                'icon': 'fas fa-tachometer-alt',
                'type': 'dashboard_access',
                'real_timestamp': datetime.now()
            }]
        return []

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
        print(f"Error en get_dashboard_chart_data: {e}")
        # Retornar estructura vacía en caso de error
        return {
            'institution_names': [],
            'students_per_institution': [],
            'teachers_per_institution': []
        }

# Rutas del Blueprint
@superadmin_bp.route('/dashboard')
@require_role('superadmin')
def dashboard():
    """Dashboard principal del superadministrador con SOLO datos reales"""
    
    # Estadísticas generales REALES
    stats = {
        'total_institutions': Institution.query.filter_by(is_active=True).count(),
        'total_users': User.query.filter_by(is_active=True).count(),
        'total_admins': User.query.filter_by(role='admin', is_active=True).count(),
        'total_teachers': User.query.filter_by(role='teacher', is_active=True).count(),
        'total_students': User.query.filter_by(role='student', is_active=True).count(),
        'total_courses': Course.query.filter_by(status='active').count(),
    }
    
    # Estadísticas de crecimiento REALES (este mes)
    current_month = datetime.now().replace(day=1)
    stats.update({
        'new_institutions_this_month': Institution.query.filter(
            Institution.created_at >= current_month,
            Institution.is_active == True
        ).count(),
        'new_users_this_week': User.query.filter(
            User.created_at >= datetime.now() - timedelta(days=7),
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
        'active_courses': Course.query.filter_by(status='active').count(),
    })
    
    # Datos REALES para gráficos
    chart_data = get_dashboard_chart_data()
    
    # Información REAL del sistema
    system_info = get_real_system_info()
    
    # Actividades REALES únicamente
    recent_activities = get_real_recent_activities()
    
    return render_template('superadmin/dashboard.html',
                         stats=stats,
                         chart_data=chart_data,
                         system_info=system_info,
                         recent_activities=recent_activities)

@superadmin_bp.route('/institutions')
@require_role('superadmin')
def institutions():
    """Lista de instituciones"""
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    
    query = Institution.query
    
    if search:
        query = query.filter(
            Institution.name.contains(search) |
            Institution.code.contains(search) |
            Institution.city.contains(search)
        )
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    institutions = query.order_by(Institution.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('superadmin/institutions.html',
                         institutions=institutions,
                         search=search,
                         status_filter=status_filter)

@superadmin_bp.route('/institutions/new', methods=['GET', 'POST'])
@require_role('superadmin')
def create_institution():
    """Crear nueva institución"""
    
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            data = request.form
            
            # Verificar que el código no exista
            if Institution.query.filter_by(code=data['code']).first():
                flash('El código de institución ya existe', 'error')
                return render_template('superadmin/create_institution.html')
            
            # Crear nueva institución
            institution = Institution(
                name=data['name'],
                code=data['code'],
                city=data['city'],
                address=data.get('address'),
                phone=data.get('phone'),
                email=data.get('email'),
                website=data.get('website'),
                status=data.get('status', 'active'),
                is_active=True
            )
            
            db.session.add(institution)
            db.session.flush()  # Para obtener el ID
            
            # Crear administrador si se solicita
            if data.get('create_admin'):
                admin_email = data.get('admin_email') or f"admin@{data['code'].lower()}.edu.co"
                
                admin_user = User(
                    full_name=f"Administrador {data['name']}",
                    email=admin_email,
                    username=f"admin_{data['code'].lower()}",
                    role='admin',
                    is_active=True,
                    institution_id=institution.id
                )
                admin_user.set_password('admin123')  # Temporal
                
                db.session.add(admin_user)
            
            db.session.commit()
            
            flash(f'Institución "{data["name"]}" creada exitosamente', 'success')
            return redirect(url_for('superadmin.institutions'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear la institución: {str(e)}', 'error')
    
    return render_template('superadmin/create_institution.html')

@superadmin_bp.route('/users')
@require_role('superadmin')
def users():
    """Lista de usuarios del sistema"""
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    role_filter = request.args.get('role', '')
    institution_filter = request.args.get('institution', '', type=int)
    
    query = User.query
    
    if search:
        query = query.filter(
            User.full_name.contains(search) |
            User.email.contains(search) |
            User.username.contains(search)
        )
    
    if role_filter:
        query = query.filter_by(role=role_filter)
    
    if institution_filter:
        query = query.filter_by(institution_id=institution_filter)
    
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Lista de instituciones para el filtro
    institutions = Institution.query.filter_by(is_active=True).all()
    
    return render_template('superadmin/users.html',
                         users=users,
                         institutions=institutions,
                         search=search,
                         role_filter=role_filter,
                         institution_filter=institution_filter)

@superadmin_bp.route('/settings')
@require_role('superadmin')
def settings():
    """Configuración del sistema"""
    return render_template('superadmin/settings.html')

@superadmin_bp.route('/api/stats')
@require_role('superadmin')
def api_stats():
    """API para obtener estadísticas en tiempo real con SOLO datos reales"""
    
    system_info = get_real_system_info()
    
    stats = {
        'users_online': system_info['connected_users'],
        'total_institutions': Institution.query.filter_by(is_active=True).count(),
        'total_users': User.query.filter_by(is_active=True).count(),
        'system_status': system_info['server_status'],
        'database_status': system_info['database_status'],
        'cpu_usage': system_info.get('cpu_usage', 'No disponible'),
        'memory_usage': system_info.get('memory_usage', 'No disponible'),
        'storage_usage': system_info.get('storage_usage', 'No disponible')
    }
    
    return jsonify(stats)