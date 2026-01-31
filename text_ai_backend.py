"""
AI Text Generation Backend using Mistral AI API

Features:
- Multiple generation modes (backtick, extension, clipboard, prompt)
- Retry logic for API errors
- Timeout protection
- Safe error handling
"""
from mistralai import Mistral
import json
import sys
import os
import re
import time
import signal
from smart_prompts import build_prompt, clean_output

# API timeout in seconds
API_TIMEOUT = 30

def timeout_handler(signum, frame):
    """Handle timeout signal."""
    raise TimeoutError("API call timed out")

def load_api_key():
    """Load API key from environment variable or config file."""
    # First try environment variable
    api_key = os.getenv('MISTRAL_API_KEY')
    if api_key:
        return api_key
    
    # Try to read from config.example.env or .env file
    config_files = ['.env', 'config.example.env', 'config.env']
    for config_file in config_files:
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    content = f.read()
                    # Look for MISTRAL_API_KEY=value pattern
                    match = re.search(r'MISTRAL_API_KEY\s*=\s*([^\s#\n]+)', content)
                    if match:
                        api_key = match.group(1).strip().strip('"').strip("'")
                        if api_key and api_key != 'your-api-key-here':
                            return api_key
            except Exception as e:
                print(f"Warning: Could not read {config_file}: {e}", file=sys.stderr)
    
    return None

# Initialize the Mistral client
api_key = load_api_key()
if not api_key:
    # Don't crash - return error in JSON format so Electron can handle it
    print(json.dumps({"error": "Missing API key! Set MISTRAL_API_KEY in .env file."}))
    sys.exit(0)

def generate_text(prompt: str, context: dict = None) -> str:
    """
    Generate text content using structured prompt and Mistral API.

    Args:
        prompt: User's text request/description
        context: Optional context (tone, style, length, mode, etc.)

    Returns:
        Generated text content
    """

    # Ensure context is a dict
    if context is None:
        context = {}

    # Get mode from context (backtick, extension, clipboard, or default prompt mode)
    mode = context.get("mode", "prompt")

    # Debug logging (safe for any prompt length)
    print(f"DEBUG: generate_text called with mode='{mode}'", file=sys.stderr)
    print(f"DEBUG: Prompt length: {len(prompt) if prompt else 0} chars", file=sys.stderr)

    # Handle different modes
    if mode == "backtick":
        # Grammar/spelling fix mode - ONLY fix, don't respond or expand
        structured_prompt = f"""Autocorrect this text also give grammar correction and inline suggestion if possible or required. Output ONLY the corrected text with no explanation.

Input: {prompt}
Output:"""

    elif mode == "extension":
        # Continue writing mode
        last_output = context.get("last_output", "") if context else ""
        structured_prompt = f"""You are a writing assistant. Continue writing from where the text left off.

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

    elif mode == "clipboard_with_instruction":
        # Clipboard + typed instruction mode - use smart prompts
        instruction = context.get("instruction", "") if context else ""
        system_prompt, structured_prompt = build_prompt(prompt, user_instruction=instruction, mode=mode)
        # Store system prompt for later use
        context["_smart_system_prompt"] = system_prompt

    elif mode == "clipboard":
        # Smart clipboard mode - auto-detect and use smart prompts
        system_prompt, structured_prompt = build_prompt(prompt, mode=mode)
        # Store system prompt for later use
        context["_smart_system_prompt"] = system_prompt

    else:
        # Default prompt mode (from overlay window)
        tone = context.get("tone", "professional") if context else "professional"

        # Build tone-specific instructions
        tone_instructions = {
            "professional": "Use formal, respectful, and business-appropriate language. Maintain a polished and courteous tone.",
            "casual": "Use friendly, relaxed, and conversational language. Write as if speaking to a friend or colleague.",
            "friendly": "Use warm, approachable, and positive language. Be personable and engaging.",
            "formal": "Use very formal, official language. Follow strict business or academic conventions.",
            "creative": "Use expressive, engaging, and imaginative language. Be descriptive and vivid.",
            "technical": "Use precise, clear, and jargon-appropriate language. Focus on accuracy and clarity.",
            "persuasive": "Use compelling, convincing language. Structure arguments clearly and use persuasive techniques.",
            "concise": "Use brief, direct, and to-the-point language. Eliminate unnecessary words."
        }

        tone_guide = tone_instructions.get(tone.lower(), tone_instructions["professional"])

        # Structured prompt for text generation
        structured_prompt = f"""You are a versatile text assistant. Generate well-structured text content based on the following request.

USER REQUEST: {prompt}

{_build_context_section(context) if context else ""}

TONE: {tone}
TONE INSTRUCTIONS: {tone_guide}

Please generate the text content that:
1. Directly addresses the user's request
2. Matches the specified tone ({tone})
3. Is clear, well-formatted, and easy to read
4. Is appropriate for the context and purpose

