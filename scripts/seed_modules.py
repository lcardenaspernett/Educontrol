# scripts/seed_modules.py
"""
Script para poblar la base de datos con los módulos del sistema EduControl
"""

from app import create_app, db
from app.models.module import Module

def seed_modules():
    """Inserta los módulos básicos del sistema"""
    
    app = create_app()
    with app.app_context():
        
        # Verificar si ya existen módulos
        existing_modules = Module.query.count()
        if existing_modules > 0:
            print(f"⚠️  Ya existen {existing_modules} módulos en la base de datos.")
            response = input("¿Desea eliminar todos y recrear? (y/n): ")
            if response.lower() == 'y':
                Module.query.delete()
                db.session.commit()
                print("🗑️  Módulos anteriores eliminados.")
            else:
                print("❌ Operación cancelada.")
                return
        
        modules_data = [
            # MÓDULOS CORE (Obligatorios)
            {
                'code': 'superadmin',
                'name': 'Módulo de Superadmin',
                'description': 'Gestión de instituciones, supervisión general del sistema, estadísticas generales por institución, control de planes y licencias, auditoría y registros de actividad',
                'icon': 'fas fa-crown',
                'category': 'core',
                'is_core': True,
                'included_roles': ['superadmin'],
                'permissions': ['manage_institutions', 'view_system_stats', 'manage_licenses', 'view_audit_logs'],
                'price_tier': 'free',
                'monthly_price': 0,
                'trial_days': 0,
                'sort_order': 1
            },
            {
                'code': 'admin_institutional',
                'name': 'Administración Institucional',
                'description': 'Configuración institucional (nombre, logo, sedes, niveles, calendario), gestión de usuarios institucionales, gestión de sedes, jornadas y grados, configuración de periodos académicos y asignaturas',
                'icon': 'fas fa-cogs',
                'category': 'core',
                'is_core': True,
                'included_roles': ['admin'],
                'permissions': ['manage_institution_config', 'manage_users', 'manage_campuses', 'manage_academic_periods'],
                'price_tier': 'free',
                'monthly_price': 0,
                'trial_days': 0,
                'sort_order': 2
            },

            # MÓDULOS ACADÉMICOS
            {
                'code': 'students',
                'name': 'Módulo de Estudiantes',
                'description': 'Registro y matrícula de estudiantes, histórico académico y calificaciones, asistencia y comportamiento, observador del estudiante, reportes de boletines por periodo y finales, carga de documentos',
                'icon': 'fas fa-user-graduate',
                'category': 'academic',
                'is_core': False,
                'included_roles': ['admin', 'coordinador', 'secretaria'],
                'permissions': ['register_students', 'view_student_records', 'manage_enrollments', 'view_academic_history', 'manage_attendance'],
                'price_tier': 'basic',
                'monthly_price': 25.00,
                'trial_days': 30,
                'sort_order': 3
            },
            {
                'code': 'teachers',
                'name': 'Módulo de Docentes',
                'description': 'Asignación de cursos y materias, registro de calificaciones, planificación de clases, gestión de tareas y actividades, observaciones académicas y de disciplina, reportes individuales por grupo y estudiante',
                'icon': 'fas fa-chalkboard-teacher',
                'category': 'academic',
                'is_core': False,
                'requires_modules': ['students'],
                'included_roles': ['docente', 'coordinador'],
                'permissions': ['assign_courses', 'register_grades', 'plan_classes', 'manage_assignments', 'academic_observations'],
                'price_tier': 'basic',
                'monthly_price': 20.00,
                'trial_days': 30,
                'sort_order': 4
            },
            {
                'code': 'parents',
                'name': 'Módulo de Padres/Acudientes',
                'description': 'Acceso al rendimiento del estudiante, consultar boletines y tareas, reportes de asistencia, comunicación con docentes y directivos',
                'icon': 'fas fa-users',
                'category': 'communication',
                'is_core': False,
                'requires_modules': ['students'],
                'included_roles': ['padre', 'acudiente'],
                'permissions': ['view_child_performance', 'view_report_cards', 'communicate_teachers', 'view_attendance'],
                'price_tier': 'basic',
                'monthly_price': 15.00,
                'trial_days': 30,
                'sort_order': 5
            },
            {
                'code': 'academic_management',
                'name': 'Módulo Académico',
                'description': 'Planes de estudio y currículo, asignación de carga académica, gestión de horarios y aulas, gestión de evaluaciones (tipo SABER, internas), nivelaciones y recuperación',
                'icon': 'fas fa-graduation-cap',
                'category': 'academic',
                'is_core': False,
                'requires_modules': ['students', 'teachers'],
                'included_roles': ['coordinador_academico', 'admin'],
                'permissions': ['manage_curriculum', 'assign_academic_load', 'manage_schedules', 'manage_evaluations'],
                'price_tier': 'premium',
                'monthly_price': 35.00,
                'trial_days': 15,
                'sort_order': 6
            },
            {
                'code': 'school_coexistence',
                'name': 'Módulo de Convivencia Escolar',
                'description': 'Registro de observaciones disciplinarias, registro de llamados de atención, acuerdos y seguimientos, informes del comité de convivencia, generación de actas',
                'icon': 'fas fa-balance-scale',
                'category': 'administrative',
                'is_core': False,
                'requires_modules': ['students'],
                'included_roles': ['coordinador_convivencia', 'psicologo', 'admin'],
                'permissions': ['register_observations', 'manage_disciplinary_actions', 'generate_coexistence_reports', 'manage_committee_acts'],
                'price_tier': 'basic',
                'monthly_price': 18.00,
                'trial_days': 30,
                'sort_order': 7
            },
            {
                'code': 'reports_certificates',
                'name': 'Módulo de Reportes y Certificados',
                'description': 'Boletines periódicos y finales, certificados de estudio, comportamiento, matrícula, etc., estadísticas por grupo, docente o institución, exportación a PDF, Excel, etc.',
                'icon': 'fas fa-file-alt',
                'category': 'administrative',
                'is_core': False,
                'requires_modules': ['students'],
                'included_roles': ['admin', 'secretaria', 'coordinador'],
                'permissions': ['generate_report_cards', 'issue_certificates', 'view_statistics', 'export_reports'],
                'price_tier': 'basic',
                'monthly_price': 22.00,
                'trial_days': 30,
                'sort_order': 8
            },
            {
                'code': 'communications',
                'name': 'Módulo de Comunicaciones',
                'description': 'Envío de circulares y notificaciones, alertas de tareas, notas, reuniones, integración con correo o WhatsApp (opcional), mensajes internos por rol',
                'icon': 'fas fa-comments',
                'category': 'communication',
                'is_core': False,
                'included_roles': ['admin', 'coordinador', 'docente', 'secretaria'],
                'permissions': ['send_circulars', 'manage_notifications', 'internal_messaging', 'whatsapp_integration'],
                'price_tier': 'premium',
                'monthly_price': 30.00,
                'trial_days': 15,
                'sort_order': 9
            },
            {
                'code': 'virtual_evaluations',
                'name': 'Evaluaciones y Tareas Virtuales (LMS)',
                'description': 'Subida de tareas, evaluaciones en línea, feedback y retroalimentación',
                'icon': 'fas fa-laptop',
                'category': 'optional',
                'is_core': False,
                'requires_modules': ['teachers', 'students'],
                'included_roles': ['docente', 'estudiante', 'coordinador'],
                'permissions': ['create_virtual_assignments', 'online_evaluations', 'digital_feedback', 'multimedia_content'],
                'price_tier': 'premium',
                'monthly_price': 45.00,
                'trial_days': 15,
                'sort_order': 10
            },
            {
                'code': 'financial_management',
                'name': 'Administración Financiera',
                'description': 'Gestión de pagos de matrícula, pensión, otros, historial de pagos y deuda por estudiante, reportes financieros por sede o curso, facturación y comprobantes',
                'icon': 'fas fa-dollar-sign',
                'category': 'financial',
                'is_core': False,
                'requires_modules': ['students'],
                'included_roles': ['admin', 'tesorero', 'contador'],
                'permissions': ['manage_payments', 'generate_invoices', 'financial_reports', 'manage_debts'],
                'price_tier': 'premium',
                'monthly_price': 40.00,
                'trial_days': 15,
                'sort_order': 11
            },
            {
                'code': 'document_management',
                'name': 'Gestión Documental',
                'description': 'Archivo de documentos por estudiante, formatos institucionales descargables, subida de documentos administrativos y legales',
                'icon': 'fas fa-folder-open',
                'category': 'administrative',
                'is_core': False,
                'included_roles': ['secretaria', 'admin'],
                'permissions': ['manage_documents', 'generate_forms', 'digital_archive', 'document_templates'],
                'price_tier': 'basic',
                'monthly_price': 12.00,
                'trial_days': 30,
                'sort_order': 12
            },
            {
                'code': 'audit_security',
                'name': 'Auditoría y Seguridad',
                'description': 'Historial de accesos, registro de cambios importantes, control de permisos por rol, alertas de seguridad',
                'icon': 'fas fa-shield-alt',
                'category': 'core',
                'is_core': False,
                'included_roles': ['admin', 'superadmin'],
                'permissions': ['view_access_logs', 'track_changes', 'manage_permissions', 'security_alerts'],
                'price_tier': 'basic',
                'monthly_price': 8.00,
                'trial_days': 30,
                'sort_order': 13
            }
        ]
        
        print("🌱 Creando módulos...")
        
        for module_data in modules_data:
            module = Module(
                code=module_data['code'],
                name=module_data['name'],
                description=module_data['description'],
                icon=module_data['icon'],
                category=module_data['category'],
                is_core=module_data['is_core'],
                price_tier=module_data['price_tier'],
                monthly_price=module_data['monthly_price'],
                trial_days=module_data['trial_days'],
                sort_order=module_data['sort_order']
            )
            
            # Asignar listas como propiedades JSON
            module.included_roles = module_data['included_roles']
            module.permissions = module_data['permissions']
            
            # Asignar dependencias si existen
            if 'requires_modules' in module_data:
                module.requires_modules = module_data['requires_modules']
            
            db.session.add(module)
            print(f"  ✅ {module.name}")
        
        db.session.commit()
        
        total_modules = Module.query.count()
        print(f"\n🎉 ¡{total_modules} módulos creados exitosamente!")
        
        # Mostrar resumen por categoría
        categories = db.session.query(Module.category).distinct().all()
        for (category,) in categories:
            count = Module.query.filter_by(category=category).count()
            print(f"  📂 {category.title()}: {count} módulos")

if __name__ == '__main__':
    seed_modules()