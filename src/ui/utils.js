// Common utility functions for the application

// Check if PyWebView API is available
function isPyWebViewReady() {
    return typeof window.pywebview !== 'undefined' &&
        typeof window.pywebview.api !== 'undefined';
}

// Wait for PyWebView API to be ready
function waitForPyWebView(maxAttempts = 20, interval = 250) {
    return new Promise((resolve, reject) => {
        let attempts = 0;

        const check = () => {
            attempts++;

            if (isPyWebViewReady()) {
                console.log(`PyWebView API ready after ${attempts} attempts`);
                resolve(true);
            } else if (attempts >= maxAttempts) {
                console.error(`PyWebView API not ready after ${maxAttempts} attempts`);
                reject(new Error('PyWebView API timeout'));
            } else {
                setTimeout(check, interval);
            }
        };

        check();
    });
}

// Safe API call wrapper
async function safeApiCall(apiFunction, ...args) {
    try {
        if (!isPyWebViewReady()) {
            throw new Error('PyWebView API not available');
        }

        return await apiFunction(...args);
    } catch (error) {
        console.error('API call failed:', error);
        throw error;
    }
}

// Initialize basic DOM elements that don't require API
function init_basic_llm_dom_elements() {
    console.log('Initializing basic DOM elements');
    // This function can be implemented if needed for basic DOM setup
}

function showAlert(message, type = 'info', duration = 5000) {
    const alertContainer = document.getElementById('alert-container');
    const alertId = 'alert-' + Date.now();

    const alertClass = {
        'success': 'alert-success',
        'error': 'alert-danger',
        'failure': 'alert-danger',
        'warning': 'alert-warning',
        'info': 'alert-info'
    }[type] || 'alert-info';

    const alertHtml = `
                <div id="${alertId}" class="alert ${alertClass} alert-dismissible fade show" role="alert">
                    ${message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            `;

    alertContainer.insertAdjacentHTML('beforeend', alertHtml);

    // Auto-dismiss after duration
    setTimeout(() => {
        const alertElement = document.getElementById(alertId);
        if (alertElement) {
            const bsAlert = new bootstrap.Alert(alertElement);
            bsAlert.close();
        }
    }, duration);
}