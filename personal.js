/**
 * Personal Customer Area functionality
 * Handles login, session management, and customer data display
 */

function toggleMobileGuideMenu() {
    const menu = document.getElementById('mobileGuideMenu');
    const button = document.querySelector('.nav-menu-action');

    if (!menu) return;

    const isOpen = menu.classList.toggle('active');

    if (button) {
        button.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    }
}

function closeMobileGuideMenu() {
    const menu = document.getElementById('mobileGuideMenu');
    const button = document.querySelector('.nav-menu-action');

    if (menu) {
        menu.classList.remove('active');
    }

    if (button) {
        button.setAttribute('aria-expanded', 'false');
    }
}

function openGuideFromMobileMenu(type) {
    closeMobileGuideMenu();
    window.location.href = `index.html?guide=${encodeURIComponent(type)}#services`;
}

class PersonalArea {
    constructor() {
        this.fireberryAPI = new FireberryAPI();
        this.sessionTimeout = 2 * 60 * 1000; // 2 minutes in milliseconds
        this.sessionTimer = null;
        this.countdownTimer = null;
        this.currentSession = null;

        this.initializeEventListeners();
        this.checkExistingSession();
    }

    /**
     * Initialize event listeners
     */
    initializeEventListeners() {
        // Login form submission
        const loginForm = document.getElementById('customer-login-form');
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => this.handleLogin(e));
        }

        // Logout button
        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => this.handleLogout());
        }

        // Input validation and formatting
        const ltdInput = document.getElementById('ltd-number');
        const phoneInput = document.getElementById('phone-number');

        if (ltdInput) {
            ltdInput.addEventListener('input', (e) => this.formatLtdInput(e));
            ltdInput.addEventListener('blur', (e) => this.validateLtdInput(e));
        }

        if (phoneInput) {
            phoneInput.addEventListener('input', (e) => this.formatPhoneInput(e));
            phoneInput.addEventListener('blur', (e) => this.validatePhoneInput(e));
        }

        // Track user activity for session management
        document.addEventListener('mousemove', () => this.resetSessionTimer());
        document.addEventListener('keypress', () => this.resetSessionTimer());
        document.addEventListener('click', () => this.resetSessionTimer());
    }

    /**
     * Check for existing session
     */
    checkExistingSession() {
        const session = localStorage.getItem('customerSession');
        if (session) {
            try {
                const sessionData = JSON.parse(session);
                const now = new Date().getTime();

                if (now < sessionData.expiresAt) {
                    this.currentSession = sessionData;
                    this.showCustomerDetails(sessionData.customerData);
                    this.startSessionTimer();
                } else {
                    localStorage.removeItem('customerSession');
                }
            } catch (error) {
                localStorage.removeItem('customerSession');
            }
        }
    }

    /**
     * Handle login form submission
     */
    async handleLogin(event) {
        event.preventDefault();

        const ltdNumber = document.getElementById('ltd-number').value.trim();
        const phoneNumber = document.getElementById('phone-number').value.trim();

        // Clear previous errors
        this.clearErrors();

        // Validate inputs
        if (!this.validateForm(ltdNumber, phoneNumber)) {
            return;
        }

        // Show loading state
        this.showLoading(true);

        try {
            // Search for customer
            const result = await this.fireberryAPI.searchCustomer(
                FireberryAPI.formatIdNumber(ltdNumber),
                FireberryAPI.formatPhoneNumber(phoneNumber)
            );

            this.showLoading(false);

            if (result.success) {
                // Create session
                const sessionData = {
                    customerData: result.customer,
                    loginTime: new Date().getTime(),
                    expiresAt: new Date().getTime() + this.sessionTimeout
                };

                localStorage.setItem('customerSession', JSON.stringify(sessionData));
                this.currentSession = sessionData;

                // Show customer details
                this.showCustomerDetails(result.customer);
                this.startSessionTimer();

            } else if (result.error === 'customer_not_found') {
                this.showError('general', 'לא נמצא חשבון העונה לפרטים שהוזנו. אנא בדקו את המידע ונסו שוב.');
            } else {
                this.showError('general', 'שגיאה בהתחברות למערכת. אנא נסו שוב מאוחר יותר.');
            }

        } catch (error) {
            this.showLoading(false);
            this.showError('general', 'שגיאה בהתחברות למערכת. אנא בדקו את החיבור לאינטרנט ונסו שוב.');
        }
    }

    /**
     * Validate form inputs
     */
    validateForm(ltdNumber, phoneNumber) {
        let isValid = true;

        if (!FireberryAPI.validateIdNumber(ltdNumber)) {
            this.showError('ltd', 'מספר עוסק מורשה חייב להכיל בדיוק 9 ספרות');
            isValid = false;
        }

        if (!FireberryAPI.validatePhoneNumber(phoneNumber)) {
            this.showError('phone', 'מספר טלפון חייב להכיל 9-10 ספרות');
            isValid = false;
        }

        return isValid;
    }

    /**
     * Format L.T.D. input (digits only)
     */
    formatLtdInput(event) {
        const input = event.target;
        input.value = input.value.replace(/\D/g, '');
    }

    /**
     * Format phone input (digits only)
     */
    formatPhoneInput(event) {
        const input = event.target;
        input.value = input.value.replace(/\D/g, '');
    }

    /**
     * Validate L.T.D. input on blur
     */
    validateLtdInput(event) {
        const value = event.target.value.trim();
        if (value && !FireberryAPI.validateIdNumber(value)) {
            this.showError('ltd', 'מספר עוסק מורשה חייב להכיל בדיוק 9 ספרות');
        } else {
            this.clearError('ltd');
        }
    }

    /**
     * Validate phone input on blur
     */
    validatePhoneInput(event) {
        const value = event.target.value.trim();
        if (value && !FireberryAPI.validatePhoneNumber(value)) {
            this.showError('phone', 'מספר טלפון חייב להכיל 9-10 ספרות');
        } else {
            this.clearError('phone');
        }
    }

    /**
     * Show customer details section
     */
    showCustomerDetails(customerData) {
        const loginSection = document.getElementById('login-section');
        const detailsSection = document.getElementById('details-section');

        if (loginSection) loginSection.style.display = 'none';
        if (detailsSection) detailsSection.style.display = 'block';

        this.populateCustomerData(customerData);
    }

    /**
     * Populate customer data in the details section
     */
    populateCustomerData(customer) {
        const customerDataContainer = document.getElementById('customer-data');
        if (!customerDataContainer) return;

        const customerInfo = [
            { label: 'שם החברה', value: customer.accountname, icon: 'fas fa-building' },
            { label: 'איש קשר', value: customer.firstname, icon: 'fas fa-user' },
            { label: 'מספר חשבון', value: customer.accountnumber, icon: 'fas fa-hashtag' },
            { label: 'טלפון ראשי', value: customer.telephone1, icon: 'fas fa-phone' },
            { label: 'טלפון נוסף', value: customer.telephone2, icon: 'fas fa-phone-alt' },
            { label: 'כתובת דוא"ל', value: customer.emailaddress1, icon: 'fas fa-envelope' },
            { label: 'כתובת', value: customer.billingcity, icon: 'fas fa-map-marker-alt' },
            { label: 'סוכן מכירות', value: customer.pcfsystemfield34, icon: 'fas fa-user-tie' },
            { label: 'דוא"ל סוכן מכירות', value: customer.pcfsystemfield266, icon: 'fas fa-envelope' },
            { label: 'דומיין מערכת טלפונים', value: customer.pcfsystemfield179, icon: 'fas fa-server' },
            { label: 'קיום הקלטות שיחות', value: customer.pcfsystemfield270, icon: 'fas fa-record-vinyl' },
            { label: 'שם משתמש למערכת טלפונים', value: customer.pcfsystemfield267, icon: 'fas fa-user' },
            { label: 'סיסמה למערכת טלפונים', value: customer.pcfsystemfield268, icon: 'fas fa-key' },
            { label: 'כמות שלוחות', value: customer.pcfsystemfield243, icon: 'fas fa-phone-square' },
            { label: 'דוא"ל שירותי בוט', value: customer.pcfsystemfield264, icon: 'fas fa-robot' },
            { label: 'דוא"ל שירות מייל לפקס', value: customer.pcfsystemfield265, icon: 'fas fa-fax' },
            { label: 'הודעת SMS', value: customer.pcfsystemfield256, icon: 'fas fa-sms' }
        ];

        const html = customerInfo.map(item => {
            if (!item.value || item.value === 'null') return '';

            return `
                <div class="detail-item">
                    <div class="detail-icon">
                        <i class="${item.icon}"></i>
                    </div>
                    <div class="detail-content">
                        <label class="detail-label">${item.label}</label>
                        <div class="detail-value">${this.escapeHtml(item.value)}</div>
                    </div>
                </div>
            `;
        }).join('');

        customerDataContainer.innerHTML = html;
    }

    /**
     * Start session timer and countdown
     */
    startSessionTimer() {
        // Clear any existing timers
        this.clearTimers();

        // Start session expiry timer
        this.sessionTimer = setTimeout(() => {
            this.handleSessionExpiry();
        }, this.sessionTimeout);

        // Start countdown display timer
        this.updateCountdownDisplay();
        this.countdownTimer = setInterval(() => {
            this.updateCountdownDisplay();
        }, 1000);
    }

    /**
     * Reset session timer on user activity
     */
    resetSessionTimer() {
        if (this.currentSession) {
            // Update session expiry time
            const newExpiryTime = new Date().getTime() + this.sessionTimeout;
            this.currentSession.expiresAt = newExpiryTime;
            localStorage.setItem('customerSession', JSON.stringify(this.currentSession));

            // Restart timers
            this.startSessionTimer();
        }
    }

    /**
     * Update countdown display
     */
    updateCountdownDisplay() {
        const countdownElement = document.getElementById('session-countdown');
        if (!countdownElement || !this.currentSession) return;

        const now = new Date().getTime();
        const timeLeft = this.currentSession.expiresAt - now;

        if (timeLeft <= 0) {
            this.handleSessionExpiry();
            return;
        }

        const minutes = Math.floor(timeLeft / 60000);
        const seconds = Math.floor((timeLeft % 60000) / 1000);
        countdownElement.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
    }

    /**
     * Handle session expiry
     */
    handleSessionExpiry() {
        alert('הפגישה שלכם הסתיימה מטעמי אבטחה. אנא התחברו שוב.');
        this.handleLogout();
    }

    /**
     * Handle logout
     */
    handleLogout() {
        // Clear session data
        localStorage.removeItem('customerSession');
        this.currentSession = null;
        this.clearTimers();

        // Reset form
        const loginForm = document.getElementById('customer-login-form');
        if (loginForm) {
            loginForm.reset();
        }

        // Show login section
        const loginSection = document.getElementById('login-section');
        const detailsSection = document.getElementById('details-section');

        if (loginSection) loginSection.style.display = 'block';
        if (detailsSection) detailsSection.style.display = 'none';

        // Clear errors
        this.clearErrors();
    }

    /**
     * Clear all timers
     */
    clearTimers() {
        if (this.sessionTimer) {
            clearTimeout(this.sessionTimer);
            this.sessionTimer = null;
        }
        if (this.countdownTimer) {
            clearInterval(this.countdownTimer);
            this.countdownTimer = null;
        }
    }

    /**
     * Show/hide loading state
     */
    showLoading(show) {
        const loadingElement = document.getElementById('loading-indicator');
        const loginBtn = document.getElementById('login-btn');

        if (loadingElement) {
            loadingElement.style.display = show ? 'block' : 'none';
        }
        if (loginBtn) {
            loginBtn.disabled = show;
        }
    }

    /**
     * Show error message
     */
    showError(type, message) {
        let errorElement;

        if (type === 'ltd') {
            errorElement = document.getElementById('ltd-error');
        } else if (type === 'phone') {
            errorElement = document.getElementById('phone-error');
        } else {
            errorElement = document.getElementById('general-error');
        }

        if (errorElement) {
            errorElement.textContent = message;
            errorElement.style.display = 'block';
        }
    }

    /**
     * Clear specific error
     */
    clearError(type) {
        let errorElement;

        if (type === 'ltd') {
            errorElement = document.getElementById('ltd-error');
        } else if (type === 'phone') {
            errorElement = document.getElementById('phone-error');
        } else {
            errorElement = document.getElementById('general-error');
        }

        if (errorElement) {
            errorElement.style.display = 'none';
            errorElement.textContent = '';
        }
    }

    /**
     * Clear all errors
     */
    clearErrors() {
        this.clearError('ltd');
        this.clearError('phone');
        this.clearError('general');
    }

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        if (typeof text !== 'string') return text;

        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new PersonalArea();
});
