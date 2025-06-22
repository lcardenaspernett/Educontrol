"""
Funciones auxiliares y utilidades
"""

from datetime import datetime
from flask import flash

def format_date(date, format='%d/%m/%Y'):
    """Formatea una fecha"""
    if date:
        return date.strftime(format)
    return ''

def format_datetime(datetime_obj, format='%d/%m/%Y %H:%M'):
    """Formatea una fecha y hora"""
    if datetime_obj:
        return datetime_obj.strftime(format)
    return ''

def get_current_year():
    """Obtiene el año actual"""
    return datetime.now().year

def flash_errors(form):
    """Muestra errores de formulario como mensajes flash"""
    for field, errors in form.errors.items():
        for error in errors:
            flash(f'{getattr(form, field).label.text}: {error}', 'error')

def generate_username_from_email(email):
    """Genera un nombre de usuario desde un email"""
    return email.split('@')[0]

def safe_string(text, max_length=50):
    """Limita la longitud de una cadena de texto"""
    if text and len(text) > max_length:
        return text[:max_length] + '...'
    return text or ''

def calculate_age(birth_date):
    """Calcula la edad desde una fecha de nacimiento"""
    if not birth_date:
        return None
    
    today = datetime.now().date()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

def validate_academic_year(year):
    """Valida que un año académico sea válido"""
    current_year = get_current_year()
    return current_year - 5 <= year <= current_year + 2

def get_academic_years_list(years_back=5, years_forward=2):
    """Obtiene una lista de años académicos válidos"""
    current_year = get_current_year()
    return [(year, str(year)) for year in range(current_year - years_back, current_year + years_forward + 1)]
