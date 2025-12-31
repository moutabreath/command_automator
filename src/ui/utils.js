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
            await waitForPyWebView();
        }

        return await apiFunction(...args);
    } catch (error) {
        console.error('API call failed:', error);
        throw error;
    }
}

// Escape HTML to prevent XSS attacks
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}


function showAlert(message, type = 'info', duration = 5000) {
    const alertContainer = document.getElementById('alert-container');
    if (!alertContainer) {
        console.error('Alert container not found');
        return;
    }
    const alertId = 'alert-' + Date.now() + '-' + Math.random().toString(36).slice(2, 11);
    const alertClass = {
        'success': 'alert-success',
        'error': 'alert-danger',
        'failure': 'alert-danger',
        'warning': 'alert-warning',
        'info': 'alert-info'
    }[type] || 'alert-info';

    const alertHtml = `
                <div id="${alertId}" class="alert ${alertClass} alert-dismissible fade show" role="alert">
                    ${escapeHtml(message)}
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

function getContactNameFromLinkedin(url) {
    const match = url.match(/linkedin\.com\/in\/([^/?]+)/);
    if (!match) return null;
    
    const slug = match[1];
    return slug.split('-')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}