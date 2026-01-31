#!/usr/bin/env python3
"""
Screenshot + Vision API module.
Captures full screen, sends with context to Claude Vision API.
"""

import sys
import json
import os
import io
import re
import base64

# Screenshot library
try:
    import mss
    HAS_MSS = True
except ImportError:
    HAS_MSS = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# Claude/Anthropic API
try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

# # Replicate API (commented out - using Claude instead)
# try:
#     import replicate
#     HAS_REPLICATE = True
# except ImportError:
#     HAS_REPLICATE = False


def load_api_key():
    """Load Anthropic API key from environment or .env file."""
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if api_key:
        return api_key

    # Try to read from .env file
    config_files = ['.env', 'config.env']
    for config_file in config_files:
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    content = f.read()
                    match = re.search(r'ANTHROPIC_API_KEY\s*=\s*([^\s#\n]+)', content)
                    if match:
                        api_key = match.group(1).strip().strip('"').strip("'")
                        if api_key and api_key != 'your-api-key-here':
                            return api_key
            except Exception:
                pass

    return None


def capture_screenshot():
    """Capture full screen and return as PNG bytes."""
    if not HAS_MSS:
        return None, "mss library not installed. Run: pip install mss"

    try:
        with mss.mss() as sct:
            # Capture the entire screen (all monitors combined or primary)
            monitor = sct.monitors[0]  # 0 = all monitors, 1 = primary
            screenshot = sct.grab(monitor)

            # Convert to PNG bytes
            if HAS_PIL:
                img = Image.frombytes('RGB', screenshot.size, screenshot.bgra, 'raw', 'BGRX')
                buffer = io.BytesIO()
                img.save(buffer, format='PNG', optimize=True)
                img_bytes = buffer.getvalue()
            else:
                # Use mss's built-in PNG conversion
                img_bytes = mss.tools.to_png(screenshot.rgb, screenshot.size)

            return img_bytes, None

    except Exception as e:
        return None, f"Screenshot failed: {str(e)}"


def call_vision_api(image_bytes, instruction):
    """Call Claude Vision API with screenshot and instruction."""
    if not HAS_ANTHROPIC:
        return None, "anthropic library not installed. Run: pip install anthropic"

    api_key = load_api_key()
    if not api_key:
        return None, "ANTHROPIC_API_KEY not found in environment or .env file"

    try:
        # Build the prompt with smart context detection
        if instruction and instruction.strip():
            prompt = instruction.strip()
        else:
            prompt = """Analyze this screenshot and respond based on what you see:

1. If there is CODE visible: Identify the programming language, explain what the code does, fix any bugs or errors, and provide the corrected code.

2. If there is TEXT visible (article, document, message, etc.): Extract and read the text. Summarize the key points concisely.

3. If there is an ERROR MESSAGE or problem: Explain the error and provide a solution.

4. If there is a QUESTION or problem to solve: Answer it directly.

5. If there is DATA/INFORMATION (charts, tables, etc.): Summarize the key insights.

Be direct and concise. Give actionable output, not descriptions."""

        # Convert image bytes to base64
        base64_image = base64.b64encode(image_bytes).decode('utf-8')

        # Create Anthropic client
        client = anthropic.Anthropic(api_key=api_key)

        # Call Claude Vision API
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": base64_image,
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ],
                }
            ],
        )

        # Extract text from response
        result = message.content[0].text

        return result, None

    except Exception as e:
        return None, f"Vision API error: {str(e)}"


# # Replicate/LLaVA version (commented out)
# def call_vision_api_replicate(image_bytes, instruction):
#     """Call Replicate API with screenshot and instruction."""
#     if not HAS_REPLICATE:
#         return None, "replicate library not installed. Run: pip install replicate"
#
#     api_key = os.getenv('REPLICATE_API_TOKEN')
#     if not api_key:
#         return None, "REPLICATE_API_TOKEN not found in environment or .env file"
#
#     os.environ['REPLICATE_API_TOKEN'] = api_key
#
#     try:
#         if instruction and instruction.strip():
#             prompt = instruction.strip()
#         else:
#             prompt = "Analyze this screenshot..."
#
#         image_file = io.BytesIO(image_bytes)
#         image_file.name = "screenshot.png"
#
#         output = replicate.run(
#             "yorickvp/llava-13b:80537f9eead1a5bfa72d5ac6ea6414379be41d4d4f6679fd776e9535d1eb58bb",
#             input={
#                 "image": image_file,
#                 "prompt": prompt,
#                 "max_tokens": 2048
#             }
#         )
#
#         if hasattr(output, '__iter__') and not isinstance(output, str):
#             result = ''.join(output)
#         else:
#             result = str(output)
#
#         return result, None
#
#     except Exception as e:
#         return None, f"Vision API error: {str(e)}"


def main():
    """Main entry point."""
    # Parse arguments
    instruction = ""
    if len(sys.argv) > 1:
        try:
            instruction = json.loads(sys.argv[1])
        except json.JSONDecodeError:
            instruction = sys.argv[1]

    print(f"DEBUG: Instruction: {instruction}", file=sys.stderr)

    # Capture screenshot
    print("DEBUG: Capturing screenshot...", file=sys.stderr)
    image_bytes, error = capture_screenshot()
    if error:
        print(json.dumps({"error": error}))
        sys.exit(1)

    print(f"DEBUG: Screenshot captured, size: {len(image_bytes)} bytes", file=sys.stderr)

    # Call vision API
    print("DEBUG: Calling Claude Vision API...", file=sys.stderr)
    result, error = call_vision_api(image_bytes, instruction)
    if error:
        print(json.dumps({"error": error}))
        sys.exit(1)

    print(f"DEBUG: Got response, length: {len(result)}", file=sys.stderr)

    # Return result
    print(json.dumps({"text": result}))


if __name__ == "__main__":
    main()
