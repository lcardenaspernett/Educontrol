# app/models/institution_module.py
from app import db
from datetime import datetime
import json

class InstitutionModule(db.Model):
    """Relación entre Institución y Módulos"""
    __tablename__ = 'institution_modules'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Claves foráneas
    institution_id = db.Column(db.Integer, db.ForeignKey('institutions.id'), nullable=False)
    module_id = db.Column(db.Integer, db.ForeignKey('modules.id'), nullable=False)
    
    # Estado del módulo para esta institución
    is_active = db.Column(db.Boolean, default=True)
    
    # Control de fechas
    activated_at = db.Column(db.DateTime, default=datetime.utcnow)
    trial_starts_at = db.Column(db.DateTime)
    trial_ends_at = db.Column(db.DateTime)
    subscription_starts_at = db.Column(db.DateTime)
    subscription_ends_at = db.Column(db.DateTime)
    
    # Configuraciones específicas del módulo para esta institución
    settings_json = db.Column(db.Text)
    usage_stats_json = db.Column(db.Text)
    last_used_at = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    institution = db.relationship('Institution', backref='institution_modules')
    module = db.relationship('Module', backref='institution_modules')
    
    # Constraint de unicidad
    __table_args__ = (db.UniqueConstraint('institution_id', 'module_id', name='unique_institution_module'),)
    
    def __repr__(self):
        return f'<InstitutionModule {self.institution_id}-{self.module_id}>'
    
    @property
    def settings(self):
        if self.settings_json:
            try:
                return json.loads(self.settings_json)
            except json.JSONDecodeError:
                return {}
        return {}
    
    @settings.setter
    def settings(self, settings_dict):
        self.settings_json = json.dumps(settings_dict)
    
    @property
    def usage_stats(self):
        if self.usage_stats_json:
            try:
                return json.loads(self.usage_stats_json)
            except json.JSONDecodeError:
                return {}
        return {}
    
    @usage_stats.setter
    def usage_stats(self, stats_dict):
        self.usage_stats_json = json.dumps(stats_dict)
    
    @property
    def is_in_trial(self):
        if not self.trial_ends_at:
            return False
        return datetime.utcnow() <= self.trial_ends_at
    
    @property
    def is_subscribed(self):
        if not self.subscription_ends_at:
            return False
        return datetime.utcnow() <= self.subscription_ends_at
    
    @property
    def status(self):
        """Retorna el estado actual del módulo"""
        if not self.is_active:
            return 'inactive'
        
        if self.module.is_core:
            return 'core'
        
        if self.is_in_trial:
            days_left = (self.trial_ends_at - datetime.utcnow()).days
            return f'trial_{days_left}_days'
        
        if self.is_subscribed:
            return 'subscribed'
        
        return 'expired'
    
    def to_dict(self):
        return {
            'id': self.id,
            'institution_id': self.institution_id,
            'module_id': self.module_id,
            'module_code': self.module.code if self.module else None,
            'module_name': self.module.name if self.module else None,
            'is_active': self.is_active,
            'status': self.status,
            'activated_at': self.activated_at.isoformat() if self.activated_at else None,
            'trial_ends_at': self.trial_ends_at.isoformat() if self.trial_ends_at else None,
            'subscription_ends_at': self.subscription_ends_at.isoformat() if self.subscription_ends_at else None,
            'settings': self.settings,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None
        }