"""
Modelos de base de datos para EduControl
"""

from app.models.user import User
from app.models.institution import Institution
from app.models.course import Course

__all__ = ['User', 'Institution', 'Course']
