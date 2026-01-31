#!/usr/bin/env python3
"""
AI Keyboard - Inline Grammar Checker
Standalone version - Pure Python
Press Ctrl+Shift+R to toggle grammar checking mode
"""

import json
import time
import threading
import os
import subprocess
from datetime import datetime
from pathlib import Path
from pynput import keyboard
from pynput.keyboard import Controller, Key, Listener, HotKey
import requests

# Terminal colors
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_status(message, status=True):
    """Print status with colored checkmark"""
    symbol = f"{Colors.GREEN}✅{Colors.RESET}" if status else f"{Colors.RED}❌{Colors.RESET}"
    print(f"{symbol} {message}")


class InlineGrammarChecker:
    """
    Inline grammar checker that monitors typing and suggests corrections
    """
    
    def __init__(self, pause_threshold=1.0, trigger_key='`', llama_endpoint="http://localhost:8080/completion"):
        """Initialize inline grammar checker"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}╔═══════════════════════════════════════════════════════════╗{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}║     AI Inline Grammar Checker - Initialization           ║{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}╚═══════════════════════════════════════════════════════════╝{Colors.RESET}\n")
        
        self.pause_threshold = pause_threshold
        self.trigger_key = trigger_key
        self.llama_endpoint = llama_endpoint
        
        # Inline mode state
        self.inline_mode_active = False
        self.typing_buffer = []
        self.grammar_suggestion = None
        self.llm_is_processing = False
        
        # Timing
        self.last_keystroke_time = None
        self.pause_check_timer = None
        
        # Controllers
        self.kb_controller = Controller()
        
        # Keyboard inject script
        self.keyboard_inject_script = Path("keyboard_inject_V2.py")
        
        # Check dependencies
        print(f"{Colors.YELLOW}🔍 Checking dependencies...{Colors.RESET}")
        if self.keyboard_inject_script.exists():
            print_status(f"keyboard_inject.py found", True)
        else:
            print_status("keyboard_inject.py NOT FOUND - will use fallback", False)
        
        # Setup hotkeys
        print(f"\n{Colors.YELLOW}⌨️  Setting up hotkeys...{Colors.RESET}")
        self._setup_hotkeys()
        
        # Test LLM
        print(f"\n{Colors.YELLOW}🦙 Testing LLM connection...{Colors.RESET}")
        self._test_llm_connection()
        
        self.is_running = False
        
        print(f"\n{Colors.BOLD}{Colors.GREEN}✅ Initialization Complete!{Colors.RESET}\n")
        print(f"{Colors.CYAN}Configuration:{Colors.RESET}")
        print(f"  ⏱️  Pause threshold: {pause_threshold}s")
        print(f"  🔑 Accept key: '{trigger_key}'")
        print(f"  ✨ Toggle: Ctrl+Shift+R")
        print(f"  🦙 LLM: {llama_endpoint}")
    
    def _test_llm_connection(self):
        """Test LLM connectivity"""
        try:
            response = requests.get(self.llama_endpoint.replace('/completion', '/health'), timeout=2)
            print_status(f"LLM server reachable", True)
        except:
            print_status(f"LLM server NOT reachable", False)
            print(f"  {Colors.YELLOW}⚠️  Start llama.cpp server first!{Colors.RESET}")
    
    def _setup_hotkeys(self):
        """Setup hotkeys"""
        self.hotkeys = {}
        
        try:
            # Ctrl+Shift+R to toggle inline mode
            self.hotkeys['toggle'] = HotKey(
                HotKey.parse('<ctrl>+<shift>+r'),
                self._toggle_inline_mode
            )
            print_status("Toggle hotkey (Ctrl+Shift+R) registered", True)
            
        except Exception as e:
            print_status(f"Hotkey registration failed: {e}", False)
    
    def _toggle_inline_mode(self):
        """Toggle inline grammar checking mode"""
        self.inline_mode_active = not self.inline_mode_active
        
        if self.inline_mode_active:
            print(f"\n{Colors.BOLD}{Colors.GREEN}✨ INLINE GRAMMAR MODE ENABLED ✨{Colors.RESET}")
            print(f"{Colors.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.RESET}")
            print(f"  📝 Type naturally")
            print(f"  ⏸️  Pause for {self.pause_threshold}s → Auto grammar check")
            print(f"  ✅ Press '{self.trigger_key}' to accept correction")
            print(f"  ❌ Keep typing to discard and start over")
            print(f"  🔄 Ctrl+Shift+R to disable")
            print(f"{Colors.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.RESET}\n")
            
            # Reset state
            self.typing_buffer = []
            self.grammar_suggestion = None
            
        else:
            print(f"\n{Colors.BOLD}{Colors.YELLOW}✨ INLINE GRAMMAR MODE DISABLED{Colors.RESET}")
            print(f"{Colors.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.RESET}\n")
            
            # Clean up
            self.typing_buffer = []
            self.grammar_suggestion = None
    
    def _call_llm_grammar(self, text):
        """Call LLM for grammar check in subprocess"""
        if self.llm_is_processing:
            print(f"{Colors.YELLOW}⚠️  LLM busy, skipping{Colors.RESET}")
            return None
        
        self.llm_is_processing = True
        
        try:
            # Call LLM processor
            result = subprocess.run([
                'python',
                'llm_processor.py',
                self.llama_endpoint,
                'grammar',
                text
            ], timeout=10, capture_output=True, text=True)
            
            if result.returncode == 0:
                response = result.stdout.strip()
                
                if response.startswith("ERROR:"):
                    print(f"{Colors.RED}❌ {response}{Colors.RESET}")
                    self.llm_is_processing = False
                    return None
                
                self.llm_is_processing = False
                return response
            else:
                print(f"{Colors.RED}❌ LLM process failed{Colors.RESET}")
                self.llm_is_processing = False
                return None
            
        except subprocess.TimeoutExpired:
            print(f"{Colors.YELLOW}⚠️  LLM timeout{Colors.RESET}")
            self.llm_is_processing = False
            return None
        except Exception as e:
            print(f"{Colors.RED}❌ Error: {e}{Colors.RESET}")
            self.llm_is_processing = False
            return None
    
    def _inject_text(self, delete_count, new_text):
        """Inject text using keyboard_inject.py or fallback"""
        
        # Try keyboard_inject.py
        if self.keyboard_inject_script.exists():
            try:
                result = subprocess.run([
                    'python',
                    str(self.keyboard_inject_script),
                    new_text,
                    '--backspace', str(delete_count),
                    '--humanize', 'false'
                ], timeout=60, capture_output=True, text=True)
                
                if result.returncode == 0:
                    return True
            except Exception as e:
                print(f"{Colors.YELLOW}⚠️  keyboard_inject_V2.py failed: {e}{Colors.RESET}")
        
        # Fallback: direct pynput
        for _ in range(delete_count):
            self.kb_controller.press(Key.backspace)
            self.kb_controller.release(Key.backspace)
            time.sleep(0.01)
        
        time.sleep(0.05)
        
        for char in new_text:
            try:
                self.kb_controller.press(char)
                self.kb_controller.release(char)
            except:
                self.kb_controller.type(char)
            time.sleep(0.01)
        
        return True
    
    def _check_and_suggest_grammar(self):
        """Check if we should run grammar check"""
        if not self.typing_buffer:
            return
        
        # Wait for pause threshold
        time.sleep(self.pause_threshold + 0.1)
        
        # Check if still paused
        if self.last_keystroke_time:
            current_pause = time.time() - self.last_keystroke_time
            
            if current_pause >= self.pause_threshold and len(self.typing_buffer) > 2:
                # Get typed text
                typed_text = "".join(self.typing_buffer)
                
                print(f"\n{Colors.CYAN}⏸️  Pause detected ({current_pause:.1f}s){Colors.RESET}")
                print(f"{Colors.BLUE}🔍 Checking grammar...{Colors.RESET}")
                print(f"   Text: \"{typed_text[:60]}{'...' if len(typed_text) > 60 else ''}\"")
                
                # Call LLM
                suggestion = self._call_llm_grammar(typed_text)
                
                if suggestion and suggestion.strip() != typed_text.strip():
                    self.grammar_suggestion = suggestion
                    
                    print(f"\n{Colors.GREEN}💡 SUGGESTION READY!{Colors.RESET}")
                    print(f"{Colors.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.RESET}")
                    print(f"{Colors.YELLOW}Original:{Colors.RESET}")
                    print(f"  {typed_text}")
                    print(f"{Colors.GREEN}Corrected:{Colors.RESET}")
                    print(f"  {suggestion}")
                    print(f"{Colors.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.RESET}")
                    print(f"  ✅ Press '{self.trigger_key}' to ACCEPT")
                    print(f"  ❌ Keep typing to DISCARD\n")
                    
                else:
                    print(f"{Colors.BLUE}✓ No corrections needed{Colors.RESET}\n")
                    self.grammar_suggestion = None
    
    def on_press(self, key):
        """Handle key press"""
        if not self.is_running:
            return
        
        try:
            # Update hotkeys
            for hotkey in self.hotkeys.values():
                hotkey.press(self.kb_listener.canonical(key))
            
            # Only process if inline mode is active
            if not self.inline_mode_active:
                return
            
            current_time = time.time()
            
            # ===== TRIGGER KEY (ACCEPT SUGGESTION) =====
            if hasattr(key, 'char') and key.char == self.trigger_key:
                if self.grammar_suggestion:
                    print(f"\n{Colors.GREEN}✅ ACCEPTING CORRECTION{Colors.RESET}")
                    
                    # Get original text
                    original_text = "".join(self.typing_buffer)
                    
                    # Replace with corrected version
                    success = self._inject_text(len(original_text), self.grammar_suggestion)
                    
                    if success:
                        print(f"{Colors.GREEN}✓ Text replaced successfully{Colors.RESET}\n")
                        
                        # Update buffer with new text
                        self.typing_buffer = list(self.grammar_suggestion)
                        self.grammar_suggestion = None
                else:
                    print(f"{Colors.YELLOW}⚠️  No suggestion to accept{Colors.RESET}")
                
                self.last_keystroke_time = current_time
                return
            
            # ===== NORMAL TYPING =====
            
            # Check if user typed after a pause (discard old suggestion)
            if self.last_keystroke_time:
                time_since_last = current_time - self.last_keystroke_time
                
                if time_since_last >= self.pause_threshold and self.grammar_suggestion:
                    print(f"\n{Colors.YELLOW}🗑️  DISCARDING old suggestion (user resumed typing){Colors.RESET}\n")
                    self.grammar_suggestion = None
                    
                    # Start fresh buffer
                    self.typing_buffer = []
            
            # Process the key
            if hasattr(key, 'char') and key.char is not None:
                char = key.char
                self.typing_buffer.append(char)
                
            elif key == Key.backspace:
                if self.typing_buffer:
                    self.typing_buffer.pop()
                
                # Discard suggestion on edit
                if self.grammar_suggestion:
                    print(f"{Colors.YELLOW}🗑️  Suggestion discarded (text edited){Colors.RESET}")
                    self.grammar_suggestion = None
                
            elif key == Key.space:
                self.typing_buffer.append(' ')
                
            elif key == Key.enter:
                # Reset on enter
                self.typing_buffer = []
                self.grammar_suggestion = None
            
            # Update timestamp
            self.last_keystroke_time = current_time
            
            # Cancel previous timer if exists
            if self.pause_check_timer:
                self.pause_check_timer.cancel()
            
            # Start new pause check timer
            self.pause_check_timer = threading.Timer(
                self.pause_threshold + 0.1,
                self._check_and_suggest_grammar
            )
            self.pause_check_timer.daemon = True
            self.pause_check_timer.start()
            
        except Exception as e:
            print(f"{Colors.RED}⚠️  Error: {e}{Colors.RESET}")
    
    def on_release(self, key):
        """Handle key release"""
        # Update hotkeys
        for hotkey in self.hotkeys.values():
            hotkey.release(self.kb_listener.canonical(key))
        
        if key == Key.esc:
            print(f"\n{Colors.YELLOW}🛑 ESC pressed - stopping...{Colors.RESET}")
            self.stop()
            return False
    
    def start(self):
        """Start monitoring"""
        if self.is_running:
            return
        
        self.is_running = True
        
        print(f"\n{Colors.BOLD}{Colors.GREEN}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.GREEN}🚀 Inline Grammar Checker Started!{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.GREEN}{'='*60}{Colors.RESET}\n")
        print(f"{Colors.CYAN}Controls:{Colors.RESET}")
        print(f"  ✨ Ctrl+Shift+R → Toggle inline mode")
        print(f"  🔑 '{self.trigger_key}' → Accept suggestion")
        print(f"  🛑 ESC → Stop")
        print(f"{Colors.BOLD}{Colors.GREEN}{'='*60}{Colors.RESET}\n")
        
        # Start keyboard listener
        with Listener(on_press=self.on_press, on_release=self.on_release) as listener:
            self.kb_listener = listener
            listener.join()
    
    def stop(self):
        """Stop monitoring"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Cancel timer
        if self.pause_check_timer:
            self.pause_check_timer.cancel()
        
        print(f"\n{Colors.BOLD}{Colors.YELLOW}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.YELLOW}🛑 Grammar Checker Stopped{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.YELLOW}{'='*60}{Colors.RESET}\n")


def main():
    print(f"{Colors.BOLD}{Colors.CYAN}")
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║     AI Inline Grammar Checker - Standalone               ║")
    print("║     Press Ctrl+Shift+R to toggle                          ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print(f"{Colors.RESET}\n")
    
    checker = InlineGrammarChecker(
        pause_threshold=2.0,
        trigger_key='`',
        llama_endpoint="http://localhost:8080/completion"
    )
    
    try:
        checker.start()
    except KeyboardInterrupt:
        checker.stop()
    except Exception as e:
        print(f"\n{Colors.RED}❌ Error: {e}{Colors.RESET}")
        checker.stop()


if __name__ == "__main__":
    main()