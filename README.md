# AI Text Bot

AI-powered text assistant for live typing, interviews, and productivity. Uses Mistral AI with smart context detection.

## Quick Start

```bash
# Install dependencies
npm install
pip install -r requirements.txt

# Add API keys to .env file
MISTRAL_API_KEY=your-key
ANTHROPIC_API_KEY=your-key    # for screenshot vision
OPENAI_API_KEY=your-key       # for voice (optional)

# Run
npm start
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Alt+Enter` | Fix grammar / continue writing / instruction mode |
| `Ctrl+Shift+D` | Process clipboard (auto-detects code/question/text) |
| `Ctrl+Shift+P` | Paste/inject AI response |
| `Ctrl+Shift+F` | Screenshot + Vision (analyzes screen) |
| `Ctrl+Shift+V` | Voice record / stop |
| `Ctrl+Shift+Space` | Toggle overlay window |
| `Ctrl+.` | Pause/resume text injection |
| `Escape` | Cancel / close popup |

## Smart Clipboard (Ctrl+Shift+D)

Auto-detects what you copied and responds appropriately:

| You Copy | AI Response |
|----------|-------------|
| "two sum problem" | Pure code solution |
| "OOP" | 25-35 word definition |
| "What is REST?" | Direct 2-4 sentence answer |
| Code + "explain this" | Follows your instruction |

Output is clean plain text - no markdown, no preambles. Ready for interviews.

## Modes

- **Backtick mode**: Grammar/spelling fix (Ctrl+Alt+Enter on typed text)
- **Extension mode**: Continue writing (Ctrl+Alt+Enter again within 2s)
- **Clipboard mode**: Smart processing (Ctrl+Shift+D)
- **Vision mode**: Screenshot analysis (Ctrl+Shift+F)
- **Voice mode**: Speech to text (Ctrl+Shift+V)

## Project Structure

```
ai-text-bot/
├── main.js               # Electron main process
├── text_ai_backend.py    # Mistral AI backend
├── smart_prompts.py      # Context-aware prompting
├── keyboard_inject.py    # Text injection
├── keystroke_monitor/    # Keyboard monitoring
├── screenshot_vision.py  # Vision AI (Claude)
├── voice_transcribe.py   # Speech to text
├── index.html            # Main UI
├── settings.html         # Settings UI
├── renderer.js           # Frontend logic
├── styles.css            # Styling
├── .env                  # API keys
└── requirements.txt      # Python dependencies
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| npm/python not found | Reinstall and add to PATH, restart PC |
| Module not found | Run `pip install -r requirements.txt` |
| Shortcuts not working | Run as Administrator |
| API errors | Check API keys in .env |

## Requirements

- Node.js 16+
- Python 3.8+
- Windows (primary), macOS/Linux (partial support)

## API Keys

- **Mistral**: https://console.mistral.ai/api-keys/
- **Anthropic**: https://console.anthropic.com/settings/keys
- **OpenAI**: https://platform.openai.com/api-keys (optional)
