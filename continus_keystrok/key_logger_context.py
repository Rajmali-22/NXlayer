#!/usr/bin/env python3
"""
AI Keyboard - Keystroke Monitor
Monitors keystrokes system-wide with context awareness and privacy protection
"""

import json
import time
import threading
import csv
from datetime import datetime
from pathlib import Path
from pynput import keyboard
import psutil
import platform
import os
import requests  # For API simulation


class KeystrokeMonitor:
    """
    Monitors keystrokes across all applications with context awareness
    """
    
    def __init__(self, output_file="keylog.json", auto_save_interval=10, pause_threshold=1.0):
        """
        Initialize the keystroke monitor
        
        Args:
            output_file: Path to JSON output file
            auto_save_interval: Seconds between auto-saves
            pause_threshold: Seconds of inactivity to trigger pause detection (default: 1.0)
        """
        self.output_file = Path(output_file)
        self.auto_save_interval = auto_save_interval
        self.pause_threshold = pause_threshold  # NEW: Configurable pause detection
        
        # CSV for pause events
        self.csv_file = Path(str(output_file).replace('.json', '_pauses.csv'))
        self.pause_json_file = Path(str(output_file).replace('.json', '_pause_contexts.json'))
        
        # Data storage
        self.sessions = []
        self.current_session = None
        self.typing_buffer = []
        self.raw_keystrokes = []
        
        # Pause detection
        self.last_keystroke_time = None
        self.pause_events = []
        self.pause_contexts = []  # Store context for each pause
        
        # API simulation
        self.api_endpoint = "http://localhost:8000/api/suggest"  # Configurable
        self.api_request_log = []
        
        # State tracking
        self.last_app = None
        self.last_window_title = None
        self.session_start_time = None
        self.is_running = False
        
        # Privacy filters
        self.BLACKLISTED_APPS = [
            # Password managers
            '1password', 'lastpass', 'keepass', 'bitwarden', 'dashlane',
            # Banking & Finance
            'bank', 'wallet', 'paypal', 'venmo', 'cashapp',
            # Sensitive apps
            'password', 'credential', 'authenticator',
            # Add more as needed
        ]
        
        # Special keys mapping
        self.SPECIAL_KEYS = {
            keyboard.Key.space: ' ',
            keyboard.Key.enter: '\n',
            keyboard.Key.tab: '\t',
            keyboard.Key.backspace: '<BACKSPACE>',
            keyboard.Key.delete: '<DELETE>',
            keyboard.Key.esc: '<ESC>',
            keyboard.Key.shift: '<SHIFT>',
            keyboard.Key.ctrl: '<CTRL>',
            keyboard.Key.alt: '<ALT>',
        }
        
        # Load existing data if available
        self._load_existing_data()
        
        print("🎹 AI Keyboard Monitor Initialized")
        print(f"📁 Output file: {self.output_file.absolute()}")
        print(f"📊 CSV pause log: {self.csv_file.absolute()}")
        print(f"🔍 Pause context JSON: {self.pause_json_file.absolute()}")
        print(f"💾 Auto-save interval: {auto_save_interval} seconds")
        print(f"⏱️  Pause threshold: {pause_threshold} seconds")
        print(f"🔒 Privacy filters: {len(self.BLACKLISTED_APPS)} blacklisted apps")
        
        # Initialize CSV file with headers
        self._initialize_csv()
    
    def _load_existing_data(self):
        """Load existing session data if file exists"""
        if self.output_file.exists():
            try:
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.sessions = data.get('sessions', [])
                print(f"📖 Loaded {len(self.sessions)} existing sessions")
            except Exception as e:
                print(f"⚠️  Could not load existing data: {e}")
                self.sessions = []
    
    def _initialize_csv(self):
        """Initialize CSV file with headers if it doesn't exist"""
        if not self.csv_file.exists():
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp',
                    'pause_duration_seconds',
                    'app_name',
                    'window_title',
                    'session_start',
                    'session_end',
                    'keystrokes_before_pause',
                    'api_request_sent',
                    'api_response_status'
                ])
            print(f"✅ Created CSV log file: {self.csv_file.name}")
    
    def get_active_window(self):
        """
        Get the currently active window/application
        Returns tuple: (app_name, window_title, process_name)
        """
        try:
            # Try platform-specific methods first
            if platform.system() == "Windows":
                return self._get_active_window_windows()
            elif platform.system() == "Darwin":  # macOS
                return self._get_active_window_mac()
            elif platform.system() == "Linux":
                return self._get_active_window_linux()
            else:
                return self._get_active_window_generic()
        except Exception as e:
            # Fallback to generic method
            return self._get_active_window_generic()
    
    def _get_active_window_windows(self):
        """Get active window on Windows"""
        try:
            import pygetwindow as gw
            active = gw.getActiveWindow()
            if active:
                # Get process info
                try:
                    pid = active._hWnd  # This might not work, fallback
                    process = psutil.Process(pid)
                    process_name = process.name()
                except:
                    process_name = "unknown"
                
                return (active.title, active.title, process_name)
        except:
            pass
        return self._get_active_window_generic()
    
    def _get_active_window_mac(self):
        """Get active window on macOS"""
        try:
            from AppKit import NSWorkspace
            app = NSWorkspace.sharedWorkspace().activeApplication()
            app_name = app['NSApplicationName']
            return (app_name, app_name, app_name)
        except:
            pass
        return self._get_active_window_generic()
    
    def _get_active_window_linux(self):
        """Get active window on Linux"""
        try:
            # This requires python-xlib
            from Xlib import display
            d = display.Display()
            window = d.get_input_focus().focus
            window_name = window.get_wm_name()
            return (window_name, window_name, "unknown")
        except:
            pass
        return self._get_active_window_generic()
    
    def _get_active_window_generic(self):
        """
        Generic method using psutil to find foreground process
        Less accurate but cross-platform
        """
        try:
            # Get all running processes
            for proc in psutil.process_iter(['name', 'pid']):
                try:
                    # This is a simple heuristic - might not be accurate
                    # Better than nothing for cross-platform support
                    return (proc.info['name'], proc.info['name'], proc.info['name'])
                except:
                    continue
        except:
            pass
        
        return ("Unknown", "Unknown", "unknown")
    
    def is_blacklisted_app(self, app_name):
        """
        Check if current app is blacklisted for privacy
        
        Args:
            app_name: Name of the application
            
        Returns:
            bool: True if app is blacklisted
        """
        if not app_name:
            return False
        
        app_lower = app_name.lower()
        for blacklisted in self.BLACKLISTED_APPS:
            if blacklisted in app_lower:
                return True
        return False
    
    def start_new_session(self, app_name, window_title, process_name):
        """Start a new typing session for a different app"""
        # Save previous session if exists
        if self.current_session:
            self._end_current_session()
        
        # Check if app is blacklisted
        if self.is_blacklisted_app(app_name):
            print(f"🔒 Skipping blacklisted app: {app_name}")
            self.current_session = None
            return
        
        self.session_start_time = datetime.now()
        self.typing_buffer = []
        self.raw_keystrokes = []
        
        self.current_session = {
            "app_name": app_name,
            "window_title": window_title,
            "process_name": process_name,
            "start_time": self.session_start_time.isoformat(),
            "end_time": None,
            "duration_seconds": 0,
            "keystrokes": {
                "raw": "",
                "final_text": "",
                "total_keys": 0,
                "backspaces": 0,
                "corrections": []
            }
        }
        
        print(f"\n📱 New session started: {app_name}")
        print(f"   Window: {window_title}")
        print(f"   Time: {self.session_start_time.strftime('%H:%M:%S')}")
    
    def detect_pause(self):
        """
        Check if a pause has occurred based on time since last keystroke
        Returns True if pause detected
        """
        if self.last_keystroke_time is None:
            return False
        
        current_time = time.time()
        time_since_last_key = current_time - self.last_keystroke_time
        
        if time_since_last_key >= self.pause_threshold:
            return True
        return False
    
    def handle_pause_event(self):
        """
        Handle a detected pause - log to CSV, save context, and simulate API request
        """
        if not self.current_session:
            return
        
        pause_time = datetime.now()
        time_since_last = time.time() - self.last_keystroke_time if self.last_keystroke_time else 0
        
        # Prepare context data for LLM
        context_data = {
            "app_name": self.current_session["app_name"],
            "window_title": self.current_session["window_title"],
            "process_name": self.current_session["process_name"],
            "start_time": self.current_session["start_time"],
            "end_time": pause_time.isoformat(),
            "duration_seconds": round((pause_time - self.session_start_time).total_seconds(), 2),
            "keystrokes": {
                "raw": "".join(self.raw_keystrokes),
                "final_text": self._process_buffer_with_backspaces(),
                "total_keys": len(self.raw_keystrokes),
                "backspaces": sum(1 for k in self.raw_keystrokes if '<BACKSPACE>' in k),
                "corrections": self.current_session["keystrokes"]["corrections"].copy()
            },
            "pause_detected_at": pause_time.isoformat(),
            "pause_duration": round(time_since_last, 2)
        }
        
        # Save to pause contexts list
        self.pause_contexts.append(context_data)
        
        # Simulate API request
        api_status = self._send_api_request(context_data)
        
        # Log to CSV
        self._log_pause_to_csv(pause_time, time_since_last, context_data, api_status)
        
        print(f"\n⏸️  PAUSE DETECTED ({time_since_last:.2f}s)")
        print(f"   App: {context_data['app_name']}")
        print(f"   Keys typed: {context_data['keystrokes']['total_keys']}")
        print(f"   API request: {api_status}")
    
    def _send_api_request(self, context_data):
        """
        Simulate sending API request to LLM with context
        
        Args:
            context_data: Dictionary with session context
            
        Returns:
            str: Status of API request
        """
        try:
            # Prepare payload for LLM
            payload = {
                "context": {
                    "app": context_data["app_name"],
                    "window": context_data["window_title"],
                    "session_start": context_data["start_time"],
                    "session_duration": context_data["duration_seconds"]
                },
                "text": context_data["keystrokes"]["final_text"],
                "raw_keystrokes": context_data["keystrokes"]["raw"],
                "metadata": {
                    "total_keys": context_data["keystrokes"]["total_keys"],
                    "backspaces": context_data["keystrokes"]["backspaces"],
                    "timestamp": context_data["pause_detected_at"]
                }
            }
            
            # Log the request
            request_log = {
                "timestamp": datetime.now().isoformat(),
                "endpoint": self.api_endpoint,
                "payload_size": len(json.dumps(payload)),
                "app_context": context_data["app_name"]
            }
            
            # SIMULATED API CALL (comment out in production or point to real endpoint)
            # Uncomment below for real API calls:
            # response = requests.post(
            #     self.api_endpoint,
            #     json=payload,
            #     timeout=5
            # )
            # status = f"Success: {response.status_code}"
            
            # For now, simulate success
            status = "SIMULATED_SUCCESS"
            request_log["status"] = status
            
            self.api_request_log.append(request_log)
            
            print(f"   📡 API Request simulated to: {self.api_endpoint}")
            print(f"      Payload size: {request_log['payload_size']} bytes")
            
            return status
            
        except Exception as e:
            error_status = f"ERROR: {str(e)}"
            print(f"   ❌ API Request failed: {error_status}")
            return error_status
    
    def _log_pause_to_csv(self, pause_time, pause_duration, context_data, api_status):
        """
        Log pause event to CSV file
        
        Args:
            pause_time: Datetime of pause
            pause_duration: Duration of pause in seconds
            context_data: Context dictionary
            api_status: Status of API request
        """
        try:
            with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    pause_time.isoformat(),
                    round(pause_duration, 2),
                    context_data["app_name"],
                    context_data["window_title"],
                    context_data["start_time"],
                    context_data["end_time"],
                    context_data["keystrokes"]["total_keys"],
                    "YES",  # API request sent
                    api_status
                ])
            
            print(f"   📊 Logged to CSV: {self.csv_file.name}")
            
        except Exception as e:
            print(f"   ⚠️  CSV logging error: {e}")
    
    def save_pause_contexts(self):
        """Save all pause contexts to JSON file"""
        try:
            data = {
                "pause_contexts": self.pause_contexts,
                "metadata": {
                    "total_pauses": len(self.pause_contexts),
                    "pause_threshold_seconds": self.pause_threshold,
                    "last_updated": datetime.now().isoformat()
                },
                "api_request_log": self.api_request_log
            }
            
            with open(self.pause_json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Saved {len(self.pause_contexts)} pause contexts to {self.pause_json_file.name}")
            
        except Exception as e:
            print(f"❌ Error saving pause contexts: {e}")
    
    def _end_current_session(self):
        """End the current session and save it"""
        if not self.current_session:
            return
        
        end_time = datetime.now()
        duration = (end_time - self.session_start_time).total_seconds()
        
        # Build final text by processing buffer
        final_text = self._process_buffer_with_backspaces()
        
        # Update session data
        self.current_session["end_time"] = end_time.isoformat()
        self.current_session["duration_seconds"] = round(duration, 2)
        self.current_session["keystrokes"]["raw"] = "".join(self.raw_keystrokes)
        self.current_session["keystrokes"]["final_text"] = final_text
        self.current_session["keystrokes"]["total_keys"] = len(self.raw_keystrokes)
        
        # Count backspaces
        backspace_count = sum(1 for k in self.raw_keystrokes if '<BACKSPACE>' in k)
        self.current_session["keystrokes"]["backspaces"] = backspace_count
        
        # Add to sessions list
        self.sessions.append(self.current_session)
        
        print(f"✅ Session ended: {self.current_session['app_name']}")
        print(f"   Duration: {duration:.1f}s")
        print(f"   Keys typed: {len(self.raw_keystrokes)}")
        print(f"   Final text length: {len(final_text)} chars")
        
        self.current_session = None
    
    def _process_buffer_with_backspaces(self):
        """
        Process the typing buffer to get final text after backspaces
        
        Returns:
            str: Final text after applying all backspaces
        """
        result = []
        
        for item in self.raw_keystrokes:
            if item == '<BACKSPACE>':
                if result:
                    result.pop()
            elif not item.startswith('<'):  # Ignore other special keys except backspace
                result.append(item)
        
        return "".join(result)
    
    def on_press(self, key):
        """
        Callback for key press events
        
        Args:
            key: The key that was pressed
        """
        if not self.is_running:
            return
        
        try:
            # Check for pause BEFORE processing new key
            current_time = time.time()
            if self.last_keystroke_time is not None:
                time_since_last = current_time - self.last_keystroke_time
                if time_since_last >= self.pause_threshold:
                    # Pause detected!
                    self.handle_pause_event()
            
            # Update last keystroke time
            self.last_keystroke_time = current_time
            
            # Get current active window
            app_name, window_title, process_name = self.get_active_window()
            
            # Check if we switched apps
            if app_name != self.last_app:
                self.start_new_session(app_name, window_title, process_name)
                self.last_app = app_name
            
            # Skip if no active session (blacklisted app)
            if not self.current_session:
                return
            
            # Process the key
            if hasattr(key, 'char') and key.char is not None:
                # Regular character
                char = key.char
                self.typing_buffer.append(char)
                self.raw_keystrokes.append(char)
                
            elif key in self.SPECIAL_KEYS:
                # Special key (space, enter, backspace, etc.)
                special = self.SPECIAL_KEYS[key]
                
                if key == keyboard.Key.backspace:
                    # Handle backspace
                    if self.typing_buffer:
                        deleted_char = self.typing_buffer.pop()
                        # Record correction
                        self.current_session["keystrokes"]["corrections"].append({
                            "timestamp": datetime.now().isoformat(),
                            "position": len(self.typing_buffer),
                            "deleted": deleted_char,
                            "reason": "backspace"
                        })
                    self.raw_keystrokes.append(special)
                
                elif key == keyboard.Key.space:
                    self.typing_buffer.append(' ')
                    self.raw_keystrokes.append(' ')
                
                elif key == keyboard.Key.enter:
                    self.typing_buffer.append('\n')
                    self.raw_keystrokes.append('\n')
                
                else:
                    # Other special keys - record but don't add to buffer
                    self.raw_keystrokes.append(special)
            
        except Exception as e:
            print(f"⚠️  Error in on_press: {e}")
    
    def on_release(self, key):
        """
        Callback for key release events
        
        Args:
            key: The key that was released
        """
        # Stop monitoring on ESC key (for testing)
        if key == keyboard.Key.esc:
            print("\n🛑 ESC pressed - stopping monitor...")
            self.stop()
            return False
    
    def auto_save_worker(self):
        """Background worker to auto-save data periodically"""
        while self.is_running:
            time.sleep(self.auto_save_interval)
            if self.is_running:
                self.save_to_json()
    
    def save_to_json(self):
        """Save all sessions to JSON file"""
        try:
            # Prepare data structure
            data = {
                "sessions": self.sessions,
                "metadata": {
                    "total_sessions": len(self.sessions),
                    "total_keystrokes": sum(s["keystrokes"]["total_keys"] for s in self.sessions),
                    "total_duration_seconds": sum(s["duration_seconds"] for s in self.sessions),
                    "last_updated": datetime.now().isoformat(),
                    "platform": platform.system(),
                }
            }
            
            # Write to file
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Saved {len(self.sessions)} sessions to {self.output_file}")
            
        except Exception as e:
            print(f"❌ Error saving to JSON: {e}")
    
    def start(self):
        """Start monitoring keystrokes"""
        if self.is_running:
            print("⚠️  Monitor is already running!")
            return
        
        self.is_running = True
        
        print("\n" + "="*60)
        print("🚀 AI Keyboard Monitor Started!")
        print("="*60)
        print("📝 Monitoring all keystrokes...")
        print("🔒 Privacy filters active")
        print("💾 Auto-saving every {} seconds".format(self.auto_save_interval))
        print("🛑 Press ESC to stop monitoring")
        print("="*60 + "\n")
        
        # Start auto-save worker thread
        save_thread = threading.Thread(target=self.auto_save_worker, daemon=True)
        save_thread.start()
        
        # Start keyboard listener
        with keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release
        ) as listener:
            listener.join()
    
    def stop(self):
        """Stop monitoring"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # End current session
        self._end_current_session()
        
        # Final save of main data
        self.save_to_json()
        
        # Save pause contexts
        self.save_pause_contexts()
        
        print("\n" + "="*60)
        print("🛑 Monitor Stopped")
        print("="*60)
        print(f"📊 Total sessions: {len(self.sessions)}")
        print(f"⌨️  Total keystrokes: {sum(s['keystrokes']['total_keys'] for s in self.sessions)}")
        print(f"⏸️  Total pauses detected: {len(self.pause_contexts)}")
        print(f"📡 API requests sent: {len(self.api_request_log)}")
        print(f"💾 Main data: {self.output_file.absolute()}")
        print(f"📊 Pause CSV: {self.csv_file.absolute()}")
        print(f"🔍 Pause contexts: {self.pause_json_file.absolute()}")
        print("="*60 + "\n")


def main():
    """Main entry point"""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║           AI Keyboard - Keystroke Monitor                 ║
    ║         Context-Aware Keystroke Tracking System           ║
    ║              With Pause Detection & API Calls             ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Create monitor instance
    monitor = KeystrokeMonitor(
        output_file="keylog.json",
        auto_save_interval=10,  # Save every 10 seconds
        pause_threshold=1.0     # Detect pause after 1 second of inactivity
    )
    
    # Add custom blacklist if needed
    # monitor.BLACKLISTED_APPS.append('your-sensitive-app')
    
    # Configure API endpoint if you have one
    # monitor.api_endpoint = "http://your-api.com/suggest"
    
    try:
        # Start monitoring
        monitor.start()
    except KeyboardInterrupt:
        print("\n\n⚠️  Keyboard interrupt detected")
        monitor.stop()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        monitor.stop()


if __name__ == "__main__":
    main()