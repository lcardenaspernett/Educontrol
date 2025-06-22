#!/usr/bin/env python3
# setup_superadmin.py - Script para configurar el sistema multi-instituci√≥n
from app import create_app, db
from app.models.user import User
from app.models.institution import Institution
from werkzeug.security import generate_password_hash

def setup_superadmin():
    """Crear el primer SuperAdmin del sistema"""
    app = create_app()
    
    with app.app_context():
        # Crear tablas si no existen
        db.create_all()
        
        # Verificar si ya existe un SuperAdmin
        existing_superadmin = User.query.filter_by(is_superadmin=True).first()
        
        if existing_superadmin:
            print(f"‚úÖ Ya existe un SuperAdmin: {existing_superadmin.email}")
            return existing_superadmin
        
        # Crear SuperAdmin
        superadmin = User(
            email='superadmin@educontrol.com',
            first_name='Super',
            last_name='Administrador',
            role='admin',
            is_superadmin=True,
            is_active=True,
            institution_id=None  # SuperAdmin no pertenece a ninguna instituci√≥n
        )
        superadmin.set_password('SuperAdmin123!')
        
        db.session.add(superadmin)
        db.session.commit()
        
        print("Ìæâ SuperAdmin creado exitosamente!")
        print(f"Ì≥ß Email: {superadmin.email}")
        print(f"Ì¥ë Password: SuperAdmin123!")
        print("‚ö†Ô∏è  CAMBIA LA CONTRASE√ëA INMEDIATAMENTE")
        
        return superadmin

def create_sample_institutions():
    """Crear instituciones de ejemplo"""
    app = create_app()
    
    with app.app_context():
        institutions_data = [
            {
                'name': 'Colegio San Jos√©',
                'code': 'CSJ001',
                'city': 'Barranquilla',
                'address': 'Calle 45 #23-67',
                'phone': '+57 5 3601234',
                'email': 'info@colegiosanjose.edu.co'
            },
            {
                'name': 'Instituto T√©cnico Industrial',
                'code': 'ITI002', 
                'city': 'Cartagena',
                'address': 'Avenida Pedro de Heredia #12-34',
                'phone': '+57 5 6641234',
                'email': 'contacto@iti.edu.co'
            },
            {
                'name': 'Universidad del Atl√°ntico',
                'code': 'UATL003',
                'city': 'Barranquilla',
                'address': 'Km 7 Antigua v√≠a Puerto Colombia',
                'phone': '+57 5 3599999',
                'email': 'rectoria@uniatlantico.edu.co'
            }
        ]
        
        for inst_data in institutions_data:
            existing = Institution.query.filter_by(code=inst_data['code']).first()
            if not existing:
                institution = Institution(**inst_data)
                db.session.add(institution)
                print(f"‚úÖ Instituci√≥n creada: {institution.name}")
        
        db.session.commit()
        print("Ìø´ Instituciones de ejemplo creadas!")

def migrate_existing_users():
    """Migrar usuarios existentes al nuevo sistema"""
    app = create_app()
    
    with app.app_context():
        # Buscar usuarios que no tienen instituci√≥n asignada
        users_without_institution = User.query.filter_by(institution_id=None).all()
        
        if users_without_institution:
            # Crear instituci√≥n por defecto para usuarios existentes
            default_institution = Institution.query.filter_by(code='DEFAULT').first()
            
            if not default_institution:
                default_institution = Institution(
                    name='Instituci√≥n Principal',
                    code='DEFAULT',
                    city='No especificada',
                    status='active'
                )
                db.session.add(default_institution)
                db.session.commit()
            
            # Asignar usuarios a instituci√≥n por defecto (excepto SuperAdmins)
            for user in users_without_institution:
                if not user.is_superadmin:
                    user.institution_id = default_institution.id
            
            db.session.commit()
            print(f"Ì±• {len(users_without_institution)} usuarios migrados a instituci√≥n por defecto")

if __name__ == '__main__':
    print("Ì∫Ä Configurando sistema multi-instituci√≥n...")
    
    # 1. Crear SuperAdmin
    setup_superadmin()
    
    # 2. Migrar usuarios existentes
    migrate_existing_users()
    
    # 3. Crear instituciones de ejemplo
    create_sample_institutions()
    
    print("\n‚úÖ Configuraci√≥n completada!")
    print("\nÌ≥ã Pr√≥ximos pasos:")
    print("1. Ejecutar migraciones: flask db upgrade")
    print("2. Iniciar aplicaci√≥n: python run.py")
    print("3. Acceder como SuperAdmin para configurar instituciones")
    print("4. Crear admins institucionales")
