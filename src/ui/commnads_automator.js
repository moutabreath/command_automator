
let initAttempts = 0;
const maxInitAttempts = 10;


async function tryInitApp() {
    initAttempts++;
    console.log(`Initialization attempt ${initAttempts}`);

    if (typeof window.pywebview !== 'undefined' && typeof window.pywebview.api !== 'undefined') {
        await initApp();
    }
    else {
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
}


async function initApp() {
    console.log('Initializing application modules...');

    await initScriptsManager();
    await initLLM();
    await initUser();
}


tryInitApp();