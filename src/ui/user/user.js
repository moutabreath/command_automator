// User Authentication JavaScript - Bootstrap Compatible

// Global user variables
window.userId = undefined;

async function initUser() {
    console.log('Initializing User...');

    await loadUserConfig();
    await initUserEventListeners();
}

async function loadUserConfig() {
    const userEmail = document.getElementById('user-email');
    if (userEmail && typeof config !== 'undefined' && config && config.user) {
        userEmail.value = config.user.email || '';
    }
}

async function saveUserConfig() {
    try {
        const userEmail = document.getElementById('user-email');
        if (userEmail && userEmail.value && isValidEmail(userEmail.value.trim())) {
            const userConfig = {
                email: userEmail.value.trim()
            };
            await window.pywebview.api.save_configuration(userConfig, 'user');
        }
    } catch (error) {
        console.log('Error saving user config:', error);
    }
}
let isLoggingIn = false;
let listenersInitialized = false;

async function initUserEventListeners() {
    if (listenersInitialized) {
        return;
    }

    const loginBtn = document.getElementById('login-btn');
    const userEmail = document.getElementById('user-email');
    if (!loginBtn) {
        console.error('Login button not found');
        return;
    }

    // Login button click
    loginBtn.addEventListener('click', async () => {
        await registerOrLogin();
    });

    // Enter key to login
    if (userEmail) {
        userEmail.addEventListener('keydown', async function (e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                await registerOrLogin();
            }
        });

        // Save email on change
        userEmail.addEventListener('change', async function () {
            await saveUserConfig();
        });
    }

    listenersInitialized = true;
}

async function registerOrLogin() {
    if (isLoggingIn) {
        return;
    }
    const emailInput = document.getElementById('user-email');
    const loginBtn = document.getElementById('login-btn');

    if (!emailInput) {
        console.error('Email input not found');
        return;
    }

    let userEmail = emailInput.value.trim();

    if (!userEmail) {
        showAlert('Please enter your email.', 'warning');
        emailInput.focus();
        return;
    }

    // Basic email validation
    if (!isValidEmail(userEmail)) {
        showAlert('Please enter a valid email address.', 'warning');
        emailInput.focus();
        return;
    }

    // Disable button during login
    if (loginBtn) {
        loginBtn.disabled = true;
        loginBtn.textContent = 'Logging in...';
    }

    const spinner = document.getElementById('spinner');
    if (spinner) {
        spinner.classList.add('visible');
        document.body.classList.add('spinner-active');
    }

    try {
        isLoggingIn = true;
        const response = await window.pywebview.api.login_or_register(userEmail);

        if (response && response.code === 'OK') {
            window.userId = response.user_id;

            // Hide login container and show job tracking
            const loginContainer = document.getElementById('login-container');
            const jobTrackingContainer = document.getElementById('job-tracking-container');

            if (loginContainer) {
                loginContainer.style.display = 'none';
            }

            if (jobTrackingContainer) {
                jobTrackingContainer.style.display = 'block';
            }

            // Initialize job tracking
            if (typeof initJobTracking === 'function') {
                await initJobTracking();
            }

            showAlert('Login successful!', 'success');
            console.log('User logged in successfully:', window.userId);
        } else {
            throw new Error(response?.text || 'Login failed');
        }
    } catch (error) {
        console.error('Login failed:', error);
        showAlert('Login failed. Please try again.', 'error');
    } finally {
        isLoggingIn = false;
        // Re-enable button
        if (loginBtn) {
            loginBtn.disabled = false;
            loginBtn.textContent = 'Login';
        }

        // Hide spinner
        if (spinner) {
            spinner.classList.remove('visible');
            document.body.classList.remove('spinner-active');
        }
    }
}function isValidEmail(email) {
    // Basic email validation regex
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}