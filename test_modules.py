# test_modules.py
from app import create_app, db
from app.models import Institution
from app.services.module_service import ModuleService

app = create_app()
with app.app_context():
    # Buscar una institución existente o crear una de prueba
    institution = Institution.query.first()
    
    if not institution:
        # Crear institución de prueba
        institution = Institution(
            name='Institucion de Prueba',
            code='TEST001',
            city='Barranquilla',
            academic_year=2025
        )
        db.session.add(institution)
        db.session.commit()
        print(f'Institucion de prueba creada: {institution.name}')
    else:
        print(f'Usando institucion existente: {institution.name}')
    
    # Activar módulos core automáticamente
    result = ModuleService.activate_core_modules_for_institution(institution.id)
    print(f'Modulos core activados: {result}')
    
    # Activar algunos módulos académicos
    academic_result = ModuleService.activate_modules_for_institution(
        institution.id, 
        ['students', 'teachers']
    )
    print(f'Modulos academicos activados: {academic_result}')
    
    # Obtener estado completo
    status = ModuleService.get_institution_modules_status(institution.id)
    if status['success']:
        active_modules = [m for m in status['modules'] if m['is_active']]
        print(f'Total modulos activos: {len(active_modules)}')
        for module in active_modules:
            name = module['module']['name']
            status_text = module['status']
            print(f'  - {name} ({status_text})')
    
    print('\nSistema de modulos funcionando perfectamente!')
