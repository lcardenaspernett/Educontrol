# app/services/module_service.py
"""
Servicio para gestión de módulos institucionales
"""

from datetime import datetime, timedelta
from app import db
from app.models.module import Module
from app.models.institution import Institution
from app.models.institution_module import InstitutionModule

class ModuleService:
    """Servicio para gestionar módulos de instituciones"""
    
    @staticmethod
    def activate_modules_for_institution(institution_id, module_codes, activated_by_user_id=None):
        """
        Activa módulos específicos para una institución
        """
        try:
            institution = Institution.query.get(institution_id)
            if not institution:
                return {'success': False, 'error': 'Institución no encontrada'}
            
            modules = Module.query.filter(Module.code.in_(module_codes)).all()
            if len(modules) != len(module_codes):
                found_codes = [m.code for m in modules]
                missing = set(module_codes) - set(found_codes)
                return {'success': False, 'error': f'Módulos no encontrados: {missing}'}
            
            activated_modules = []
            errors = []
            
            for module in modules:
                # Verificar dependencias
                dependency_check = ModuleService._check_dependencies(institution_id, module)
                if not dependency_check['success']:
                    errors.append(f"{module.name}: {dependency_check['error']}")
                    continue
                
                # Verificar si ya está activado
                existing = InstitutionModule.query.filter_by(
                    institution_id=institution_id,
                    module_id=module.id
                ).first()
                
                if existing:
                    if existing.is_active:
                        continue  # Ya está activo
                    else:
                        # Reactivar módulo existente
                        existing.is_active = True
                        existing.activated_at = datetime.utcnow()
                        ModuleService._set_trial_period(existing, module)
                else:
                    # Crear nueva activación
                    inst_module = InstitutionModule(
                        institution_id=institution_id,
                        module_id=module.id,
                        is_active=True,
                        activated_at=datetime.utcnow()
                    )
                    ModuleService._set_trial_period(inst_module, module)
                    db.session.add(inst_module)
                
                activated_modules.append(module.name)
            
            db.session.commit()
            
            return {
                'success': True,
                'activated_modules': activated_modules,
                'errors': errors if errors else None
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def activate_core_modules_for_institution(institution_id):
        """
        Activa automáticamente todos los módulos core para una institución nueva
        """
        core_modules = Module.query.filter_by(is_core=True).all()
        core_codes = [module.code for module in core_modules]
        
        return ModuleService.activate_modules_for_institution(institution_id, core_codes)
    
    @staticmethod
    def deactivate_module(institution_id, module_code):
        """
        Desactiva un módulo específico
        """
        try:
            module = Module.query.filter_by(code=module_code).first()
            if not module:
                return {'success': False, 'error': 'Módulo no encontrado'}
            
            if module.is_core:
                return {'success': False, 'error': 'No se pueden desactivar módulos core'}
            
            # Verificar dependencias (otros módulos que dependen de este)
            dependent_check = ModuleService._check_dependent_modules(institution_id, module_code)
            if not dependent_check['success']:
                return dependent_check
            
            inst_module = InstitutionModule.query.filter_by(
                institution_id=institution_id,
                module_id=module.id
            ).first()
            
            if inst_module:
                inst_module.is_active = False
                db.session.commit()
                return {'success': True, 'message': f'Módulo {module.name} desactivado'}
            else:
                return {'success': False, 'error': 'Módulo no estaba activado'}
                
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_institution_modules_status(institution_id):
        """
        Obtiene el estado de todos los módulos para una institución
        """
        try:
            # Obtener todos los módulos con su estado para la institución
            all_modules = Module.query.order_by(Module.sort_order).all()
            modules_status = []
            
            for module in all_modules:
                inst_module = InstitutionModule.query.filter_by(
                    institution_id=institution_id,
                    module_id=module.id
                ).first()
                
                if inst_module:
                    status = {
                        'module': module.to_dict(),
                        'is_active': inst_module.is_active,
                        'status': inst_module.status,
                        'activated_at': inst_module.activated_at.isoformat() if inst_module.activated_at else None,
                        'trial_ends_at': inst_module.trial_ends_at.isoformat() if inst_module.trial_ends_at else None,
                        'can_use': inst_module.is_active and (module.is_core or inst_module.is_in_trial or inst_module.is_subscribed)
                    }
                else:
                    status = {
                        'module': module.to_dict(),
                        'is_active': False,
                        'status': 'not_installed',
                        'activated_at': None,
                        'trial_ends_at': None,
                        'can_use': False
                    }
                
                modules_status.append(status)
            
            return {'success': True, 'modules': modules_status}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_available_modules_for_selection():
        """
        Obtiene módulos disponibles para selección en formularios (no core)
        """
        modules = Module.query.filter_by(is_active=True, is_core=False).order_by(Module.category, Module.sort_order).all()
        
        # Agrupar por categoría
        grouped = {}
        for module in modules:
            if module.category not in grouped:
                grouped[module.category] = []
            grouped[module.category].append(module.to_dict())
        
        return grouped
    
    @staticmethod
    def _check_dependencies(institution_id, module):
        """
        Verifica que las dependencias de un módulo estén activas
        """
        if not module.requires_modules:
            return {'success': True}
        
        for required_code in module.requires_modules:
            required_module = Module.query.filter_by(code=required_code).first()
            if not required_module:
                return {'success': False, 'error': f'Módulo requerido no encontrado: {required_code}'}
            
            inst_module = InstitutionModule.query.filter_by(
                institution_id=institution_id,
                module_id=required_module.id,
                is_active=True
            ).first()
            
            if not inst_module:
                return {'success': False, 'error': f'Requiere el módulo: {required_module.name}'}
        
        return {'success': True}
    
    @staticmethod
    def _check_dependent_modules(institution_id, module_code):
        """
        Verifica si hay módulos activos que dependen del módulo a desactivar
        """
        dependent_modules = Module.query.filter(
            Module.requires_modules_json.contains(f'"{module_code}"')
        ).all()
        
        active_dependents = []
        for dep_module in dependent_modules:
            inst_module = InstitutionModule.query.filter_by(
                institution_id=institution_id,
                module_id=dep_module.id,
                is_active=True
            ).first()
            
            if inst_module:
                active_dependents.append(dep_module.name)
        
        if active_dependents:
            return {
                'success': False, 
                'error': f'No se puede desactivar. Los siguientes módulos dependen de este: {", ".join(active_dependents)}'
            }
        
        return {'success': True}
    
    @staticmethod
    def _set_trial_period(inst_module, module):
        """
        Establece el período de prueba para un módulo
        """
        if module.is_core or module.trial_days == 0:
            # Módulos core no tienen período de prueba
            inst_module.trial_starts_at = None
            inst_module.trial_ends_at = None
        else:
            # Establecer período de prueba
            inst_module.trial_starts_at = datetime.utcnow()
            inst_module.trial_ends_at = datetime.utcnow() + timedelta(days=module.trial_days)
    
    @staticmethod
    def extend_trial_period(institution_id, module_code, additional_days):
        """
        Extiende el período de prueba de un módulo
        """
        try:
            module = Module.query.filter_by(code=module_code).first()
            if not module:
                return {'success': False, 'error': 'Módulo no encontrado'}
            
            inst_module = InstitutionModule.query.filter_by(
                institution_id=institution_id,
                module_id=module.id
            ).first()
            
            if not inst_module:
                return {'success': False, 'error': 'Módulo no está activado'}
            
            if inst_module.trial_ends_at:
                inst_module.trial_ends_at += timedelta(days=additional_days)
            else:
                # Si no tenía período de prueba, crear uno
                inst_module.trial_starts_at = datetime.utcnow()
                inst_module.trial_ends_at = datetime.utcnow() + timedelta(days=additional_days)
            
            db.session.commit()
            
            return {
                'success': True, 
                'message': f'Período de prueba extendido por {additional_days} días',
                'new_trial_end': inst_module.trial_ends_at.isoformat()
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}