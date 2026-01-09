// Modern Admin Panel JavaScript
(function() {
    'use strict';

    // DOM Ready
    document.addEventListener('DOMContentLoaded', function() {
        console.log('Admin Panel loaded');
        initDropdowns();
        initAlerts();
        initSearch();
        initAnimations();
        initCharts();
    });

    // Dropdown Navigation
    function initDropdowns() {
        const dropdownToggles = document.querySelectorAll('.dropdown-toggle');

        dropdownToggles.forEach(function(toggle) {
            toggle.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();

                const navItem = this.closest('.nav-item');
                const isActive = navItem.classList.contains('active');

                // Close all other dropdowns
                document.querySelectorAll('.nav-item.has-dropdown').forEach(function(item) {
                    if (item !== navItem) {
                        item.classList.remove('active');
                    }
                });

                // Toggle current dropdown
                navItem.classList.toggle('active', !isActive);
            });
        });

        // Close dropdowns when clicking outside
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.nav-item')) {
                document.querySelectorAll('.nav-item.has-dropdown.active').forEach(function(item) {
                    item.classList.remove('active');
                });
            }
        });

        // Prevent dropdown menu clicks from closing
        document.querySelectorAll('.dropdown-menu').forEach(function(menu) {
            menu.addEventListener('click', function(e) {
                e.stopPropagation();
            });
        });
    }

    // Alert Auto-dismiss
    function initAlerts() {
        const alerts = document.querySelectorAll('.alert');

        alerts.forEach(function(alert) {
            // Auto-dismiss after 5 seconds
            setTimeout(function() {
                alert.style.transition = 'all 0.3s ease';
                alert.style.opacity = '0';
                alert.style.transform = 'translateY(-10px)';

                setTimeout(function() {
                    alert.remove();
                }, 300);
            }, 5000);
        });
    }

    // Global Search
    function initSearch() {
        const searchInput = document.getElementById('globalSearch');
        const tableSearchInput = document.getElementById('searchInput');

        if (searchInput) {
            searchInput.addEventListener('keyup', function(e) {
                if (e.key === 'Enter') {
                    const query = this.value.trim();
                    if (query) {
                        // Search functionality - can be extended
                        console.log('Searching for:', query);
                    }
                }
            });
        }

        // Table search
        if (tableSearchInput) {
            tableSearchInput.addEventListener('keyup', function() {
                const value = this.value.toLowerCase();
                const rows = document.querySelectorAll('#dataTable tbody tr');

                rows.forEach(function(row) {
                    const text = row.textContent.toLowerCase();
                    row.style.display = text.includes(value) ? '' : 'none';
                });
            });
        }
    }

    // Animations
    function initAnimations() {
        // Animate stat cards
        const statCards = document.querySelectorAll('.stat-card');

        statCards.forEach(function(card, index) {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';

            setTimeout(function() {
                card.style.transition = 'all 0.5s cubic-bezier(0.4, 0, 0.2, 1)';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, 100 + (index * 100));
        });

        // Animate stat values (counter animation)
        const statValues = document.querySelectorAll('.stat-value');

        statValues.forEach(function(el) {
            const text = el.textContent;
            const numMatch = text.match(/[\d,]+/);

            if (numMatch) {
                const target = parseInt(numMatch[0].replace(/,/g, ''));
                const prefix = text.substring(0, text.indexOf(numMatch[0]));
                const suffix = text.substring(text.indexOf(numMatch[0]) + numMatch[0].length);

                if (target > 0) {
                    animateCounter(el, 0, target, 1500, prefix, suffix);
                }
            }
        });

        // Table row animations
        const tableRows = document.querySelectorAll('tbody tr');

        tableRows.forEach(function(row, index) {
            row.style.opacity = '0';
            row.style.transform = 'translateX(-10px)';

            setTimeout(function() {
                row.style.transition = 'all 0.3s ease';
                row.style.opacity = '1';
                row.style.transform = 'translateX(0)';
            }, 200 + (index * 50));
        });
    }

    // Counter Animation
    function animateCounter(element, start, end, duration, prefix, suffix) {
        prefix = prefix || '';
        suffix = suffix || '';

        let startTime = null;

        function step(timestamp) {
            if (!startTime) startTime = timestamp;

            const progress = Math.min((timestamp - startTime) / duration, 1);
            const easeProgress = 1 - Math.pow(1 - progress, 3); // Ease out cubic
            const current = Math.floor(easeProgress * (end - start) + start);

            element.textContent = prefix + current.toLocaleString() + suffix;

            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        }

        window.requestAnimationFrame(step);
    }

    // Charts (if Chart.js is available)
    function initCharts() {
        if (typeof Chart === 'undefined') return;

        // Sales Chart
        const salesCanvas = document.getElementById('salesChart');
        if (salesCanvas) {
            const ctx = salesCanvas.getContext('2d');

            const gradient = ctx.createLinearGradient(0, 0, 0, 300);
            gradient.addColorStop(0, 'rgba(99, 102, 241, 0.3)');
            gradient.addColorStop(1, 'rgba(99, 102, 241, 0.02)');

            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                    datasets: [{
                        label: 'Revenue',
                        data: [12000, 19000, 15000, 25000, 22000, 30000],
                        borderColor: '#6366f1',
                        backgroundColor: gradient,
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4,
                        pointBackgroundColor: '#6366f1',
                        pointBorderColor: '#ffffff',
                        pointBorderWidth: 3,
                        pointRadius: 5,
                        pointHoverRadius: 7
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        x: {
                            grid: { display: false },
                            ticks: { color: '#64748b' }
                        },
                        y: {
                            grid: { color: 'rgba(100, 116, 139, 0.1)' },
                            ticks: {
                                color: '#64748b',
                                callback: function(value) {
                                    return 'Rs ' + value.toLocaleString();
                                }
                            }
                        }
                    },
                    interaction: {
                        intersect: false,
                        mode: 'index'
                    }
                }
            });
        }

        // Orders Chart
        const ordersCanvas = document.getElementById('ordersChart');
        if (ordersCanvas) {
            new Chart(ordersCanvas, {
                type: 'doughnut',
                data: {
                    labels: ['Pending', 'Processing', 'Shipped', 'Delivered'],
                    datasets: [{
                        data: [30, 20, 25, 25],
                        backgroundColor: [
                            'rgba(245, 158, 11, 0.85)',
                            'rgba(99, 102, 241, 0.85)',
                            'rgba(139, 92, 246, 0.85)',
                            'rgba(16, 185, 129, 0.85)'
                        ],
                        borderColor: '#ffffff',
                        borderWidth: 3
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '65%',
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                padding: 16,
                                color: '#64748b',
                                font: { size: 13, weight: '500' }
                            }
                        }
                    }
                }
            });
        }
    }

    // Utility: Show Notification
    window.showNotification = function(message, type) {
        type = type || 'success';

        const icons = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };

        const notification = document.createElement('div');
        notification.className = 'alert ' + type;
        notification.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999; min-width: 300px; max-width: 450px;';
        notification.innerHTML = '<i class="fas ' + icons[type] + '"></i><span>' + message + '</span><button class="alert-close" onclick="this.parentElement.remove()"><i class="fas fa-times"></i></button>';

        document.body.appendChild(notification);

        setTimeout(function() {
            notification.style.opacity = '0';
            notification.style.transform = 'translateY(-10px)';
            setTimeout(function() {
                notification.remove();
            }, 300);
        }, 4000);
    };

    // Utility: Format Currency
    window.formatCurrency = function(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    };

    // Utility: Format Number
    window.formatNumber = function(num) {
        return new Intl.NumberFormat('en-US').format(num);
    };

    // Delete Confirmation
    document.addEventListener('click', function(e) {
        if (e.target.matches('.delete-btn, .delete-btn *')) {
            e.preventDefault();

            const btn = e.target.closest('.delete-btn');
            const deleteUrl = btn.getAttribute('href');
            const itemName = btn.dataset.itemName || 'this item';

            if (confirm('Are you sure you want to delete ' + itemName + '? This action cannot be undone.')) {
                window.location.href = deleteUrl;
            }
        }
    });

})();
