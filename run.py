#!/usr/bin/env python3
"""
EduControl - Sistema de Gestión Educativa
Archivo principal para ejecutar la aplicación Flask
"""

import os
from app import create_app
from flask_migrate import upgrade

# Obtener configuración del entorno
config_name = os.environ.get('FLASK_CONFIG', 'default')

# Crear la aplicación
app = create_app(config_name)

@app.cli.command()
def deploy():
    """Comando para despliegue en producción"""
    # Migrar base de datos a la última revisión
    upgrade()

if __name__ == '__main__':
    # Ejecutar la aplicación
    app.run(debug=True, host='0.0.0.0', port=5000)
