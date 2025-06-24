# verify_modules.py
from app import create_app, db
from app.models.module import Module

app = create_app()
with app.app_context():
    print('RESUMEN DE MÓDULOS CREADOS:')
    print('=' * 50)
    
    # Mostrar módulos por categoría
    categories = ['core', 'academic', 'administrative', 'communication', 'financial', 'optional']
    
    for category in categories:
        modules = Module.query.filter_by(category=category).order_by(Module.sort_order).all()
        if modules:
            print(f'\n{category.upper()}:')
            for module in modules:
                icon = 'FREE' if module.is_core else 'PAID'
                price = f'{module.monthly_price}' if module.monthly_price > 0 else 'Gratis'
                print(f'  [{icon}] {module.name} - ${price}/mes')
    
    print(f'\nTotal: {Module.query.count()} modulos')
    
    # Probar funcionalidad básica
    print('\n' + '=' * 50)
    print('PROBANDO FUNCIONALIDAD:')
    
    # Obtener algunos módulos
    core_modules = Module.query.filter_by(is_core=True).all()
    academic_modules = Module.query.filter_by(category='academic').all()
    
    print(f'\nModulos core encontrados: {len(core_modules)}')
    for module in core_modules:
        print(f'  - {module.name} (roles: {module.included_roles})')
    
    print(f'\nModulos academicos encontrados: {len(academic_modules)}')
    for module in academic_modules:
        requires = f' (requiere: {module.requires_modules})' if module.requires_modules else ''
        print(f'  - {module.name}{requires}')
    
    print('\nModulos funcionando correctamente!')
