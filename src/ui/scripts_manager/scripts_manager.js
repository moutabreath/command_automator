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
    }
}

async function saveAutomatorConfig() {
    try {
        let scriptsManagerConfig = {};
        scriptsManagerConfig.selected_script = document.getElementById('script-select').value;
        scriptsManagerConfig.additional_text = document.getElementById('additional-text').value;
        scriptsManagerConfig.flags = document.getElementById('flags').value;
        await window.pywebview.api.save_commands_configuration(scriptsManagerConfig);
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
    try {
        // Validate required DOM elements exist
        const requiredElements = [
            'script-select', 'script-description', 'additional-text', 
            'flags', 'result', 'execute-btn', 'spinner'
        ];
        const missingElements = requiredElements.filter(id => !document.getElementById(id));
        if (missingElements.length > 0) {
            console.error('Missing required DOM elements:', missingElements);
            return false;
        }
        
        // Clear any previous error messages
        const resultElement = document.getElementById('result');
        if (resultElement.value.includes('Error:')) {
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

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

async function initScriptsManagerEventHandlers() {
    document.getElementById('script-select').addEventListener('change', async () => {
        await updateDescription();
        await saveAutomatorConfig();
    });

    const debouncedSave = debounce(saveAutomatorConfig, 500);
    document.getElementById('additional-text').addEventListener('input', () => {
        debouncedSave();
    });
    document.getElementById('flags').addEventListener('input', () => {
        debouncedSave();
    });
    document.getElementById('execute-btn').addEventListener('click', async () => {
        await executeScript();
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