// resources/llm_prompt.js
document.addEventListener('pywebviewready', () => {
    document.getElementById('send-btn').addEventListener('click', callLLM);
    document.getElementById('query-box').addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            callLLM();
            e.preventDefault();
        }
    });
});

async function callLLM() {
    const query = document.getElementById('query-box').value.trim();
    if (!query) return;

    // Optionally, disable UI while waiting
    document.getElementById('send-btn').disabled = true;
    document.getElementById('query-box').disabled = true;

    // Call backend (replace with your actual backend method)
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