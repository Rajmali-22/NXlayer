#!/usr/bin/env python3
"""
Whisper Speech-to-Text transcription using OpenAI API
"""

import sys
import json
import os
from pathlib import Path

def get_api_key():
    """Get OpenAI API key from environment or .env file"""
    # Check environment variable first
    api_key = os.environ.get('OPENAI_API_KEY')
    if api_key and api_key != 'your-api-key-here':
        return api_key

    # Try to read from .env file
    script_dir = Path(__file__).parent
    env_files = ['.env', 'config.env', 'config.example.env']

    for env_file in env_files:
        env_path = script_dir / env_file
        if env_path.exists():
            try:
                with open(env_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('OPENAI_API_KEY') and '=' in line:
                            key = line.split('=', 1)[1].strip()
                            # Remove quotes if present
                            key = key.strip('"\'')
                            if key and key != 'your-api-key-here':
                                return key
            except Exception as e:
                print(f"Warning: Could not read {env_file}: {e}", file=sys.stderr)

    return None

def transcribe_audio(audio_path):
    """Transcribe audio file using OpenAI Whisper API"""
    import requests

    api_key = get_api_key()
    if not api_key:
        return {"error": "OpenAI API key not found. Add OPENAI_API_KEY to your .env file."}

    if not os.path.exists(audio_path):
        return {"error": f"Audio file not found: {audio_path}"}

    file_size = os.path.getsize(audio_path)
    print(f"Transcribing audio file: {audio_path} ({file_size} bytes)", file=sys.stderr)

    url = "https://api.openai.com/v1/audio/transcriptions"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    try:
        with open(audio_path, 'rb') as audio_file:
            files = {
                'file': ('audio.webm', audio_file, 'audio/webm')
            }
            data = {
                'model': 'whisper-1'
            }

            # Make request with timeout and retries
            for attempt in range(3):
                try:
                    response = requests.post(
                        url,
                        headers=headers,
                        files=files,
                        data=data,
                        timeout=60
                    )
                    break
                except requests.exceptions.ConnectionError as e:
                    if attempt < 2:
                        print(f"Connection error, retrying... (attempt {attempt + 1})", file=sys.stderr)
                        import time
                        time.sleep(1)
                        # Reset file position for retry
                        audio_file.seek(0)
                    else:
                        raise

        if response.status_code == 200:
            result = response.json()
            print(f"Transcription successful: {result.get('text', '')[:50]}...", file=sys.stderr)
            return {"text": result.get("text", "")}
        else:
            error_msg = response.json().get("error", {}).get("message", response.text)
            print(f"API error: {error_msg}", file=sys.stderr)
            return {"error": f"Whisper API error: {error_msg}"}

    except requests.exceptions.Timeout:
        return {"error": "Request timed out. Try a shorter recording."}
    except requests.exceptions.ConnectionError as e:
        return {"error": f"Network connection error: {str(e)}"}
    except Exception as e:
        return {"error": f"Transcription failed: {str(e)}"}

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No audio file path provided"}))
        return

    audio_path = sys.argv[1]
    result = transcribe_audio(audio_path)
    print(json.dumps(result))

if __name__ == "__main__":
    main()
