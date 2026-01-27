"""
AI Text Generation Backend using Mistral AI API
"""
from mistralai import Mistral
import json
import sys
import os
import re

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
    raise ValueError(
        "Missing API key! Set MISTRAL_API_KEY environment variable or add it to .env/config.example.env file.\n"
        "Get your API key from: https://console.mistral.ai/api-keys/"
    )

def generate_text(prompt: str, context: dict = None) -> str:
    """
    Generate text content using structured prompt and Mistral API.
    
    Args:
        prompt: User's text request/description
        context: Optional context (tone, style, length, etc.)
    
    Returns:
        Generated text content
    """
    
    # Get tone from context, default to professional
    tone = context.get("tone", "professional") if context else "professional"
    
    # Debug logging
    print(f"DEBUG: generate_text called with tone='{tone}'", file=sys.stderr)
    print(f"DEBUG: Full context: {context}", file=sys.stderr)
    
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

    import time
    
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            with Mistral(api_key=api_key) as mistral:
                response = mistral.chat.complete(
                    model="mistral-small-latest",
                    messages=[
                        {
                            "role": "user",
                            "content": structured_prompt
                        }
                    ],
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
                
                return '\n'.join(cleaned_lines).strip()
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
        sys.exit(1)
    
    # Parse the prompt (it comes JSON-stringified from Electron)
    try:
        prompt = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        # If not valid JSON, try stripping quotes and parsing again
        try:
            # Windows command line might add extra quotes
            cleaned = sys.argv[1].strip('"').strip("'")
            prompt = json.loads(cleaned)
        except:
            # If still fails, use as-is
            prompt = sys.argv[1]
            print(f"DEBUG: Using prompt as-is (not JSON): {prompt[:50]}...", file=sys.stderr)
    
    context = None
    
    # Try to parse context if provided as second argument
    if len(sys.argv) > 2:
        try:
            context = json.loads(sys.argv[2])
            print(f"DEBUG: Context received: {context}", file=sys.stderr)
        except json.JSONDecodeError as e:
            # Try stripping quotes that Windows might add
            try:
                cleaned = sys.argv[2].strip('"').strip("'")
                context = json.loads(cleaned)
                print(f"DEBUG: Context received (after cleaning): {context}", file=sys.stderr)
            except Exception as e2:
                print(f"DEBUG: Failed to parse context: {e2}", file=sys.stderr)
                print(f"DEBUG: Raw context arg: {repr(sys.argv[2])}", file=sys.stderr)
                pass
    
    print(f"DEBUG: Prompt: {prompt[:50]}...", file=sys.stderr)
    print(f"DEBUG: Tone: {context.get('tone') if context else 'default'}", file=sys.stderr)
    
    text = generate_text(prompt, context)
    print(json.dumps({"text": text}))

if __name__ == "__main__":
    main()
