#!/usr/bin/env python3
"""
AI Backend Service - Persistent process with streaming support.

Runs continuously like keystroke_monitor.py.
Communicates via stdin/stdout JSON messages.
Supports streaming responses for low latency.
"""

import sys
import json
import os
import re
import time
import threading
from mistralai import Mistral

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

API_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 2

# ══════════════════════════════════════════════════════════════════════════════
# API KEY LOADING
# ══════════════════════════════════════════════════════════════════════════════

def load_api_key():
    """Load API key from environment or config files."""
    api_key = os.getenv('MISTRAL_API_KEY')
    if api_key:
        return api_key

    config_files = ['.env', 'config.example.env', 'config.env']
    for config_file in config_files:
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    content = f.read()
                    match = re.search(r'MISTRAL_API_KEY\s*=\s*([^\s#\n]+)', content)
                    if match:
                        key = match.group(1).strip().strip('"').strip("'")
                        if key and key != 'your-api-key-here':
                            return key
            except Exception:
                pass
    return None


# ══════════════════════════════════════════════════════════════════════════════
# IPC - Communication with Electron
# ══════════════════════════════════════════════════════════════════════════════

class IPC:
    """Handles stdin/stdout communication with Electron."""

    @staticmethod
    def send(data):
        """Send JSON message to Electron."""
        try:
            print(json.dumps(data), flush=True)
        except Exception:
            pass

    @staticmethod
    def send_error(message):
        """Send error event."""
        IPC.send({"event": "error", "message": message})

    @staticmethod
    def send_chunk(text, is_final=False):
        """Send streaming chunk."""
        IPC.send({
            "event": "chunk",
            "text": text,
            "final": is_final
        })

    @staticmethod
    def send_complete(text):
        """Send complete response."""
        IPC.send({
            "event": "complete",
            "text": text
        })


# ══════════════════════════════════════════════════════════════════════════════
# PROMPT BUILDERS
# ══════════════════════════════════════════════════════════════════════════════

def build_messages(prompt, context):
    """Build messages array based on mode."""
    mode = context.get("mode", "prompt") if context else "prompt"

    if mode == "backtick":
        return [
            {
                "role": "system",
                "content": "You are an autocorrect tool. You ONLY fix spelling and grammar. You output ONLY the corrected text. No explanations. No preambles. No extra words. Just the fixed text."
            },
            {"role": "user", "content": prompt}
        ]

    elif mode == "extension":
        last_output = context.get("last_output", "") if context else ""
        structured = f"""You are a writing assistant. Continue writing from where the text left off.

PREVIOUS TEXT:
{last_output}

ORIGINAL CONTEXT:
{prompt}

INSTRUCTIONS:
1. Continue writing naturally from where the previous text ended
2. Maintain the same tone, style, and voice
3. Add 1-2 more sentences that flow naturally
4. Keep the continuation relevant to the context
5. Don't repeat what was already said

IMPORTANT:
- Output ONLY the continuation (new text to append)
- Do NOT repeat the previous text
- Do NOT include explanations
- Make it flow naturally as if it's one continuous piece"""
        return [{"role": "user", "content": structured}]

    elif mode == "clipboard_with_instruction":
        instruction = context.get("instruction", "") if context else ""
        return [
            {
                "role": "system",
                "content": """You follow the user's INSTRUCTION to process the CONTENT. Output ONLY the result with NO preambles, NO explanations.

RULES:
- Follow the instruction exactly
- Output only the requested content
- No "Here's..." or "Sure..." introductions
- Start directly with the output"""
            },
            {"role": "user", "content": f"CONTENT:\n{prompt}\n\nINSTRUCTION: {instruction}"}
        ]

    elif mode == "clipboard":
        return [
            {
                "role": "system",
                "content": """You respond to clipboard content with NO preambles, NO explanations. Output ONLY the response.

RULES:
- CODE: Output only code. No "Here's the code" or explanations. Just the code with proper indentation.
- EMAIL/MESSAGE: Output only the reply text. No "Here's a reply" intro.
- QUESTION: Output only the answer. No "The answer is" intro.
- Start directly with the content. No introductions."""
            },
            {"role": "user", "content": prompt}
        ]

    else:
        # Default prompt mode
        tone = context.get("tone", "professional") if context else "professional"
        tone_instructions = {
            "professional": "Use formal, respectful, and business-appropriate language.",
            "casual": "Use friendly, relaxed, and conversational language.",
            "friendly": "Use warm, approachable, and positive language.",
            "formal": "Use very formal, official language.",
            "creative": "Use expressive, engaging, and imaginative language.",
            "technical": "Use precise, clear, and jargon-appropriate language.",
            "persuasive": "Use compelling, convincing language.",
            "concise": "Use brief, direct, and to-the-point language."
        }
        tone_guide = tone_instructions.get(tone.lower(), tone_instructions["professional"])

        structured = f"""You are a versatile text assistant. Generate well-structured text content.

USER REQUEST: {prompt}

TONE: {tone}
TONE INSTRUCTIONS: {tone_guide}

IMPORTANT:
- Generate ONLY the text body/content
- Do NOT include titles, headers, or subject lines unless requested
- No explanations or meta-commentary
- Start directly with the content
- Output should be ready to use as-is"""

        return [{"role": "user", "content": structured}]


