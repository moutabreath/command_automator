// User Authentication JavaScript - Bootstrap Compatible

// Global user variables
window.userId = undefined;

async function initUser() {
    console.log('Initializing User...');

    await loadUserConfig();
    await initUserEventListeners();
}

async function loadUserConfig() {
    try {
        let userConfig = await window.pywebview.api.load_user_config();
        const userEmail = document.getElementById('user-email');
        if (userEmail && userConfig) {
            userEmail.value = userConfig.email || '';
        }
    } catch (error) {
        console.log('Error loading user config:', error);
    }
}

async function saveUserConfig() {
    try {
        const userEmail = document.getElementById('user-email');
        if (userEmail && userEmail.value && isValidEmail(userEmail.value.trim())) {
            const userConfig = {
                email: userEmail.value.trim()
            };
            await window.pywebview.api.save_user_config(userConfig);
        }
    } catch (error) {
        console.log('Error saving user config:', error);
    }
}

async function initUserEventListeners() {
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
}

async function registerOrLogin() {
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
        const response = await window.pywebview.api.login_or_register(userEmail);
        
        if (response && response.code === 'OK') {
            window.userId = response.text;
            
            // Hide login container and show job tracking
            const loginContainer = document.getElementById('llm-login-container');
            const jobInfoRow = document.getElementById('job-info-row');
            
            if (loginContainer) {
                loginContainer.style.display = 'none';
            }
            
            if (jobInfoRow) {
                jobInfoRow.style.display = 'block';
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
}

function isValidEmail(email) {
    // Basic email validation regex
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}