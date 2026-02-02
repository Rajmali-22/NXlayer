# GhostType

AI-powered stealth typing assistant for real-time typing, coding interviews, and productivity. Features smart context detection, human-like typing simulation, and invisible screen-share mode.

## Features

- **Smart AI Responses** - Auto-detects code problems, definitions, questions, and instructions
- **Human-like Typing** - Natural typing speed with realistic variations
- **Ultra Human Mode** - Chain-of-thought code injection for coding interviews
- **Screen Share Invisible** - Windows excluded from screen capture (Zoom, Meet, Teams)
- **Voice Input** - Hold-to-talk speech recognition
- **Vision Analysis** - Screenshot + AI analysis

## Quick Start

```bash
# Install dependencies
npm install
pip install -r requirements.txt

# Configure API keys
cp config.example.env .env
# Edit .env with your keys

# Run
npm start
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+D` | Process clipboard (code/question/text) |
| `Ctrl+Shift+P` | Inject AI response |
| `Ctrl+Alt+Enter` | Fix grammar / continue writing |
| `Ctrl+Shift+F` | Screenshot + Vision analysis |
| `Ctrl+Shift+V` | Voice input (hold to talk) |
| `Ctrl+Shift+S` | Open settings |
| `Ctrl+Shift+Space` | Toggle overlay window |
| `Escape` | Cancel / close popup |

## Settings

Access with `Ctrl+Shift+S`:

| Setting | Description |
|---------|-------------|
| **AI Assistant** | Master on/off toggle |
| **Dark Mode** | UI theme |
| **Human-like Typing** | Natural speed variation |
| **Auto Inject** | Skip suggestion popup |
| **Live Mode** | Auto-suggest on typing pause |
| **Coding Mode** | Show code + explanation windows |
| **Ultra Human Typing** | Chain-of-thought code injection |

## Modes

### Smart Clipboard (Ctrl+Shift+D)

Auto-detects content type and responds appropriately:

| You Copy | AI Response |
|----------|-------------|
| `"two sum problem"` | Clean code solution |
| `"OOP"` | 25-35 word definition |
| `"What is REST?"` | Direct 2-4 sentence answer |
| Code + `"explain this"` | Follows your instruction |

### Ultra Human Typing (Interview Mode)

For coding interviews - types code like a real developer:

1. Enable **Ultra Human Typing** in Settings
2. Copy the coding problem
3. Click in your code editor
4. Press `Ctrl+Shift+P`
5. AI generates and types code with:
   - Main skeleton first with `pass`
   - Navigates up to add helper functions
   - Returns to implement main
   - Realistic typos and corrections
   - Variable pauses between sections

### Other Modes

- **Grammar Mode** - Fix spelling/grammar (`Ctrl+Alt+Enter` on typed text)
- **Extension Mode** - Continue writing (`Ctrl+Alt+Enter` again within 2s)
- **Vision Mode** - Analyze screenshots (`Ctrl+Shift+F`)
- **Voice Mode** - Speech to text (`Ctrl+Shift+V` hold to talk)

## Project Structure

```
ghosttype/
├── main.js                      # Electron main process
├── ai_backend_service.py        # Persistent AI backend
├── smart_prompts.py             # Context-aware prompting
├── keyboard_inject.py           # Text injection (pynput)
├── keystroke_monitor.py         # Keyboard monitoring
├── pyautogui_typer_V3 (1).py    # Human-like code typing
├── pyautogui_typer_V3_Sign (1).py  # LeetCode-style typing
├── screenshot_vision.py         # Vision AI (Claude)
├── voice_transcribe.py          # Speech recognition
├── index.html                   # Main overlay UI
├── output.html                  # Suggestion popup
├── explanation.html             # Code explanation window
├── settings.html                # Settings UI
├── settings_renderer.js         # Settings logic
├── renderer.js                  # Frontend logic
└── requirements.txt             # Python dependencies
```

## Requirements

- Node.js 16+
- Python 3.8+
- Windows 10/11 (primary support)
- macOS/Linux (partial support)

## API Keys

Create `.env` file with:

```env
MISTRAL_API_KEY=your-key-here
```

Get keys from:
- **Mistral**: https://console.mistral.ai/api-keys/

Optional:
- **Anthropic** (vision): https://console.anthropic.com/settings/keys
- **OpenAI** (voice): https://platform.openai.com/api-keys

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Shortcuts not working | Run as Administrator |
| Module not found | `pip install -r requirements.txt` |
| Unicode errors | Set `PYTHONIOENCODING=utf-8` |
| API errors | Check keys in `.env` |
| Window visible in screen share | Restart app after enabling |

## License

MIT License
