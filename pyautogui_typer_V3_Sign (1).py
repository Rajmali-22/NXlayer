#!/usr/bin/env python3
"""
CODE TYPER - Fixed Indentation
Enter → Home → Spaces (to handle auto-indent in VS Code/LeetCode)
"""

import sys
import os
import re
import time
import random
from mistralai import Mistral
import pyautogui

# Config
MIN_DELAY = 0.08
MAX_DELAY = 0.15
PAUSE_BETWEEN_LINES = (0.1, 0.3)

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.08

# ============================================================================
# MISTRAL
# ============================================================================

def load_api_key():
    api_key = os.getenv('MISTRAL_API_KEY')
    if api_key:
        return api_key
    
    for config_file in ['.env', 'config.env']:
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    for line in f:
                        if 'MISTRAL_API_KEY' in line:
                            match = re.search(r'MISTRAL_API_KEY\s*=\s*([^\s#\n]+)', line)
                            if match:
                                key = match.group(1).strip().strip('"').strip("'")
                                if key and key != 'your-api-key-here':
                                    return key
            except:
                pass
    return None

def init_llm():
    api_key = load_api_key()
    if not api_key:
        print("❌ MISTRAL_API_KEY not found!")
        sys.exit(1)
    return Mistral(api_key=api_key)

def generate_code(client, problem, presignature):
    """Generate code to type inside presignature"""
    
    prompt = f"""Complete this function:

{presignature}

Problem: {problem}

CRITICAL RULES:
- NO comments
- NO extra docstrings
- Helper functions INSIDE class at SAME indentation as main method
- Output code with EXACT indentation (count every space)
- Each line must have correct number of leading spaces

Example format if presignature is:
class Solution:
    def method(self):

Then your output should be:
        helper_var = 5
        result = helper_var * 2
        return result

(Note: 8 spaces for code inside method, 4 more for nested blocks)

Output ONLY the code lines (with exact spaces):"""
    
    print("[LLM] Generating code...")
    
    response = client.chat.complete(
        model="mistral-small-latest",
        messages=[{"role": "user", "content": prompt}]
    )
    
    code = response.choices[0].message.content.strip()
    
    # Clean markdown
    code = re.sub(r'```python\n', '', code)
    code = re.sub(r'```', '', code)
    
    # Remove comments
    lines = []
    for line in code.split('\n'):
        # Remove inline comments
        if '#' in line:
            line = line.split('#')[0].rstrip()
        lines.append(line)
    
    code = '\n'.join(lines)
    
    print("✅ Code generated")
    return code

# ============================================================================
# TYPING WITH PROPER INDENTATION
# ============================================================================

def analyze_indentation(code):
    """Pre-analyze indentation for each line"""
    lines = code.split('\n')
    line_info = []
    
    for idx, line in enumerate(lines):
        # Count leading spaces
        num_spaces = 0
        for char in line:
            if char == ' ':
                num_spaces += 1
            else:
                break
        
        stripped = line.lstrip()
        
        line_info.append({
            'index': idx,
            'raw': line,
            'spaces': num_spaces,
            'content': stripped,
            'is_empty': not stripped
        })
    
    return line_info

def type_code(code):
    """Type code with Enter→Home→Spaces pattern"""
    
    line_info = analyze_indentation(code)
    
    print("\n" + "="*70)
    print("INDENTATION ANALYSIS:")
    print("="*70)
    for info in line_info:
        if not info['is_empty']:
            print(f"Line {info['index']+1}: {info['spaces']} spaces | {info['content'][:50]}")
    print("="*70)
    
    print("\n🎬 TYPING...\n")
    
    for idx, info in enumerate(line_info):
        # Random pause between lines
        if idx > 0:
            pause = random.uniform(*PAUSE_BETWEEN_LINES)
            time.sleep(pause)
        
        # For every line except the first:
        # 1. Press Enter (creates new line, may auto-indent)
        # 2. Press Home (go to leftmost - resets any auto-indent)
        # 3. Press Space N times (manual indentation control)
        
        if idx > 0:
            print(f"\n  [ENTER] New line")
            pyautogui.press('enter')
            time.sleep(0.08)
            
            print(f"  [HOME] Reset to left")
            pyautogui.press('home')
            time.sleep(0.08)
        
        # Handle empty lines
        if info['is_empty']:
            print(f"  [LINE {idx+1}] Empty line (skip)")
            continue
        
        # Type indentation (spaces)
        if info['spaces'] > 0:
            print(f"  [INDENT] {info['spaces']} spaces")
            for _ in range(info['spaces']):
                pyautogui.press('space')
                time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
        
        # Type the content
        print(f"  [TYPE] {info['content'][:60]}")
        for char in info['content']:
            pyautogui.write(char, interval=random.uniform(MIN_DELAY, MAX_DELAY))
    
    print("\n✅ TYPING COMPLETE")

# ============================================================================
# MAIN
# ============================================================================

def main():
    if len(sys.argv) < 3:
        print("""
CODE TYPER - Fixed Indentation

USAGE:
    python typer.py "problem" "presignature"

EXAMPLE:
    python typer.py "two sum" 'class Solution(object):
    def twoSum(self, nums, target):
        """

        """
        '

HOW IT WORKS:
1. Cursor should be at the position where typing starts
2. For each line: Enter → Home → Space×N → Type content
3. This handles auto-indent in VS Code/LeetCode
4. Presignature is never touched/erased

IMPORTANT:
- Place cursor EXACTLY where code should start
- Don't touch presignature after placing cursor
- Script will handle all indentation with spaces
""")
        sys.exit(1)
    
    problem = sys.argv[1]
    presignature = sys.argv[2]
    
    print("\n" + "="*70)
    print("CODE TYPER - FIXED INDENTATION")
    print("="*70)
    
    # Init LLM
    client = init_llm()
    print("✅ Mistral ready")
    
    # Generate code
    code = generate_code(client, problem, presignature)
    
    print("\n" + "="*70)
    print("GENERATED CODE:")
    print("="*70)
    print(code)
    print("="*70)
    
    # Show what will happen
    print("\n" + "="*70)
    print("TYPING SEQUENCE:")
    print("="*70)
    print("Line 1: Type directly (cursor already positioned)")
    print("Line 2+: Enter → Home → Space×N → Type content")
    print("="*70)
    
    # Countdown
    print("\n⏰ Starting in 3 seconds")
    print("🏃 Place cursor EXACTLY where code should start!")
    print("⚠️  DO NOT touch presignature")
    print("⚠️  Mouse to corner = abort\n")
    
    for i in range(3, 0, -1):
        print(f"   {i}...")
        time.sleep(1)
    
    # Type
    type_code(code)
    
    print("\n" + "="*70)
    print("EXPECTED RESULT:")
    print("="*70)
    print(presignature)
    print(code)
    print("="*70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️ Stopped by user")
    except pyautogui.FailSafeException:
        print("\n⚠️ FAILSAFE - Mouse in corner")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()