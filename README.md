# ⚡ WorkspaceAI — Intelligent Windows Tab & Workspace Manager

> A lightweight, privacy-first desktop assistant that helps you manage all open windows and applications using AI-powered semantic search and optional voice commands — no cloud required.

---

## 📌 Project Overview

WorkspaceAI sits on top of Windows and gives you a clean, organized view of every open application. Instead of Alt-Tabbing through a sea of windows, you can:

- **Type or speak** natural language commands like *"find my Python tutorial"*
- **Auto-group** windows into Work / Study / Entertainment with one AI click
- **Save workspace sessions** and restore them in a single click
- **Search semantically** — it understands *meaning*, not just keywords

All processing happens **100% locally** on your machine. Nothing is sent to the cloud.

---

## ⚙️ Installation Steps

### Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.10 or higher |
| Windows | 10 / 11 (for full window control) |
| RAM | 4 GB minimum (8 GB recommended) |
| Disk | ~500 MB (model weights + dependencies) |

### Step 1 — Clone the repository

```bash
git clone https://github.com/your-username/workspace-ai.git
cd workspace-ai
```

### Step 2 — Create a virtual environment (recommended)

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
```

### Step 3 — Install core dependencies

```bash
pip install -r requirements.txt
```

> **Note:** The first run will automatically download the AI embedding model (~22 MB). This is a one-time download.

### Step 4 — (Optional) Enable Voice Commands

**Option A — Vosk (fully offline, ~50 MB model)**

```bash
pip install vosk sounddevice scipy

# Download the small English model:
# https://alphacephei.com/vosk/models → vosk-model-small-en-us-0.15
# Extract to: models/vosk-model-small-en-us/
```

**Option B — Whisper-tiny (offline, ~150 MB model)**

```bash
pip install openai-whisper sounddevice scipy
```

---

## ▶️ How to Run

### Quick Launch (Windows)

```
Double-click run.bat
```

### Command Line

```bash
python main.py
```

### macOS / Linux (demo mode — no real window control)

```bash
bash run.sh
```

The app launches in **demo mode** on non-Windows systems, showing simulated windows so you can explore the UI without Windows APIs.

---

## 🧠 AI Model Explanation

### Embedding Model: `all-MiniLM-L6-v2`

| Property | Value |
|---|---|
| **Size** | ~22 MB (weights) |
| **Parameters** | ~22 million |
| **Embedding dimensions** | 384 |
| **Inference speed** | < 10ms per query on CPU |
| **RAM usage** | ~80 MB loaded |

**Why this model?**

`all-MiniLM-L6-v2` is a distilled version of a larger BERT model, specifically optimized for semantic similarity tasks. It was chosen because:

1. **It is tiny** — at 22 MB it loads in under a second
2. **It is accurate** — despite its size, it scores well on semantic textual similarity benchmarks
3. **It runs on CPU** — no GPU required, making it accessible on any laptop
4. **It is truly offline** — after the first download, zero internet access is needed

### Fallback: TF-IDF

When `sentence-transformers` is not installed, the app automatically falls back to a built-in TF-IDF index. This requires zero additional downloads and still provides good keyword-based matching.

### Intent Parser

A lightweight rule-based intent parser (no LLM needed) handles commands like:
- `"find X"` → search intent
- `"close X"` → close intent  
- `"switch to Work"` → group switch
- `"save session morning"` → session save

No 1B+ parameter LLM is required for basic command understanding — the rule engine covers the MVP. The architecture is ready to plug in a quantized TinyLlama or Phi-2 model for more complex reasoning if desired.

---

## 🎤 Voice Command Usage Guide

### Setup

1. Install a voice backend (see Installation Step 4)
2. If using Vosk: download and extract the model to `models/vosk-model-small-en-us/`
3. Ensure your microphone is connected and set as default

### Activating Voice

- Click the **🎤 button** in the top-right of the toolbar
- The button turns red while listening
- Speak your command clearly
- The command is processed automatically

### Example Voice Commands

| Say | Action |
|---|---|
| `"Find my Python tutorial"` | Searches and focuses matching window |
| `"Open Visual Studio Code"` | Finds and focuses VS Code |
| `"Switch to Work workspace"` | Switches to Work group |
| `"Close Spotify"` | Closes Spotify window |
| `"Minimize Slack"` | Minimizes Slack |
| `"Save session morning work"` | Saves current layout as "morning work" |

### Demo Mode (no microphone)

Click the 🎤 button and type your command in the text dialog. Identical processing applies.

---

## 🗂️ Feature Breakdown

### 1. Window Detection
- Enumerates all visible, non-empty windows using `win32gui`
- Extracts: title, process name, PID, position, minimize state
- Refreshes every 3 seconds automatically

### 2. Smart Grouping
- Automatic categorization using keyword heuristics:
  - **Work**: VS Code, Slack, Teams, Outlook, GitHub, Explorer…
  - **Study**: Tutorials, Stack Overflow, Documentation, YouTube…
  - **Entertainment**: Spotify, Netflix, Steam, Discord…
- Manual override via dropdown on each window card
- AI-powered bulk re-grouping with "🧠 Auto-Group All" button

### 3. Semantic Search
- Real-time embedding-based search across all window titles
- Finds windows by meaning, not just exact keywords
- Example: searching `"coding"` finds `"Visual Studio Code"` and `"GitHub"`
- Graceful fallback to TF-IDF when model not installed

### 4. Voice Commands
- Offline speech-to-text via Vosk or Whisper-tiny
- Natural language command parsing
- Maps speech to window actions

### 5. Session Management
- Save up to unlimited named sessions
- Sessions store: window list, groups, process names
- Restore attempts to match saved windows to currently open ones
- Sessions persisted as JSON files in `sessions/`

### 6. Modern UI
- Dark glassmorphic theme
- Color-coded workspace groups
- Process-specific emoji icons
- Live window count + status bar
- Smooth scan-refresh cycle

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **UI** | PyQt6 (native Windows feel) |
| **Window Control** | pywin32 (`win32gui`, `win32process`, `win32con`) |
| **Process Info** | psutil |
| **AI Embeddings** | sentence-transformers (`all-MiniLM-L6-v2`) |
| **Vector Math** | NumPy |
| **Voice (Option A)** | Vosk + sounddevice |
| **Voice (Option B)** | OpenAI Whisper-tiny + sounddevice |
| **Config** | JSON |
| **Sessions** | JSON flat files |
| **Language** | Python 3.10+ |

---

## 📁 Project Structure

```
workspace_manager/
├── main.py                  # Entry point — wires all modules together
├── requirements.txt         # Python dependencies
├── run.bat                  # Windows one-click launcher
├── run.sh                   # Unix launcher
│
├── core/
│   ├── __init__.py
│   ├── window_manager.py    # Window detection + control (pywin32)
│   └── session_manager.py   # Save / restore workspace sessions
│
├── ai/
│   ├── __init__.py
│   └── engine.py            # Semantic search + smart grouping + NL parser
│
├── voice/
│   ├── __init__.py
│   └── processor.py         # Speech-to-text (Vosk / Whisper)
│
├── ui/
│   ├── __init__.py
│   └── main_window.py       # PyQt6 dashboard UI
│
├── config/
│   ├── __init__.py          # Config loader with defaults
│   └── config.json          # User settings
│
├── models/
│   └── vosk-model-small-en-us/   # Vosk model (optional, download separately)
│
├── sessions/                # Auto-created; stores session JSON files
└── logs/
    └── app.log              # Runtime logs
