# Prompt: Run and Check AI-Text-Bot Test Suite

Copy the text below and send it to Claude (or another AI) to have it run and verify the project’s tests.

---

## Instructions for Claude

You are in the **ai-text-bot** project (Electron + Python AI typing assistant). Please do the following:

1. **Run the full test suite**
   - From the project root, run: `python -m pytest tests/ -v`
   - If `pytest` is missing, run: `pip install pytest` (or `pip install -r requirements.txt`) first.

2. **Confirm results**
   - Report how many tests ran and how many passed/failed.
   - If any test fails, show the failure output and suggest a fix (code or test) so all tests pass.

3. **Scope of the test suite (30+ test cases)**
   - **ai_backend_service**: API key loading (env, missing, “your-key” skip), `clean_response` (empty, subject line, normal), `build_messages` (backtick, extension, clipboard, prompt, explanation), `handle_request` (ping, unknown command, empty prompt).
   - **smart_prompts**: `detect_text_type` (email, system_design, behavioral, code/dp, term, question, general), `build_prompt` (custom instruction, auto-detect), `clean_output` (code fence, bold, preambles, empty).
   - **keyboard_inject**: `unescape_text`, `get_typing_delay`, `get_typo_char`, `SHIFT_CHARS` / `SPECIAL_KEYS`.
   - **text_ai_backend**: `_build_context_section` (empty, recipient/purpose, length/style).
   - **keystroke_monitor**: `State.reset_buffer`, `Config` constants.
   - **screenshot_vision**: `load_api_key` from env.
   - **voice_transcribe**: `transcribe_audio` (error on UnknownValueError, success returns `{ "text": "..." }`).

4. **Optional**
   - If you can run commands: execute `python -m pytest tests/ -v` and paste the output.
   - If you cannot run commands: list what each test is intended to verify and what could cause failures (e.g. missing env, wrong mocks, import path).

Please respond with: (1) command you ran, (2) test count and pass/fail summary, (3) any failures and suggested fixes, (4) optional coverage or improvement suggestions.

---

**Project root**: directory containing `main.js`, `ai_backend_service.py`, `smart_prompts.py`, `keyboard_inject.py`, `text_ai_backend.py`, `keystroke_monitor/`, `screenshot_vision.py`, `voice_transcribe.py`, and the `tests/` folder.
