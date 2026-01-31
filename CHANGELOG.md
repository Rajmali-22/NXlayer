# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Coding Mode: Toggle in settings for interview support
  - Separate explanation window showing code walkthrough
  - Two API calls: one for code, one for explanation
- Code snippet detection: Copy code to get detailed explanation
- Smart detection for DSA categories (DP, Graph, Tree, etc.)
- System design and behavioral interview prompts
- Streaming AI responses for lower latency
- 42 unit tests covering all major components

### Changed
- Cleaned up AI backend service (removed debug logs)
- Improved API key loading (skips placeholder keys)
- Streamlined smart prompts detection

### Removed
- Legacy `text_ai_backend.py` (replaced by streaming version)
- Unused `parse_code_response()` and `is_code_problem()` functions

### Fixed
- API key validation now properly rejects keys containing "your-"
- Streaming chunks now correctly sent to output window

## [1.0.0] - 2025-01-01

### Added
- Initial release
- Electron app with global shortcuts
- Keystroke monitoring with privacy filters
- AI text generation via Mistral API
- Multiple trigger modes: backtick, clipboard, voice, live
- Grammar correction (backtick trigger)
- Smart prompt detection (email, code, question, etc.)
- Text injection via keyboard simulation
- Settings panel with toggles
- Screenshot + vision analysis
- Voice input (hold-to-talk)
- Auto-inject mode
- Live mode (auto-suggest on pause)
- Human-like typing option
