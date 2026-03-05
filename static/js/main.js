// Main JavaScript file for Smart Life Analyzer

// API Helper Functions
const API = {
    baseUrl: '/api/',
    
    async request(endpoint, options = {}) {
        const url = this.baseUrl + endpoint;
        
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
            }
        };
        
        const mergedOptions = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(url, mergedOptions);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('API Request Error:', error);
            throw error;
        }
    },
    
    async get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    },
    
    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },
    
    async put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },
    
    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }
};

// Utility Functions
const Utils = {
    formatDate(date) {
        return new Date(date).toLocaleDateString('en-US', {
            weekday: 'short',
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    },
    
    formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    },
    
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <div class="toast-content">
                <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
                <span>${message}</span>
            </div>
            <button class="toast-close">&times;</button>
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => toast.classList.add('show'), 10);
        
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 5000);
        
        toast.querySelector('.toast-close').addEventListener('click', () => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        });
    },
    
    validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }
};

// Theme Manager
const ThemeManager = {
    init() {
        this.loadTheme();
        this.setupThemeToggle();
    },
    
    loadTheme() {
        const theme = localStorage.getItem('theme') || 'light';
        this.setTheme(theme);
    },
    
    setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
    },
    
    setupThemeToggle() {
        const toggle = document.getElementById('theme-toggle');
        if (toggle) {
            toggle.addEventListener('click', () => {
                const currentTheme = document.documentElement.getAttribute('data-theme');
                const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
                this.setTheme(newTheme);
            });
        }
    }
};

// Chart Manager
const ChartManager = {
    charts: {},
    
    createChart(canvasId, config) {
        const ctx = document.getElementById(canvasId)?.getContext('2d');
        if (!ctx) return null;
        
        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }
        
        this.charts[canvasId] = new Chart(ctx, config);
        return this.charts[canvasId];
    },
    
    destroyChart(canvasId) {
        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
            delete this.charts[canvasId];
        }
    },
    
    updateChart(canvasId, data) {
        if (this.charts[canvasId]) {
            this.charts[canvasId].data = data;
            this.charts[canvasId].update();
        }
    }
};

// Form Validation
const FormValidator = {
    patterns: {
        email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
        phone: /^[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}$/,
        password: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/
    },
    
    validateField(field, value) {
        const type = field.getAttribute('data-validation') || field.type;
        
        switch(type) {
            case 'email':
                return this.patterns.email.test(value);
            case 'tel':
                return this.patterns.phone.test(value);
            case 'password':
                return this.patterns.password.test(value);
            case 'number':
                const min = parseFloat(field.getAttribute('min')) || -Infinity;
                const max = parseFloat(field.getAttribute('max')) || Infinity;
                const numValue = parseFloat(value);
                return !isNaN(numValue) && numValue >= min && numValue <= max;
            default:
                return value.trim() !== '';
        }
    },
    
    showValidation(field, isValid) {
        field.classList.toggle('is-valid', isValid);
        field.classList.toggle('is-invalid', !isValid);
    }
};

// Sidebar Navigation
const Navigation = {
    init() {
        this.setupNavLinks();
        this.setupMobileMenu();
    },
    
    setupNavLinks() {
        const navLinks = document.querySelectorAll('.nav-item');
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                if (link.href === '#' || link.getAttribute('href') === '#') {
                    e.preventDefault();
                }
                
                navLinks.forEach(l => l.classList.remove('active'));
                link.classList.add('active');
            });
        });
    },
    
    setupMobileMenu() {
        const menuToggle = document.getElementById('mobile-menu-toggle');
        const sidebar = document.querySelector('.sidebar');
        
        if (menuToggle && sidebar) {
            menuToggle.addEventListener('click', () => {
                sidebar.classList.toggle('mobile-open');
            });
        }
    }
};

// Dashboard Widgets
const DashboardWidgets = {
    async refreshAll() {
        try {
            await Promise.all([
                this.refreshStats(),
                this.refreshCharts(),
                this.refreshSuggestions()
            ]);
            Utils.showToast('Dashboard refreshed', 'success');
        } catch (error) {
            Utils.showToast('Error refreshing dashboard', 'error');
            console.error('Refresh error:', error);
        }
    },
    
    async refreshStats() {
        // Implement stat refresh logic
        console.log('Refreshing stats...');
    },
    
    async refreshCharts() {
        // Implement chart refresh logic
        console.log('Refreshing charts...');
    },
    
    async refreshSuggestions() {
        // Implement suggestions refresh logic
        console.log('Refreshing suggestions...');
    }
};

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize managers
    ThemeManager.init();
    Navigation.init();
    
    // Set up global event listeners
    setupGlobalListeners();
    
    // Initialize forms
    setupForms();
});

function setupGlobalListeners() {
    // Refresh dashboard button
    const refreshBtn = document.getElementById('refresh-dashboard');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => DashboardWidgets.refreshAll());
    }
    
    // Logout confirmation
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            if (!confirm('Are you sure you want to logout?')) {
                e.preventDefault();
            }
        });
    }
    
    // Auto-save forms on change
    document.querySelectorAll('.auto-save').forEach(form => {
        form.addEventListener('change', Utils.debounce(() => {
            saveForm(form);
        }, 1000));
    });
}

function setupForms() {
    // Real-time validation
    document.querySelectorAll('[data-validation]').forEach(field => {
        field.addEventListener('input', () => {
            const isValid = FormValidator.validateField(field, field.value);
            FormValidator.showValidation(field, isValid);
        });
    });
    
    // Password strength indicator
    const passwordFields = document.querySelectorAll('input[type="password"]');
    passwordFields.forEach(field => {
        if (field.id.includes('password') && !field.id.includes('confirm')) {
            field.addEventListener('input', updatePasswordStrength);
        }
    });
}

async function saveForm(form) {
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    
    try {
        const response = await API.post('save-preferences/', data);
        if (response.success) {
            Utils.showToast('Settings saved', 'success');
        }
    } catch (error) {
        Utils.showToast('Error saving settings', 'error');
    }
}

function updatePasswordStrength(event) {
    const password = event.target.value;
    const strength = calculatePasswordStrength(password);
    
    const strengthBar = document.querySelector('.strength-bar');
    const strengthText = document.querySelector('.strength-text');
    
    if (strengthBar && strengthText) {
        strengthBar.style.width = `${strength.score * 25}%`;
        strengthBar.className = `strength-bar ${strength.level}`;
        strengthText.textContent = `Strength: ${strength.level}`;
    }
}

function calculatePasswordStrength(password) {
    let score = 0;
    
    // Length check
    if (password.length >= 8) score++;
    if (password.length >= 12) score++;
    
    // Character variety checks
    if (/[a-z]/.test(password)) score++;
    if (/[A-Z]/.test(password)) score++;
    if (/[0-9]/.test(password)) score++;
    if (/[^A-Za-z0-9]/.test(password)) score++;
    
    const levels = ['weak', 'fair', 'good', 'strong', 'very-strong'];
    const level = levels[Math.min(score, levels.length - 1)];
    
    return { score, level };
}

// Export for use in other modules
window.SmartLifeAnalyzer = {
    API,
    Utils,
    ThemeManager,
    ChartManager,
    FormValidator,
    Navigation,
    DashboardWidgets
};