# ══════════════════════════════════════════════════════════════════════════════
# TEXT GENERATION (STREAMING)
# ══════════════════════════════════════════════════════════════════════════════

def generate_streaming(prompt, context, client):
    """Generate text with streaming output."""
    messages = build_messages(prompt, context)
    full_text = ""

    for attempt in range(MAX_RETRIES):
        try:
            # Use streaming
            stream = client.chat.stream(
                model="mistral-small-latest",
                messages=messages
            )

            for event in stream:
                if hasattr(event, 'data') and hasattr(event.data, 'choices'):
                    for choice in event.data.choices:
                        if hasattr(choice, 'delta') and hasattr(choice.delta, 'content'):
                            chunk = choice.delta.content
                            if chunk:
                                full_text += chunk
                                IPC.send_chunk(chunk, is_final=False)

            # Clean up text
            full_text = clean_response(full_text)
            IPC.send_chunk("", is_final=True)
            return full_text

        except Exception as e:
            error_str = str(e)

            # Handle retryable errors
            if '503' in error_str or 'overloaded' in error_str.lower():
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))
                    continue
                else:
                    return f"Error: API overloaded. Tried {MAX_RETRIES} times."

            if '429' in error_str or 'rate limit' in error_str.lower():
                return "Error: API rate limit exceeded."

            if '401' in error_str or 'unauthorized' in error_str.lower():
                return "Error: Invalid API key."

            return f"Error: {error_str}"

    return "Error: Failed after multiple attempts."


def generate_non_streaming(prompt, context, client):
    """Generate text without streaming (fallback)."""
    messages = build_messages(prompt, context)

    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.complete(
                model="mistral-small-latest",
                messages=messages
            )

            if hasattr(response, 'choices') and response.choices:
                if hasattr(response.choices[0], 'message'):
                    if hasattr(response.choices[0].message, 'content'):
                        text = response.choices[0].message.content
                        return clean_response(text)

            return "Error: No content in response."

        except Exception as e:
            error_str = str(e)
            if '503' in error_str or 'overloaded' in error_str.lower():
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))
                    continue
            return f"Error: {error_str}"

    return "Error: Failed after multiple attempts."


def clean_response(text):
    """Clean up AI response text."""
    if not text:
        return ""

    lines = text.strip().split('\n')
    cleaned = []
    skip_next = False

    for line in lines:
        if line.lower().startswith('subject:'):
            skip_next = True
            continue
        if skip_next and line.strip() == '':
            skip_next = False
            continue
        if not skip_next:
            cleaned.append(line)

    return '\n'.join(cleaned).strip()


# ══════════════════════════════════════════════════════════════════════════════
# REQUEST HANDLER
# ══════════════════════════════════════════════════════════════════════════════

def handle_request(request, client):
    """Handle incoming request from Electron."""
    cmd = request.get("cmd", "")

    if cmd == "generate":
        prompt = request.get("prompt", "")
        context = request.get("context", {})
        streaming = request.get("streaming", True)

        if not prompt:
            IPC.send({"event": "complete", "text": "", "error": "Empty prompt"})
            return

        if streaming:
            text = generate_streaming(prompt, context, client)
        else:
            text = generate_non_streaming(prompt, context, client)
            IPC.send_complete(text)

    elif cmd == "ping":
        IPC.send({"event": "pong"})

    elif cmd == "shutdown":
        IPC.send({"event": "shutdown_ack"})
        return "shutdown"

    else:
        IPC.send_error(f"Unknown command: {cmd}")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN LOOP
# ══════════════════════════════════════════════════════════════════════════════

def main():
    """Main entry point - persistent service."""
    # Load API key
    api_key = load_api_key()
    if not api_key:
        IPC.send_error("Missing API key! Set MISTRAL_API_KEY in .env file.")
        IPC.send({"event": "started", "success": False})
        return

    # Initialize Mistral client (kept warm)
    try:
        client = Mistral(api_key=api_key)
        IPC.send({"event": "started", "success": True, "pid": os.getpid()})
    except Exception as e:
        IPC.send_error(f"Failed to initialize Mistral client: {e}")
        IPC.send({"event": "started", "success": False})
        return

    # Main loop - read commands from stdin
    running = True
    while running:
        try:
            line = sys.stdin.readline()
            if not line:
                break

            line = line.strip()
            if not line:
                continue

            try:
                request = json.loads(line)
                result = handle_request(request, client)
                if result == "shutdown":
                    running = False
            except json.JSONDecodeError:
                IPC.send_error(f"Invalid JSON: {line}")

        except Exception as e:
            IPC.send_error(f"stdin error: {e}")
            break

    IPC.send({"event": "stopped"})


if __name__ == "__main__":
    main()
