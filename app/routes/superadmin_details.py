# FUNCIÓN AUXILIAR: Generar password aleatorio seguro
def generate_random_password(length=12):
    """Genera una contraseña aleatoria segura"""
    import string
    import secrets
    
    # Caracteres permitidos
    letters = string.ascii_letters
    digits = string.digits
    symbols = "!@#$%&*"
    
    # Asegurar al menos un carácter de cada tipo
    password = [
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.ascii_uppercase), 
        secrets.choice(digits),
        secrets.choice(symbols)
    ]
    
    # Completar con caracteres aleatorios
    all_chars = letters + digits + symbols
    for _ in range(length - 4):
        password.append(secrets.choice(all_chars))
    
    # Mezclar la lista
    secrets.SystemRandom().shuffle(password)
    
    return ''.join(password)

# VERIFICACIÓN: Endpoint para revisar detalles completos de la institución
@superadmin_bp.route('/institutions/<int:institution_id>/details')
@login_required
@superadmin_required
def institution_details(institution_id):
    """Mostrar detalles completos de una institución con módulos y configuración"""
    try:
        # Obtener la institución
        institution = Institution.query.get_or_404(institution_id)
        
        # Obtener estado de módulos usando ModuleService
        from app.services.module_service import ModuleService
        modules_status = ModuleService.get_institution_modules_status(institution_id)
        
        # Obtener usuarios de la institución
        from app.models.user import User
        institution_users = User.query.filter_by(institution_id=institution_id).all()
        
        # Separar por roles
        users_by_role = {}
        for user in institution_users:
            role = user.role
            if role not in users_by_role:
                users_by_role[role] = []
            users_by_role[role].append({
                'id': user.id,
                'username': getattr(user, 'username', 'N/A'),
                'email': user.email,
                'full_name': getattr(user, 'full_name', f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip()),
                'is_active': user.is_active,
                'created_at': user.created_at.strftime('%d/%m/%Y %H:%M') if hasattr(user, 'created_at') and user.created_at else 'N/A'
            })
        
        # Obtener configuración adicional si existe
        additional_settings = {}
        if hasattr(institution, 'get_settings'):
            additional_settings = institution.get_settings() or {}
        elif hasattr(institution, 'settings_json') and institution.settings_json:
            import json
            try:
                additional_settings = json.loads(institution.settings_json)
            except:
                additional_settings = {}
        
        # Estadísticas rápidas
        stats = {
            'total_modules': 0,
            'active_modules': 0,
            'trial_modules': 0,
            'subscribed_modules': 0,
            'total_users': len(institution_users),
            'admin_users': len(users_by_role.get('admin', [])),
            'other_users': len(institution_users) - len(users_by_role.get('admin', []))
        }
        
        if modules_status['success']:
            modules = modules_status['modules']
            stats['total_modules'] = len(modules)
            stats['active_modules'] = len([m for m in modules if m['is_active']])
            stats['trial_modules'] = len([m for m in modules if m['is_active'] and m.get('trial_ends_at')])
            stats['subscribed_modules'] = len([m for m in modules if m['is_active'] and not m.get('trial_ends_at')])
        
        # Log de acceso
        security_logger.info(
            f'INSTITUTION_DETAILS_ACCESS - Institution: {institution.name} ({institution.code}) - '
            f'User: {current_user.username} - IP: {request.remote_addr}'
        )
        
        return render_template('superadmin/institution_details.html',
                             institution=institution,
                             modules_status=modules_status,
                             users_by_role=users_by_role,
                             additional_settings=additional_settings,
                             stats=stats)
        
    except Exception as e:
        security_logger.error(
            f'INSTITUTION_DETAILS_ERROR - ID: {institution_id} - '
            f'User: {current_user.username} - Error: {str(e)} - IP: {request.remote_addr}'
        )
        flash('Error al obtener detalles de la institución', 'error')
        return redirect(url_for('superadmin.institutions'))

@superadmin_bp.route('/institutions/<int:institution_id>/modules/status')
@login_required
@superadmin_required
def institution_modules_status_api(institution_id):
    """API para obtener el estado actual de módulos de una institución"""
    try:
        # Verificar que la institución existe
        institution = Institution.query.get_or_404(institution_id)
        
        # Obtener estado de módulos
        from app.services.module_service import ModuleService
        modules_status = ModuleService.get_institution_modules_status(institution_id)
        
        if modules_status['success']:
            # Agregar información adicional útil
            modules = modules_status['modules']
            
            # Contar por estado
            status_counts = {
                'active': 0,
                'inactive': 0,
                'trial': 0,
                'expired': 0
            }
            
            # Información detallada por módulo
            detailed_modules = []
            
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            
            for module_info in modules:
                module = module_info['module']
                is_active = module_info['is_active']
                trial_ends_at = module_info.get('trial_ends_at')
                
                # Determinar estado específico
                if not is_active:
                    status = 'inactive'
                    status_counts['inactive'] += 1
                elif trial_ends_at:
                    trial_end = datetime.fromisoformat(trial_ends_at.replace('Z', '+00:00'))
                    if trial_end > now:
                        status = 'trial'
                        status_counts['trial'] += 1
                    else:
                        status = 'expired'
                        status_counts['expired'] += 1
                else:
                    status = 'active'
                    status_counts['active'] += 1
                
                detailed_modules.append({
                    'code': module['code'],
                    'name': module['name'],
                    'category': module['category'],
                    'is_active': is_active,
                    'status': status,
                    'trial_ends_at': trial_ends_at,
                    'monthly_price': module.get('monthly_price', 0),
                    'can_use': module_info['can_use']
                })
            
            return jsonify({
                'success': True,
                'institution': {
                    'id': institution.id,
                    'name': institution.name,
                    'code': institution.code
                },
                'modules': detailed_modules,
                'status_counts': status_counts,
                'total_modules': len(modules)
            })
        else:
            return jsonify({
                'success': False,
                'error': modules_status.get('error', 'Error desconocido')
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
