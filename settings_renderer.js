const { ipcRenderer } = require('electron');

// Settings state
let settings = {
    humanizeEnabled: false,
    autoInjectEnabled: false,
    darkMode: true
};

// DOM Elements
let darkModeToggle;
let humanizeToggle;
let autoInjectToggle;
let closeBtn;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    darkModeToggle = document.getElementById('dark-mode-toggle');
    humanizeToggle = document.getElementById('humanize-toggle');
    autoInjectToggle = document.getElementById('auto-inject-toggle');
    closeBtn = document.getElementById('close-btn');

    loadSettings();
    setupEventListeners();
    updateUI();
});

function setupEventListeners() {
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

    // Close button
    closeBtn.addEventListener('click', () => {
        ipcRenderer.send('close-settings-window');
    });
}

function loadSettings() {
    try {
        const saved = localStorage.getItem('ai-text-bot-settings');
        if (saved) {
            const parsed = JSON.parse(saved);
            settings = { ...settings, ...parsed };
        }
    } catch (e) {
        console.error('Failed to load settings:', e);
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
    darkModeToggle.checked = settings.darkMode;
    humanizeToggle.checked = settings.humanizeEnabled;
    autoInjectToggle.checked = settings.autoInjectEnabled;
    applyTheme();
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
    if (newSettings.humanizeEnabled !== undefined) {
        settings.humanizeEnabled = newSettings.humanizeEnabled;
    }
    if (newSettings.autoInjectEnabled !== undefined) {
        settings.autoInjectEnabled = newSettings.autoInjectEnabled;
    }
    if (newSettings.darkMode !== undefined) {
        settings.darkMode = newSettings.darkMode;
    }
    updateUI();
});
