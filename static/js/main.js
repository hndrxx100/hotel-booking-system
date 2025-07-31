/**
 * Main JavaScript file for Hotel Management System
 * Contains common functionality used across the application
 */

$(document).ready(function() {
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize form validations
    initializeFormValidations();
    
    // Initialize date pickers
    initializeDatePickers();
    
    // Initialize auto-refresh functionality
    initializeAutoRefresh();
    
    // Initialize notification system
    initializeNotifications();
});

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize form validations
 */
function initializeFormValidations() {
    // Real-time validation for forms
    $('.needs-validation').on('submit', function(e) {
        if (!this.checkValidity()) {
            e.preventDefault();
            e.stopPropagation();
        }
        $(this).addClass('was-validated');
    });
    
    // Phone number validation
    $('input[type="tel"], input[name*="phone"]').on('input', function() {
        const phone = $(this).val().replace(/\D/g, '');
        if (phone.length >= 10) {
            $(this).removeClass('is-invalid').addClass('is-valid');
        } else {
            $(this).removeClass('is-valid').addClass('is-invalid');
        }
    });
    
    // Email validation
    $('input[type="email"]').on('blur', function() {
        const email = $(this).val();
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        
        if (email === '' || emailRegex.test(email)) {
            $(this).removeClass('is-invalid').addClass('is-valid');
        } else {
            $(this).removeClass('is-valid').addClass('is-invalid');
        }
    });
    
    // Password strength indicator
    $('input[type="password"]').on('input', function() {
        const password = $(this).val();
        const strength = calculatePasswordStrength(password);
        showPasswordStrength($(this), strength);
    });
}

/**
 * Calculate password strength
 */
function calculatePasswordStrength(password) {
    let strength = 0;
    
    if (password.length >= 8) strength += 1;
    if (password.match(/[a-z]/)) strength += 1;
    if (password.match(/[A-Z]/)) strength += 1;
    if (password.match(/[0-9]/)) strength += 1;
    if (password.match(/[^a-zA-Z0-9]/)) strength += 1;
    
    return strength;
}

/**
 * Show password strength indicator
 */
function showPasswordStrength(input, strength) {
    let strengthText = '';
    let strengthClass = '';
    
    switch (strength) {
        case 0:
        case 1:
            strengthText = 'Very Weak';
            strengthClass = 'text-danger';
            break;
        case 2:
            strengthText = 'Weak';
            strengthClass = 'text-warning';
            break;
        case 3:
            strengthText = 'Medium';
            strengthClass = 'text-info';
            break;
        case 4:
            strengthText = 'Strong';
            strengthClass = 'text-success';
            break;
        case 5:
            strengthText = 'Very Strong';
            strengthClass = 'text-success fw-bold';
            break;
    }
    
    // Remove existing strength indicator
    input.next('.password-strength').remove();
    
    // Add new strength indicator
    if (input.val().length > 0) {
        input.after(`<div class="password-strength small ${strengthClass}">Password strength: ${strengthText}</div>`);
    }
}

/**
 * Initialize date pickers
 */
function initializeDatePickers() {
    // Set minimum dates for check-in/check-out
    const today = new Date().toISOString().split('T')[0];
    const tomorrow = new Date(Date.now() + 86400000).toISOString().split('T')[0];
    
    $('input[name="check_in"]').attr('min', today);
    $('input[name="check_out"]').attr('min', tomorrow);
    
    // Update check-out minimum when check-in changes
    $('input[name="check_in"]').on('change', function() {
        const checkInDate = new Date(this.value);
        const checkOutMin = new Date(checkInDate.getTime() + 86400000).toISOString().split('T')[0];
        $('input[name="check_out"]').attr('min', checkOutMin);
        
        // Clear check-out if it's now invalid
        const checkOutValue = $('input[name="check_out"]').val();
        if (checkOutValue && checkOutValue <= this.value) {
            $('input[name="check_out"]').val('');
        }
    });
    
    // Initialize bootstrap datepickers if available
    if ($.fn.datepicker) {
        $('.datepicker').datepicker({
            format: 'yyyy-mm-dd',
            autoclose: true,
            todayHighlight: true,
            startDate: 'today'
        });
    }
}

/**
 * Initialize auto-refresh functionality
 */
