# Discord Multi‑Tool

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![macOS](https://img.shields.io/badge/macOS-Silicon%20%7C%20Intel-brightgreen)](https://www.apple.com/macos/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Discord](https://img.shields.io/badge/Discord-PTB%20%7C%20Canary%20%7C%20Stable-5865F2)](https://discord.com)

A powerful multi‑tool for macOS that lets you run multiple Discord instances simultaneously with different accounts, and optionally auto‑complete quests on them.

---

## ✨ Features

- **Multiple Discord Instances** – Launch 2, 3, or more Discord windows side‑by‑side, each with its own account.
- **Account Manager** – Store and manage multiple Discord tokens with names and notes.
- **Auto‑Login** – Automatically inject tokens into new instances so you don’t have to log in manually.
- **Quest Helper** – Automatically detect and complete active Discord quests on running instances (video, play, stream, activity).
- **Dark Minimalist GUI** – Clean, black‑based interface with snowflake decorations and status indicators (inspired by blankboii.xyz).
- **Window Visibility Fixes** – Ensures windows actually appear on screen using multiple activation techniques.
- **Conflict Prevention** – Intelligently kills only unmanaged Discord processes, keeping your own instances and their children alive.
- **Isolated Data Directories** – Each account gets its own user data folder, preventing session conflicts.
- **Live Resource Monitoring** – See CPU and memory usage for each running instance.
- **Import/Export Accounts** – Easily backup or transfer your account list.

---

## 📋 Prerequisites

- **macOS 11.0+** (Big Sur or newer) – Intel or Apple Silicon.
- **Discord Desktop App** installed (Stable, PTB, or Canary).
- **Python 3.9+** (3.10 or 3.11 recommended).
- **Homebrew** (optional, for easy Python installation).

---

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/blan3bo1/Discord-Multitool.git
cd Discord-Multitool
```

### 2. Set up a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

If `requirements.txt` is not present, install the essential packages manually:
```bash
pip install psutil requests websocket-client pytz
```

### 4. Configure your Discord path
Edit `config.json` (it will be created automatically on first run) to match your Discord version:

```json
{
    "discord_path": "/Applications/Discord.app",
    "discord_executable": "Discord",          // "Discord PTB" or "Discord Canary" if needed
    "max_instances": 3,
    "instance_delay": 5,
    "debug_port_start": 9222,
    "injection_delay": 15,
    "auto_login": true,
    "auto_start_quests": false,
    "log_level": "INFO"
}
```

### 5. Add your accounts
Run the GUI and go to **Accounts** → **Add**, or manually edit `accounts.json` (a template will be created the first time you run the tool).

**Getting your Discord token:**
- Open Discord in your **browser** (not the app).
- Press `F12` to open Developer Tools.
- Go to the **Console** tab.
- Type: `localStorage.getItem('token')` and press Enter.
- Copy the output (remove the surrounding quotes).

### 6. Launch the GUI
```bash
python gui.py
```

---

## 🖥️ GUI Overview

The interface is split into three tabs:

### 📋 Accounts Tab
- List of all your accounts with their status (running/stopped), PID, port, CPU/memory usage.
- Buttons to launch selected accounts, launch all enabled, stop all, refresh, and manage accounts.
- **Selection is persistent** – even with auto‑refresh, your chosen accounts stay selected.
- Double‑click an account to edit its details.

### 🎮 Quest Helper Tab
- Run the quest‑completion script on selected accounts or on all running instances.
- Progress and errors are shown in the log area.

### ⚙️ Settings Tab
- Configure Discord path, executable name, instance limits, delays, and auto‑login.
- Changes are saved to `config.json`.

The footer displays the current time in PDT (matching blankboii.xyz), along with the "I'm Too Tired / dnd / Sleeping ngl is" status line.

---

## 📁 File Structure

```
Discord-Quest-Completer/
├── gui.py                     # Main GUI application
├── launcher.py                 # Terminal version (optional)
├── config.json                 # Configuration file
├── accounts.json               # Stored accounts (tokens)
├── requirements.txt            # Python dependencies
├── discord_manager/            # Core modules
│   ├── account_manager.py
│   ├── logger.py
│   └── utils.py
└── discord_quest_helper/       # Quest injection modules
    ├── injector.py
    ├── quest_helper.js
    └── logger.py
```

---

## ⚙️ Configuration Details

| Key                  | Description                                                                 | Default                     |
|----------------------|-----------------------------------------------------------------------------|-----------------------------|
| `discord_path`       | Path to the Discord `.app` bundle                                           | `/Applications/Discord.app` |
| `discord_executable` | Name of the executable inside `Contents/MacOS/`                             | `"Discord"`                 |
| `max_instances`      | Maximum concurrent Discord instances                                        | `3`                         |
| `instance_delay`     | Seconds to wait between launching instances                                 | `5`                         |
| `debug_port_start`   | Starting port for remote debugging                                          | `9222`                      |
| `injection_delay`    | Seconds to wait after launch before injecting quest helper                  | `15`                        |
| `auto_login`         | Automatically inject token via DevTools after launch                        | `false`                     |
| `auto_start_quests`  | Automatically run quest helper after launching                              | `false`                     |
| `log_level`          | Logging detail (`INFO`, `DEBUG`, `WARNING`, `ERROR`)                        | `"INFO"`                    |

---

## 🐛 Troubleshooting

| Problem                          | Possible Solution |
|----------------------------------|-------------------|
| `ModuleNotFoundError: No module named 'pytz'` | Install it: `pip install pytz` |
| Discord executable not found     | Check `discord_path` and `discord_executable` in `config.json`. Run `ls -la "/Applications/Discord.app/Contents/MacOS/"` to see actual executable names. |
| Second instance window doesn’t appear | Make sure you have granted Terminal/Accessibility permissions in **System Settings > Privacy & Security > Accessibility**. |
| Instances keep getting killed     | Our conflict killer now preserves child processes. If you still see killings, run `killall Discord` manually, then restart the launcher. |
| Auto‑login fails                  | Ensure the debug port is reachable: `curl http://localhost:9222/json/list`. Increase `injection_delay` in config. |
| Quest helper doesn’t complete quests | Discord may have updated its internal modules. The quest script may need an update. Check the console for errors. |
| `_tkinter.TclError: cannot use geometry manager grid inside ... pack` | This has been fixed in the latest GUI. If you still encounter it, ensure you are using the provided `gui.py` without modifications. |

---

## ⚠️ Disclaimer

**This tool is for educational purposes only.** Using it to automate Discord interactions violates Discord’s Terms of Service and may result in account suspension or termination. The author is not responsible for any consequences arising from the use of this software. Use at your own risk.

---

## 📄 License

MIT License – see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgements

- Thanks to @aamiaa https://gist.github.com/aamiaa/204cd9d42013ded9faf646fae7f89fbb
- Built with Python, Tkinter, and a lot of ❄.

---

**⭐ Star this repo if you find it useful!**  
[GitHub Repository](https://github.com/blan3bo1/Discord-Quest-Completer)
