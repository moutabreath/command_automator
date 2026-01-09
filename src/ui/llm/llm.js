async function initLLM() {
    console.log('Initializing LLM...');

    await loadLLMConfig();
    await initLLMEventListeners();
}

async function loadLLMConfig() {
    const outputPath = document.getElementById('output-file-path');
    if (outputPath) {
        outputPath.value = (config?.llm?.output_file_path) || '';
    }
}

async function saveLLMConfig() {
    let llmConfig = {};
    try {
        const outputPathElement = document.getElementById('output-file-path');
        if (outputPathElement) {
            llmConfig.output_file_path = outputPathElement.value;
            await window.pywebview.api.save_configuration(llmConfig, 'llm');
        }
    } catch (error) {
        console.log('Error saving LLM config:', error);
    }
}

async function initLLMEventListeners() {
    const sendBtn = document.getElementById('send-btn');
    const queryBox = document.getElementById('query-box');
    const selectFolderBtn = document.getElementById('select-folder-btn');
    const selectImageBtn = document.getElementById('select-image-btn');
    const outputFilePath = document.getElementById('output-file-path');
    const cancelButton = document.getElementById('cancel-btn');

    if (!sendBtn || !queryBox) {
        console.error('Required LLM elements not found');
        return;
    }

    queryBox.addEventListener('input', autoResize);

    // Send button click
    sendBtn.addEventListener('click', async () => {
        await callLLM();
    });

    if (cancelButton) {
        cancelButton.addEventListener('click', async () => {
            await cancelLLMJob();
        });
    }
    // Enter key to send (Shift+Enter for new line)
    queryBox.addEventListener('keydown', async function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            await callLLM();
        }
        if (e.ctrlKey && e.altKey && e.key === 'j') {
            e.preventDefault();
            cancelLLMJob();
        }
    });

    // Folder selection
    if (selectFolderBtn) {
        selectFolderBtn.addEventListener('click', async () => {
            await initFolderUploadEvent();
        });
    }

    // Image selection
    if (selectImageBtn) {
        selectImageBtn.addEventListener('click', async () => {
            await initImageUploadEvent();
        });
    }

    // Output file path change
    if (outputFilePath) {
        outputFilePath.addEventListener('input', debounce(async function () {
            await saveLLMConfig();
        }, 500));
    }

    // Window resize handler for image preview
    window.addEventListener('resize', () => {
        const imagePreviewDiv = document.getElementById('image-preview');
        if (imagePreviewDiv && imagePreviewDiv.style.display !== 'none' && imagePreviewDiv.hasChildNodes()) {
            updateImagePreviewSize();
        }
    });
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
        showToast('Error selecting folder', 'error');
    }
}

async function initImageUploadEvent() {
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = 'image/*';
    fileInput.onchange = (event) => {
        handleImageUpload(event);
        fileInput.remove();
    };
    fileInput.click();
}

function handleImageUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    // Validate file size (10MB limit)
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
        showToast('Image file is too large. Please select an image under 10MB.', 'error');
        return;
    }

    // Validate file type
    if (!file.type.startsWith('image/')) {
        showToast('Please select a valid image file.', 'error');
        return;
    }

    const reader = new FileReader();
    reader.onload = function (e) {
        displayImageThumbnail(e.target.result);
    };
    reader.onerror = function (e) {
        console.error('Error reading file:', e);
        showToast('Failed to read the image file.', 'error');
    };
    reader.readAsDataURL(file);
}

function removeImageThumbnail() {
    const imagePreviewDiv = document.getElementById('image-preview');
    if (!imagePreviewDiv) return;
    imagePreviewDiv.innerHTML = '';
    imagePreviewDiv.style.display = 'none';
}

function updateImagePreviewSize() {
    const imagePreviewDiv = document.getElementById('image-preview');
    const queryBox = document.getElementById('query-box');

    if (queryBox && imagePreviewDiv && imagePreviewDiv.style.display !== 'none') {
        const queryBoxWidth = queryBox.offsetWidth;
        const thumbnailSize = Math.min(200, queryBoxWidth / 4);
        imagePreviewDiv.style.width = `${thumbnailSize}px`;
        imagePreviewDiv.style.height = `${thumbnailSize}px`;
    }
}

function displayImageThumbnail(imageData) {
    const imagePreviewDiv = document.getElementById('image-preview');
    if (!imagePreviewDiv) return;

    imagePreviewDiv.innerHTML = '';

    if (imageData) {
        imagePreviewDiv.style.display = 'block';
        updateImagePreviewSize();

        const img = document.createElement('img');
        img.src = imageData;
        img.alt = 'Selected image';
        imagePreviewDiv.appendChild(img);

        const removeBtn = document.createElement('button');
        removeBtn.innerHTML = '×';
        removeBtn.title = 'Remove image';
        removeBtn.className = 'remove-image-btn';
        removeBtn.type = 'button';
        removeBtn.addEventListener('click', removeImageThumbnail);
        imagePreviewDiv.appendChild(removeBtn);
    } else {
        imagePreviewDiv.style.display = 'none';
    }
}

