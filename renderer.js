const { ipcRenderer } = require('electron');

let currentGeneratedText = '';
let promptInput = null;
let generateBtn = null;
let statusDiv = null;
let micBtn = null;

// Voice recording state
let isRecording = false;

document.addEventListener('DOMContentLoaded', () => {
    promptInput = document.getElementById('prompt-input');
    generateBtn = document.getElementById('generate-btn');
    statusDiv = document.getElementById('status');
    micBtn = document.getElementById('mic-btn');

    // Generate button click
    generateBtn.addEventListener('click', handleGenerate);

    // Enter key to generate
    promptInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleGenerate();
        }
    });

    // Voice input - click to record (Python handles duration)
    if (micBtn) {
        micBtn.addEventListener('click', startRecording);
    }

    // Listen for voice shortcut from main process (Ctrl+Shift+V)
    ipcRenderer.on('start-voice-recording', () => {
        console.log('Voice shortcut received');
        startRecording();
    });

    // Hold-to-talk events
    ipcRenderer.on('voice-recording-started', () => {
        console.log('Hold-to-talk: Recording started');
        isRecording = true;
        if (micBtn) {
            micBtn.classList.add('recording');
            micBtn.disabled = true;
        }
        showStatus('Recording... Release Ctrl+Shift+V to stop', 'loading');
    });

    ipcRenderer.on('voice-recording-stopping', () => {
        console.log('Hold-to-talk: Recording stopping');
        showStatus('Processing speech...', 'loading');
    });

    ipcRenderer.on('voice-recording-result', (event, result) => {
        console.log('Hold-to-talk: Result received', result);
        isRecording = false;
        if (micBtn) {
            micBtn.classList.remove('recording');
            micBtn.disabled = false;
        }

        if (result.error) {
            showStatus('Error: ' + result.error, 'error');
        } else if (result.text) {
            // Append transcribed text to prompt input
            const currentText = promptInput.value.trim();
            if (currentText) {
                promptInput.value = currentText + ' ' + result.text;
            } else {
                promptInput.value = result.text;
            }
            promptInput.focus();
            showStatus('Voice input ready. Press Enter or Generate.', 'success');
        } else {
            showStatus('No speech detected. Try again.', 'error');
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

// Voice recording function - uses Python for recording and Google Speech Recognition (free)
async function startRecording() {
    if (isRecording) return;

    isRecording = true;
    micBtn.classList.add('recording');
    micBtn.disabled = true;
    showStatus('Listening... Speak now (stops on silence)', 'loading');

    try {
        // Call Python to record and transcribe
        const result = await ipcRenderer.invoke('transcribe-audio', {
            timeout: 30,       // Max wait for speech to start
            phraseTimeout: 20  // Max recording duration
        });

        if (result.error) {
            showStatus('Error: ' + result.error, 'error');
        } else if (result.text) {
            // Append transcribed text to prompt input
            const currentText = promptInput.value.trim();
            if (currentText) {
                promptInput.value = currentText + ' ' + result.text;
            } else {
                promptInput.value = result.text;
            }
            promptInput.focus();
            showStatus('Voice input ready. Press Enter or Generate.', 'success');
        } else {
            showStatus('No speech detected. Try again.', 'error');
        }
    } catch (error) {
        console.error('Voice recording error:', error);
        showStatus('Voice input failed: ' + error.message, 'error');
    } finally {
        isRecording = false;
        micBtn.classList.remove('recording');
        micBtn.disabled = false;
    }
}

function stopRecording() {
    // Python handles the recording timeout automatically
    // This is kept for compatibility with the event listeners
}
