// Modern Admin Panel JavaScript
$(document).ready(function () {
    // Sidebar is always visible - no toggle needed

    // Dropdown menu functionality
    $('.dropdown-toggle').on('click', function(e) {
        e.preventDefault();
        const target = $(this).data('target');
        const dropdown = $('#' + target);
        const icon = $(this).find('.fa-chevron-down');
        
        // Close other dropdowns
        $('.dropdown-menu').not(dropdown).removeClass('show');
        $('.dropdown-toggle .fa-chevron-down').not(icon).removeClass('fa-rotate-180');
        
        // Toggle current dropdown
        dropdown.toggleClass('show');
        icon.toggleClass('fa-rotate-180');
    });

    // Close dropdown when clicking outside
    $(document).on('click', function(e) {
        if (!$(e.target).closest('.dropdown-toggle').length) {
            $('.dropdown-menu').removeClass('show');
            $('.dropdown-toggle .fa-chevron-down').removeClass('fa-rotate-180');
        }
    });

    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        $('.alert').fadeOut('slow');
    }, 5000);

    // Smooth animations for cards
    $('.stat-card').each(function(index) {
        $(this).css('animation-delay', (index * 0.1) + 's');
        $(this).addClass('slide-in');
    });

    // Loading button functionality
    $('.btn').on('click', function(e) {
        const btn = $(this);
        if (btn.hasClass('loading-btn')) return;
        
        const originalText = btn.html();
        btn.addClass('loading-btn');
        btn.html('<span class="loading"></span> Loading...');
        
        // Reset after 3 seconds (you can remove this in production)
        setTimeout(() => {
            btn.removeClass('loading-btn');
            btn.html(originalText);
        }, 3000);
    });

    // Confirm deletion modals
    $('.delete-btn').on('click', function(e) {
        e.preventDefault();
        const deleteUrl = $(this).attr('href');
        const itemName = $(this).data('item-name') || 'this item';
        
        if (confirm(`Are you sure you want to delete ${itemName}? This action cannot be undone.`)) {
            window.location.href = deleteUrl;
        }
    });

    // Search functionality
    $('#searchInput').on('keyup', function() {
        const value = $(this).val().toLowerCase();
        $('#dataTable tbody tr').filter(function() {
            $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1);
        });
    });

    // Responsive sidebar for mobile
    if (window.innerWidth <= 768) {
        $('#sidebar').addClass('active');
    }

    $(window).on('resize', function() {
        if (window.innerWidth <= 768) {
            $('#sidebar').addClass('active');
        } else {
            $('#sidebar').removeClass('active');
        }
    });

    // Counter animation
    function animateCounter(element, start, end, duration) {
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            const current = Math.floor(progress * (end - start) + start);
            element.text(current.toLocaleString());
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };
        window.requestAnimationFrame(step);
    }

    // Animate counters on page load
    $('.stat-value').each(function() {
        const $this = $(this);
        const countTo = parseInt($this.text().replace(/[^0-9]/g, ''));
        if (countTo > 0) {
            $this.text('0');
            animateCounter($this, 0, countTo, 1500);
        }
    });

    // Form validation enhancement
    $('.form-control').on('blur', function() {
        const $this = $(this);
        if ($this.val().trim() === '' && $this.attr('required')) {
            $this.addClass('is-invalid');
        } else {
            $this.removeClass('is-invalid');
        }
    });

    // Status badge hover effects
    $('.badge').hover(
        function() {
            $(this).css('transform', 'scale(1.05)');
        },
        function() {
            $(this).css('transform', 'scale(1)');
        }
    );
});

// Chart.js configuration for dashboard
function initializeDashboardCharts() {
    // Sales Chart
    if (document.getElementById('salesChart')) {
        const ctx = document.getElementById('salesChart').getContext('2d');
        
        const gradient = ctx.createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, 'rgba(59, 130, 246, 0.3)');
        gradient.addColorStop(1, 'rgba(59, 130, 246, 0.05)');

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                datasets: [{
                    label: 'Sales',
                    data: [12000, 19000, 15000, 25000, 22000, 30000],
                    borderColor: 'rgb(59, 130, 246)',
                    backgroundColor: gradient,
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: 'rgb(59, 130, 246)',
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 3,
                    pointRadius: 6,
                    pointHoverRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: '#64748b'
                        }
                    },
                    y: {
                        grid: {
                            color: 'rgba(100, 116, 139, 0.1)'
                        },
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

    // Orders Chart (Doughnut)
    if (document.getElementById('ordersChart')) {
        const ctx2 = document.getElementById('ordersChart').getContext('2d');
        new Chart(ctx2, {
            type: 'doughnut',
            data: {
                labels: ['Pending', 'Processing', 'Shipped', 'Delivered'],
                datasets: [{
                    data: [30, 20, 25, 25],
                    backgroundColor: [
                        'rgba(245, 158, 11, 0.8)',
                        'rgba(59, 130, 246, 0.8)',
                        'rgba(139, 92, 246, 0.8)',
                        'rgba(16, 185, 129, 0.8)'
                    ],
                    borderColor: [
                        '#f59e0b',
                        '#3b82f6',
                        '#8b5cf6',
                        '#10b981'
                    ],
                    borderWidth: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '60%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            color: '#64748b',
                            font: {
                                size: 14,
                                weight: '500'
                            }
                        }
                    }
                }
            }
        });
    }
}

// Utility functions
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

function formatNumber(num) {
    return new Intl.NumberFormat('en-US').format(num);
}

function showNotification(message, type = 'success') {
    const notification = $(`
        <div class="alert ${type} fade-in" style="position: fixed; top: 20px; right: 20px; z-index: 9999; min-width: 300px;">
            <i class="fas fa-check-circle" style="margin-right: 8px;"></i>
            ${message}
        </div>
    `);
    
    $('body').append(notification);
    
    setTimeout(() => {
        notification.fadeOut(() => {
            notification.remove();
        });
    }, 4000);
}

// Initialize everything when document is ready
$(document).ready(function() {
    // Add loading class to body initially
    $('body').addClass('fade-in');
    
    // Initialize charts if Chart.js is available
    if (typeof Chart !== 'undefined') {
        initializeDashboardCharts();
    }
    
    console.log('🚀 Modern Admin Panel Loaded Successfully!');
});