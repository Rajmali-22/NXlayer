# Keyboard Injection Fallback Mechanism

The application has a robust multi-level fallback system for keyboard injection when using `Ctrl+Shift+P`:

## Fallback Chain (Priority Order)

### 1. **Primary Method: Rust Keyboard Injector** ⚡ (Fastest)
- **Location**: `keyboard-inject/target/release/keyboard-inject.exe` (or debug build)
- **How it works**: Native Windows API keyboard injection via Rust
- **Speed**: Instant (direct keyboard events)
- **When it fails**: 
  - Executable not found
  - Execution error
  - Permission issues

### 2. **Fallback 1: Clipboard + robotjs Ctrl+V** 📋 (Fast)
- **How it works**: 
  1. Copy text to clipboard
  2. Use robotjs to simulate `Ctrl+V`
- **Speed**: Very fast (clipboard paste)
- **When it fails**:
  - robotjs not installed/compiled
  - robotjs permission issues
  - Clipboard write fails

### 3. **Fallback 2: Clipboard Only** 📋 (Manual)
- **How it works**: Copy text to clipboard only
- **Speed**: Instant (but requires manual `Ctrl+V`)
- **User action**: User must press `Ctrl+V` manually
- **When it fails**: Clipboard write fails (rare)

## Error Handling

All fallback levels include:
- ✅ Console logging for debugging
- ✅ Error catching and graceful degradation
- ✅ User-friendly error messages
- ✅ Automatic text clearing after successful/failed attempts

## Console Messages

The app will log:
- `"Rust injection successful"` - Primary method worked
- `"Falling back to clipboard method..."` - Primary method failed
- `"Fallback: Text pasted via clipboard + Ctrl+V"` - Fallback 1 worked
- `"Text copied to clipboard. Please press Ctrl+V manually."` - Fallback 2 (manual)
- `"All injection methods failed. Text could not be pasted."` - Complete failure

## Building Rust Injector

To use the fastest method, build the Rust injector:
```bash
cd keyboard-inject
cargo build --release
```

See `BUILD_RUST.md` for detailed instructions.
