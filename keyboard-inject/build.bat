@echo off
echo Building Rust keyboard injector...
cargo build --release
if %ERRORLEVEL% EQU 0 (
    echo Build successful!
) else (
    echo Build failed! Make sure Rust is installed.
    pause
)