function initializeAutoRefresh() {
    // Auto-refresh for dashboards every 5 minutes
    if (window.location.pathname.includes('dashboard')) {
        setInterval(function() {
            if (document.visibilityState === 'visible') {
                location.reload();
            }
        }, 300000); // 5 minutes
    }
    
    // Auto-refresh for booking management every 2 minutes
    if (window.location.pathname.includes('bookings')) {
        setInterval(function() {
            if (document.visibilityState === 'visible') {
                refreshBookingsTable();
            }
        }, 120000); // 2 minutes
    }
}

/**
 * Refresh bookings table if DataTable is present
 */
function refreshBookingsTable() {
    if (typeof bookingsTable !== 'undefined' && bookingsTable) {
        bookingsTable.ajax.reload(null, false); // Keep current page
    }
}

/**
 * Initialize notification system
 */
function initializeNotifications() {
    // Auto-hide success alerts after 5 seconds
    $('.alert-success').delay(5000).fadeOut('slow');
    
    // Auto-hide info alerts after 7 seconds
    $('.alert-info').delay(7000).fadeOut('slow');
    
    // Keep error alerts visible until manually dismissed
    $('.alert-danger').on('click', '.btn-close', function() {
        $(this).closest('.alert').fadeOut('fast');
    });
}

/**
 * Show loading state for buttons
 */
function showButtonLoading(button, originalText = null) {
    const $button = $(button);
    if (!originalText) {
        originalText = $button.html();
    }
    $button.data('original-text', originalText);
    $button.prop('disabled', true).html('<i class="fas fa-spinner fa-spin me-1"></i>Loading...');
}

/**
 * Hide loading state for buttons
 */
function hideButtonLoading(button) {
    const $button = $(button);
    const originalText = $button.data('original-text') || 'Submit';
    $button.prop('disabled', false).html(originalText);
}

/**
 * Format currency for display
 */
function formatCurrency(amount, currency = 'USD') {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency
    }).format(amount);
}

/**
 * Format phone number for display
 */
function formatPhoneNumber(phone) {
    const cleaned = phone.replace(/\D/g, '');
    const match = cleaned.match(/^(\d{3})(\d{3})(\d{4})$/);
    if (match) {
        return '(' + match[1] + ') ' + match[2] + '-' + match[3];
    }
    return phone;
}

/**
 * Validate email format
 */
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
 * Show confirmation dialog
 */
function showConfirmationDialog(title, message, callback) {
    const modal = $(`
        <div class="modal fade" id="confirmationModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">${title}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p>${message}</p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary" id="confirmAction">Confirm</button>
                    </div>
                </div>
            </div>
        </div>
    `);
    
    $('body').append(modal);
    modal.modal('show');
    
    modal.find('#confirmAction').on('click', function() {
        callback();
        modal.modal('hide');
    });
    
    modal.on('hidden.bs.modal', function() {
        modal.remove();
    });
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info', duration = 5000) {
    const toastId = 'toast-' + Date.now();
    const bgClass = type === 'error' ? 'bg-danger' : type === 'success' ? 'bg-success' : 'bg-info';
    
    const toast = $(`
        <div class="toast ${bgClass} text-white" id="${toastId}" role="alert">
            <div class="toast-header ${bgClass} text-white border-0">
                <i class="fas fa-${type === 'error' ? 'exclamation-circle' : type === 'success' ? 'check-circle' : 'info-circle'} me-2"></i>
                <strong class="me-auto">Hotel Management</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `);
    
    // Create toast container if it doesn't exist
    if ($('#toast-container').length === 0) {
        $('body').append('<div id="toast-container" class="position-fixed top-0 end-0 p-3" style="z-index: 9999;"></div>');
    }
    
    $('#toast-container').append(toast);
    
    const bsToast = new bootstrap.Toast(toast[0], {
        delay: duration
    });
    
    bsToast.show();
    
    // Remove toast element after it's hidden
    toast.on('hidden.bs.toast', function() {
        $(this).remove();
    });
}

/**
 * Scroll to top function
 */
function scrollToTop() {
    $('html, body').animate({ scrollTop: 0 }, 'slow');
}

/**
 * Add scroll to top button
 */
$(window).scroll(function() {
    if ($(this).scrollTop() > 200) {
        if ($('#scrollToTop').length === 0) {
            $('body').append(`
                <button id="scrollToTop" class="btn btn-primary position-fixed" 
                        style="bottom: 20px; right: 20px; z-index: 9999; border-radius: 50%; width: 50px; height: 50px;"
                        onclick="scrollToTop()" title="Scroll to top">
                    <i class="fas fa-arrow-up"></i>
                </button>
            `);
        }
    } else {
        $('#scrollToTop').remove();
    }
});