```

---

## 🧪 Example Commands and Use Cases

### Typed Commands

```
find my python tutorial
```
→ Searches for windows related to Python tutorials and focuses the best match

```
open the document I was editing
```
→ Finds Word / Notepad windows and brings them to focus

```
switch to work workspace
```
→ Filters the view to show only Work-group windows

```
close spotify
```
→ Finds the Spotify window and closes it (with confirmation)

```
save session deep focus
```
→ Saves current window layout as "deep focus"

### Voice Commands (same text, spoken aloud)

```
"Find my GitHub tab"
"Switch to study workspace"  
"Minimize all entertainment apps"
"Open Visual Studio Code"
"Save session afternoon"
```

---

## 🚀 Future Improvements

| Feature | Description |
|---|---|
| **Browser integration** | Chrome/Firefox extension to read actual tab URLs and titles |
| **Global hotkey** | `Ctrl+Shift+Space` overlay toggle |
| **AI tab summaries** | Use a quantized Phi-2 or TinyLlama to summarize open tab content |
| **Usage pattern learning** | Track app usage frequency and suggest workspace changes |
| **Time-based suggestions** | Morning → Work mode, Evening → Entertainment mode |
| **Focus mode** | Hide all non-Work windows with one click |
| **Multi-monitor support** | Per-monitor window grouping |
| **System tray icon** | Run minimized to tray, pop up on hotkey |
| **Plugin API** | Let users write custom grouping rules or actions |
| **Whisper streaming** | Real-time transcription instead of buffered chunks |

---

## 🔒 Privacy

- **Zero data leaves your machine.** All AI inference runs locally.
- Window titles and process names are held **in RAM only** during the session.
- Sessions are stored as plain JSON files in the `sessions/` folder — you own your data.
- The embedding model is downloaded once from Hugging Face and cached locally.

---

## 🐛 Troubleshooting

**App won't start / PyQt6 error**
```bash
pip install --upgrade PyQt6
```

**Windows not detected (shows demo data)**
```bash
pip install pywin32 psutil
# Then run: python -m pywin32_postinstall -install
```

**AI search not working / slow**
```bash
pip install sentence-transformers torch
```

**Voice not working**
- Check your default microphone in Windows Sound Settings
- Make sure sounddevice is installed: `pip install sounddevice`
- For Vosk: confirm model folder path `models/vosk-model-small-en-us/` exists

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

*Built with ❤️ using Python, PyQt6, and lightweight AI.*
