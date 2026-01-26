# Application Flow Documentation

## Text Generation Flow

### 1. User Input (Frontend - renderer.js)
- User selects **tone** from dropdown (`tone-select`)
- User enters **prompt** in input field (`prompt-input`)
- User clicks "Generate" or presses Enter

### 2. Frontend Handler (renderer.js - handleGenerate())
```javascript
// Gets values
const prompt = promptInput.value.trim();
const tone = toneSelect.value; // e.g., "casual", "professional"

// Creates context object
const context = { tone: tone };

// Sends to main process via IPC
ipcRenderer.invoke('generate-text', prompt, context)
```

### 3. Main Process Handler (main.js - generate-text)
```javascript
ipcMain.handle('generate-text', async (event, prompt, context) => {
  // Receives: prompt (string), context (object with tone)
  
  // Converts to JSON strings for command line
  args = [pythonScript, JSON.stringify(prompt), JSON.stringify(context)]
  
  // Spawns Python process
  spawn('python', args, { env: {...} })
})
```

### 4. Python Script (text_ai_backend.py - main())
```python
# Receives command line arguments
sys.argv[1] = JSON string of prompt
sys.argv[2] = JSON string of context (e.g., '{"tone":"casual"}')

# Parses JSON
prompt = json.loads(sys.argv[1])
context = json.loads(sys.argv[2])  # {"tone": "casual"}

# Calls generation function
text = generate_text(prompt, context)
```

### 5. Text Generation (text_ai_backend.py - generate_text())
```python
# Extracts tone from context
tone = context.get("tone", "professional")  # Gets "casual" from context

# Builds prompt with tone instructions
structured_prompt = f"""
USER REQUEST: {prompt}
TONE: {tone}
TONE INSTRUCTIONS: {tone_guide}
...
"""

# Calls Mistral API
response = mistral.chat.complete(
    model="mistral-small-latest",
    messages=[{"role": "user", "content": structured_prompt}]
)

# Returns generated text
return text
```

### 6. Response Flow (Back to Frontend)
- Python prints: `{"text": "generated text..."}`
- main.js parses JSON and resolves promise
- renderer.js receives result with `result.text`
- Display in output window
- User presses Ctrl+Shift+P to paste

## Debugging

Check the console logs:
- **Frontend console**: Shows prompt and tone being sent
- **Main process console**: Shows args being passed to Python
- **Python stderr**: Shows DEBUG messages about prompt and context received

## Common Issues

1. **Prompt not passed**: Check if prompt contains special characters that need escaping
2. **Tone not applied**: Verify context object is being created and passed correctly
3. **JSON parsing errors**: Check if prompt/context are properly JSON-stringified
