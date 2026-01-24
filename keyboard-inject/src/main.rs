use std::env;
use windows::{
    Win32::UI::Input::KeyboardAndMouse::*,
};

fn send_key_input(vkey: u8, flags: KEYBD_EVENT_FLAGS) {
    unsafe {
        keybd_event(vkey, 0, flags, 0);
    }
}

fn send_text(text: &str) {
    // Small delay to ensure target window is ready
    std::thread::sleep(std::time::Duration::from_millis(50));
    
    unsafe {
        for ch in text.chars() {
            let (vkey, shift_needed) = get_virtual_key(ch);
            
            // Press Shift if needed
            if shift_needed {
                send_key_input(VK_SHIFT.0 as u8, KEYBD_EVENT_FLAGS(0));
            }
            
            // Press the key
            send_key_input(vkey, KEYBD_EVENT_FLAGS(0));
            
            // Release the key
            send_key_input(vkey, KEYBD_EVENT_FLAGS(KEYEVENTF_KEYUP));
            
            // Release Shift if it was pressed
            if shift_needed {
                send_key_input(VK_SHIFT.0 as u8, KEYBD_EVENT_FLAGS(KEYEVENTF_KEYUP));
            }
            
            // Minimal delay between characters (1ms for speed)
            std::thread::sleep(std::time::Duration::from_millis(1));
        }
    }
}

fn get_virtual_key(ch: char) -> (u8, bool) {
    match ch {
        'a'..='z' => ((ch as u8 - b'a' + b'A') as u8, false),
        'A'..='Z' => (ch as u8, true),
        '0'..='9' => (ch as u8, false),
        ' ' => (VK_SPACE.0 as u8, false),
        '\n' => (VK_RETURN.0 as u8, false),
        '\t' => (VK_TAB.0 as u8, false),
        _ => {
            // For special characters, use VkKeyScan
            unsafe {
                let scan = VkKeyScanW(ch as u16);
                let vkey = (scan.0 & 0xFF) as u8;
                let shift = (scan.0 & 0x0100) != 0;
                
                if vkey != 0 {
                    (vkey, shift)
                } else {
                    // Fallback: map common characters
                    match ch {
                        '.' => (VK_OEM_PERIOD.0 as u8, false),
                        ',' => (VK_OEM_COMMA.0 as u8, false),
                        '!' => (VK_1.0 as u8, true),
                        '@' => (VK_2.0 as u8, true),
                        '#' => (VK_3.0 as u8, true),
                        '$' => (VK_4.0 as u8, true),
                        '%' => (VK_5.0 as u8, true),
                        '^' => (VK_6.0 as u8, true),
                        '&' => (VK_7.0 as u8, true),
                        '*' => (VK_8.0 as u8, true),
                        '(' => (VK_9.0 as u8, true),
                        ')' => (VK_0.0 as u8, true),
                        '-' => (VK_OEM_MINUS.0 as u8, false),
                        '=' => (VK_OEM_PLUS.0 as u8, false),
                        '[' => (VK_OEM_4.0 as u8, false),
                        ']' => (VK_OEM_6.0 as u8, false),
                        '\\' => (VK_OEM_5.0 as u8, false),
                        ';' => (VK_OEM_1.0 as u8, false),
                        '\'' => (VK_OEM_7.0 as u8, false),
                        '/' => (VK_OEM_2.0 as u8, false),
                        '`' => (VK_OEM_3.0 as u8, false),
                        _ => (ch as u8, false),
                    }
                }
            }
        }
    }
}

fn main() {
    let args: Vec<String> = env::args().collect();
    
    if args.len() < 2 {
        eprintln!("Usage: keyboard-inject <text>");
        std::process::exit(1);
    }
    
    let text = &args[1];
    
    // Split by newlines and send each line
    let lines: Vec<&str> = text.split('\n').collect();
    
    for (i, line) in lines.iter().enumerate() {
        if !line.is_empty() {
            send_text(line);
        }
        
        // Press Enter after each line except the last
        if i < lines.len() - 1 {
            unsafe {
                send_key_input(VK_RETURN.0 as u8, KEYBD_EVENT_FLAGS(0));
                send_key_input(VK_RETURN.0 as u8, KEYBD_EVENT_FLAGS(KEYEVENTF_KEYUP));
            }
            std::thread::sleep(std::time::Duration::from_millis(10));
        }
    }
}
