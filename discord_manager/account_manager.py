"""
Account Manager - Handles multiple Discord accounts with bypass techniques
"""

import json
import os
import subprocess
import time
import psutil
import hashlib
import websocket
import requests
from pathlib import Path
from typing import List, Optional
from .logger import get_logger

logger = get_logger()


class DiscordAccount:
    """Represents a Discord account"""
    
    def __init__(self, name: str, token: str, enabled: bool = True, notes: str = ""):
        self.name = name
        self.token = token
        self.enabled = enabled
        self.notes = notes
        self.process = None
        self.debug_port = None
        self.data_dir = None
        self.quests_active = False
        
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "name": self.name,
            "token": self.token,
            "enabled": self.enabled,
            "notes": self.notes
        }
    
    def __str__(self):
        return f"DiscordAccount(name='{self.name}', enabled={self.enabled})"


class AccountManager:
    """Manages multiple Discord accounts"""
    
    def __init__(self, accounts_file="accounts.json"):
        self.accounts_file = Path(accounts_file)
        self.accounts: List[DiscordAccount] = []
        self.base_data_dir = Path.home() / ".discord_multi" / "instances"
        self.load_accounts()
        
        # Create base data directory
        self.base_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Kill any conflicting processes on startup
        self.check_for_conflicts()
    
    def load_accounts(self):
        """Load accounts from JSON file"""
        if not self.accounts_file.exists():
            logger.warning(f"Accounts file not found: {self.accounts_file}")
            self.create_template()
            return
        
        try:
            with open(self.accounts_file, 'r') as f:
                data = json.load(f)
            
            # Handle both old and new format
            if isinstance(data, dict) and "accounts" in data:
                accounts_data = data["accounts"]
            elif isinstance(data, list):
                accounts_data = data
            else:
                accounts_data = []
            
            for acc_data in accounts_data:
                account = DiscordAccount(
                    name=acc_data["name"],
                    token=acc_data["token"],
                    enabled=acc_data.get("enabled", True),
                    notes=acc_data.get("notes", "")
                )
                self.accounts.append(account)
                
            logger.info(f"Loaded {len(self.accounts)} accounts")
            
        except Exception as e:
            logger.error(f"Failed to load accounts: {e}")
            self.create_template()
    
    def create_template(self):
        """Create a template accounts.json file"""
        template = {
            "accounts": [
                {
                    "name": "Main Account",
                    "token": "YOUR_DISCORD_TOKEN_HERE",
                    "enabled": True,
                    "notes": "Primary account"
                },
                {
                    "name": "Alt Account",
                    "token": "YOUR_OTHER_TOKEN_HERE",
                    "enabled": True,
                    "notes": "Secondary account"
                }
            ]
        }
        
        with open(self.accounts_file, 'w') as f:
            json.dump(template, f, indent=4)
            
        logger.info(f"Created template accounts file: {self.accounts_file}")
        logger.info("Please add your Discord tokens to accounts.json")
    
    def save_accounts(self):
        """Save accounts to JSON file"""
        data = {
            "accounts": [acc.to_dict() for acc in self.accounts]
        }
        
        with open(self.accounts_file, 'w') as f:
            json.dump(data, f, indent=4)
    
    def add_account(self, name: str, token: str, enabled: bool = True, notes: str = ""):
        """Add a new account"""
        # Check if account already exists
        for acc in self.accounts:
            if acc.name.lower() == name.lower():
                logger.warning(f"Account '{name}' already exists")
                return None
        
        account = DiscordAccount(name, token, enabled, notes)
        self.accounts.append(account)
        self.save_accounts()
        logger.info(f"Added account: {name}")
        return account
    
    def remove_account(self, name: str):
        """Remove an account"""
        # Stop if running
        for acc in self.accounts:
            if acc.name == name and acc.process:
                self.stop_instance(acc)
        
        self.accounts = [acc for acc in self.accounts if acc.name != name]
        self.save_accounts()
        logger.info(f"Removed account: {name}")
    
    def get_user_data_dir(self, account: DiscordAccount) -> Path:
        """Get unique user data directory for an account"""
        # Create a safe directory name from account name
        safe_name = "".join(c for c in account.name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_name = safe_name.replace(' ', '_')
        
        # Add a hash of the token to make it truly unique
        token_hash = hashlib.md5(account.token.encode()).hexdigest()[:8]
        
        account_dir = self.base_data_dir / f"{safe_name}_{token_hash}"
        
        # Create directory
        account_dir.mkdir(parents=True, exist_ok=True)
        return account_dir
    
    def check_for_conflicts(self):
        """Check for conflicting Discord processes and kill them, but keep our own children."""
        killed = 0
        # Build a set of all PIDs that belong to our managed instances (including children)
        our_pids = set()
        for account in self.accounts:
            if account.process and account.process.poll() is None:
                main_pid = account.process.pid
                our_pids.add(main_pid)
                try:
                    # Add all child PIDs
                    parent = psutil.Process(main_pid)
                    our_pids.update([child.pid for child in parent.children(recursive=True)])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

        for proc in psutil.process_iter(['name', 'pid', 'cmdline']):
            try:
                proc_name = proc.info['name'] or ''
                proc_cmdline = ' '.join(proc.info['cmdline'] or [])
                # Check if it's a Discord process
                if 'discord' in proc_name.lower() or 'discord' in proc_cmdline.lower():
                    if proc.info['pid'] not in our_pids:
                        logger.warning(f"Killing unmanaged Discord process: {proc.info['pid']}")
                        proc.kill()
                        killed += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if killed > 0:
            logger.info(f"Killed {killed} conflicting Discord processes")
            time.sleep(2)
        return killed
    
    def auto_login(self, account: DiscordAccount):
        """Use DevTools to set token in localStorage and reload Discord."""
        if not account.process or account.process.poll() is not None:
            logger.error(f"Account {account.name} not running")
            return False

        # Wait a bit for DevTools to be ready
        time.sleep(3)

        try:
            # Get list of pages
            resp = requests.get(f"http://localhost:{account.debug_port}/json/list")
            targets = resp.json()
            # Find the main page (type 'page')
            main_target = next((t for t in targets if t.get('type') == 'page'), None)
            if not main_target:
                logger.error("No page target found for auto-login")
                return False

            # Connect to WebSocket
            ws_url = f"ws://localhost:{account.debug_port}/devtools/page/{main_target['id']}"
            ws = websocket.create_connection(ws_url)

            # Enable Runtime domain
            ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
            ws.recv()

            # Set token in localStorage and reload
            script = f"""
            localStorage.setItem('token', '{account.token}');
            console.log('[Auto-login] Token set');
            location.reload();
            """
            cmd = {
                "id": 2,
                "method": "Runtime.evaluate",
                "params": {
                    "expression": script,
                    "awaitPromise": False
                }
            }
            ws.send(json.dumps(cmd))
            ws.recv()
            ws.close()

            logger.info(f"✅ Token injected for {account.name}, reloading...")
            return True
        except Exception as e:
            logger.error(f"Auto-login failed for {account.name}: {e}")
            return False
    
    def ensure_window_visible(self, account: DiscordAccount):
        """Ensure Discord window is visible for an account using multiple methods"""
        if not account.process or account.process.poll() is not None:
            return False
        
        pid = account.process.pid
        logger.info(f"Attempting to show window for {account.name} (PID: {pid})...")
        
        try:
            # Method 1: Activate via System Events by PID
            script1 = f'''
            tell application "System Events"
                set frontmost of (first process whose unix id is {pid}) to true
                tell (first process whose unix id is {pid})
                    set visible to true
                    activate
                end tell
            end tell
            '''
            subprocess.run(['osascript', '-e', script1], check=False, capture_output=True)
            time.sleep(1)
            
            # Method 2: Try to open Discord URL scheme (opens or focuses window)
            script2 = f'''
            tell application "Discord"
                activate
                open location "discord://"
            end tell
            '''
            subprocess.run(['osascript', '-e', script2], check=False, capture_output=True)
            time.sleep(1)
            
            # Method 3: Raise first window via UI scripting (requires accessibility)
            script3 = f'''
            tell application "System Events"
                tell (first process whose unix id is {pid})
                    if exists window 1 then
                        set frontmost to true
                        perform action "AXRaise" of window 1
                    else
                        -- Try to create a window by simulating Cmd+N
                        keystroke "n" using command down
                    end if
                end tell
            end tell
            '''
            subprocess.run(['osascript', '-e', script3], check=False, capture_output=True)
            
            logger.info(f"✅ Window activation attempted for {account.name}")
            return True
        except Exception as e:
            logger.error(f"Window activation failed: {e}")
            return False
    
    def launch_instance(self, account: DiscordAccount, discord_path: str, executable_name: str, debug_port: int, auto_login_enabled: bool = False):
        """Launch a Discord instance for a specific account with bypass techniques"""
        if not account.enabled:
            logger.info(f"Account {account.name} is disabled, skipping")
            return None
        
        # Check if already running
        if account.process and account.process.poll() is None:
            logger.warning(f"Account {account.name} already has a running instance")
            return account.process
        
        # First, kill any conflicting processes (but keep our children)
        self.check_for_conflicts()
        
        # Generate a truly unique port based on account name and token
        unique_seed = abs(hash(account.name + account.token)) % 10000
        actual_port = debug_port + (unique_seed % 100)  # Spread ports out
        
        # Determine executable path
        app_bundle = discord_path  # e.g., "/Applications/Discord.app"
        executable_variants = [
            f"{app_bundle}/Contents/MacOS/{executable_name}",
            f"/Applications/Discord.app/Contents/MacOS/Discord",
            f"/Applications/Discord PTB.app/Contents/MacOS/Discord PTB",
            f"/Applications/Discord Canary.app/Contents/MacOS/Discord Canary",
        ]
        
        discord_exe = None
        for variant in executable_variants:
            if os.path.exists(variant):
                discord_exe = variant
                logger.info(f"Using executable: {discord_exe}")
                break
        
        if not discord_exe:
            logger.error(f"No Discord executable found. Tried: {executable_variants}")
            return None
        
        # Create unique user data directory
        user_data_dir = self.get_user_data_dir(account)
        account.data_dir = user_data_dir
        account.debug_port = actual_port
        
        # Create necessary directories and files
        try:
            local_storage_dir = user_data_dir / "Local Storage" / "leveldb"
            local_storage_dir.mkdir(parents=True, exist_ok=True)
            token_file = local_storage_dir / "token.txt"
            with open(token_file, 'w') as f:
                f.write(account.token)
        except Exception as e:
            logger.debug(f"Error creating token file: {e}")
        
        # Build base command arguments (common for all methods)
        common_args = [
            f"--remote-debugging-port={actual_port}",
            "--remote-allow-origins=*",
            f"--user-data-dir={user_data_dir}",
            "--no-sandbox",
            "--disable-gpu",
            "--disable-accelerated-2d-canvas",
            "--disable-setuid-sandbox",
            "--disable-breakpad",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-features=TranslateUI,NetworkService,NetworkServiceInProcess,ChromeWhatsNewUI",
            "--disable-notifications",
            "--disable-background-timer-throttling",
            "--disable-renderer-backgrounding",
            "--disable-backgrounding-occluded-windows",
            "--disable-ipc-flooding-protection",
            "--force-fieldtrials=*CachedMemory/",
            "--disable-session-crashed-bubble",
            "--disable-login-animations",
            "--disable-modal-animations",
            "--hide-scrollbars",
            "--mute-audio",
            "--disable-default-apps",
            "--disable-sync",
            "--disable-component-update",
            "--disable-background-networking",
            "--disable-crash-reporter",
            "--force-device-scale-factor=1",
            "--force-color-profile=srgb",
            "--start-maximized",
            "--new-window",
            "--activate-on-launch",
            "--enable-crashpad",
        ]
        
        # Environment variables for isolation
        env = os.environ.copy()
        env["ELECTRON_IS_DEV"] = "0"
        env["DISCORD_TOKEN"] = account.token
        env["DISCORD_USER_DATA_DIR"] = str(user_data_dir)
        env["DISCORD_INSTANCE_ID"] = str(hash(account.name + account.token))
        env["CHROME_USER_DATA_DIR"] = str(user_data_dir)
        env["XDG_CONFIG_HOME"] = str(user_data_dir / "config")
        env["XDG_DATA_HOME"] = str(user_data_dir / "data")
        env["XDG_CACHE_HOME"] = str(user_data_dir / "cache")
        env["TMPDIR"] = str(user_data_dir / "tmp")
        env["ELECTRON_ENABLE_STACK_DUMPING"] = "1"
        env["ELECTRON_ENABLE_LOGGING"] = "1"
        env["ELECTRON_FORCE_WINDOW_MENU_BAR"] = "1"
        
        # Create XDG directories
        for dir_name in ["config", "data", "cache", "tmp"]:
            (user_data_dir / dir_name).mkdir(exist_ok=True)
        
        # Define multiple launch methods
        launch_methods = [
            {
                "name": "Direct Popen with all flags",
                "fn": lambda: subprocess.Popen(
                    [discord_exe] + common_args,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                    env=env,
                    start_new_session=True
                )
            },
            {
                "name": "open -n (new instance) with args",
                "fn": lambda: subprocess.Popen(
                    ["open", "-n", "-a", app_bundle, "--args"] + common_args,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                    env=env,
                    start_new_session=True
                )
            },
            {
                "name": "Minimal flags via Popen",
                "fn": lambda: subprocess.Popen(
                    [discord_exe, f"--user-data-dir={user_data_dir}", "--no-sandbox", "--start-maximized"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                    env=env,
                    start_new_session=True
                )
            }
        ]
        
        for method in launch_methods:
            try:
                logger.debug(f"Trying launch method: {method['name']}")
                process = method["fn"]()
                time.sleep(4)  # Give it time to initialize
                
                if process.poll() is None:
                    # Success
                    account.process = process
                    logger.info(f"✅ Launched {account.name} (PID: {process.pid}, Port: {actual_port})")
                    
                    # Save PID and port
                    with open(user_data_dir / "instance.pid", 'w') as f:
                        f.write(str(process.pid))
                    with open(user_data_dir / "debug.port", 'w') as f:
                        f.write(str(actual_port))
                    
                    # Wait a bit more and then force window to front
                    time.sleep(3)
                    self.ensure_window_visible(account)
                    
                    # Auto-login if enabled
                    if auto_login_enabled:
                        logger.info(f"Attempting auto-login for {account.name}...")
                        self.auto_login(account)
                    
                    # Run a quick conflict check to clean up any stragglers (but keep our new children)
                    self.check_for_conflicts()
                    
                    return process
                else:
                    logger.debug(f"Launch method {method['name']} failed, process died.")
            except Exception as e:
                logger.debug(f"Launch method {method['name']} error: {e}")
                continue
        
        logger.error(f"❌ All launch methods failed for {account.name}")
        return None
    
    def stop_instance(self, account: DiscordAccount):
        """Stop a specific Discord instance"""
        if account.process and account.process.poll() is None:
            logger.info(f"Stopping Discord for {account.name}...")
            account.process.terminate()
            try:
                account.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    account.process.kill()
                except:
                    pass
            account.process = None
            account.quests_active = False
            logger.info(f"✅ Stopped {account.name}")
    
    def stop_all(self):
        """Stop all running Discord instances"""
        logger.info("Stopping all Discord instances...")
        for account in self.accounts:
            self.stop_instance(account)
        try:
            subprocess.run(['pkill', '-f', 'Discord'], check=False)
        except:
            pass
    
    def get_running_instances(self):
        """Get list of running instances"""
        running = []
        for account in self.accounts:
            if account.process and account.process.poll() is None:
                running.append(account)
        return running
    
    def get_instance_status(self, account: DiscordAccount):
        """Get detailed status of an instance"""
        if not account.process:
            return "Not running"
        if account.process.poll() is not None:
            return f"Stopped (code: {account.process.poll()})"
        try:
            proc = psutil.Process(account.process.pid)
            cpu = proc.cpu_percent(interval=0.1)
            mem = proc.memory_info().rss / 1024 / 1024
            return f"Running (PID: {account.process.pid}, CPU: {cpu:.1f}%, RAM: {mem:.1f}MB)"
        except:
            return "Running (status unknown)"
    
    def cleanup_stale_instances(self):
        """Clean up stale instance directories"""
        cleaned = 0
        for instance_dir in self.base_data_dir.iterdir():
            if instance_dir.is_dir():
                pid_file = instance_dir / "instance.pid"
                if pid_file.exists():
                    try:
                        with open(pid_file, 'r') as f:
                            pid = int(f.read().strip())
                        try:
                            os.kill(pid, 0)
                        except OSError:
                            logger.info(f"Cleaning up stale instance: {instance_dir}")
                            import shutil
                            shutil.rmtree(instance_dir)
                            cleaned += 1
                    except:
                        pass
        if cleaned > 0:
            logger.info(f"Cleaned up {cleaned} stale instances")
        return cleaned
    
    def bring_all_windows_to_front(self):
        """Bring all Discord windows to front"""
        logger.info("Bringing all Discord windows to front...")
        for account in self.get_running_instances():
            self.ensure_window_visible(account)