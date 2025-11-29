async function loadLLMConfig() {
    try {
        let llmConfig = await window.pywebview.api.load_llm_configuration();
        const outputPath = document.getElementById('output-file-path');
        if (outputPath) {
            outputPath.value = llmConfig.outputFilePath || '';
        }
    } catch (error) {
        console.log('Error loading config:', error);
    }
}

async function saveLLMConfig() {
    let llmConfig = {};
    try {
        const outputPathElement = document.getElementById('output-file-path');
        if (outputPathElement) {
            llmConfig.outputFilePath = outputPathElement.value;
            await window.pywebview.api.save_llm_configuration(llmConfig);
        }
        } catch (error) {
            console.log('Error saving config:', error);
        }
}

function init_basic_llm_dom_elements() {
    const queryBox = document.getElementById('query-box');
    if (!queryBox) return;

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
    window.addEventListener('resize', () => {
        const imagePreviewDiv = document.getElementById('image-preview');
        if (imagePreviewDiv.style.display !== 'none' && imagePreviewDiv.hasChildNodes()) {
            const queryBox = document.getElementById('query-box');
            if (queryBox) {
                const queryBoxWidth = queryBox.offsetWidth;
                const thumbnailSize = queryBoxWidth / 4;
                imagePreviewDiv.style.width = `${thumbnailSize}px`;
                imagePreviewDiv.style.height = `${thumbnailSize}px`;
            }
        }
    });
}

async function initFolderUploadEvent() {
    try {
        const result = await window.pywebview.api.select_folder();
        if (result && result.length > 0) {
            const outputPath = document.getElementById('output-file-path');
            if (outputPath) {
                outputPath.value = result[0];
                await saveLLMConfig();
            }
        }
    } catch (error) {
        console.error('Error selecting folder:', error);
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
        // Validate file size (e.g., 10MB limit)
        const maxSize = 10 * 1024 * 1024; // 10MB
        if (file.size > maxSize) {
            alert('Image file is too large. Please select an image under 10MB.');
            return;
        }
        
        // Validate file type
        if (!file.type.startsWith('image/')) {
            alert('Please select a valid image file.');
            return;
        }
        
        const reader = new FileReader();
        reader.onload = function (e) {
            displayImageThumbnail(e.target.result);
        };
        reader.onerror = function (e) {
            console.error('Error reading file:', e);
            alert('Failed to read the image file.');
        };
        reader.readAsDataURL(file);
    }
}
function removeImageThumbnail() {
    const imagePreviewDiv = document.getElementById('image-preview');
    if (!imagePreviewDiv) return;
    imagePreviewDiv.innerHTML = '';
    imagePreviewDiv.style.display = 'none';
}

function displayImageThumbnail(imageData) {
    const imagePreviewDiv = document.getElementById('image-preview');
    if (!imagePreviewDiv) return;

    imagePreviewDiv.innerHTML = ''; // Clear previous thumbnail

    if (imageData) {
        imagePreviewDiv.style.display = 'block';

        const queryBox = document.getElementById('query-box');
        if (queryBox){
            const queryBoxWidth = queryBox.offsetWidth;
            const thumbnailSize = queryBoxWidth / 4;

            imagePreviewDiv.style.width = `${thumbnailSize}px`;
            imagePreviewDiv.style.height = `${thumbnailSize}px`;
        }

        const img = document.createElement('img');
        img.src = imageData;
        imagePreviewDiv.appendChild(img);

        const removeBtn = document.createElement('button');
        removeBtn.innerHTML = '&times;'; // A nicer 'x' character
        removeBtn.title = 'Remove image';
        removeBtn.className = 'remove-image-btn';

        removeBtn.addEventListener('click', removeImageThumbnail);
        imagePreviewDiv.appendChild(removeBtn);
    } else {
        imagePreviewDiv.style.display = 'none';
    }
}

function autoResize() {
    const queryBox = document.getElementById('query-box');
    if (!queryBox) return;

    const MIN_HEIGHT = 24;
    queryBox.style.height = 'auto';
    queryBox.style.height = Math.max(MIN_HEIGHT, queryBox.scrollHeight) + 'px';
}

async function callLLM() {
    const query = document.getElementById('query-box').value.trim();
    const folderInput = document.getElementById('output-file-path').value;
    if (!query) return;

    const sendBtn = document.getElementById('send-btn');
    const queryBox = document.getElementById('query-box');
    const responseBox = document.getElementById('response-box');
    const spinner = document.getElementById('spinner');
    const imagePreview = document.getElementById('image-preview');
    
    if (!sendBtn || !queryBox || !responseBox || !spinner) {
        console.error('Required DOM elements not found');
        return;
    }

    // Create query element
    const queryElem = document.createElement('div');
    queryElem.className = 'llm-query';
    queryElem.textContent = query;

    // Append to response box
    responseBox.appendChild(queryElem);
    document.getElementById('query-box').value = '';
    let response = '';

    const img = imagePreview.querySelector('img');
    const imageData = img ? img.src : '';
    spinner.style.visibility = 'visible';
    
    response = await getMessageFromLLMResponse(query, imageData, folderInput);
    spinner.style.visibility = 'hidden';

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
    document.getElementById('query-box').focus();
}

async function getMessageFromLLMResponse(prompt, imageData, outputPath) {
    let message = 'Unknown error occurred';
    try {
        // call backend
        let resp = await window.pywebview.api.call_llm(prompt, imageData, outputPath, userId);

        // backend may return a JSON string or an object; normalize to object
        if (typeof resp === 'string') {
            try {
                resp = JSON.parse(resp);
            } catch (e) {
                console.error('call_llm returned non-JSON string', resp);
                throw e;
            }
        }

        if (!resp || typeof resp !== 'object') {
            console.error('Unexpected call_llm response:', resp);
            return 'Invalid response from LLM';
        }

        const { text = '', code = '' } = resp;

        // handle result codes (adjust strings to match enum names)
        message = text;
        switch (code) {
            case 'OK':
                if (message === undefined || message === ""){
                    return "LLM returned empty message";
                }
                return message;
            case 'ERROR_MODEL_OVERLOADED':
                message = 'Model overloaded. Please try again later.';
                break;
            case 'ERROR_LOADING_IMAGE_TO_MODEL':
                message = 'Failed loading image for model.';
                break;
            case 'ERROR_COMMUNICATING_WITH_LLM':
                message = text || 'Error communicating with LLM';
                break;
            default:               
                message = text || 'Error communicating with LLM';
                break;
        }
        
    } catch (err) {
        console.error('callLLM failed:', err);
        message = 'Unknown error occurred';
    }
    
    return message;
}