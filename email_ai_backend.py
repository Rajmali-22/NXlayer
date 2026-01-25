"""
AI Email Completion Backend using Mistral AI API
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

def generate_professional_email(prompt: str, context: dict = None) -> str:
    """
    Generate a professional email using structured prompt and Gemini API.
    
    Args:
        prompt: User's email request/description
        context: Optional context (recipient, subject, tone, etc.)
    
    Returns:
        Generated professional email text
    """
    
    # Structured prompt for professional email generation
    structured_prompt = f"""You are a professional email assistant. Generate a well-structured, professional email body based on the following request.

USER REQUEST: {prompt}

{_build_context_section(context) if context else ""}

Please generate ONLY the email body content that:
1. Has an appropriate greeting (e.g., "Dear [Name]," or "Hello,")
2. Contains the main message content - clear and concise
3. Uses professional language
4. Has a proper closing (e.g., "Best regards," "Sincerely," etc.)
5. Is well-formatted and easy to read

IMPORTANT:
- Do NOT include a subject line
- Do NOT include "Subject:" or any subject field
- Generate ONLY the email body text starting with the greeting
- Do not include any explanations, meta-commentary, or instructions
- Start directly with the greeting and end with the closing signature"""

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
            return f"Error generating email: {error_str}"
    
    return "Error: Failed to generate email after multiple attempts."

def _build_context_section(context: dict) -> str:
    """Build context section for the prompt."""
    context_parts = []
    
    if context.get("recipient"):
        context_parts.append(f"Recipient: {context['recipient']}")
    if context.get("subject"):
        context_parts.append(f"Subject: {context['subject']}")
    if context.get("tone"):
        context_parts.append(f"Tone: {context['tone']}")
    if context.get("purpose"):
        context_parts.append(f"Purpose: {context['purpose']}")
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
    
    prompt = sys.argv[1]
    context = None
    
    # Try to parse context if provided as second argument
    if len(sys.argv) > 2:
        try:
            context = json.loads(sys.argv[2])
        except:
            pass
    
    email = generate_professional_email(prompt, context)
    print(json.dumps({"email": email}))

if __name__ == "__main__":
    main()
