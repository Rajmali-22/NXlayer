const { ipcRenderer } = require('electron');

let currentGeneratedText = '';
let promptInput = null;
let generateBtn = null;
let statusDiv = null;

document.addEventListener('DOMContentLoaded', () => {
    promptInput = document.getElementById('prompt-input');
    generateBtn = document.getElementById('generate-btn');
    statusDiv = document.getElementById('status');

    // Generate button click
    generateBtn.addEventListener('click', handleGenerate);

    // Enter key to generate
    promptInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleGenerate();
        }
    });

});


async function handleGenerate() {
    const prompt = promptInput.value.trim();
    const toneSelect = document.getElementById('tone-select');
    const tone = toneSelect ? toneSelect.value : 'professional';

    console.log('=== Frontend: Generate Request ===');
    console.log('Prompt:', prompt);
    console.log('Selected Tone:', tone);

    if (!prompt) {
        showStatus('Please enter a prompt', 'error');
        return;
    }

    generateBtn.disabled = true;
    showStatus('Generating text...', 'loading');

    try {
        const context = { tone: tone };
        console.log('Sending to main process - Prompt:', prompt, 'Context:', context);
        const result = await ipcRenderer.invoke('generate-text', prompt, context);

        if (result.error) {
            showStatus('Error: ' + result.error, 'error');
        } else if (result.text) {
            currentGeneratedText = result.text;
            // Send to main process for global shortcut
            ipcRenderer.send('set-generated-text', result.text);
            // Show inline suggestion near cursor
            ipcRenderer.invoke('show-inline-suggestion', result.text);
            showStatus('Ctrl+Shift+P to paste | Esc to cancel', 'success');
        } else {
            showStatus('Unexpected response format', 'error');
        }
    } catch (error) {
        showStatus('Error: ' + error.message, 'error');
        console.error('Generation error:', error);
    } finally {
        generateBtn.disabled = false;
    }
}

function showStatus(message, type) {
    statusDiv.textContent = message;
    statusDiv.className = 'status ' + (type || '');
    statusDiv.classList.remove('hidden');
}
