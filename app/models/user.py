"""
Modelo User para EduControl
Maneja usuarios del sistema con roles multi-tenant
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(UserMixin, db.Model):
    """Modelo de User del sistema"""
    
    __tablename__ = 'users'
    
    # Campos principales
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=True, index=True)  # NUEVO CAMPO
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Control de roles y estado
    role = db.Column(db.Enum('superadmin', 'admin', 'teacher', 'student', 'parent',
                           name='user_role'), nullable=False, default='student')
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Multi-tenant
    institution_id = db.Column(db.Integer, db.ForeignKey('institutions.id'), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relaciones
    institution = db.relationship('Institution', back_populates='users', foreign_keys=[institution_id])
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def set_password(self, password):
        """Establece la contraseña hasheada"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verifica la contraseña"""
        return check_password_hash(self.password_hash, password)
    
    # Propiedades para facilitar consultas
    @property
    def institution_name(self):
        return self.institution.name if self.institution else None
    
    @property
    def is_institution_admin(self):
        return self.role == 'admin' and self.institution_id is not None
    
    @property
    def is_superadmin(self):
        """Verifica si es superadministrador"""
        return self.role == 'superadmin'
    
    def is_admin(self):
        """Verifica si es administrador institucional"""
        return self.role == 'admin'
    
    def is_teacher(self):
        """Verifica si es docente"""
        return self.role == 'teacher'
    
    def is_student(self):
        """Verifica si es estudiante"""
        return self.role == 'student'
    
    def is_parent(self):
        """Verifica si es padre/madre"""
        return self.role == 'parent'
    
    def can_access_institution(self, institution_id):
        """Verifica si puede acceder a una institución específica"""
        if self.is_superadmin:
            return True
        return self.institution_id == institution_id
    
    def to_dict(self):
        """Convierte el usuario a diccionario"""
        return {
            'id': self.id,
            'full_name': self.full_name,
            'email': self.email,
            'username': self.username,  # AGREGADO
            'role': self.role,
            'is_active': self.is_active,
            'institution_id': self.institution_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }