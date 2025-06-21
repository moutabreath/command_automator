async function loadLLMConfig() {
    try {
        config = await window.pywebview.api.load_llm_configuration();
        document.getElementById('output-file-path').value = config.outpuFilePath || '';
        document.getElementById('save-to-files').value = config.saveToFiles || '';
    } catch (error) {
        console.error('Error loading config:', error);
        config = { selected_script: '', additional_text: '', flags: '' };
    }
}

async function saveLLMConfig() {
    let config = {};
    try {
        config.outpuFilePath = document.getElementById('output-file-path').value;
        config.saveToFiles = document.getElementById('save-to-files').value;
        const result = await window.pywebview.api.save_llm_configuration(config);
    } catch (error) {
        console.error('Error saving config:', error);
    }
}

function init_basic_llm_dom_elements(){
    const queryBox = document.getElementById('query-box');
    queryBox.addEventListener('input', autoResize);
    autoResize();
}

async function initLLM() {
    console.log('Initializing LLM...');

    if (typeof window.pywebview === 'undefined' || typeof window.pywebview.api === 'undefined') {
        console.error('PyWebView API not available');
        document.getElementById('result').value = 'Error: PyWebView API not available';
        return;
    }

    await loadLLMConfig();
    await initLLMEventListeners();
}


async function initLLMEventListeners() {
    document.getElementById('send-btn').addEventListener('click', async () => {
        await callLLM();
    });
    document.getElementById('query-box').addEventListener('keydown', async function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            await callLLM();
            e.preventDefault();
        }
    });
    document.getElementById('select-folder-btn').addEventListener('click', async () => {
        await initFolderUploadEvent();
    });
}

async function initFolderUploadEvent() {
    const result = await window.pywebview.api.select_folder();
    if (result && result.length > 0) {
        document.getElementById('output-file-path').value = result[0];
    }
}
function autoResize() {
    const queryBox = document.getElementById('query-box');
    queryBox.style.height = 'auto';
    queryBox.style.height = Math.max(24, queryBox.scrollHeight) + 'px';
}

async function callLLM() {
    const query = document.getElementById('query-box').value.trim();
    if (!query) return;

    // Optionally, disable UI while waiting
    document.getElementById('send-btn').disabled = true;
    document.getElementById('query-box').disabled = true;

    let response = '';
    try {
        response = await window.pywebview.api.call_llm(query);
    } catch (e) {
        response = 'Error: ' + e;
    }

    // Append query and response to the response box
    const responseBox = document.getElementById('response-box');
    responseBox.value += `You: ${query}\nLLM: ${response}\n\n`;
    responseBox.scrollTop = responseBox.scrollHeight;

    // Reset UI
    document.getElementById('query-box').value = '';
    document.getElementById('send-btn').disabled = false;
    document.getElementById('query-box').disabled = false;
    document.getElementById('query-box').focus();
}


