# app/models/module.py
from app import db
from datetime import datetime
import json

class Module(db.Model):
    """Modelo de Módulo del sistema"""
    __tablename__ = 'modules'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50), default='fas fa-cog')
    category = db.Column(db.Enum('core', 'academic', 'administrative', 
                                'communication', 'financial', 'optional',
                                name='module_category'), nullable=False)
    
    # Control de activación
    is_core = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Dependencias y roles (como JSON)
    requires_modules_json = db.Column(db.Text)  # JSON con códigos de módulos requeridos
    included_roles_json = db.Column(db.Text)    # JSON con roles que incluye
    permissions_json = db.Column(db.Text)       # JSON con permisos
    
    # Configuración de precio
    price_tier = db.Column(db.Enum('free', 'basic', 'premium', name='price_tier'), default='basic')
    monthly_price = db.Column(db.Numeric(8, 2), default=0.00)
    trial_days = db.Column(db.Integer, default=30)
    
    # Orden de visualización
    sort_order = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Module {self.code}>'
    
    # Propiedades para manejar JSON
    @property
    def requires_modules(self):
        if self.requires_modules_json:
            try:
                return json.loads(self.requires_modules_json)
            except json.JSONDecodeError:
                return []
        return []
    
    @requires_modules.setter
    def requires_modules(self, modules_list):
        self.requires_modules_json = json.dumps(modules_list)
    
    @property
    def included_roles(self):
        if self.included_roles_json:
            try:
                return json.loads(self.included_roles_json)
            except json.JSONDecodeError:
                return []
        return []
    
    @included_roles.setter
    def included_roles(self, roles_list):
        self.included_roles_json = json.dumps(roles_list)
    
    @property
    def permissions(self):
        if self.permissions_json:
            try:
                return json.loads(self.permissions_json)
            except json.JSONDecodeError:
                return []
        return []
    
    @permissions.setter
    def permissions(self, permissions_list):
        self.permissions_json = json.dumps(permissions_list)
    
    @property
    def has_requirements(self):
        return len(self.requires_modules) > 0
    
    @property
    def is_premium(self):
        return self.price_tier == 'premium'
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'icon': self.icon,
            'category': self.category,
            'is_core': self.is_core,
            'is_active': self.is_active,
            'requires_modules': self.requires_modules,
            'included_roles': self.included_roles,
            'permissions': self.permissions,
            'price_tier': self.price_tier,
            'monthly_price': float(self.monthly_price) if self.monthly_price else 0.0,
            'trial_days': self.trial_days,
            'sort_order': self.sort_order
        }