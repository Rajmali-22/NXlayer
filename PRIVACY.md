# Privacy Policy

## Data Collection

AI Text Bot collects and processes data locally on your machine to provide its functionality.

### What is Collected

| Data Type | Purpose | Storage |
|-----------|---------|---------|
| Keystrokes | Text capture for AI assistance | Local RAM buffer, optionally `keylog.json` |
| Clipboard content | AI processing when triggered | Temporary (in memory) |
| Screenshots | Vision analysis (Ctrl+Shift+F) | Temporary (in memory) |
| Voice recordings | Speech-to-text transcription | Temporary (in memory) |

### What is NOT Collected

- No personal identification information
- No analytics or telemetry
- No usage statistics sent to third parties
- No persistent storage of screenshots or voice recordings

## Data Transmission

Data is sent ONLY to the AI providers you configure:

| Provider | Data Sent | When |
|----------|-----------|------|
| Mistral AI | Text prompts | On AI trigger (Ctrl+Shift+D, backtick, etc.) |
| Anthropic | Screenshots + prompts | On vision trigger (Ctrl+Shift+F) |
| OpenAI | Audio recordings | On voice input (Ctrl+Shift+V) |

**No data is sent to any other third party.**

## Local Storage

### keylog.json
- Stores up to 500 recent text entries (max 2000 chars each)
- Used for debugging and context
- Can be deleted at any time
- Listed in `.gitignore` (not committed)

### .env
- Contains your API keys
- Never committed to version control
- Keep secure and do not share

## Privacy Filters

The keystroke monitor automatically pauses in sensitive contexts:

- Banking websites
- Password managers (1Password, LastPass, Bitwarden, etc.)
- Windows with "password", "login", "signin" in title
- Private/Incognito browser windows

See `keystroke_monitor/config.py` for the full list.

## Your Rights

- **Access**: All data is stored locally on your machine
- **Delete**: Delete `keylog.json` anytime, or uninstall the app
- **Control**: Disable features via Settings (Ctrl+Shift+S)
- **Transparency**: Full source code available for review

## Contact

For privacy concerns, open an issue on the GitHub repository.
