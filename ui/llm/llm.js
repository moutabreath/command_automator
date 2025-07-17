async function loadLLMConfig() {
    try {
        config = await window.pywebview.api.load_llm_configuration();
        document.getElementById('output-file-path').value = config.outpuFilePath || '';
        document.getElementById('save-to-files').checked = config.saveToFiles || '';
    } catch (error) {
        console.log('Error loading config:', error);
        config = { selected_script: '', additional_text: '', flags: '' };
    }
}

async function saveLLMConfig() {
    let config = {};
    try {
        const folderValue = document.getElementById('output-file-path').value;
        const isSaveToFilesChecked = document.getElementById('save-to-files').checked;

        config.outpuFilePath = folderValue;
        config.saveToFiles = isSaveToFilesChecked;
        await window.pywebview.api.save_llm_configuration(config);
    } catch (error) {
        console.log('Error saving config:', error);
    }
}

function init_basic_llm_dom_elements() {
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
    document.getElementById('select-image-btn').addEventListener('click', async () => {
        await initImageUploadEvent();
    });
    document.getElementById('output-file-path').addEventListener('input', async function (e) {
        console.log('Folder input changed:', e.target.value);
        await saveLLMConfig();
    });
    document.getElementById('save-to-files').addEventListener('change', async () => {
        await saveLLMConfig();
    });
    window.addEventListener('resize', () => {
        const imagePreviewDiv = document.getElementById('image-preview');
        if (imagePreviewDiv.style.display !== 'none' && imagePreviewDiv.hasChildNodes()) {
            const queryBox = document.getElementById('query-box');
            if(queryBox) {
                const queryBoxWidth = queryBox.offsetWidth;
                const thumbnailSize = queryBoxWidth / 4;
                imagePreviewDiv.style.width = `${thumbnailSize}px`;
                imagePreviewDiv.style.height = `${thumbnailSize}px`;
            }
        }
    });
}

async function initFolderUploadEvent() {
    const result = await window.pywebview.api.select_folder();
    if (result && result.length > 0) {
        document.getElementById('output-file-path').value = result[0];
    }
}

async function initImageUploadEvent() {
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = 'image/*'; // Accept only image files
    fileInput.onchange = handleImageUpload;
    fileInput.click(); // Trigger file selection dialog
}

function handleImageUpload(event) {
    const file = event.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function (e) {
            displayImageThumbnail(e.target.result);
        };
        reader.readAsDataURL(file);
    }
}

function displayImageThumbnail(imageData) {
    const imagePreviewDiv = document.getElementById('image-preview');
    imagePreviewDiv.innerHTML = ''; // Clear previous thumbnail

    if (imageData) {
        imagePreviewDiv.style.display = 'block';
        const queryBox = document.getElementById('query-box');
        const queryBoxWidth = queryBox.offsetWidth;
        const thumbnailSize = queryBoxWidth / 4;

        imagePreviewDiv.style.width = `${thumbnailSize}px`;
        imagePreviewDiv.style.height = `${thumbnailSize}px`;

        const img = document.createElement('img');
        img.src = imageData;
        imagePreviewDiv.appendChild(img);
    } else {
        imagePreviewDiv.style.display = 'none';
    }
}
function autoResize() {
    const queryBox = document.getElementById('query-box');
    queryBox.style.height = 'auto';
    queryBox.style.height = Math.max(24, queryBox.scrollHeight) + 'px';
}

async function callLLM() {
    const spinner = document.getElementById('spinner');
    spinner.style.display = 'flex';

    const query = document.getElementById('query-box').value.trim();
    const imageFilePath = ""
    const saveToFiles = document.getElementById('save-to-files').checked;
    const folderInput = document.getElementById('output-file-path').value
    if (!query) return;
    document.getElementById('send-btn').disabled = true;
    document.getElementById('query-box').disabled = true;


    // Append query and response to the response box
    const responseBox = document.getElementById('response-box');

    // Create query element
    const queryElem = document.createElement('div');
    queryElem.className = 'llm-query';
    queryElem.textContent = query;

    // Append to response box
    responseBox.appendChild(queryElem);
    document.getElementById('query-box').value = '';
    let response = '';
    try {
        response = await window.pywebview.api.call_llm(query, imageFilePath, saveToFiles, folderInput);
    } catch (e) {
        response = 'Error: ' + e;
    }
    finally {
        spinner.style.display = 'none';
    }

    // Create response element
    const responseElem = document.createElement('div');
    responseElem.className = 'llm-response';
    responseElem.style.userSelect = 'text';
    responseElem.textContent = response;
    responseBox.appendChild(responseElem);

    // Scroll to bottom
    responseBox.scrollTop = responseBox.scrollHeight;

    // Reset UI
 
    document.getElementById('send-btn').disabled = false;
    document.getElementById('query-box').disabled = false;
    document.getElementById('send-btn').disabled = false;
    document.getElementById('query-box').disabled = false;

    document.getElementById('query-box').focus();
}