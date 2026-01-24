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

    // Ctrl+P to accept and paste
    document.addEventListener('keydown', async (e) => {
        if (e.ctrlKey && e.key === 'p') {
            e.preventDefault();
            if (currentGeneratedText) {
                await acceptAndPaste();
            }
        }
    });

});


async function handleGenerate() {
    const prompt = promptInput.value.trim();
    
    if (!prompt) {
        showStatus('Please enter a prompt', 'error');
        return;
    }

    generateBtn.disabled = true;
    showStatus('Generating email...', 'loading');
    hideOutput();

    try {
        const result = await ipcRenderer.invoke('generate-email', prompt);
        
        if (result.error) {
            showStatus('Error: ' + result.error, 'error');
        } else if (result.email) {
            currentGeneratedText = result.email;
            // Send to main process for global shortcut
            ipcRenderer.send('set-generated-text', result.email);
            displayOutput(result.email);
            showStatus('Email generated! Press Ctrl+Shift+P to accept and paste', 'success');
            
            // Focus back on input
            promptInput.focus();
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

function displayOutput(text) {
    // Send text to main process to display in output window
    ipcRenderer.invoke('show-output', text);
}

function hideOutput() {
    // Hide the output window
    ipcRenderer.invoke('hide-output');
    currentGeneratedText = '';
}

async function acceptAndPaste() {
    if (!currentGeneratedText) return;
    
    try {
        showStatus('Pasting text...', 'loading');
        
        // Hide the output first
        hideOutput();
        
        // Small delay to ensure window loses focus
        await new Promise(resolve => setTimeout(resolve, 150));
        
        // Type the text at cursor position
        const result = await ipcRenderer.invoke('type-text', currentGeneratedText);
        
        if (result.success) {
            if (result.method === 'clipboard' || result.method === 'clipboard-fallback') {
                showStatus('Text copied to clipboard! Press Ctrl+V to paste.', 'success');
            } else {
                showStatus('Text pasted successfully!', 'success');
            }
            promptInput.value = '';
            setTimeout(() => {
                statusDiv.classList.add('hidden');
            }, 3000);
        } else {
            showStatus('Error pasting text: ' + (result.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        showStatus('Error: ' + error.message, 'error');
        console.error('Paste error:', error);
    }
}

function showStatus(message, type) {
    statusDiv.textContent = message;
    statusDiv.className = 'status ' + (type || '');
    statusDiv.classList.remove('hidden');
}
