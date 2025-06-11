const automatorBtn = document.getElementById('tab-automator-btn');
const llmBtn = document.getElementById('tab-llm-btn');
const automatorTab = document.getElementById('tab-automator');
const llmTab = document.getElementById('tab-llm');

automatorBtn.onclick = () => {
    automatorBtn.classList.add('selected');
    llmBtn.classList.remove('selected');
    automatorTab.classList.add('active');
    llmTab.classList.remove('active');
};
llmBtn.onclick = () => {
    llmBtn.classList.add('selected');
    automatorBtn.classList.remove('selected');
    llmTab.classList.add('active');
    automatorTab.classList.remove('active');
};
