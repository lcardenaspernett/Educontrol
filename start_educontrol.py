#!/usr/bin/env python3
"""
Script de inicio completo para EduControl
Inicializa la base de datos y lanza la aplicación
"""

import os
import sys
import subprocess
from datetime import datetime

def print_banner():
    """Muestra el banner de EduControl"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║    ███████╗██████╗ ██╗   ██╗ ██████╗ ██████╗ ███╗   ██╗    ║
    ║    ██╔════╝██╔══██╗██║   ██║██╔════╝██╔═══██╗████╗  ██║    ║
    ║    █████╗  ██║  ██║██║   ██║██║     ██║   ██║██╔██╗ ██║    ║
    ║    ██╔══╝  ██║  ██║██║   ██║██║     ██║   ██║██║╚██╗██║    ║
    ║    ███████╗██████╔╝╚██████╔╝╚██████╗╚██████╔╝██║ ╚████║    ║
    ║    ╚══════╝╚═════╝  ╚═════╝  ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝    ║
    ║                                                              ║
    ║            Sistema de Gestión Educativa v1.0.2              ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_requirements():
    """Verifica que las dependencias estén instaladas"""
    required_packages = [
        'flask',
        'flask-sqlalchemy',
        'flask-migrate',
        'flask-login',
        'flask-bootstrap',
        'werkzeug'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Faltan dependencias: {', '.join(missing_packages)}")
        print("\n💡 Instala las dependencias con:")
        print("   pip install -r requirements.txt")
        return False
    
    return True

def create_requirements_file():
    """Crea el archivo requirements.txt si no existe"""
    requirements_content = """Flask==2.3.3
Flask-SQLAlchemy==3.0.5
Flask-Migrate==4.0.5
Flask-Login==0.6.3
Flask-Bootstrap==3.3.7.1
Flask-WTF==1.1.1
Werkzeug==2.3.7
python-dotenv==1.0.0
WTForms==3.0.1
"""
    
    if not os.path.exists('requirements.txt'):
        with open('requirements.txt', 'w') as f:
            f.write(requirements_content)
        print("✅ Archivo requirements.txt creado")

def create_folder_structure():
    """Crea la estructura de carpetas necesaria"""
    folders = [
        'app/static/css',
        'app/static/js',
        'app/static/img',
        'app/templates/auth',
        'app/templates/errors',
        'app/templates/superadmin',
        'app/models',
        'app/routes',
        'app/auth',
        'migrations'
    ]
    
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
    
    print("✅ Estructura de carpetas verificada")

def initialize_database():
    """Inicializa la base de datos"""
    try:
        # Importar después de verificar dependencias
        from app import create_app, db
        from app.models.user import User
        from app.models.institution import Institution
        
        app = create_app()
        
        with app.app_context():
            print("🔄 Inicializando base de datos...")
            
            # Crear todas las tablas
            db.create_all()
            
            # Verificar si ya existe el superadmin
            existing_superadmin = User.query.filter_by(role='superadmin').first()
            
            if not existing_superadmin:
                print("👑 Creando superadministrador...")
                
                # Crear superadministrador
                superadmin = User(
                    full_name="Super Administrador",
                    email="superadmin@educontrol.com",
                    username="superadmin",
                    role="superadmin",
                    is_active=True,
                    institution_id=None
                )
                superadmin.set_password("admin123")
                db.session.add(superadmin)
                
                # Crear institución de ejemplo
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
                db.session.flush()
                
                # Crear admin institucional
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
                
                db.session.commit()
                print("✅ Usuarios de ejemplo creados")
            else:
                print("✅ Base de datos ya inicializada")
            
            return True
            
    except Exception as e:
        print(f"❌ Error al inicializar la base de datos: {e}")
        return False

def show_credentials():
    """Muestra las credenciales de acceso"""
    print("\n" + "="*60)
    print("🔑 CREDENCIALES DE ACCESO")
    print("="*60)
    print("\n🌟 SUPERADMINISTRADOR:")
    print("   📧 Email: superadmin@educontrol.com")
    print("   👤 Usuario: superadmin")
    print("   🔒 Contraseña: admin123")
    
    print("\n🏛️  ADMINISTRADOR INSTITUCIONAL:")
    print("   📧 Email: admin@colegio-ejemplo.edu.co")
    print("   👤 Usuario: admin")
    print("   🔒 Contraseña: admin123")
    
    print("\n👨‍🏫 PROFESOR:")
    print("   📧 Email: maria.garcia@colegio-ejemplo.edu.co")
    print("   👤 Usuario: mgarcia")
    print("   🔒 Contraseña: profesor123")
    
    print("\n🎓 ESTUDIANTE:")
    print("   📧 Email: juan.perez@colegio-ejemplo.edu.co")
    print("   👤 Usuario: jperez")
    print("   🔒 Contraseña: estudiante123")
    print("\n" + "="*60)

def launch_application():
    """Lanza la aplicación Flask"""
    print("\n🚀 Iniciando EduControl...")
    print("📡 Servidor disponible en: http://localhost:5000")
    print("🛑 Presiona Ctrl+C para detener el servidor\n")
    
    try:
        # Ejecutar la aplicación
        os.system("python run.py")
    except KeyboardInterrupt:
        print("\n\n👋 EduControl detenido. ¡Hasta luego!")

def main():
    """Función principal"""
    print_banner()
    
    print("🔍 Verificando sistema...")
    
    # Crear archivo requirements.txt si no existe
    create_requirements_file()
    
    # Verificar dependencias
    if not check_requirements():
        return
    
    # Crear estructura de carpetas
    create_folder_structure()
    
    # Inicializar base de datos
    if not initialize_database():
        print("❌ No se pudo inicializar la base de datos")
        return
    
    # Mostrar credenciales
    show_credentials()
    
    # Preguntar si quiere iniciar la aplicación
    response = input("\n¿Deseas iniciar la aplicación ahora? (s/n): ").strip().lower()
    
    if response in ['s', 'si', 'sí', 'y', 'yes']:
        launch_application()
    else:
        print("\n💡 Para iniciar EduControl manualmente, ejecuta:")
        print("   python run.py")
        print("\n📚 Documentación: https://github.com/tu-usuario/educontrol")

if __name__ == "__main__":
    main()