# app/models/institution.py
from app import db
from datetime import datetime
import json

class Institution(db.Model):
    """Modelo de Institución educativa"""
    __tablename__ = 'institutions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    city = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    website = db.Column(db.String(200))
    status = db.Column(db.String(20), default='active')  # active, inactive, suspended
    
    # Configuración visual
    logo = db.Column(db.String(255), nullable=True)  # Ruta del logo
    color_primary = db.Column(db.String(7), default='#007bff')  # Color hex
    color_secondary = db.Column(db.String(7), default='#6c757d')
    
    # Configuración académica
    academic_year = db.Column(db.Integer, nullable=False, default=2024)
    settings_json = db.Column(db.Text, nullable=True)  # JSON con configuraciones personalizadas
    
    # Control de estado
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones (CORREGIDAS - lazy='dynamic' solo para one-to-many)
    users = db.relationship('User', back_populates='institution', lazy='dynamic', cascade="all, delete")
    courses = db.relationship('Course', back_populates='institution', lazy='dynamic', cascade="all, delete")
    
    def __repr__(self):
        return f'<Institution {self.name}>'
    
    def get_settings(self):
        """Obtiene los parámetros como diccionario"""
        if self.settings_json:
            try:
                return json.loads(self.settings_json)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_settings(self, settings_dict):
        """Establece los parámetros desde un diccionario"""
        self.settings_json = json.dumps(settings_dict)
    
    @property
    def total_students(self):
        return self.users.filter_by(role='student', is_active=True).count()
    
    @property
    def total_teachers(self):
        return self.users.filter_by(role='teacher', is_active=True).count()
    
    @property
    def total_admins(self):
        return self.users.filter_by(role='admin', is_active=True).count()
    
    def to_dict(self):
        """Convierte la institución a diccionario"""
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'city': self.city,
            'address': self.address,
            'phone': self.phone,
            'email': self.email,
            'website': self.website,
            'status': self.status,
            'is_active': self.is_active,
            'academic_year': self.academic_year,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'total_students': self.total_students,
            'total_teachers': self.total_teachers,
            'total_admins': self.total_admins
        }