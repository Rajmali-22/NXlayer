#!/usr/bin/env python3
"""
Voice-to-Text transcription using Google Speech Recognition (free)
Records from microphone and transcribes using Google's free API
"""

import sys
import json
import speech_recognition as sr

def transcribe_from_file(audio_path):
    """Transcribe from an audio file"""
    recognizer = sr.Recognizer()

    try:
        with sr.AudioFile(audio_path) as source:
            audio = recognizer.record(source)

        # Use Google's free speech recognition
        text = recognizer.recognize_google(audio)
        return {"text": text}

    except sr.UnknownValueError:
        return {"error": "Could not understand audio. Please speak clearly."}
    except sr.RequestError as e:
        return {"error": f"Speech recognition service error: {e}"}
    except Exception as e:
        return {"error": f"Transcription error: {str(e)}"}

def transcribe_live(timeout=10, phrase_timeout=3):
    """Record from microphone and transcribe"""
    recognizer = sr.Recognizer()

    try:
        with sr.Microphone() as source:
            print("Adjusting for ambient noise...", file=sys.stderr)
            recognizer.adjust_for_ambient_noise(source, duration=0.5)

            print("Listening...", file=sys.stderr)
            # Listen with timeout
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_timeout)

        print("Processing speech...", file=sys.stderr)

        # Use Google's free speech recognition
        text = recognizer.recognize_google(audio)
        print(f"Transcribed: {text}", file=sys.stderr)
        return {"text": text}

    except sr.WaitTimeoutError:
        return {"error": "No speech detected. Please try again."}
    except sr.UnknownValueError:
        return {"error": "Could not understand audio. Please speak clearly."}
    except sr.RequestError as e:
        return {"error": f"Speech recognition service error: {e}"}
    except OSError as e:
        if "No Default Input Device" in str(e) or "Invalid number of channels" in str(e):
            return {"error": "No microphone found. Please connect a microphone."}
        return {"error": f"Microphone error: {str(e)}"}
    except Exception as e:
        return {"error": f"Transcription error: {str(e)}"}

def main():
    # Check command line arguments
    if len(sys.argv) > 1:
        arg = sys.argv[1]

        if arg == "--live":
            # Live recording mode
            timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            phrase_timeout = int(sys.argv[3]) if len(sys.argv) > 3 else 5
            result = transcribe_live(timeout, phrase_timeout)
        else:
            # File mode - transcribe from audio file
            result = transcribe_from_file(arg)
    else:
        # Default: live recording
        result = transcribe_live()

    print(json.dumps(result))

if __name__ == "__main__":
    main()
