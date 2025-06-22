// JavaScript principal para EduControl

document.addEventListener('DOMContentLoaded', function() {
    
    // ===== FUNCIONALIDAD DEL SIDEBAR =====
    initializeSidebar();
    
    // ===== BOOTSTRAP COMPONENTS =====
    // Inicializar tooltips de Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Inicializar popovers de Bootstrap
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-dismiss alerts después de 5 segundos
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Confirmar acciones destructivas
    var confirmButtons = document.querySelectorAll('[data-confirm]');
    confirmButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            var message = this.getAttribute('data-confirm') || '¿Estás seguro?';
            if (!confirm(message)) {
                e.preventDefault();
                return false;
            }
        });
    });

    // Validación de formularios en tiempo real
    var forms = document.querySelectorAll('.needs-validation');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Auto-resize textareas
    var textareas = document.querySelectorAll('textarea[data-auto-resize]');
    textareas.forEach(function(textarea) {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
    });

    // Toggle password visibility
    var passwordToggles = document.querySelectorAll('.password-toggle');
    passwordToggles.forEach(function(toggle) {
        toggle.addEventListener('click', function() {
            var input = document.querySelector(this.getAttribute('data-target'));
            var icon = this.querySelector('i');
            
            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.remove('bi-eye');
                icon.classList.add('bi-eye-slash');
            } else {
                input.type = 'password';
                icon.classList.remove('bi-eye-slash');
                icon.classList.add('bi-eye');
            }
        });
    });

    // Búsqueda en tiempo real
    var searchInputs = document.querySelectorAll('[data-search-target]');
    searchInputs.forEach(function(input) {
        input.addEventListener('input', function() {
            var target = document.querySelector(this.getAttribute('data-search-target'));
            var searchTerm = this.value.toLowerCase();
            var items = target.querySelectorAll('[data-searchable]');
            
            items.forEach(function(item) {
                var text = item.textContent.toLowerCase();
                if (text.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    });

    // Loading states para botones
    var loadingButtons = document.querySelectorAll('[data-loading-text]');
    loadingButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            var originalText = this.innerHTML;
            var loadingText = this.getAttribute('data-loading-text');
            
            this.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>' + loadingText;
            this.disabled = true;
            
            // Restaurar después de 3 segundos si no se envía el formulario
            setTimeout(function() {
                button.innerHTML = originalText;
                button.disabled = false;
            }, 3000);
        });
    });

    // Números con formato
    var numberInputs = document.querySelectorAll('input[data-format="number"]');
    numberInputs.forEach(function(input) {
        input.addEventListener('blur', function() {
            var value = parseFloat(this.value);
            if (!isNaN(value)) {
                this.value = value.toLocaleString('es-CO');
            }
        });
        
        input.addEventListener('focus', function() {
            this.value = this.value.replace(/[^\d.-]/g, '');
        });
    });

    // Copiar al portapapeles
    var copyButtons = document.querySelectorAll('[data-clipboard-target]');
    copyButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            var target = document.querySelector(this.getAttribute('data-clipboard-target'));
            
            if (target) {
                navigator.clipboard.writeText(target.textContent).then(function() {
                    showToast('Copiado al portapapeles', 'success');
                });
            }
        });
    });

    // Exponer funciones globalmente
    window.EduControl = {
        showToast: showToast,
        confirmDelete: window.confirmDelete,
        showLoading: window.showLoading,
        hideLoading: window.hideLoading,
        sidebar: {
            collapse: collapseSidebar,
            expand: expandSidebar,
            toggle: toggleSidebar
        }
    };
});