function autoResize() {
    const queryBox = document.getElementById('query-box');
    if (!queryBox) return;

    const MIN_HEIGHT = 60;
    queryBox.style.height = 'auto';
    queryBox.style.height = Math.max(MIN_HEIGHT, queryBox.scrollHeight) + 'px';
}

async function cancelLLMJob() {
    try {
        await window.pywebview.api.cancel_llm_operation();
        showToast('LLM operation cancelled', 'info');
    } catch (error) {
        console.error('LLM cancel failed:', error);
        showToast('Failed to cancel operation', 'error');
    }
}

async function callLLM() {
    const queryBox = document.getElementById('query-box');
    const query = queryBox ? queryBox.value.trim() : '';
    const folderInput = document.getElementById('output-file-path');
    const outputPath = folderInput ? folderInput.value : '';

    if (!query) return;

    const sendBtn = document.getElementById('send-btn');
    const responseBox = document.getElementById('response-box');
    
    const imagePreview = document.getElementById('image-preview');

    if (!sendBtn || !queryBox || !responseBox) {
        console.error('Required DOM elements not found');
        return;
    }

    // Disable input during processing
    sendBtn.disabled = true;
    queryBox.disabled = true;

    // Create query element
    const queryElem = document.createElement('div');
    queryElem.className = 'llm-query';
    queryElem.textContent = query;

    // Append to response box
    responseBox.appendChild(queryElem);
    queryBox.value = '';
    autoResize();

    // Get image data if present
    const img = imagePreview ? imagePreview.querySelector('img') : null;
    const imageData = img ? img.src : '';

    const spinner = document.getElementById('spinner');
    const cancelBtn = document.getElementById('cancel-btn');
    showSpinnedAndCancelButton(spinner, cancelBtn);
    
    let response = '';
    try {
        response = await getMessageFromLLMResponse(query, imageData, outputPath);
    } catch (error) {
        console.error('LLM call failed:', error);
        response = 'Error: Failed to get response from LLM';
    }

    hideSpinneAndCancelButon(spinner, cancelBtn);
    
    // Create response element
    addReponseToResponseBox(response, responseBox);

    // Clear image after sending
    if (imageData) {
        removeImageThumbnail();
    }

    // Re-enable input
    sendBtn.disabled = false;
    queryBox.disabled = false;
    queryBox.focus();
}

function addReponseToResponseBox(response, responseBox) {
    const responseElem = document.createElement('div');
    responseElem.className = 'llm-response';
    responseElem.textContent = response;
    responseBox.appendChild(responseElem);

    // Scroll to bottom
    responseBox.scrollTop = responseBox.scrollHeight;
}

function hideSpinneAndCancelButon(spinner, cancelBtn) {
    spinner.classList.remove('visible');
    document.body.classList.remove('spinner-active');

    if (cancelBtn) {
        cancelBtn.style.display = 'none';
    }
}

function showSpinnedAndCancelButton(spinner, cancelBtn) {
    
    spinner.classList.add('visible');
    document.body.classList.add('spinner-active');

    if (cancelBtn) {
        cancelBtn.style.display = 'block';
        console.log('Cancel button display set to block');
    } else {
        console.error('Cancel button not found!');
    }
    return { spinner, cancelBtn };
}

async function getMessageFromLLMResponse(prompt, imageData, outputPath) {
    let message = 'Unknown error occurred';
    try {
        const userId = window.userId || window.user_id || '';
        let resp = await window.pywebview.api.call_llm(prompt, imageData, outputPath, userId);

        // Normalize response to object
        if (typeof resp === 'string') {
            try {
                resp = JSON.parse(resp);
            } catch (e) {
                console.error('call_llm returned non-JSON string', resp);
                return resp; // Return as-is if not JSON
            }
        }

        if (!resp || typeof resp !== 'object') {
            console.error('Unexpected call_llm response:', resp);
            return 'Invalid response from LLM';
        }

        const { text = '', code = '' } = resp;

        // Handle result codes
        switch (code) {
            case 'OK':
                if (!text || text === '') {
                    return 'LLM returned empty message';
                }
                return text;
            case 'ERROR_MODEL_OVERLOADED':
                return 'Model overloaded. Please try again later.';
            case 'ERROR_LOADING_IMAGE_TO_MODEL':
                return 'Failed loading image for model.';
            case 'ERROR_COMMUNICATING_WITH_LLM':
                return text || 'Error communicating with LLM';
            default:
                return text || 'Error communicating with LLM';
        }
    } catch (err) {
        console.error('callLLM failed:', err);
        return 'Unknown error occurred';
    }
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = 'position:fixed;top:20px;right:20px;padding:15px;background:#333;color:#fff;border-radius:4px;z-index:9999;';
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}