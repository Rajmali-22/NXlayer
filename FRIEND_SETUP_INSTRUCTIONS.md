# AI Text Bot — Setup & Use (Instructions for a Friend)

Hey — here’s how to run the AI Text Bot on your machine and use it day to day.

---

## What it does

- **Overlay bar:** Type a prompt (e.g. “draft a thank-you email”), pick a tone, get AI text; paste it where you’re typing.
- **Grammar fix:** Type something, press **Ctrl+Alt+Enter** → text is corrected in place.
- **Continue writing:** After a grammar fix, press **Ctrl+Alt+Enter** again within ~2 seconds (without typing) → AI continues the text.
- **Clipboard:** Copy anything, press **Ctrl+Shift+D** → AI processes it (fix/summarize/translate etc.) and you can paste the result. You can also type an instruction (e.g. “translate to Spanish”) then **Ctrl+Shift+D**.
- **Screenshot + Vision:** Press **Ctrl+Shift+F** → screen is captured and sent to AI; you can type a question (e.g. “what’s on this page?”). Optional: needs Anthropic API key.
- **Voice:** Press **Ctrl+Shift+V** (or use the mic in the overlay) → speak → text goes into the prompt bar. No API key for voice (uses Google Speech).

---

## Prerequisites

- **Windows** (for full keystroke/window features; overlay + paste can work on Mac/Linux).
- **Node.js 16+** and **npm**.
- **Python 3.7+** in your PATH.
- **Mistral API key** (free tier is enough to start): https://console.mistral.ai/api-keys/

---

## Setup (step by step)

### 1. Get the project

Clone or download the repo and open a terminal in the project folder (e.g. `ai-text-bot`).

### 2. Install Node dependencies

```bash
npm install
```

If it asks to rebuild `robotjs`, run:

```bash
npm run rebuild
```

(If rebuild fails, you can still use the app; paste will fall back to clipboard + Ctrl+V.)

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Add your API key

Create a file named **`.env`** in the project root (same folder as `package.json`) with:

```
MISTRAL_API_KEY=your-mistral-api-key-here
```

Replace `your-mistral-api-key-here` with your key from https://console.mistral.ai/api-keys/

**Optional (for screenshot vision):**  
If you want **Ctrl+Shift+F** (screenshot + AI), add:

```
ANTHROPIC_API_KEY=your-anthropic-key-here
```

Get it from: https://console.anthropic.com/settings/keys

### 5. Run the app

```bash
npm start
```

You should see a small overlay bar at the bottom of the screen. Use **Ctrl+Shift+Space** to show/hide it.

---

## Shortcuts (cheat sheet)

| Shortcut | Action |
|----------|--------|
| **Ctrl+Shift+Space** | Show / hide the overlay prompt bar |
| **Ctrl+Shift+P** | Paste the last generated text at cursor (after you’ve seen it in the popup) |
| **Ctrl+Alt+Enter** | Send current typed text to AI: grammar fix, or “continue writing”, or instruction |
| **Ctrl+Shift+D** | Process clipboard (with optional typed instruction) |
| **Ctrl+Shift+F** | Screenshot + Vision AI (needs Anthropic key) |
| **Ctrl+Shift+V** | Start / stop voice input (transcription into prompt bar) |
| **Escape** | Cancel / close suggestion popup |
| **Ctrl+.** | Pause / resume while the app is “typing” the result |

---

## First things to try

1. **Ctrl+Shift+Space** → type “Write a two-sentence intro for an email” → press Enter → when the popup shows the text, click where you want it and press **Ctrl+Shift+P**.
2. Type a sentence with a typo (e.g. “I went too the store”) → **Ctrl+Alt+Enter** → it should correct in place.
3. Copy a paragraph → **Ctrl+Shift+D** → get a summary or other result; paste with **Ctrl+Shift+P** if it’s in the popup.

---

## Settings (optional)

- There’s a **Settings** window (e.g. from the tray icon if you have one, or as noted in the app). There you can:
  - Turn **context mode** on and add a profile (e.g. paste your resume) so the AI adapts to you and the app you’re in.
  - Turn **auto-inject** on so that after generating, the text is typed/pasted automatically (no need to press Ctrl+Shift+P).
  - Toggle **humanize** for slower, more “human” typing when the app injects text.

---

## If something doesn’t work

- **“No text / API error”** → Check that `.env` exists in the project root and contains `MISTRAL_API_KEY=...` with a valid key.
- **Shortcuts do nothing** → Try running the terminal (or Electron) as administrator; some apps block global shortcuts.
- **Paste doesn’t type at cursor** → The app will copy to clipboard; paste manually with **Ctrl+V**. You can try `npm run rebuild` for better injection.
- **Voice not working** → Check microphone permissions and that no other app is using the mic.

For more detail, see **README.md** and **doc.txt** in the project.

---

You can copy this whole file or the sections you need and send it to your friend (e.g. as a message, email, or shared doc). If you want a shorter “message version”, I can trim it to a few paragraphs.
