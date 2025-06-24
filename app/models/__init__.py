"""
Modelos de base de datos para EduControl
"""

from app.models.user import User
from app.models.institution import Institution
from app.models.course import Course
from app.models.module import Module
from app.models.institution_module import InstitutionModule

__all__ = ['User', 'Institution', 'Course', 'Module', 'InstitutionModule']