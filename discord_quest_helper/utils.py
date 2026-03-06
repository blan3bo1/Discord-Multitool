"""
Utility functions for Discord Quest Helper
"""

import json
import os
import platform
import subprocess
from pathlib import Path


def load_config(config_path=None):
    """Load configuration from file"""
    if config_path is None:
        # Look for config in multiple locations
        possible_paths = [
            Path.cwd() / "config.json",
            Path.home() / ".discord_quest_helper" / "config.json",
            Path(__file__).parent.parent / "config.json"
        ]
        
        for path in possible_paths:
            if path.exists():
                config_path = path
                break
    
    default_config = {
        "auto_start": True,
        "debug_port": 9222,
        "log_level": "INFO",
        "discord_path": "/Applications/Discord.app",
        "quest_types": ["WATCH_VIDEO", "PLAY_ON_DESKTOP", "STREAM_ON_DESKTOP", "PLAY_ACTIVITY"],
        "rate_limits": {
            "video_progress": 7,
            "heartbeat_interval": 20,
            "max_retries": 3
        },
        "injection_delay": 10
    }
    
    if config_path and Path(config_path).exists():
        with open(config_path, 'r') as f:
            user_config = json.load(f)
            default_config.update(user_config)
    
    return default_config


def is_discord_running():
    """Check if Discord is running"""
    try:
        result = subprocess.run(['pgrep', '-f', 'Discord'], capture_output=True)
        return result.returncode == 0
    except:
        return False


def kill_discord():
    """Kill all Discord processes"""
    try:
        subprocess.run(['pkill', '-f', 'Discord'], check=False)
        return True
    except:
        return False


def get_system_info():
    """Get system information for debugging"""
    return {
        "os": platform.system(),
        "os_version": platform.version(),
        "machine": platform.machine(),
        "python_version": platform.python_version()
    }