IMPORTANT:
- Generate ONLY the text body/content
- Do NOT include titles, headers, or subject lines unless specifically requested
- Do not include any explanations, meta-commentary, or instructions
- Start directly with the content
- Output should be ready to use as-is"""

    max_retries = 3
    retry_delay = 2  # seconds

    # Build messages based on mode
    if mode == "backtick":
        # Use system message for strict autocorrect behavior
        messages = [
            {
                "role": "system",
                "content": "You are an autocorrect tool. You ONLY fix spelling and grammar. You output ONLY the corrected text. No explanations. No preambles. No extra words. Just the fixed text."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    elif mode == "clipboard_with_instruction" or mode == "clipboard":
        # Use smart prompts system - context has _smart_system_prompt stored
        smart_system = context.get("_smart_system_prompt", "You are a helpful assistant. Output only what is requested. No preambles.")
        messages = [
            {
                "role": "system",
                "content": smart_system
            },
            {
                "role": "user",
                "content": structured_prompt
            }
        ]
    else:
        messages = [
            {
                "role": "user",
                "content": structured_prompt
            }
        ]

    for attempt in range(max_retries):
        try:
            with Mistral(api_key=api_key) as mistral:
                response = mistral.chat.complete(
                    model="mistral-small-latest",
                    messages=messages,
                    stream=False
                )
            
            # Extract text from Mistral response
            text = None
            
            # Mistral response structure: response.choices[0].message.content
            if hasattr(response, 'choices') and response.choices:
                if hasattr(response.choices[0], 'message'):
                    if hasattr(response.choices[0].message, 'content'):
                        text = response.choices[0].message.content
            
            if text:
                # Clean up the text - remove any subject lines if present
                lines = text.strip().split('\n')
                cleaned_lines = []
                skip_next = False
                for line in lines:
                    # Skip subject lines
                    if line.lower().startswith('subject:'):
                        skip_next = True
                        continue
                    if skip_next and line.strip() == '':
                        skip_next = False
                        continue
                    if not skip_next:
                        cleaned_lines.append(line)

                result = '\n'.join(cleaned_lines).strip()

                # Apply smart prompts cleaning for clipboard modes
                if mode in ["clipboard", "clipboard_with_instruction"]:
                    result = clean_output(result)

                return result
            else:
                return "Error: No text content received from API. Response structure may have changed."
                
        except Exception as e:
            error_str = str(e)
            
            # Check for 503 or rate limit errors
            if '503' in error_str or 'UNAVAILABLE' in error_str or 'overloaded' in error_str.lower() or 'service unavailable' in error_str.lower():
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (attempt + 1)
                    print(f"API overloaded. Retrying in {wait_time} seconds... (Attempt {attempt + 1}/{max_retries})", file=sys.stderr)
                    time.sleep(wait_time)
                    continue
                else:
                    return f"Error: API is currently overloaded. Please try again in a few moments. (Attempted {max_retries} times)"
            
            # Check for other API errors
            if '429' in error_str or 'quota' in error_str.lower() or 'rate limit' in error_str.lower():
                return "Error: API rate limit exceeded. Please wait a moment and try again."
            
            # Check for authentication errors
            if '401' in error_str or 'unauthorized' in error_str.lower() or 'invalid api key' in error_str.lower():
                return "Error: Invalid API key. Please check your MISTRAL_API_KEY."
            
            # Generic error
            return f"Error generating text: {error_str}"

    return "Error: Failed to generate text after multiple attempts."

def _build_context_section(context: dict) -> str:
    """Build context section for the prompt."""
    context_parts = []
    
    if context.get("recipient"):
        context_parts.append(f"Recipient/Audience: {context['recipient']}")
    if context.get("purpose"):
        context_parts.append(f"Purpose: {context['purpose']}")
    if context.get("length"):
        context_parts.append(f"Length: {context['length']}")
    if context.get("style"):
        context_parts.append(f"Style: {context['style']}")
    if context.get("additional_info"):
        context_parts.append(f"Additional Information: {context['additional_info']}")
    
    if context_parts:
        return "CONTEXT:\n" + "\n".join(context_parts) + "\n"
    return ""

def main():
    """Main function to handle command-line input."""
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No prompt provided"}))
        sys.exit(0)

    try:
        # Parse the prompt (it comes JSON-stringified from Electron)
        try:
            prompt = json.loads(sys.argv[1])
        except json.JSONDecodeError:
            # If not valid JSON, try stripping quotes and parsing again
            try:
                cleaned = sys.argv[1].strip('"').strip("'")
                prompt = json.loads(cleaned)
            except:
                # If still fails, use as-is
                prompt = sys.argv[1]

        # Validate prompt
        if not prompt or not isinstance(prompt, str):
            print(json.dumps({"error": "Invalid prompt"}))
            sys.exit(0)

        # Limit prompt size (max 50KB)
        MAX_PROMPT_SIZE = 50000
        if len(prompt) > MAX_PROMPT_SIZE:
            prompt = prompt[:MAX_PROMPT_SIZE]
            print(f"DEBUG: Prompt truncated to {MAX_PROMPT_SIZE} chars", file=sys.stderr)

        context = None

        # Try to parse context if provided as second argument
        if len(sys.argv) > 2:
            try:
                context = json.loads(sys.argv[2])
            except json.JSONDecodeError:
                try:
                    cleaned = sys.argv[2].strip('"').strip("'")
                    context = json.loads(cleaned)
                except:
                    context = None

        print(f"DEBUG: Prompt length: {len(prompt)} chars", file=sys.stderr)
        print(f"DEBUG: Mode: {context.get('mode', 'default') if context else 'default'}", file=sys.stderr)

        text = generate_text(prompt, context)
        print(json.dumps({"text": text}))

    except Exception as e:
        # Catch-all error handler
        print(json.dumps({"error": f"Unexpected error: {str(e)}"}))
        sys.exit(0)

if __name__ == "__main__":
    main()
