"""
Utility functions for Discord Multi-Account Launcher
"""

import os
import platform
import subprocess
from pathlib import Path


def get_system_info():
    """Get system information for debugging"""
    return {
        "os": platform.system(),
        "os_version": platform.version(),
        "machine": platform.machine(),
        "python_version": platform.python_version()
    }


def kill_process_on_port(port):
    """Kill process using a specific port"""
    try:
        result = subprocess.run(['lsof', '-ti', f':{port}'], capture_output=True, text=True)
        pids = result.stdout.strip().split('\n')
        for pid in pids:
            if pid:
                os.kill(int(pid), 9)
        return len(pids)
    except:
        return 0


def check_discord_installed(path="/Applications/Discord.app"):
    """Check if Discord is installed at the given path"""
    return Path(path).exists()


def get_discord_version(path="/Applications/Discord.app"):
    """Try to get Discord version"""
    plist_path = Path(path) / "Contents" / "Info.plist"
    if plist_path.exists():
        try:
            import plistlib
            with open(plist_path, 'rb') as f:
                plist = plistlib.load(f)
                return plist.get('CFBundleShortVersionString', 'Unknown')
        except:
            pass
    return "Unknown"