// ===== FUNCIONES DEL SIDEBAR =====
function initializeSidebar() {
    const sidebar = document.querySelector('#sidebar');
    const sidebarToggle = document.querySelector('#sidebar-toggle');
    const collapseBtn = document.querySelector('.sidebar-collapse-btn');
    const mainContent = document.querySelector('.main-content');
    
    if (!sidebar) return; // No hay sidebar en esta página
    
    // Estado del sidebar
    let isCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
    
    // Aplicar estado inicial
    if (isCollapsed) {
        collapseSidebar();
    }
    
    // Toggle desde el navbar (hamburger)
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function(e) {
            e.preventDefault();
            toggleSidebar();
        });
    }
    
    // Toggle desde el botón del sidebar
    if (collapseBtn) {
        collapseBtn.addEventListener('click', function(e) {
            e.preventDefault();
            toggleSidebar();
        });
    }
    
    // Auto-expandir en pantallas grandes cuando se hace hover
    if (window.innerWidth > 768) {
        sidebar.addEventListener('mouseenter', function() {
            if (isCollapsed) {
                sidebar.classList.add('hover-expanded');
            }
        });
        
        sidebar.addEventListener('mouseleave', function() {
            if (isCollapsed) {
                sidebar.classList.remove('hover-expanded');
            }
        });
    }
    
    // Responsive: auto-colapsar en móvil
    function handleResize() {
        if (window.innerWidth <= 768) {
            collapseSidebar();
        }
    }
    
    window.addEventListener('resize', handleResize);
    
    // Cerrar sidebar en móvil al hacer click fuera
    document.addEventListener('click', function(e) {
        if (window.innerWidth <= 768) {
            if (!sidebar.contains(e.target) && !sidebarToggle?.contains(e.target)) {
                if (!sidebar.classList.contains('collapsed')) {
                    collapseSidebar();
                }
            }
        }
    });
    
    // Función para alternar
    function toggleSidebar() {
        if (sidebar.classList.contains('collapsed')) {
            expandSidebar();
        } else {
            collapseSidebar();
        }
    }
    
    // Función para colapsar
    function collapseSidebar() {
        sidebar.classList.add('collapsed');
        if (mainContent) {
            mainContent.classList.add('sidebar-collapsed');
        }
        
        // Cambiar icono del botón
        if (collapseBtn) {
            const icon = collapseBtn.querySelector('i');
            if (icon) {
                icon.className = 'fas fa-chevron-right';
            }
        }
        
        // Guardar estado
        localStorage.setItem('sidebarCollapsed', 'true');
        isCollapsed = true;
    }
    
    // Función para expandir
    function expandSidebar() {
        sidebar.classList.remove('collapsed');
        if (mainContent) {
            mainContent.classList.remove('sidebar-collapsed');
        }
        
        // Cambiar icono del botón
        if (collapseBtn) {
            const icon = collapseBtn.querySelector('i');
            if (icon) {
                icon.className = 'fas fa-chevron-left';
            }
        }
        
        // Guardar estado
        localStorage.setItem('sidebarCollapsed', 'false');
        isCollapsed = false;
    }
    
    // Exponer funciones globalmente
    window.collapseSidebar = collapseSidebar;
    window.expandSidebar = expandSidebar;
    window.toggleSidebar = toggleSidebar;
}

// ===== FUNCIONES DE UTILIDAD =====

// Función para mostrar toasts
function showToast(message, type = 'info', duration = 3000) {
    var toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }

    var toastId = 'toast-' + Date.now();
    var toastHtml = `
        <div id="${toastId}" class="toast align-items-center text-white bg-${type} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;

    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    var toastElement = document.getElementById(toastId);
    var toast = new bootstrap.Toast(toastElement, { delay: duration });
    toast.show();

    // Limpiar el toast después de que se oculte
    toastElement.addEventListener('hidden.bs.toast', function() {
        this.remove();
    });
}

// Función para confirmar eliminación
window.confirmDelete = function(message = '¿Estás seguro de que deseas eliminar este elemento?') {
    return confirm(message);
};

// Función para mostrar loading
window.showLoading = function(element, text = 'Cargando...') {
    element.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>' + text;
    element.disabled = true;
};

// Función para ocultar loading
window.hideLoading = function(element, originalText) {
    element.innerHTML = originalText;
    element.disabled = false;
};

// ===== FUNCIONES AUXILIARES =====

// Función para formatear números como moneda colombiana
function formatCurrency(amount) {
    return new Intl.NumberFormat('es-CO', {
        style: 'currency',
        currency: 'COP',
        minimumFractionDigits: 0
    }).format(amount);
}

// Función para formatear fechas
function formatDate(date, options = {}) {
    const defaultOptions = {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    };
    
    return new Date(date).toLocaleDateString('es-CO', { ...defaultOptions, ...options });
}

// Función para validar email
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Función para generar colores aleatorios
function getRandomColor() {
    const colors = ['primary', 'secondary', 'success', 'danger', 'warning', 'info'];
    return colors[Math.floor(Math.random() * colors.length)];
}

// ===== FUNCIONES ESPECÍFICAS PARA DASHBOARD =====

// Funciones para los botones de acciones rápidas
function showNotification(message, type) {
    showToast(message, type);
}

function checkSystemStatus() {
    showToast('Sistema operativo: CPU 12%, RAM 45%, Disco 68%', 'success');
    
    // Simular actualización de estado
    setTimeout(() => {
        showToast('Última verificación: Todo funcionando correctamente', 'info');
    }, 1500);
}

// Agregar efectos hover a las estadísticas
document.addEventListener('DOMContentLoaded', function() {
    const statsCards = document.querySelectorAll('.stats-card');
    
    statsCards.forEach(card => {
        card.addEventListener('click', function() {
            const label = this.querySelector('.stats-label').textContent;
            showToast('Mostrando detalles de: ' + label, 'info');
        });
    });
});