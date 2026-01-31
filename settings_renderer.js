const { ipcRenderer } = require('electron');

// Settings state
let settings = {
    masterEnabled: true,
    humanizeEnabled: false,
    autoInjectEnabled: false,
    liveModeEnabled: false,
    darkMode: true
};

// DOM Elements
let masterToggle;
let darkModeToggle;
let humanizeToggle;
let autoInjectToggle;
let liveModeToggle;
let closeBtn;

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    masterToggle = document.getElementById('master-toggle');
    darkModeToggle = document.getElementById('dark-mode-toggle');
    humanizeToggle = document.getElementById('humanize-toggle');
    autoInjectToggle = document.getElementById('auto-inject-toggle');
    liveModeToggle = document.getElementById('live-mode-toggle');
    closeBtn = document.getElementById('close-btn');

    await loadSettings();
    setupEventListeners();
    updateUI();
});

function setupEventListeners() {
    // Master toggle
    masterToggle.addEventListener('change', () => {
        settings.masterEnabled = masterToggle.checked;
        saveSettings();
        ipcRenderer.send('settings-master-toggle', settings.masterEnabled);
        updateDisabledState();
    });

    // Dark mode toggle
    darkModeToggle.addEventListener('change', () => {
        settings.darkMode = darkModeToggle.checked;
        saveSettings();
        applyTheme();
    });

    // Human-like typing toggle
    humanizeToggle.addEventListener('change', () => {
        settings.humanizeEnabled = humanizeToggle.checked;
        saveSettings();
        ipcRenderer.send('settings-humanize-toggle', settings.humanizeEnabled);
    });

    // Auto-inject toggle
    autoInjectToggle.addEventListener('change', () => {
        settings.autoInjectEnabled = autoInjectToggle.checked;
        saveSettings();
        ipcRenderer.invoke('set-auto-inject', settings.autoInjectEnabled);
    });

    // Live mode toggle
    liveModeToggle.addEventListener('change', () => {
        settings.liveModeEnabled = liveModeToggle.checked;
        saveSettings();
        ipcRenderer.send('settings-live-mode-toggle', settings.liveModeEnabled);
    });

    // Close button
    closeBtn.addEventListener('click', () => {
        ipcRenderer.send('close-settings-window');
    });
}

async function loadSettings() {
    // Load from localStorage
    try {
        const saved = localStorage.getItem('ai-text-bot-settings');
        if (saved) {
            const parsed = JSON.parse(saved);
            settings = { ...settings, ...parsed };
        }
    } catch (e) {
        console.error('Failed to load settings from localStorage:', e);
    }

    // Sync with main process state
    try {
        const mainState = await ipcRenderer.invoke('get-settings-state');
        if (mainState) {
            settings.masterEnabled = mainState.masterEnabled;
            settings.autoInjectEnabled = mainState.autoInjectEnabled;
            settings.humanizeEnabled = mainState.humanizeEnabled;
            settings.liveModeEnabled = mainState.liveModeEnabled;
        }
    } catch (e) {
        console.error('Failed to sync settings with main process:', e);
    }
}

function saveSettings() {
    try {
        localStorage.setItem('ai-text-bot-settings', JSON.stringify(settings));
    } catch (e) {
        console.error('Failed to save settings:', e);
    }
}

function updateUI() {
    masterToggle.checked = settings.masterEnabled;
    darkModeToggle.checked = settings.darkMode;
    humanizeToggle.checked = settings.humanizeEnabled;
    autoInjectToggle.checked = settings.autoInjectEnabled;
    liveModeToggle.checked = settings.liveModeEnabled;
    applyTheme();
    updateDisabledState();
}

function updateDisabledState() {
    // Disable other toggles when master is off
    const isEnabled = settings.masterEnabled;
    humanizeToggle.disabled = !isEnabled;
    autoInjectToggle.disabled = !isEnabled;
    liveModeToggle.disabled = !isEnabled;

    // Visual feedback
    const behaviorItems = document.querySelectorAll('.setting-item');
    behaviorItems.forEach((item, index) => {
        // Skip master toggle (index 0) and dark mode (index 1)
        if (index > 1) {
            item.style.opacity = isEnabled ? '1' : '0.5';
        }
    });
}

function applyTheme() {
    const body = document.body;

    if (settings.darkMode) {
        body.classList.remove('light-mode');
    } else {
        body.classList.add('light-mode');
    }
}

// Listen for settings sync from main process
ipcRenderer.on('sync-settings', (event, newSettings) => {
    if (newSettings.masterEnabled !== undefined) {
        settings.masterEnabled = newSettings.masterEnabled;
    }
    if (newSettings.humanizeEnabled !== undefined) {
        settings.humanizeEnabled = newSettings.humanizeEnabled;
    }
    if (newSettings.autoInjectEnabled !== undefined) {
        settings.autoInjectEnabled = newSettings.autoInjectEnabled;
    }
    if (newSettings.liveModeEnabled !== undefined) {
        settings.liveModeEnabled = newSettings.liveModeEnabled;
    }
    if (newSettings.darkMode !== undefined) {
        settings.darkMode = newSettings.darkMode;
    }
    updateUI();
});
