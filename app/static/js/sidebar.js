// Funcionalidad del sidebar mejorada
document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebarToggleMobile = document.getElementById('sidebarToggleMobile');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    const mainWrapper = document.querySelector('.main-wrapper');

    // Toggle sidebar en desktop
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
            
            // Sincronizar el main-wrapper
            if (mainWrapper) {
                mainWrapper.classList.toggle('sidebar-collapsed');
            }
            
            // Cambiar icono del botón
            const icon = this.querySelector('i');
            if (icon) {
                if (sidebar.classList.contains('collapsed')) {
                    icon.className = 'fas fa-chevron-right';
                    this.title = 'Expandir menú';
                } else {
                    icon.className = 'fas fa-bars';
                    this.title = 'Colapsar menú';
                }
            }
            
            // Guardar estado en localStorage
            const isCollapsed = sidebar.classList.contains('collapsed');
            localStorage.setItem('sidebarCollapsed', isCollapsed);
        });
    }

    // Toggle sidebar en móvil
    if (sidebarToggleMobile) {
        sidebarToggleMobile.addEventListener('click', function() {
            sidebar.classList.toggle('show');
            sidebarOverlay.classList.toggle('show');
            document.body.style.overflow = sidebar.classList.contains('show') ? 'hidden' : '';
        });
    }

    // Cerrar sidebar al hacer click en overlay
    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', function() {
            sidebar.classList.remove('show');
            sidebarOverlay.classList.remove('show');
            document.body.style.overflow = '';
        });
    }

    // Cerrar sidebar en móvil al cambiar tamaño de ventana
    window.addEventListener('resize', function() {
        if (window.innerWidth > 991.98) {
            sidebar.classList.remove('show');
            sidebarOverlay.classList.remove('show');
            document.body.style.overflow = '';
        }
    });

    // Hover para expandir temporalmente cuando está colapsado (solo desktop)
    if (window.innerWidth > 991.98) {
        sidebar.addEventListener('mouseenter', function() {
            if (this.classList.contains('collapsed')) {
                this.classList.add('hover-expanded');
            }
        });
        
        sidebar.addEventListener('mouseleave', function() {
            if (this.classList.contains('collapsed')) {
                this.classList.remove('hover-expanded');
            }
        });
    }

    // Restaurar estado del sidebar desde localStorage
    const savedState = localStorage.getItem('sidebarCollapsed');
    if (savedState === 'true' && window.innerWidth > 991.98) {
        sidebar.classList.add('collapsed');
        if (mainWrapper) {
            mainWrapper.classList.add('sidebar-collapsed');
        }
        
        // Actualizar icono del botón
        if (sidebarToggle) {
            const icon = sidebarToggle.querySelector('i');
            if (icon) {
                icon.className = 'fas fa-chevron-right';
                sidebarToggle.title = 'Expandir menú';
            }
        }
    }

    // Auto-cerrar alerts después de 5 segundos
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            if (alert && typeof bootstrap !== 'undefined' && bootstrap.Alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000);
    });

    // Smooth scroll para enlaces internos
    document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Tooltips para elementos con data-bs-toggle="tooltip"
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // Confirmación para acciones destructivas
    const dangerButtons = document.querySelectorAll('.btn-danger[data-confirm]');
    dangerButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            const message = this.getAttribute('data-confirm') || '¿Estás seguro de que quieres continuar?';
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });

    // Efecto de loading en botones de formulario
    const submitButtons = document.querySelectorAll('button[type="submit"]');
    submitButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            const form = this.closest('form');
            if (form && form.checkValidity()) {
                const originalText = this.innerHTML;
                this.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Procesando...';
                this.disabled = true;
                
                // Restaurar después de 30 segundos como fallback
                setTimeout(function() {
                    button.innerHTML = originalText;
                    button.disabled = false;
                }, 30000);
            }
        });
    });

    // Actualizar enlaces activos según la URL actual
    updateActiveNavLinks();

    // Funciones adicionales para controlar el sidebar programáticamente
    window.sidebarControls = {
        toggle: function() {
            if (sidebarToggle) {
                sidebarToggle.click();
            }
        },
        collapse: function() {
            if (!sidebar.classList.contains('collapsed')) {
                sidebarToggle.click();
            }
        },
        expand: function() {
            if (sidebar.classList.contains('collapsed')) {
                sidebarToggle.click();
            }
        },
        isCollapsed: function() {
            return sidebar.classList.contains('collapsed');
        }
    };
});

// Función para actualizar enlaces activos
function updateActiveNavLinks() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(function(link) {
        const href = link.getAttribute('href');
        if (href && (currentPath === href || (href !== '/' && currentPath.startsWith(href)))) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}

// Función para mostrar notificaciones toast
function showToast(message, type) {
    type = type || 'info';
    const toastContainer = document.getElementById('toast-container') || createToastContainer();
    
    const toastId = 'toast-' + Date.now();
    const toastHtml = `
        <div class="toast align-items-center text-white bg-${type} border-0" role="alert" id="${toastId}">
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas fa-${getToastIcon(type)} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    const toastElement = document.getElementById(toastId);
    if (typeof bootstrap !== 'undefined' && bootstrap.Toast) {
        const toast = new bootstrap.Toast(toastElement);
        toast.show();
        
        // Remover elemento después de que se oculte
        toastElement.addEventListener('hidden.bs.toast', function() {
            this.remove();
        });
    }
}

// Crear contenedor de toasts si no existe
function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '1055';
    document.body.appendChild(container);
    return container;
}

// Obtener icono según el tipo de toast
function getToastIcon(type) {
    const icons = {
        'success': 'check-circle',
        'danger': 'exclamation-triangle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle',
        'primary': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

// Función para copiar texto al portapapeles
function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(function() {
            showToast('Texto copiado al portapapeles', 'success');
        }).catch(function() {
            showToast('Error al copiar el texto', 'danger');
        });
    } else {
        // Fallback para navegadores más antiguos
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        try {
            document.execCommand('copy');
            showToast('Texto copiado al portapapeles', 'success');
        } catch (err) {
            showToast('Error al copiar el texto', 'danger');
        }
        document.body.removeChild(textArea);
    }
}

// Función para formatear números
function formatNumber(number) {
    return new Intl.NumberFormat('es-CO').format(number);
}

// Función para formatear fechas
function formatDate(date, options) {
    options = options || {};
    const defaultOptions = {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    };
    const finalOptions = Object.assign({}, defaultOptions, options);
    return new Intl.DateTimeFormat('es-CO', finalOptions).format(new Date(date));
}

// Función para validar email
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Función para debounce (útil para búsquedas)
function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction() {
        const context = this;
        const args = arguments;
        const later = function() {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func.apply(context, args);
    };
}

// Exponer funciones globalmente si es necesario
window.EduControl = {
    showToast: showToast,
    copyToClipboard: copyToClipboard,
    formatNumber: formatNumber,
    formatDate: formatDate,
    isValidEmail: isValidEmail,
    debounce: debounce,
    updateActiveNavLinks: updateActiveNavLinks,
    sidebar: window.sidebarControls
};