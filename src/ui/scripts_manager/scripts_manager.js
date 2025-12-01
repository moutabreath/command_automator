document.addEventListener('pywebviewready', async function () {
    console.log('pywebviewready event fired');
    initAttempts = 0; // Reset attempts since pywebview is ready
    await tryInitApp();
});


document.addEventListener('DOMContentLoaded', function () {
    console.log('DOM loaded, starting initialization');

    // Clear result box initially
    const resultElement = document.getElementById('result');
    if (resultElement) {
        resultElement.value = '';
    }
    tryInitApp();
});

async function loadScripts() {
    try {
        const scripts = await window.pywebview.api.load_scripts();
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
        const option = document.createElement('option');
        option.value = '';
        option.textContent = 'No scripts available';
        select.appendChild(option);
    }
}

async function updateDescription() {
    try {
        const select = document.getElementById('script-select');
        if (select.value) {
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

async function loadScriptsManagerConfig() {
    try {
        let scriptsManagerConfig = await window.pywebview.api.load_commands_configuration();
        if (!scriptsManagerConfig || scriptsManagerConfig === "" || scriptsManagerConfig === " ") {
            return;
        }
        document.getElementById('script-select').value = scriptsManagerConfig.selected_script || '';
        document.getElementById('additional-text').value = scriptsManagerConfig.additional_text || '';
        document.getElementById('flags').value = scriptsManagerConfig.flags || '';
        await updateDescription();
    } catch (error) {
        console.log('Error loading config:', error);
        scriptsManagerConfig = { selected_script: '', additional_text: '', flags: '' };
    }
}

async function saveAutomatorConfig() {
    try {
        let scriptsManagerConfig = {}
        scriptsManagerConfig.selected_script = document.getElementById('script-select').value;
        scriptsManagerConfig.additional_text = document.getElementById('additional-text').value;
        scriptsManagerConfig.flags = document.getElementById('flags').value;
        const result = await window.pywebview.api.save_commands_configuration(scriptsManagerConfig);
    } catch (error) {
        console.log('Error saving config:', error);
    }
}

async function executeScript() {
    const spinner = document.getElementById('spinner');
    spinner.style.visibility = 'visible';
    try {
        const script = document.getElementById('script-select').value;
        const additional = document.getElementById('additional-text').value;
        const flags = document.getElementById('flags').value;
        const resultBox = document.getElementById('result');

        if (!script) {
            resultBox.value = "Please select a script first";
            return;
        }

        resultBox.value = "Executing...";

        const response = await window.pywebview.api.execute_script(script, additional, flags);
        resultBox.value = response;
    } catch (error) {
        console.error('Error executing script:', error);
        document.getElementById('result').value = `Execution error: ${error.message}`;
    }
    finally {
        spinner.style.visibility = 'hidden';
    }
}

async function initScriptsManager() {
    if (typeof window.pywebview === 'undefined' || typeof window.pywebview.api === 'undefined') {
        console.log('PyWebView API not yet available, waiting...');
        return false;
    }

    console.log('PyWebView API is available, initializing Commands Automator');

    try {
        // Clear any previous error messages
        const resultElement = document.getElementById('result');
        if (resultElement && resultElement.value.includes('Error:')) {
            resultElement.value = '';
        }

        await loadScripts();
        await loadScriptsManagerConfig();
        await initScriptsManagerEventHandlers();
        return true;
    } catch (error) {
        console.error('Error initializing Commands Automator:', error);
        return false;
    }
}

async function initScriptsManagerEventHandlers() {
    document.getElementById('script-select').addEventListener('change', async () => {
        await updateDescription();
        await saveAutomatorConfig();
    });

    document.getElementById('additional-text').addEventListener('input', async () => {
        await saveAutomatorConfig();
    });
    document.getElementById('flags').addEventListener('input', async () => {
        await saveAutomatorConfig();
    });
    document.getElementById('execute-btn').addEventListener('click', async () => {
        await executeScript();
    });
}

async function initApp() {
    console.log('Initializing application...');

    const automatorReady = await initScriptsManager();
    if (!automatorReady) {
        console.log('Commands Automator not ready, will retry later');
        return false;
    }

    if (typeof initLLM === 'function') await initLLM();
    if (typeof initUser === 'function') await initUser();
    if (typeof initJobTracking === 'function') await initJobTracking();

    console.log('Application initialized successfully');
    return true;
}



let initAttempts = 0;
const maxInitAttempts = 10;

async function tryInitApp() {
    initAttempts++;
    console.log(`Initialization attempt ${initAttempts}`);

    if (typeof window.pywebview !== 'undefined' && typeof window.pywebview.api !== 'undefined') {
        const success = await initApp();
        if (success) {
            console.log('Application initialized successfully');
            return;
        }
    }

    if (initAttempts < maxInitAttempts) {
        console.log(`PyWebView API not ready, retrying in 500ms (attempt ${initAttempts}/${maxInitAttempts})`);
        setTimeout(tryInitApp, 500);
    } else {
        console.error('Failed to initialize after maximum attempts');
        const resultElement = document.getElementById('result');
        if (resultElement) {
            resultElement.value = 'Error: Failed to connect to application backend';
        }
    }
}

