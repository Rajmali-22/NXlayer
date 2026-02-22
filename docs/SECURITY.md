# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly:

1. **Do not** open a public GitHub issue for security vulnerabilities
2. Email the maintainers directly or use GitHub's private vulnerability reporting
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We will acknowledge receipt within 48 hours and aim to provide a fix within 7 days for critical issues.

## Security Considerations

### API Keys
- Never commit `.env` files containing real API keys
- Use `config.example.env` as a template with placeholder values
- Rotate API keys immediately if accidentally exposed

### Keystroke Monitoring
- This application monitors keystrokes system-wide for its core functionality
- Privacy filters exclude sensitive windows (banks, password managers)
- `keylog.json` stores typed text locally only - no data is sent externally except to AI APIs
- Users should be aware of the keylogging functionality

### Data Storage
- All data is stored locally on the user's machine
- No telemetry or analytics are collected
- AI requests are sent only to the configured API provider (Mistral by default)

### Electron Security
- Current implementation uses `nodeIntegration: true` for simplicity
- For hardened deployments, consider enabling `contextIsolation` and using preload scripts

## Best Practices for Users

1. Keep API keys in `.env` file only (never share or commit)
2. Review the privacy filters in `keystroke_monitor/config.py`
3. Clear `keylog.json` periodically if desired
4. Use on trusted machines only (keystroke monitoring is powerful)
5. Keep dependencies updated (`npm update`, `pip install -U -r requirements.txt`)
