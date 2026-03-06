# Discord Multi-Account Launcher & Quest Helper

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![macOS](https://img.shields.io/badge/macOS-Silicon%20%7C%20Intel-brightgreen)](https://www.apple.com/macos/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Discord](https://img.shields.io/badge/Discord-PTB%20%7C%20Canary%20%7C%20Stable-5865F2)](https://discord.com)

A powerful multi‑tool for macOS that allows you to run multiple Discord instances simultaneously with different accounts, and optionally auto‑complete quests on them.

---

## ✨ Features

- **Multiple Discord Instances** – Launch 2, 3, or more Discord windows side‑by‑side, each with its own account.
- **Account Manager** – Store and manage multiple Discord tokens with names and notes.
- **Auto‑Login** – Automatically inject tokens into new instances so you don't have to log in manually.
- **Quest Helper** – Automatically detect and complete active Discord quests on running instances (video, play, stream, activity).
- **Window Visibility Fixes** – Ensures windows actually appear on screen using multiple activation techniques.
- **Conflict Prevention** – Intelligently kills only unmanaged Discord processes, keeping your own instances and their children alive.
- **Isolated Data Directories** – Each account gets its own user data folder, preventing session conflicts.
- **Simple Menu Interface** – Easy‑to‑use terminal menus for launching, managing accounts, and running quests.

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
git clone https://github.com/blan3bo1/Discord-Quest-Completer.git
cd Discord-Quest-Completer
```

### 2. Set up a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure your Discord path and accounts

Edit `config.json` to match your Discord version:

```json
{
    "discord_path": "/Applications/Discord.app",
    "discord_executable": "Discord PTB",   // "Discord", "Discord PTB", or "Discord Canary"
    "log_level": "INFO",
    "max_instances": 3,
    "instance_delay": 5,
    "debug_port_start": 9222,
    "injection_delay": 15,
    "auto_login": true,                     // automatically log in using token
    "auto_start_quests": false
}
```

Then add your accounts in `accounts.json` (a template will be created automatically on first run). You can also manage accounts through the menu.

### 5. Run the launcher
```bash
python gui.py
```

You will see the main menu. From there, you can launch accounts, manage them, or run the quest helper.

---

## 🔑 Getting Your Discord Token

1. Open **Discord in your browser** (not the desktop app).
2. Press `F12` to open Developer Tools.
3. Go to the **Console** tab.
4. Type:  
   ```js
   localStorage.getItem('token')
   ```
5. Copy the output (it will be a long string inside quotes – remove the quotes).

> ⚠️ **Keep your tokens secure!** Never share them or commit them to public repositories.

---

## 📖 Usage Guide

### Main Menu

```
╔════════════════════════════════════════════════╗
║            Discord Multi-Tool v1.0             ║
║         Account Manager + Quest Helper         ║
╚════════════════════════════════════════════════╝

📋 Main Menu:
  🔐 ACCOUNT MANAGEMENT:
  1. Launch all enabled accounts
  2. Select accounts to launch
  3. Manage accounts (add/remove)
  4. View running instances
  5. Stop all instances

  🎮 QUEST HELPER:
  6. Run quest helper on running instances
  7. Launch + auto-run quests
  8. Check quest status on all accounts

  ⚙️  SETTINGS:
  9. Settings
  0. Exit
```

#### Account Management (option 3)
- **Add account** – enter name and token.
- **Remove account** – delete an account.
- **Enable/Disable** – toggle whether the account is included in "Launch all".
- **Edit notes** – add reminders.

#### Launching Instances
- **Launch all enabled** – starts every enabled account (respecting `max_instances`).
- **Select accounts** – choose which accounts to launch from a numbered list.

After launch, you’ll be asked if you want to run the quest helper on the new instances.

#### Quest Helper
- **Run quest helper on running instances** – injects the quest‑completion JavaScript into all currently running Discord windows.
- **Launch + auto‑run quests** – launches selected accounts and immediately runs the quest helper on them.
- **Check quest status** – shows which accounts have the quest helper active (coming soon with detailed progress).

#### Settings
- Configure Discord path, executable name, max instances, delays, auto‑login, and logging level.

---

## ⚙️ Configuration Files

### `config.json`
| Key                  | Description                                                                 | Default                     |
|----------------------|-----------------------------------------------------------------------------|-----------------------------|
| `discord_path`       | Path to the Discord `.app` bundle                                           | `/Applications/Discord.app` |
| `discord_executable` | Name of the executable inside `Contents/MacOS/`                             | `"Discord"`                 |
| `log_level`          | Logging detail (`INFO`, `DEBUG`, etc.)                                      | `"INFO"`                    |
| `max_instances`      | Maximum number of concurrent Discord instances                              | `3`                         |
| `instance_delay`     | Seconds to wait between launching instances                                 | `5`                         |
| `debug_port_start`   | Starting port for remote debugging (each instance gets a unique port)       | `9222`                      |
| `injection_delay`    | Seconds to wait after launch before injecting quest helper                  | `15`                        |
| `auto_login`         | If `true`, automatically injects the token via DevTools after launch        | `false`                     |
| `auto_start_quests`  | If `true`, automatically runs quest helper after launching (skips prompt)   | `false`                     |

### `accounts.json`
```json
{
    "accounts": [
        {
            "name": "Main",
            "token": "YOUR_TOKEN_HERE",
            "enabled": true,
            "notes": "Primary account"
        },
        {
            "name": "Alt",
            "token": "ANOTHER_TOKEN",
            "enabled": true,
            "notes": "Backup"
        }
    ]
}
```

---

## 🛠️ How It Works

1. **Isolation** – Each account gets its own user data directory (`~/.discord_multi/instances/`), preventing cookie/session conflicts.
2. **Launch Bypass** – Uses multiple methods (`subprocess.Popen`, `open -n`) and a slew of Chromium flags to force new windows and avoid Discord’s single‑instance lock.
3. **Auto‑Login** – After launch, the script connects to Chrome DevTools on the instance’s debug port, sets `localStorage.token`, and reloads the page.
4. **Conflict Management** – Before each launch, it kills any Discord processes **not** spawned by this tool, but leaves child processes of managed instances untouched.
5. **Quest Helper** – Injects a JavaScript payload (via DevTools) that hooks into Discord’s internal Webpack modules to spoof quest progress.

---

## 🐛 Troubleshooting

| Problem                          | Possible Solution |
|----------------------------------|-------------------|
| Discord executable not found     | Check `discord_path` and `discord_executable` in `config.json`. Run `ls -la "/Applications/Discord.app/Contents/MacOS/"` to see actual executable names. |
| Second instance window doesn’t appear | Try selecting **“Bring all windows to front”** (add this option to the menu if missing). Ensure you have granted Terminal accessibility permissions in **System Settings > Privacy & Security > Accessibility**. |
| Instances keep getting killed     | Our conflict killer should now keep child processes. If you still see killings, run `killall Discord` manually, then restart the launcher. |
| Auto‑login fails                  | Make sure the debug port is reachable: `curl http://localhost:9222/json/list`. Increase `injection_delay` in config. |
| Quest helper doesn’t complete quests | Discord may have updated its internal modules. The quest script may need an update. Check console output for errors. |
| “Address already in use” error    | Run `lsof -ti:9222 \| xargs kill -9` to free the port. |

---

## ⚠️ Disclaimer

**This tool is for educational purposes only.** Using it to automate Discord interactions violates Discord’s Terms of Service and may result in account suspension or termination. The author is not responsible for any consequences arising from the use of this software. Use at your own risk.

---

## 📄 License

MIT License – see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgements

- Thanks to @aamiaa for their amazing "Complete Recent Discord Quest." JavaScript that this uses for the quest helper
---

**⭐ Star this repo if you find it useful!**  
[GitHub Repository](https://github.com/blan3bo1/Discord-Quest-Completer)
