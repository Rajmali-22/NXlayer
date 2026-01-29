# AI Text Bot - Text Generation Assistant

An AI-powered text generation bot with a transparent overlay interface that helps you write any type of text content using Mistral AI.

## Features

- 🤖 **AI-Powered Text Generation**: Uses Mistral AI to generate text in various tones and styles
- 🪟 **Transparent Overlay**: Non-intrusive transparent window that stays on top
- ⌨️ **Quick Paste**: Press Tab to accept and paste generated text at your cursor position
- 🎯 **Smart Positioning**: Output appears near your cursor position
- 🌐 **Cross-Platform**: Works on Windows, macOS, and Linux

## Prerequisites

- **Python 3.7+** installed and in your PATH
- **Node.js 16+** and npm
- **Mistral AI API Key**: Get one from [Mistral AI Console](https://console.mistral.ai/api-keys/)

## Available Tones

- **Professional**: Formal, respectful, business-appropriate
- **Casual**: Friendly, relaxed, conversational
- **Friendly**: Warm, approachable, positive
- **Formal**: Very formal, official language
- **Creative**: Expressive, engaging, imaginative
- **Technical**: Precise, clear, jargon-appropriate
- **Persuasive**: Compelling, convincing arguments
- **Concise**: Brief, direct, to-the-point

## Setup Instructions

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Mistral AI API

You need to set up your Mistral AI API key. Add it to your `.env` file or set it as an environment variable.

**Option A: Environment Variable (Recommended)**
```bash
# Windows (PowerShell)
$env:MISTRAL_API_KEY="your-api-key-here"

# Windows (CMD)
set MISTRAL_API_KEY=your-api-key-here

# macOS/Linux
export MISTRAL_API_KEY="your-api-key-here"
```

**Option B: .env File**
Create a `.env` file in the project root:
```
MISTRAL_API_KEY=your-api-key-here
```

Get your API key from: https://console.mistral.ai/api-keys/

### 3. Install Node.js Dependencies

```bash
npm install
```

**Important**: After installing, you need to rebuild `robotjs` for Electron:

```bash
npm run rebuild
```

Or it will automatically rebuild after `npm install` (via postinstall script).

**Note**: `robotjs` may require additional build tools. If you encounter issues:

- **Windows**: Install [windows-build-tools](https://github.com/nodejs/node-gyp#on-windows) or [Visual Studio Build Tools](https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022)
- **macOS**: Install Xcode Command Line Tools: `xcode-select --install`
- **Linux**: Install build essentials: `sudo apt-get install build-essential libxtst-dev libpng++-dev`

**If robotjs fails to build**: The app will fall back to copying text to clipboard. You can then manually paste with Ctrl+V.

### 4. Run the Application

```bash
npm start
```

## Usage

1. **Toggle Window**: Press `Ctrl+Shift+Space` (or `Cmd+Shift+Space` on macOS) to show/hide the overlay
2. **Select Tone**: Choose the tone/style from the dropdown (Professional, Casual, Friendly, etc.)
3. **Enter Prompt**: Type your request, e.g., "Write a message to my team about the project update"
4. **Generate**: Press Enter or click the Generate button
5. **Review**: The generated text will appear in a transparent floating window at the top-left
6. **Accept**: Press `Ctrl+Shift+P` to accept and paste the text at your current cursor position
7. **Close**: Press `Escape` or click the × button to close the output without pasting

## Example Prompts

- "Write a message to my boss requesting time off next week" (Professional tone)
- "Create a casual update about the project progress" (Casual tone)
- "Draft a friendly reminder about the team meeting" (Friendly tone)
- "Write a technical explanation of how the new feature works" (Technical tone)
- "Create a persuasive pitch for the new product idea" (Persuasive tone)

## Project Structure

```
ai-text-bot/
├── email_ai_backend.py    # Python backend for Mistral AI
├── main.js                # Electron main process
├── index.html             # UI structure
├── styles.css             # Styling
├── renderer.js            # Frontend logic
├── package.json           # Node.js dependencies
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Troubleshooting

### Python Script Not Found
- Ensure Python is in your PATH
- On Windows, you may need to use `python3` instead of `python`

### robotjs Installation Issues
- Make sure you have the required build tools installed
- Try: `npm install --build-from-source robotjs`

### API Authentication Errors
- Verify your `MISTRAL_API_KEY` environment variable is set correctly
- Check that your API key is valid and has credits/quota available
- Get a new API key from: https://console.mistral.ai/api-keys/

### Window Not Appearing
- Check if the window is hidden behind other applications
- Try pressing `Ctrl+Shift+Space` again to toggle visibility

## Keyboard Shortcuts

- `Ctrl+Shift+Space` / `Cmd+Shift+Space`: Toggle overlay window
- `Enter`: Generate email from input
- `Ctrl+Shift+P`: Accept and paste generated text
- `Escape`: Close output display

## License

MIT
