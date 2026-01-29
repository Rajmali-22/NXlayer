const { app, BrowserWindow, globalShortcut, ipcMain, clipboard } = require('electron');
const { spawn } = require('child_process');
const path = require('path');

// Try to load robotjs, but handle errors gracefully
let robot = null;
try {
  robot = require('robotjs');
} catch (error) {
  console.warn('robotjs not available:', error.message);
  console.warn('Falling back to clipboard method. Please run: npm run rebuild');
}

// Load uiohook for key release detection (hold-to-talk)
let uIOhook = null;
try {
  const uiohook = require('uiohook-napi');
  uIOhook = uiohook.uIOhook;
} catch (error) {
  // uiohook-napi not available - hold-to-talk will be disabled
}

let mainWindow = null;
let outputWindow = null;
let isWindowVisible = false;

// Voice recording state
let voiceProcess = null;
let isVoiceRecording = false;

function createWindow() {
  const { screen } = require('electron');
  const primaryDisplay = screen.getPrimaryDisplay();
  const { width, height } = primaryDisplay.workAreaSize;
  
  // Calculate position at bottom center
  const windowWidth = 800;
  const windowHeight = 200;
  const x = Math.floor((width - windowWidth) / 2);
  const y = height - windowHeight;
  
  // Create transparent overlay window
  mainWindow = new BrowserWindow({
    width: windowWidth,
    height: windowHeight,
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    skipTaskbar: true,
    resizable: false,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      enableRemoteModule: true
    },
    // Position at bottom of screen
    x: x,
    y: y
  });

  mainWindow.loadFile('index.html');
  
  // Show window initially so user knows it's running
  // User can hide it with Ctrl+Shift+Space
  mainWindow.show();
  isWindowVisible = true;
  
  // Prevent window from being minimized
  mainWindow.setMinimumSize(800, 200);

  // Handle window close
  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Allow mouse events on the window
  mainWindow.setIgnoreMouseEvents(false);
}

function createOutputWindow() {
  // Create a compact inline suggestion popup (like autocomplete)
  outputWindow = new BrowserWindow({
    width: 450,
    height: 180,
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    skipTaskbar: true,
    resizable: false,
    minimizable: false,
    maximizable: false,
    closable: false,
    focusable: false,  // Don't steal focus from target app
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      enableRemoteModule: true
    }
  });

  outputWindow.loadFile('output.html');
  outputWindow.hide();

  outputWindow.on('closed', () => {
    outputWindow = null;
  });
}

