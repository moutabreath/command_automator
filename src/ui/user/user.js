async function initUser() {
    console.log('Initializing User...');

    if (typeof window.pywebview === 'undefined' || typeof window.pywebview.api === 'undefined') {
        console.error('PyWebView API not available');
        document.getElementById('result').value = 'Error: PyWebView API not available';
        return;
    }

    await loadUserConfig();
    await initUserEventListeners();
}

async function loadUserConfig() {
    try {
        let userConfig = await window.pywebview.api.load_user_config();
        const userEmail = document.getElementById('user-email');
        if (userEmail) {
            userEmail.value = userConfig.email || '';
        }
    } catch (error) {
        console.log('Error loading config:', error);
    }
}


async function initUserEventListeners() {
    document.getElementById('login-btn').addEventListener('click', async () => {
        await registerOrLogin();
    });
}

userId = undefined;

async function registerOrLogin(){
    const emailInput = document.getElementById('user-email');
    user_email = emailInput.value.trim();
    if (!user_email) {
        alert('Please enter your email.');
        return;
    }

    try {
        response = await window.pywebview.api.login_or_register(user_email);
        if (response.code === "OK") {
            user_id = response.text;
        }
        if (user_id) {
            document.getElementById('llm-login-container').style.display = 'none';
            document.getElementById('job-info-row').style.display = 'flex';
        }
    } catch (error) {
        console.error('Login failed:', error);
        alert('Login failed. Please check the console for details.');
    }
}