/**
 * Initialize search functionality
 */
function initializeSearch() {
    $('.search-input').on('input', function() {
        const searchTerm = $(this).val().toLowerCase();
        const targetTable = $(this).data('target');
        
        if (targetTable) {
            $(`${targetTable} tbody tr`).each(function() {
                const rowText = $(this).text().toLowerCase();
                if (rowText.includes(searchTerm)) {
                    $(this).show();
                } else {
                    $(this).hide();
                }
            });
        }
    });
}

/**
 * Handle AJAX errors globally
 */
$(document).ajaxError(function(event, xhr, settings, thrownError) {
    console.error('AJAX Error:', {
        url: settings.url,
        status: xhr.status,
        error: thrownError
    });
    
    if (xhr.status === 401) {
        showToast('Session expired. Please log in again.', 'error');
        setTimeout(() => {
            window.location.href = '/login';
        }, 2000);
    } else if (xhr.status === 403) {
        showToast('You do not have permission to perform this action.', 'error');
    } else if (xhr.status >= 500) {
        showToast('Server error occurred. Please try again later.', 'error');
    } else {
        showToast('An unexpected error occurred.', 'error');
    }
});

/**
 * CSRF token handling for AJAX requests
 */
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
            const token = $('meta[name=csrf-token]').attr('content') || 
                         $('input[name=csrf_token]').val();
            if (token) {
                xhr.setRequestHeader("X-CSRFToken", token);
            }
        }
    }
});

/**
 * Prevent double form submission
 */
$('form').on('submit', function() {
    const submitButton = $(this).find('button[type="submit"]');
    if (submitButton.data('submitted')) {
        return false;
    }
    
    submitButton.data('submitted', true);
    showButtonLoading(submitButton);
    
    // Re-enable after 5 seconds as fallback
    setTimeout(() => {
        submitButton.data('submitted', false);
        hideButtonLoading(submitButton);
    }, 5000);
});

/**
 * Auto-save form data to localStorage
 */
function enableAutoSave(formSelector, key) {
    const form = $(formSelector);
    const storageKey = 'autosave_' + key;
    
    // Load saved data
    const savedData = localStorage.getItem(storageKey);
    if (savedData) {
        const data = JSON.parse(savedData);
        Object.keys(data).forEach(name => {
            form.find(`[name="${name}"]`).val(data[name]);
        });
    }
    
    // Save data on input
    form.find('input, textarea, select').on('input change', function() {
        const formData = {};
        form.find('input, textarea, select').each(function() {
            if ($(this).attr('name') && $(this).attr('type') !== 'password') {
                formData[$(this).attr('name')] = $(this).val();
            }
        });
        localStorage.setItem(storageKey, JSON.stringify(formData));
    });
    
    // Clear saved data on successful form submission
    form.on('submit', function() {
        setTimeout(() => {
            localStorage.removeItem(storageKey);
        }, 1000);
    });
}

/**
 * Initialize accessibility features
 */
function initializeAccessibility() {
    // Add skip to main content link
    if ($('#skip-to-main').length === 0) {
        $('body').prepend(`
            <a href="#main-content" id="skip-to-main" class="visually-hidden-focusable btn btn-primary position-absolute" 
               style="top: 10px; left: 10px; z-index: 10000;">
                Skip to main content
            </a>
        `);
    }
    
    // Add main content landmark if not present
    if ($('main').length === 0) {
        $('body > .container, body > .container-fluid').first().wrap('<main id="main-content"></main>');
    } else {
        $('main').attr('id', 'main-content');
    }
    
    // Enhance focus visibility
    $('button, a, input, select, textarea').on('focus', function() {
        $(this).addClass('focus-visible');
    }).on('blur', function() {
        $(this).removeClass('focus-visible');
    });
    
    // Add ARIA labels to form controls without labels
    $('input, select, textarea').each(function() {
        if (!$(this).attr('aria-label') && !$(this).attr('aria-labelledby')) {
            const placeholder = $(this).attr('placeholder');
            if (placeholder) {
                $(this).attr('aria-label', placeholder);
            }
        }
    });
}

// Initialize accessibility features when DOM is ready
$(document).ready(function() {
    initializeAccessibility();
    initializeSearch();
});

// Export functions for global use
window.HotelManagement = {
    showButtonLoading,
    hideButtonLoading,
    formatCurrency,
    formatPhoneNumber,
    isValidEmail,
    showConfirmationDialog,
    showToast,
    scrollToTop,
    enableAutoSave
};
