"""
Modelo Curso para EduControl
Representa los cursos o asignaturas de las instituciones
"""

from datetime import datetime
from app import db

class Course(db.Model):
    """Modelo de Curso"""
    
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    code = db.Column(db.String(20), unique=True, nullable=False)
    status = db.Column(db.String(20), default='active')  # active, inactive
    
    # Relación con institución (many-to-one)
    institution_id = db.Column(db.Integer, db.ForeignKey('institutions.id'), nullable=False)
    institution = db.relationship('Institution', back_populates='courses')
    
    # Relación con profesores (many-to-one)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    teacher = db.relationship('User', foreign_keys=[teacher_id])
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Course {self.name}>'
    
    # Propiedades para facilitar consultas
    @property
    def is_active(self):
        return self.status == 'active'
    
    @property
    def teacher_name(self):
        return self.teacher.full_name if self.teacher else None
    
    @property
    def institution_name(self):
        return self.institution.name if self.institution else None
    
    def to_dict(self):
        """Convierte el curso a diccionario"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'code': self.code,
            'status': self.status,
            'institution_id': self.institution_id,
            'institution_name': self.institution_name,
            'teacher_id': self.teacher_id,
            'teacher_name': self.teacher_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }