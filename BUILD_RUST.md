# Building the Rust Keyboard Injector

The Rust keyboard injector provides fast, native keyboard input injection. Follow these steps to build it:

## Step 1: Install Rust

1. **Download Rust installer:**
   - Visit: https://rustup.rs/
   - Or run in PowerShell:
     ```powershell
     Invoke-WebRequest -Uri https://win.rustup.rs/x86_64 -OutFile rustup-init.exe
     .\rustup-init.exe
     ```

2. **After installation, restart your terminal/PowerShell**

3. **Verify installation:**
   ```bash
  
   cargo --version
   ```

## Step 2: Build the Injector

1. **Navigate to the keyboard-inject directory:**
   ```bash
   cd keyboard-inject
   ```

2. **Build in release mode (optimized):**
   ```bash
   cargo build --release
   ```

   Or use the batch file:
   ```bash
   build.bat
   ```

3. **The executable will be at:**
   ```
   keyboard-inject/target/release/keyboard-inject.exe
   ```

## Step 3: Test

After building, restart the Electron app. The Rust injector should now be detected automatically.

## Troubleshooting

- **"cargo: command not found"**: Rust is not installed or not in PATH. Restart terminal after installation.
- **Build errors**: Make sure you have the latest Rust toolchain: `rustup update`
- **Windows API errors**: The code uses Windows-specific APIs, so it only works on Windows.

## Alternative: Use Clipboard Fallback

If you don't want to install Rust, the app will automatically fall back to clipboard paste (Ctrl+V) method, which is also fast.
