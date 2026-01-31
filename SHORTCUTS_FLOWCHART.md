# AI Text Bot — Shortcuts Flowchart

## Main flowchart: User presses shortcut → outcome

```mermaid
flowchart TD
    START([User presses shortcut])
    START --> K1{Ctrl+Shift+Space?}
    START --> K2{Ctrl+Shift+P?}
    START --> K3{Ctrl+Alt+Enter?}
    START --> K4{Ctrl+Shift+D?}
    START --> K5{Ctrl+Shift+F?}
    START --> K6{Ctrl+Shift+V?}
    START --> K7{Escape?}
    START --> K8{Ctrl+.?}

    K1 -->|Yes| A1[Show or hide overlay window]
    A1 --> END1([Done])

    K2 -->|Yes| A2{Last suggestion exists?}
    A2 -->|Yes| A2a[Hide windows → keyboard_inject or robotjs paste]
    A2 -->|No| A2b[Nothing]
    A2a --> END2([Done])
    A2b --> END2

    K3 -->|Yes| A3[Send buffer to keystroke monitor]
    A3 --> A3a{Buffer type?}
    A3a -->|Plain text| B1[Backtick: grammar fix]
    A3a -->|After recent trigger, no typing| B2[Extension: continue writing]
    A3a -->|Command-like| B3[Instruction mode]
    B1 --> C1[text_ai_backend → Mistral]
    B2 --> C1
    B3 --> C1
    C1 --> C2{Auto-inject ON?}
    C2 -->|Yes| C2a[Inject at cursor]
    C2 -->|No| C2b[Show suggestion popup]
    C2a --> END3([Done])
    C2b --> END3

    K4 -->|Yes| A4[Read clipboard + typed buffer]
    A4 --> A4a{Buffer has instruction?}
    A4a -->|Yes| D1[clipboard_with_instruction]
    A4a -->|No| D2[clipboard auto-detect]
    D1 --> D3[text_ai_backend → Mistral]
    D2 --> D3
    D3 --> D4[Show popup or inject]
    D4 --> END4([Done])

    K5 -->|Yes| A5[Show vision popup for instruction]
    A5 --> A5a[User types instruction or leaves blank]
    A5a --> A5b[Hide window → screenshot]
    A5b --> A5c[screenshot_vision.py → Anthropic]
    A5c --> A5d[Show result in popup]
    A5d --> END5([Done])

    K6 -->|Yes| A6[Start or stop voice recording]
    A6 --> A6a{Recording?}
    A6a -->|Start| A6b[voice_transcribe.py records]
    A6a -->|Stop| A6c[Transcribe → append to overlay prompt]
    A6c --> END6([Done])

    K7 -->|Yes| A7[Close popup / clear state]
    A7 --> END7([Done])

    K8 -->|Yes| A8[Pause or resume keyboard injection]
    A8 --> END8([Done])
```

---

## Simplified: Shortcut → Action (one line each)

```mermaid
flowchart LR
    subgraph Shortcuts
        S1[Ctrl+Shift+Space]
        S2[Ctrl+Shift+P]
        S3[Ctrl+Alt+Enter]
        S4[Ctrl+Shift+D]
        S5[Ctrl+Shift+F]
        S6[Ctrl+Shift+V]
        S7[Escape]
        S8[Ctrl+.]
    end

    subgraph Actions
        A1[Toggle overlay]
        A2[Paste last suggestion]
        A3[Trigger: grammar / extend / instruction]
        A4[Clipboard + optional instruction]
        A5[Screenshot + Vision]
        A6[Voice record / stop]
        A7[Cancel]
        A8[Pause / resume injection]
    end

    S1 --> A1
    S2 --> A2
    S3 --> A3
    S4 --> A4
    S5 --> A5
    S6 --> A6
    S7 --> A7
    S8 --> A8
```

---

## Trigger flow (Ctrl+Alt+Enter) detail

```mermaid
flowchart TD
    T1([Ctrl+Alt+Enter])
    T1 --> T2[Keystroke monitor sends trigger event]
    T2 --> T3[main.js receives buffer + window + app_category]
    T3 --> T4{Context mode ON?}
    T4 -->|Yes| T5[Add profile + app rules + memory]
    T4 -->|No| T6[Standard prompt]
    T5 --> T7[text_ai_backend.py]
    T6 --> T7
    T7 --> T8{Trigger type?}
    T8 -->|backtick| T9[Grammar fix mode]
    T8 -->|extension| T10[Continue writing mode]
    T8 -->|instruction| T11[Instruction mode]
    T9 --> T12[Mistral API]
    T10 --> T12
    T11 --> T12
    T12 --> T13{Auto-inject ON?}
    T13 -->|Yes| T14[Inject at cursor]
    T13 -->|No| T15[Show popup → user Ctrl+Shift+P to paste]
    T14 --> T16([Done])
    T15 --> T16
```

---

## Viewing the flowcharts

- **GitHub / GitLab:** Open this `.md` file; Mermaid diagrams render automatically.
- **VS Code:** Install "Markdown Preview Mermaid Support" and preview the file.
- **Online:** Copy the ` ```mermaid ` blocks into [mermaid.live](https://mermaid.live) to edit or export as PNG/SVG.
