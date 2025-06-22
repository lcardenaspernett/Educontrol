#!/usr/bin/env python3
"""
Script para inicializar la base de datos de EduControl
Crea todas las tablas y datos iniciales necesarios
"""

import os
import sys
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.user import User
from app.models.institution import Institution

def init_database():
    """Inicializa la base de datos con las tablas y datos básicos"""
    
    app = create_app()
    
    with app.app_context():
        try:
            print("🔄 Iniciando configuración de base de datos...")
            
            # Eliminar todas las tablas existentes (¡CUIDADO en producción!)
            print("📝 Eliminando tablas existentes...")
            db.drop_all()
            
            # Crear todas las tablas
            print("🏗️  Creando nuevas tablas...")
            db.create_all()
            
            # Crear superadministrador inicial
            print("👑 Creando superadministrador...")
            superadmin = User(
                full_name="Super Administrador",
                email="superadmin@educontrol.com",
                username="superadmin",
                role="superadmin",
                is_active=True,
                institution_id=None  # Los superadmin no pertenecen a una institución específica
            )
            superadmin.set_password("admin123")  # Cambiar en producción
            
            db.session.add(superadmin)
            
            # Crear institución de ejemplo
            print("🏫 Creando institución de ejemplo...")
            institucion_ejemplo = Institution(
                name="Colegio Ejemplo",
                code="CEJ001",
                city="Barranquilla",
                address="Calle 45 #23-67",
                phone="+57 5 3601234",
                email="info@colegio-ejemplo.edu.co",
                status="active",
                is_active=True,
                academic_year=2025
            )
            
            db.session.add(institucion_ejemplo)
            db.session.flush()  # Para obtener el ID
            
            # Crear administrador institucional
            print("👨‍💼 Creando administrador institucional...")
            admin_institucional = User(
                full_name="Administrador Institucional",
                email="admin@colegio-ejemplo.edu.co",
                username="admin",
                role="admin",
                is_active=True,
                institution_id=institucion_ejemplo.id
            )
            admin_institucional.set_password("admin123")
            
            db.session.add(admin_institucional)
            
            # Crear algunos usuarios de ejemplo
            print("👥 Creando usuarios de ejemplo...")
            
            # Profesor de ejemplo
            profesor = User(
                full_name="María García",
                email="maria.garcia@colegio-ejemplo.edu.co",
                username="mgarcia",
                role="teacher",
                is_active=True,
                institution_id=institucion_ejemplo.id
            )
            profesor.set_password("profesor123")
            db.session.add(profesor)
            
            # Estudiante de ejemplo
            estudiante = User(
                full_name="Juan Pérez",
                email="juan.perez@colegio-ejemplo.edu.co",
                username="jperez",
                role="student",
                is_active=True,
                institution_id=institucion_ejemplo.id
            )
            estudiante.set_password("estudiante123")
            db.session.add(estudiante)
            
            # Padre de ejemplo
            padre = User(
                full_name="Carlos Pérez",
                email="carlos.perez@gmail.com",
                username="cperez",
                role="parent",
                is_active=True,
                institution_id=institucion_ejemplo.id
            )
            padre.set_password("padre123")
            db.session.add(padre)
            
            # Confirmar todos los cambios
            db.session.commit()
            
            print("✅ Base de datos inicializada correctamente!")
            print("\n📋 Credenciales creadas:")
            print("🔹 Superadministrador:")
            print("   📧 Email: superadmin@educontrol.com")
            print("   🔑 Username: superadmin")
            print("   🗝️  Password: admin123")
            print("\n🔹 Administrador Institucional:")
            print("   📧 Email: admin@colegio-ejemplo.edu.co")
            print("   🔑 Username: admin")
            print("   🗝️  Password: admin123")
            print("\n🔹 Profesor de Ejemplo:")
            print("   📧 Email: maria.garcia@colegio-ejemplo.edu.co")
            print("   🔑 Username: mgarcia")
            print("   🗝️  Password: profesor123")
            print("\n🔹 Estudiante de Ejemplo:")
            print("   📧 Email: juan.perez@colegio-ejemplo.edu.co")
            print("   🔑 Username: jperez")
            print("   🗝️  Password: estudiante123")
            
            print("\n🎉 ¡Listo! Puedes ejecutar la aplicación con:")
            print("   python run.py")
            print("\n💡 Accede con cualquiera de las credenciales de arriba")
            
        except Exception as e:
            print(f"❌ Error al inicializar la base de datos: {e}")
            db.session.rollback()
            raise e

def reset_superadmin():
    """Resetea solo la contraseña del superadministrador"""
    
    app = create_app()
    
    with app.app_context():
        try:
            superadmin = User.query.filter_by(role='superadmin').first()
            
            if superadmin:
                superadmin.set_password("admin123")
                db.session.commit()
                print("✅ Contraseña del superadministrador reseteada")
                print("🔑 Username: superadmin")
                print("🗝️  Password: admin123")
            else:
                print("❌ No se encontró el superadministrador")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            db.session.rollback()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "reset-superadmin":
        reset_superadmin()
    else:
        init_database()