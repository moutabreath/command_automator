let config = {};

async function loadScripts() {
    try {
        console.log('Loading scripts...');
        const scripts = await window.pywebview.api.load_scripts();
        console.log('Scripts loaded:', scripts);

        const select = document.getElementById('script-select');
        select.innerHTML = '';

        if (scripts && scripts.length > 0) {
            scripts.forEach(name => {
                const option = document.createElement('option');
                option.value = name;
                option.textContent = name;
                select.appendChild(option);
            });
            await updateDescription();
        } else {
            console.warn('No scripts found');
            const option = document.createElement('option');
            option.value = '';
            option.textContent = 'No scripts available';
            select.appendChild(option);
        }
    } catch (error) {
        console.error('Error loading scripts:', error);
        document.getElementById('result').value = `Error loading scripts: ${error.message}`;
    }
}

async function updateDescription() {
    try {
        const select = document.getElementById('script-select');
        if (select.value) {
            console.log('Getting description for:', select.value);
            const desc = await window.pywebview.api.get_script_description(select.value);
            document.getElementById('script-description').value = desc;
        } else {
            document.getElementById('script-description').value = '';
        }
    } catch (error) {
        console.error('Error updating description:', error);
        document.getElementById('script-description').value = 'Error loading description';
    }
}

async function loadConfig() {
    try {
        console.log('Loading configuration...');
        config = await window.pywebview.api.load_configuration();
        console.log('Config loaded:', config);

        document.getElementById('script-select').value = config.selected_script || '';
        document.getElementById('additional-text').value = config.additional_text || '';
        document.getElementById('flags').value = config.flags || '';
        await updateDescription();
    } catch (error) {
        console.error('Error loading config:', error);
        config = { selected_script: '', additional_text: '', flags: '' };
    }
}

async function saveConfig() {
    try {
        config.selected_script = document.getElementById('script-select').value;
        config.additional_text = document.getElementById('additional-text').value;
        config.flags = document.getElementById('flags').value;

        console.log('Saving config:', config);
        const result = await window.pywebview.api.save_configuration(config);
        console.log('Config saved:', result);
    } catch (error) {
        console.error('Error saving config:', error);
    }
}

async function executeScript() {
    try {
        await saveConfig();

        const script = document.getElementById('script-select').value;
        const additional = document.getElementById('additional-text').value;
        const flags = document.getElementById('flags').value;
        const resultBox = document.getElementById('result');

        if (!script) {
            resultBox.value = "Please select a script first";
            return;
        }

        resultBox.value = "Executing...";
        console.log('Executing script:', { script, additional, flags });

        const response = await window.pywebview.api.execute_script(script, additional, flags);
        console.log('Execution response:', response);
        resultBox.value = response;
    } catch (error) {
        console.error('Error executing script:', error);
        document.getElementById('result').value = `Execution error: ${error.message}`;
    }
}

// Wait for pywebview to be ready
async function initializeApp() {
    console.log('Initializing app...');

    // Check if pywebview API is available
    if (typeof window.pywebview === 'undefined' || typeof window.pywebview.api === 'undefined') {
        console.error('PyWebView API not available');
        document.getElementById('result').value = 'Error: PyWebView API not available';
        return;
    }

    console.log('PyWebView API is available');

    // Load initial data
    await loadScripts();
    await loadConfig();

    // Set up event listeners
    document.getElementById('script-select').addEventListener('change', async () => {
        updateDescription();
        await saveConfig();
    });

    document.getElementById('additional-text').addEventListener('input', saveConfig);
    document.getElementById('flags').addEventListener('input', saveConfig);
    document.getElementById('execute-btn').addEventListener('click', executeScript);
}




// Try multiple initialization methods
document.addEventListener('pywebviewready', async function () {
    console.log('pywebviewready event fired');
    await initializeApp();
});

document.addEventListener('DOMContentLoaded', function () {
    console.log('DOMContentLoaded event fired');

    // If pywebview is already ready, initialize immediately
    if (typeof window.pywebview !== 'undefined' && typeof window.pywebview.api !== 'undefined') {
        console.log('PyWebView already ready, initializing...');
        initializeApp();
    } else {
        // Otherwise wait a bit and try again
        setTimeout(() => {
            if (typeof window.pywebview !== 'undefined' && typeof window.pywebview.api !== 'undefined') {
                console.log('PyWebView ready after timeout, initializing...');
                initializeApp();
            } else {
                console.error('PyWebView API still not available after timeout');
            }
        }, 1000);
    }
});

// Fallback initialization
window.addEventListener('load', function () {
    console.log('Window load event fired');

    if (typeof window.pywebview !== 'undefined' && typeof window.pywebview.api !== 'undefined') {
        // Only initialize if not already done
        if (!document.getElementById('script-select').options.length) {
            console.log('Fallback initialization...');
            initializeApp();
        }
    }
});