// Register global shortcut to toggle window (Ctrl+Shift+Space)
app.whenReady().then(() => {
  createWindow();
  createOutputWindow();

  const toggleShortcut = globalShortcut.register('CommandOrControl+Shift+Space', () => {
    if (mainWindow) {
      if (isWindowVisible) {
        mainWindow.hide();
        isWindowVisible = false;
      } else {
        mainWindow.show();
        mainWindow.focus();
        isWindowVisible = true;
      }
    }
  });
  
  // Register Ctrl+Shift+P to paste generated text using Rust injection
  const pasteShortcut = globalShortcut.register('CommandOrControl+Shift+P', async () => {
    if (lastGeneratedText) {
      // Hide windows first
      if (mainWindow) {
        mainWindow.hide();
        isWindowVisible = false;
      }
      if (outputWindow) {
        outputWindow.hide();
      }

      // Use Rust-based keyboard injection
      const rustInjectPath = path.join(__dirname, 'keyboard-inject', 'target', 'release', 'keyboard-inject.exe');
      const fs = require('fs');

      // Also check for debug build (in case release wasn't built)
      const rustInjectPathDebug = path.join(__dirname, 'keyboard-inject', 'target', 'debug', 'keyboard-inject.exe');
      const actualPath = fs.existsSync(rustInjectPath) ? rustInjectPath :
                        (fs.existsSync(rustInjectPathDebug) ? rustInjectPathDebug : null);

      if (actualPath) {
        try {
          // Small delay to ensure focus is on target app
          await new Promise(resolve => setTimeout(resolve, 150));

          // Escape the text for command line
          let escapedText = lastGeneratedText
            .replace(/\\/g, '\\\\')  // Escape backslashes first
            .replace(/"/g, '\\"')     // Escape quotes
            .replace(/\n/g, '\\n')   // Convert newlines to \n strings
            .replace(/\r/g, '\\r')   // Convert carriage returns to \r strings
            .replace(/\t/g, '\\t');  // Convert tabs to \t strings (Rust will convert to spaces)

          // Wrap in quotes for command line
          escapedText = `"${escapedText}"`;

          // Call Rust injector - pass text as argument
          const { exec } = require('child_process');
          const command = `"${actualPath}" ${escapedText}`;

          exec(command, { maxBuffer: 10 * 1024 * 1024 }, (error, stdout, stderr) => {
            if (error) {
              // Fallback: clipboard + Ctrl+V
              try {
                clipboard.writeText(lastGeneratedText);
                if (robot) {
                  setTimeout(() => {
                    try {
                      robot.keyTap('v', 'control');
                    } catch (robotError) {
                      // robotjs paste failed
                    }
                  }, 50);
                }
              } catch (clipError) {
                // Clipboard write failed
              }
              lastGeneratedText = '';
            } else {
              lastGeneratedText = '';
            }
          });
        } catch (error) {
          lastGeneratedText = '';
        }
      } else {
        // Rust injector not built - fallback to clipboard
        try {
          clipboard.writeText(lastGeneratedText);
          if (robot) {
            await new Promise(resolve => setTimeout(resolve, 50));
            robot.keyTap('v', 'control');
          }
        } catch (err) {
          // Fallback failed
        }
        lastGeneratedText = '';
      }
    }
  });
  
  // Register Ctrl+Shift+V for voice input (hold-to-talk)
  const voiceShortcut = globalShortcut.register('CommandOrControl+Shift+V', async () => {
    if (isVoiceRecording) return; // Already recording
    startVoiceRecording();
  });

  // Set up key release detection for hold-to-talk
  if (uIOhook) {
    uIOhook.on('keyup', (e) => {
      // V key code is 47 in uiohook
      if (e.keycode === 47 && isVoiceRecording) {
        stopVoiceRecording();
      }
    });

    // Escape key (keycode 1) to close output window
    uIOhook.on('keydown', (e) => {
      if (e.keycode === 1 && outputWindow && outputWindow.isVisible()) {
        outputWindow.hide();
      }
    });

    uIOhook.start();
  }

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('will-quit', () => {
  globalShortcut.unregisterAll();
  if (uIOhook) {
    uIOhook.stop();
  }
});

// Voice recording functions for hold-to-talk
function startVoiceRecording() {
  if (isVoiceRecording) return;

  isVoiceRecording = true;

  // Show window and notify
  if (mainWindow) {
    mainWindow.show();
    mainWindow.focus();
    isWindowVisible = true;
    mainWindow.webContents.send('voice-recording-started');
  }

  // Start Python recording (saves to temp file)
  const pythonScript = path.join(__dirname, 'voice_transcribe.py');
  voiceProcess = spawn('python', [pythonScript, '--record'], {
    cwd: __dirname
  });

  voiceProcess.on('close', (code) => {
    voiceProcess = null;
    // Transcription will be triggered by stopVoiceRecording
  });

  voiceProcess.on('error', (err) => {
    isVoiceRecording = false;
    voiceProcess = null;
    if (mainWindow) {
      mainWindow.webContents.send('voice-recording-result', { error: err.message });
    }
  });
}

function stopVoiceRecording() {
  if (!isVoiceRecording) return;

  isVoiceRecording = false;

  if (mainWindow) {
    mainWindow.webContents.send('voice-recording-stopping');
  }

  // Kill the recording process
  if (voiceProcess) {
    if (process.platform === 'win32') {
      const { exec } = require('child_process');
      exec(`taskkill /pid ${voiceProcess.pid} /T /F`, (err) => {
        // Small delay to ensure file is saved, then transcribe
        setTimeout(transcribeSavedRecording, 300);
      });
    } else {
      try {
        voiceProcess.kill('SIGTERM');
      } catch (e) {
        // Error killing voice process
      }
      setTimeout(transcribeSavedRecording, 300);
    }
  } else {
    // Process already closed, just transcribe
    transcribeSavedRecording();
  }
}

function transcribeSavedRecording() {
  const pythonScript = path.join(__dirname, 'voice_transcribe.py');
  const transcribeProcess = spawn('python', [pythonScript, '--transcribe'], {
    cwd: __dirname
  });

  let output = '';
  let errorOutput = '';

  transcribeProcess.stdout.on('data', (data) => {
    output += data.toString();
  });

  transcribeProcess.stderr.on('data', (data) => {
    errorOutput += data.toString();
  });

  transcribeProcess.on('close', (code) => {
    let result = { error: 'No result' };

    if (output.trim()) {
      try {
        result = JSON.parse(output.trim());
      } catch (e) {
        result = { error: 'Failed to parse result' };
      }
    } else if (errorOutput) {
      result = { error: errorOutput };
    }

    if (mainWindow) {
      mainWindow.webContents.send('voice-recording-result', result);
    }
  });

  transcribeProcess.on('error', (err) => {
    if (mainWindow) {
      mainWindow.webContents.send('voice-recording-result', { error: err.message });
    }
  });
}

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// IPC handler for generating text
ipcMain.handle('generate-text', async (event, prompt, context) => {
  return new Promise((resolve, reject) => {
    const pythonScript = path.join(__dirname, 'text_ai_backend.py');

    // Pass prompt and context as JSON strings for proper parsing
    const promptJson = JSON.stringify(prompt);
    const args = [pythonScript, promptJson];

    if (context && Object.keys(context).length > 0) {
      const contextJson = JSON.stringify(context);
      args.push(contextJson);
    }

    // Try to read API key from config file and pass as environment variable
    const fs = require('fs');
    let env = { ...process.env };
    
    // Try to read from config.example.env or .env
    const configFiles = ['.env', 'config.example.env', 'config.env'];
    for (const configFile of configFiles) {
      const configPath = path.join(__dirname, configFile);
      if (fs.existsSync(configPath)) {
        try {
          const configContent = fs.readFileSync(configPath, 'utf8');
          // Try Mistral API key first, then fallback to Google for compatibility
          const mistralKeyMatch = configContent.match(/MISTRAL_API_KEY\s*=\s*([^\s#\n]+)/);
          const googleKeyMatch = configContent.match(/GOOGLE_API_KEY\s*=\s*([^\s#\n]+)/);
          
          if (mistralKeyMatch) {
            const apiKey = mistralKeyMatch[1].trim().replace(/^["']|["']$/g, '');
            if (apiKey && apiKey !== 'your-api-key-here') {
              env.MISTRAL_API_KEY = apiKey;
            }
          } else if (googleKeyMatch) {
            // Fallback to Google API key for backward compatibility
            const apiKey = googleKeyMatch[1].trim().replace(/^["']|["']$/g, '');
            if (apiKey && apiKey !== 'your-api-key-here') {
              env.GOOGLE_API_KEY = apiKey;
            }
          }
        } catch (err) {
          // Could not read config file
        }
      }
    }

    // Escape JSON for Windows command line
    const escapedArgs = args.map(arg => {
      // If it's a JSON string (starts with { or [), wrap it in quotes
      if ((arg.startsWith('{') || arg.startsWith('[')) && !arg.startsWith('"')) {
        // Escape inner quotes and wrap in double quotes
        return '"' + arg.replace(/"/g, '\\"') + '"';
      }
      return arg;
    });

    const pythonProcess = spawn('python', escapedArgs, {
      cwd: __dirname,
      shell: true,
      env: env
    });

    let output = '';
    let errorOutput = '';

    pythonProcess.stdout.on('data', (data) => {
      output += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
      errorOutput += data.toString();
    });

    pythonProcess.on('close', (code) => {
      if (code === 0) {
        try {
          const result = JSON.parse(output);
          resolve(result);
        } catch (e) {
          reject(new Error('Failed to parse Python output: ' + output));
        }
      } else {
        reject(new Error('Python script error: ' + errorOutput));
      }
    });
  });
});

// IPC handler for showing inline suggestion at cursor
ipcMain.handle('show-inline-suggestion', async (event, text) => {
  if (outputWindow) {
    const { screen } = require('electron');

    // Get cursor position (mouse position as proxy for text cursor)
    const cursor = screen.getCursorScreenPoint();
    const display = screen.getDisplayNearestPoint(cursor);
    const workArea = display.workArea;

    // Get window dimensions
    const [popupWidth, popupHeight] = outputWindow.getSize();

    // Position inline - just below cursor like autocomplete
    let x = cursor.x;
    let y = cursor.y + 20;  // Small offset below cursor

    // Keep on screen - flip above if needed
    if (y + popupHeight > workArea.y + workArea.height) {
      y = cursor.y - popupHeight - 5;
    }

    // Keep on screen - adjust horizontal
    if (x + popupWidth > workArea.x + workArea.width) {
      x = workArea.x + workArea.width - popupWidth - 10;
    }

    x = Math.max(workArea.x, x);
    y = Math.max(workArea.y, y);

    outputWindow.setPosition(Math.round(x), Math.round(y));
    outputWindow.showInactive();  // Show without stealing focus

    await new Promise(resolve => setTimeout(resolve, 50));
    outputWindow.webContents.send('display-text', text);
  }
});

// IPC handler for showing output in output window (legacy - redirects to inline)
ipcMain.handle('show-output', async (event, text) => {
  if (outputWindow) {
    const { screen } = require('electron');
    const cursor = screen.getCursorScreenPoint();
    const display = screen.getDisplayNearestPoint(cursor);
    const workArea = display.workArea;
    const [popupWidth, popupHeight] = outputWindow.getSize();

    let x = cursor.x;
    let y = cursor.y + 20;

    if (y + popupHeight > workArea.y + workArea.height) {
      y = cursor.y - popupHeight - 5;
    }
    if (x + popupWidth > workArea.x + workArea.width) {
      x = workArea.x + workArea.width - popupWidth - 10;
    }

    x = Math.max(workArea.x, x);
    y = Math.max(workArea.y, y);

    outputWindow.setPosition(Math.round(x), Math.round(y));
    outputWindow.showInactive();

    await new Promise(resolve => setTimeout(resolve, 50));
    outputWindow.webContents.send('display-text', text);
  }
});

// IPC handler for hiding output window
ipcMain.handle('hide-output', async () => {
  if (outputWindow) {
    outputWindow.hide();
  }
});

// Store for global paste shortcut
let lastGeneratedText = '';

// IPC handler to store generated text for global shortcut
ipcMain.on('set-generated-text', (event, text) => {
  lastGeneratedText = text;
});

// IPC handler for inline text injection using Rust injector
ipcMain.handle('inject-text', async (event, text) => {
  try {
    // Hide main window to allow focus on target app
    if (mainWindow) {
      mainWindow.hide();
      isWindowVisible = false;
    }
    if (outputWindow) {
      outputWindow.hide();
    }

    // Small delay to ensure focus is on the target application
    await new Promise(resolve => setTimeout(resolve, 150));

    // Use Rust-based keyboard injection
    const rustInjectPath = path.join(__dirname, 'keyboard-inject', 'target', 'release', 'keyboard-inject.exe');
    const fs = require('fs');
    const rustInjectPathDebug = path.join(__dirname, 'keyboard-inject', 'target', 'debug', 'keyboard-inject.exe');
    const actualPath = fs.existsSync(rustInjectPath) ? rustInjectPath :
                      (fs.existsSync(rustInjectPathDebug) ? rustInjectPathDebug : null);

    if (actualPath) {
      return new Promise((resolve) => {
        // Escape the text for command line
        let escapedText = text
          .replace(/\\/g, '\\\\')
          .replace(/"/g, '\\"')
          .replace(/\n/g, '\\n')
          .replace(/\r/g, '\\r')
          .replace(/\t/g, '\\t');

        escapedText = `"${escapedText}"`;

        const { exec } = require('child_process');
        const command = `"${actualPath}" ${escapedText}`;

        exec(command, { maxBuffer: 10 * 1024 * 1024 }, (error, stdout, stderr) => {
          if (error) {
            console.error('Rust injection error:', error);
            // Fallback to clipboard
            try {
              clipboard.writeText(text);
              if (robot) {
                setTimeout(() => {
                  robot.keyTap('v', 'control');
                  resolve({ success: true, method: 'clipboard-fallback' });
                }, 50);
              } else {
                resolve({ success: true, method: 'clipboard', message: 'Press Ctrl+V to paste' });
              }
            } catch (clipError) {
              resolve({ success: false, error: clipError.message });
            }
          } else {
            resolve({ success: true, method: 'keyboard-inject' });
          }
        });
      });
    } else {
      // Fallback to clipboard
      clipboard.writeText(text);
      if (robot) {
        await new Promise(resolve => setTimeout(resolve, 50));
        robot.keyTap('v', 'control');
        return { success: true, method: 'clipboard-fallback' };
      }
      return { success: true, method: 'clipboard', message: 'Press Ctrl+V to paste' };
    }
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// IPC handler for voice transcription using Python + Google Speech Recognition (free)
ipcMain.handle('transcribe-audio', async (event, options = {}) => {
  return new Promise((resolve) => {
    const timeout = options.timeout || 10;
    const phraseTimeout = options.phraseTimeout || 5;

    const pythonScript = path.join(__dirname, 'voice_transcribe.py');

    const pythonProcess = spawn('python', [pythonScript, '--live', timeout.toString(), phraseTimeout.toString()], {
      cwd: __dirname
    });

    let output = '';
    let errorOutput = '';

    pythonProcess.stdout.on('data', (data) => {
      output += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
      errorOutput += data.toString();
    });

    pythonProcess.on('close', (code) => {
      if (code === 0 && output.trim()) {
        try {
          const result = JSON.parse(output.trim());
          resolve(result);
        } catch (e) {
          resolve({ error: 'Failed to parse transcription result' });
        }
      } else {
        resolve({ error: errorOutput || 'Transcription failed' });
      }
    });

    pythonProcess.on('error', (err) => {
      resolve({ error: 'Failed to start voice recognition: ' + err.message });
    });
  });
});

// IPC handler for typing text at cursor position
ipcMain.handle('type-text', async (event, text) => {
  try {
    // Hide both windows to allow focus on target app
    if (mainWindow) {
      mainWindow.hide();
      isWindowVisible = false;
    }
    if (outputWindow) {
      outputWindow.hide();
    }
    
    // Small delay to ensure focus is on the target application
    await new Promise(resolve => setTimeout(resolve, 100));
    
    // Always use clipboard paste method (much faster than typing)
    clipboard.writeText(text);
    
    // Small delay to ensure clipboard is ready
    await new Promise(resolve => setTimeout(resolve, 50));
    
    if (robot) {
      // Simulate Ctrl+V to paste instantly
      try {
        robot.keyTap('v', 'control');
        return { success: true, method: 'clipboard-paste' };
      } catch (error) {
        return {
          success: true,
          method: 'clipboard',
          message: 'Text copied to clipboard. Press Ctrl+V to paste.'
        };
      }
    } else {
      return { 
        success: true, 
        method: 'clipboard',
        message: 'Text copied to clipboard. Press Ctrl+V to paste.' 
      };
    }
  } catch (error) {
    // Last resort: copy to clipboard
    try {
      clipboard.writeText(text);
      return { 
        success: true, 
        method: 'clipboard-fallback',
        message: 'Text copied to clipboard. Press Ctrl+V to paste.' 
      };
    } catch (clipError) {
      return { success: false, error: error.message };
    }
  }
});
