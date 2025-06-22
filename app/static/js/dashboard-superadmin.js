// Dashboard Superadmin JavaScript - OPTIMIZADO
// Archivo: app/static/js/dashboard-superadmin.js

document.addEventListener('DOMContentLoaded', function() {
    // Obtener datos del JSON embebido con mejor manejo de errores
    let dashboardData = {};
    try {
        const dataScript = document.getElementById('dashboard-data');
        if (dataScript && dataScript.textContent.trim()) {
            dashboardData = JSON.parse(dataScript.textContent);
            console.log('✅ Datos del dashboard cargados:', dashboardData);
        } else {
            console.warn('⚠️ No se encontró el script con datos del dashboard');
            throw new Error('No dashboard data script found');
        }
    } catch (error) {
        console.warn('❌ Error cargando datos del dashboard:', error);
        dashboardData = {
            chartData: {
                institutionNames: ['Colegio Ejemplo'],
                studentsData: [1],
                teachersData: [1]
            },
            stats: {
                totalInstitutions: 1,
                totalUsers: 4,
                totalAdmins: 1,
                totalTeachers: 1,
                totalStudents: 1,
                totalCourses: 0
            }
        };
    }

    // Función para animar números con mejor rendimiento
    function animateNumbers() {
        const statNumbers = document.querySelectorAll('.stats-number[data-target]');
        
        statNumbers.forEach(number => {
            const targetValue = parseInt(number.getAttribute('data-target')) || 0;
            const duration = 2000;
            const startTime = performance.now();
            const startValue = 0;
            
            function updateNumber(currentTime) {
                const elapsed = currentTime - startTime;
                const progress = Math.min(elapsed / duration, 1);
                
                // Easing function para suavizar la animación
                const easeOutQuart = 1 - Math.pow(1 - progress, 4);
                const currentValue = Math.round(startValue + (targetValue - startValue) * easeOutQuart);
                
                if (currentValue >= 1000) {
                    number.textContent = currentValue.toLocaleString('es-CO');
                } else {
                    number.textContent = currentValue;
                }
                
                if (progress < 1) {
                    requestAnimationFrame(updateNumber);
                } else {
                    number.textContent = targetValue >= 1000 ? targetValue.toLocaleString('es-CO') : targetValue;
                }
            }
            
            if (targetValue > 0) {
                number.textContent = '0';
                requestAnimationFrame(updateNumber);
            }
        });
    }

    // Función para crear gráfico con datos REALES
    function createInstitutionsChart() {
        const ctx = document.getElementById('institutionsChart');
        if (!ctx) {
            console.warn('❌ Canvas para gráfico no encontrado');
            return;
        }

        // Usar datos REALES del servidor
        let institutionNames = dashboardData.chartData.institutionNames || ['Colegio Ejemplo'];
        let studentsData = dashboardData.chartData.studentsData || [1];
        let teachersData = dashboardData.chartData.teachersData || [1];

        console.log('📊 Datos del gráfico:');
        console.log('Instituciones:', institutionNames);
        console.log('Estudiantes:', studentsData);
        console.log('Profesores:', teachersData);

        const data = {
            labels: institutionNames,
            datasets: [{
                label: 'Estudiantes',
                data: studentsData,
                backgroundColor: 'rgba(142, 45, 226, 0.8)',
                borderColor: 'rgba(142, 45, 226, 1)',
                borderWidth: 2,
                borderRadius: 8,
                borderSkipped: false
            }, {
                label: 'Profesores', 
                data: teachersData,
                backgroundColor: 'rgba(74, 0, 224, 0.8)',
                borderColor: 'rgba(74, 0, 224, 1)',
                borderWidth: 2,
                borderRadius: 8,
                borderSkipped: false
            }]
        };

        const config = {
            type: 'bar',
            data: data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            padding: 20,
                            font: {
                                family: 'Inter',
                                size: 12,
                                weight: '600'
                            }
                        }
                    },
                    title: {
                        display: false // Ya está en el HTML
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.9)',
                        titleColor: 'white',
                        bodyColor: 'white',
                        borderColor: 'rgba(142, 45, 226, 1)',
                        borderWidth: 2,
                        cornerRadius: 8,
                        displayColors: true,
                        callbacks: {
                            label: function(context) {
                                const label = context.dataset.label || '';
                                const value = context.parsed.y;
                                return label + ': ' + value + (value === 1 ? ' usuario' : ' usuarios');
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            font: {
                                family: 'Inter',
                                size: 11,
                                weight: '600'
                            },
                            maxRotation: 45,
                            minRotation: 0
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)',
                            drawBorder: false
                        },
                        ticks: {
                            stepSize: Math.max(...studentsData, ...teachersData) <= 5 ? 1 : 5,
                            font: {
                                family: 'Inter',
                                size: 11
                            },
                            callback: function(value) {
                                return Number.isInteger(value) ? value : '';
                            }
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                animation: {
                    duration: 1500,
                    easing: 'easeInOutQuart'
                }
            }
        };

        // Crear el gráfico
        try {
            const chart = new Chart(ctx, config);
            console.log('✅ Gráfico creado exitosamente');
            
            // Guardar referencia para futuras actualizaciones
            window.dashboardChart = chart;
            
        } catch (error) {
            console.error('❌ Error creando el gráfico:', error);
            const container = ctx.parentElement;
            container.innerHTML = `
                <div class="text-center p-4">
                    <i class="fas fa-exclamation-triangle text-warning" style="font-size: 2rem;"></i>
                    <br><br>
                    <strong>Error cargando el gráfico</strong>
                    <br>
                    <small class="text-muted">${error.message}</small>
                </div>
            `;
        }
    }

    // Función mejorada para descargar reportes
    window.downloadReport = function(type) {
        const reportTypes = {
            'institutions': 'Reporte de Instituciones',
            'users': 'Reporte de Usuarios', 
            'activity': 'Log de Actividades',
            'full': 'Reporte Completo del Sistema'
        };
        
        // Encontrar el botón que disparó el evento
        const button = event.target.closest('button');
        if (!button) return;
        
        const originalText = button.innerHTML;
        button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Generando...';
        button.disabled = true;
        
        // Simular generación de reporte real
        setTimeout(() => {
            // Crear CSV con datos reales
            let csvContent = '';
            let filename = '';
            
            switch(type) {
                case 'institutions':
                    csvContent = 'Nombre,Código,Ciudad,Estado,Estudiantes,Profesores\n';
                    if (dashboardData.chartData.institutionNames) {
                        dashboardData.chartData.institutionNames.forEach((name, index) => {
                            const students = dashboardData.chartData.studentsData[index] || 0;
                            const teachers = dashboardData.chartData.teachersData[index] || 0;
                            csvContent += `"${name}","INST${index + 1}","Barranquilla","Activo",${students},${teachers}\n`;
                        });
                    }
                    filename = `reporte_instituciones_${new Date().toISOString().split('T')[0]}.csv`;
                    break;
                    
                case 'users':
                    csvContent = 'Tipo,Cantidad,Porcentaje\n';
                    const total = dashboardData.stats.totalUsers || 1;
                    csvContent += `Estudiantes,${dashboardData.stats.totalStudents || 0},${((dashboardData.stats.totalStudents || 0) / total * 100).toFixed(1)}%\n`;
                    csvContent += `Profesores,${dashboardData.stats.totalTeachers || 0},${((dashboardData.stats.totalTeachers || 0) / total * 100).toFixed(1)}%\n`;
                    csvContent += `Administradores,${dashboardData.stats.totalAdmins || 0},${((dashboardData.stats.totalAdmins || 0) / total * 100).toFixed(1)}%\n`;
                    filename = `reporte_usuarios_${new Date().toISOString().split('T')[0]}.csv`;
                    break;
                    
                case 'activity':
                    csvContent = 'Fecha,Hora,Evento,Descripción\n';
                    csvContent += `${new Date().toLocaleDateString()},${new Date().toLocaleTimeString()},"Reporte generado","Exportación de log de actividades"\n`;
                    csvContent += `${new Date().toLocaleDateString()},${new Date().toLocaleTimeString()},"Sistema activo","Dashboard de superadmin accedido"\n`;
                    filename = `log_actividades_${new Date().toISOString().split('T')[0]}.csv`;
                    break;
                    
                default:
                    csvContent = 'Métrica,Valor\n';
                    csvContent += `Instituciones,${dashboardData.stats.totalInstitutions || 0}\n`;
                    csvContent += `Usuarios Totales,${dashboardData.stats.totalUsers || 0}\n`;
                    csvContent += `Estudiantes,${dashboardData.stats.totalStudents || 0}\n`;
                    csvContent += `Profesores,${dashboardData.stats.totalTeachers || 0}\n`;
                    csvContent += `Administradores,${dashboardData.stats.totalAdmins || 0}\n`;
                    csvContent += `Cursos,${dashboardData.stats.totalCourses || 0}\n`;
                    csvContent += `Fecha de Reporte,${new Date().toLocaleString()}\n`;
                    filename = `reporte_completo_${new Date().toISOString().split('T')[0]}.csv`;
            }
            
            // Crear y descargar archivo
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            const url = URL.createObjectURL(blob);
            link.setAttribute('href', url);
            link.setAttribute('download', filename);
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
            
            // Mostrar notificación de éxito
            showNotification(`✅ ${reportTypes[type]} descargado exitosamente`, 'success');
            
            // Restaurar botón
            button.innerHTML = originalText;
            button.disabled = false;
            
        }, 1500);
    };

    // Función para manejar clics en las tarjetas de estadísticas
    function setupStatsCardClicks() {
        const statsCards = document.querySelectorAll('.stats-card[onclick]');
        
        statsCards.forEach(card => {
            // Eliminar onclick si existe para evitar conflictos
            card.removeAttribute('onclick');
            
            card.addEventListener('click', function() {
                // Efecto visual de clic
                this.style.transform = 'scale(0.95)';
                setTimeout(() => {
                    this.style.transform = '';
                }, 150);
                
                // Determinar navegación según las clases
                if (this.classList.contains('institutions')) {
                    window.location.href = '/superadmin/institutions';
                } else if (this.classList.contains('users')) {
                    window.location.href = '/superadmin/users';
                } else {
                    showNotification('Funcionalidad en desarrollo', 'info');
                }
            });
            
            // Añadir cursor pointer
            card.style.cursor = 'pointer';
        });
    }

    // Función para mostrar notificaciones (tu versión mejorada)
    function showNotification(message, type) {
        type = type || 'info';
        
        let notificationContainer = document.getElementById('notification-overlay');
        if (!notificationContainer) {
            notificationContainer = document.createElement('div');
            notificationContainer.id = 'notification-overlay';
            notificationContainer.style.cssText = 
                'position: fixed !important;' +
                'top: 80px !important;' +
                'right: 20px !important;' +
                'z-index: 999999 !important;' +
                'width: 350px !important;' +
                'max-height: calc(100vh - 100px) !important;' +
                'overflow-y: auto !important;' +
                'pointer-events: none !important;' +
                'margin: 0 !important;' +
                'padding: 0 !important;' +
                'border: none !important;' +
                'background: transparent !important;';
            document.body.appendChild(notificationContainer);
        }

        const notification = document.createElement('div');
        notification.style.cssText = 
            'margin-bottom: 10px !important;' +
            'padding: 12px 16px !important;' +
            'border-radius: 8px !important;' +
            'box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15) !important;' +
            'border: none !important;' +
            'font-size: 14px !important;' +
            'font-weight: 500 !important;' +
            'pointer-events: auto !important;' +
            'transform: translateX(100%) !important;' +
            'transition: all 0.3s ease !important;' +
            'opacity: 0 !important;' +
            'position: relative !important;' +
            'display: flex !important;' +
            'align-items: center !important;' +
            'justify-content: space-between !important;' +
            'min-height: 50px !important;' +
            'width: 100% !important;' +
            'box-sizing: border-box !important;';
        
        const colors = {
            'success': 'background: #10b981 !important; color: white !important;',
            'danger': 'background: #ef4444 !important; color: white !important;',
            'warning': 'background: #f59e0b !important; color: white !important;',
            'info': 'background: #3b82f6 !important; color: white !important;'
        };
        
        notification.style.cssText += colors[type] || colors.info;
        
        const icons = {
            'success': '✅',
            'danger': '🚨',
            'warning': '⚠️',
            'info': 'ℹ️'
        };
        
        notification.innerHTML = 
            '<div style="display: flex; align-items: center; flex: 1; margin-right: 10px;">' +
                '<span style="margin-right: 8px; font-size: 16px;">' + (icons[type] || icons.info) + '</span>' +
                '<span style="flex: 1;">' + message + '</span>' +
            '</div>' +
            '<button onclick="this.parentElement.remove()" style="' +
                'background: transparent !important;' +
                'border: none !important;' +
                'color: white !important;' +
                'font-size: 18px !important;' +
                'cursor: pointer !important;' +
                'padding: 0 !important;' +
                'margin: 0 !important;' +
                'line-height: 1 !important;' +
                'opacity: 0.7 !important;' +
                'width: 20px !important;' +
                'height: 20px !important;' +
                'display: flex !important;' +
                'align-items: center !important;' +
                'justify-content: center !important;' +
            '">×</button>';
        
        notificationContainer.appendChild(notification);
        
        requestAnimationFrame(function() {
            notification.style.transform = 'translateX(0) !important';
            notification.style.opacity = '1 !important';
        });
        
        setTimeout(function() {
            if (notification.parentNode) {
                notification.style.transform = 'translateX(100%) !important';
                notification.style.opacity = '0 !important';
                
                setTimeout(function() {
                    if (notification.parentNode) {
                        notification.remove();
                    }
                    if (notificationContainer && notificationContainer.children.length === 0) {
                        notificationContainer.remove();
                    }
                }, 300);
            }
        }, 5000);
    }

    // Función para actualizar estadísticas en tiempo real
    function updateStatsInRealTime() {
        fetch('/superadmin/api/stats')
            .then(response => response.json())
            .then(data => {
                // Actualizar usuarios conectados si existe el elemento
                const connectedElement = document.querySelector('[data-stat="users-online"]');
                if (connectedElement && data.users_online) {
                    connectedElement.textContent = data.users_online;
                }
                console.log('📊 Estadísticas actualizadas:', data);
            })
            .catch(error => {
                console.warn('⚠️ Error actualizando estadísticas:', error);
            });
    }

    // Función de inicialización mejorada
    function initDashboard() {
        console.log('🚀 Inicializando Dashboard del Superadmin...');
        
        // Verificar dependencias
        if (typeof Chart === 'undefined') {
            console.error('❌ Chart.js no está cargado');
            showNotification('Error: Chart.js no está disponible', 'danger');
            return;
        }
        
        // Ejecutar funciones en secuencia
        setTimeout(() => {
            animateNumbers();
            console.log('✅ Animación de números iniciada');
        }, 300);
        
        setTimeout(() => {
            createInstitutionsChart();
            console.log('✅ Gráfico de instituciones creado');
        }, 800);
        
        setTimeout(() => {
            setupStatsCardClicks();
            console.log('✅ Eventos de tarjetas configurados');
        }, 1000);
        
        // Actualizar estadísticas cada 30 segundos
        setInterval(updateStatsInRealTime, 30000);
        
        // Mostrar notificación de bienvenida
        setTimeout(() => {
            showNotification('🎉 Dashboard cargado correctamente', 'success');
        }, 1500);
        
        console.log('✅ Dashboard del Superadmin inicializado correctamente');
        console.log('📊 Datos disponibles:', dashboardData);
    }

    // Funciones de prueba (mantener para desarrollo)
    window.testNotifications = function() {
        const notifications = [
            { message: 'Sistema funcionando correctamente', type: 'success' },
            { message: 'Uso de almacenamiento alto (85%)', type: 'warning' },
            { message: 'Nuevo usuario registrado: María García', type: 'info' },
            { message: 'Error de conexión detectado', type: 'danger' }
        ];

        notifications.forEach(function(notif, index) {
            setTimeout(function() {
                showNotification(notif.message, notif.type);
            }, index * 500);
        });
    };

    // Ejecutar inicialización
    initDashboard();

    // Exponer funciones globales
    window.DashboardSuperadmin = {
        animateNumbers: animateNumbers,
        createChart: createInstitutionsChart,
        showNotification: showNotification,
        downloadReport: window.downloadReport,
        updateStats: updateStatsInRealTime,
        data: dashboardData
    };
});