let config = {};

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
        document.getElementById('result').value = `Error loading scripts: ${error.message}`;
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

async function loadAutomatorConfig() {
    try {
        config = await window.pywebview.api.load_commands_configuration();
        if (config === "" || config === " "){
            return;
        }
        document.getElementById('script-select').value = config.selected_script || '';
        document.getElementById('additional-text').value = config.additional_text || '';
        document.getElementById('flags').value = config.flags || '';
        await updateDescription();
    } catch (error) {
        console.log('Error loading config:', error);
        config = { selected_script: '', additional_text: '', flags: '' };
    }
}

async function saveAutomatorConfig() {
    try {
        config.selected_script = document.getElementById('script-select').value;
        config.additional_text = document.getElementById('additional-text').value;
        config.flags = document.getElementById('flags').value;
        const result = await window.pywebview.api.save_commands_configuration(config);
    } catch (error) {
        console.log('Error saving config:', error);
    }
}

async function executeScript() {
    const spinner = document.getElementById('spinner');
    spinner.style.display = 'flex';
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
        spinner.style.display = 'none';
    }
}

async function initCommandsAutomator() {
    if (typeof window.pywebview === 'undefined' || typeof window.pywebview.api === 'undefined') {
        console.error('PyWebView API not available');
        document.getElementById('result').value = 'Error: PyWebView API not available';
        return;
    }

    console.log('PyWebView API is available');

    await loadScripts();
    await loadAutomatorConfig();
    await initCommandsAutomatorEventHandlers();

}

async function initCommandsAutomatorEventHandlers() {
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
    await initCommandsAutomator();
    await initLLM();
}


document.addEventListener('pywebviewready', async function () {
    console.log('pywebviewready event fired');
    await initCommandsAutomator();
});

document.addEventListener('DOMContentLoaded', function () {
    init_basic_llm_dom_elements();
    if (typeof window.pywebview !== 'undefined' && typeof window.pywebview.api !== 'undefined') {
        console.log('PyWebView already ready, initializing...');
        initApp();
    } else {
        setTimeout(() => {
            if (typeof window.pywebview !== 'undefined' && typeof window.pywebview.api !== 'undefined') {
                initApp();
            } else {
                console.error('PyWebView API still not available after timeout');
            }
        }, 1000);
    }
});
