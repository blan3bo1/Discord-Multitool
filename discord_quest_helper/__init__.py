"""
Discord Quest Helper Package
"""

from .injector import DiscordInjector
from .discord_launcher import launch_discord_with_debug
from .logger import setup_logger, get_logger
from .utils import load_config

__version__ = "1.0.0"
__all__ = ["DiscordInjector", "launch_discord_with_debug", "setup_logger", "get_logger", "load_config"]