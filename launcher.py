#!/usr/bin/env python3
"""
Discord Multi-Tool - Account Manager & Quest Completer
"""

import os
import sys
import json
import signal
import time
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from discord_manager.account_manager import AccountManager
from discord_manager.logger import setup_logger, get_logger

# Import quest stuff
from discord_quest_helper import DiscordInjector


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n\n🛑 Shutting down Discord Multi-Tool...")
    if 'account_manager' in globals():
        account_manager.stop_all()
    sys.exit(0)


def load_config():
    """Load configuration from file"""
    config_path = Path(__file__).parent / "config.json"
    default_config = {
        "discord_path": "/Applications/Discord.app",
        "discord_executable": "Discord",  # Change to "Discord PTB" or "Discord Canary" if needed
        "log_level": "INFO",
        "max_instances": 3,
        "instance_delay": 5,
        "debug_port_start": 9222,
        "injection_delay": 15,
        "auto_start_quests": False
    }
    
    if config_path.exists():
        with open(config_path, 'r') as f:
            user_config = json.load(f)
            default_config.update(user_config)
    
    return default_config


def clear_screen():
    """Clear the terminal screen"""
    os.system('clear' if os.name == 'posix' else 'cls')


def print_banner():
    """Print fancy banner"""
    print("""
    ╔════════════════════════════════════════════════╗
    ║            Discord Multi-Tool v1.0             ║
    ║         Account Manager + Quest Helper         ║
    ╚════════════════════════════════════════════════╝
    """)


def main_menu(account_manager, config):
    """Display main menu"""
    while True:
        clear_screen()
        print_banner()
        
        print("\n📋 Main Menu:")
        print("  🔐 ACCOUNT MANAGEMENT:")
        print("  1. Launch all enabled accounts")
        print("  2. Select accounts to launch")
        print("  3. Manage accounts (add/remove)")
        print("  4. View running instances")
        print("  5. Stop all instances")
        print("")
        print("  🎮 QUEST HELPER:")
        print("  6. Run quest helper on running instances")
        print("  7. Launch + auto-run quests")
        print("  8. Check quest status on all accounts")
        print("")
        print("  ⚙️  SETTINGS:")
        print("  9. Settings")
        print("  0. Exit")
        
        choice = input("\n👉 Enter choice: ").strip()
        
        if choice == "1":
            launch_all_enabled(account_manager, config)
        elif choice == "2":
            select_accounts(account_manager, config)
        elif choice == "3":
            manage_accounts_menu(account_manager)
        elif choice == "4":
            show_running_instances(account_manager)
        elif choice == "5":
            account_manager.stop_all()
            input("\n✅ All instances stopped. Press Enter to continue...")
        elif choice == "6":
            run_quest_helper_on_all(account_manager, config)
        elif choice == "7":
            launch_and_run_quests(account_manager, config)
        elif choice == "8":
            check_quest_status(account_manager, config)
        elif choice == "9":
            settings_menu(config)
        elif choice == "0":
            account_manager.stop_all()
            print("\n👋 Goodbye!")
            sys.exit(0)
        else:
            input("\n❌ Invalid choice. Press Enter to continue...")


def launch_all_enabled(account_manager, config):
    """Launch all enabled accounts"""
    clear_screen()
    print_banner()
    print("\n🚀 Launching all enabled accounts...")
    
    enabled_accounts = [acc for acc in account_manager.accounts if acc.enabled]
    
    if not enabled_accounts:
        print("\n❌ No enabled accounts found!")
        input("Press Enter to continue...")
        return
    
    print(f"\n📊 Found {len(enabled_accounts)} enabled account(s)")
    
    # Check max instances
    max_instances = config.get("max_instances", 3)
    if len(enabled_accounts) > max_instances:
        print(f"\n⚠️  You have {len(enabled_accounts)} accounts but max_instances is set to {max_instances}")
        print(f"Only the first {max_instances} will be launched")
        enabled_accounts = enabled_accounts[:max_instances]
    
    # Launch each account
    for i, account in enumerate(enabled_accounts, 1):
        print(f"\n[{i}/{len(enabled_accounts)}] Launching {account.name}...")
        
        process = account_manager.launch_instance(
            account, 
            config.get("discord_path"),
            config.get("discord_executable"),
            config.get("debug_port_start", 9222) + (i * 10)  # Space out ports
        )
        
        if process:
            print(f"  ✅ Launched (PID: {process.pid}, Port: {account.debug_port})")
        else:
            print(f"  ❌ Failed to launch")
        
        # Wait between launches
        if i < len(enabled_accounts):
            delay = config.get("instance_delay", 5)
            print(f"  ⏱️  Waiting {delay} seconds before next launch...")
            time.sleep(delay)
    
    print(f"\n✅ Launched {len([a for a in enabled_accounts if a.process])} instance(s)")
    
    # Ask if user wants to run quest helper
    if config.get("auto_start_quests", False):
        run_quest_helper_on_all(account_manager, config)
    else:
        run_now = input("\n🎮 Run quest helper on these instances? (y/N): ").strip().lower()
        if run_now == 'y':
            run_quest_helper_on_all(account_manager, config)
        else:
            input("\nPress Enter to return to menu...")


def select_accounts(account_manager, config):
    """Select specific accounts to launch"""
    clear_screen()
    print_banner()
    print("\n🎯 Select accounts to launch:")
    
    enabled_accounts = [acc for acc in account_manager.accounts if acc.enabled]
    
    if not enabled_accounts:
        print("\n❌ No enabled accounts found!")
        input("Press Enter to continue...")
        return
    
    print("\nEnabled accounts:")
    for i, account in enumerate(enabled_accounts, 1):
        print(f"  {i}. {account.name}")
    
    print("\nEnter numbers (comma-separated, e.g., 1,3,5) or 'all':")
    choice = input("👉 ").strip()
    
    selected = []
    if choice.lower() == 'all':
        selected = enabled_accounts
    else:
        try:
            indices = [int(x.strip()) - 1 for x in choice.split(',') if x.strip().isdigit()]
            selected = [enabled_accounts[i] for i in indices if 0 <= i < len(enabled_accounts)]
        except:
            print("\n❌ Invalid input")
            input("Press Enter to continue...")
            return
    
    if not selected:
        print("\n❌ No accounts selected")
        input("Press Enter to continue...")
        return
    
    print(f"\n🚀 Launching {len(selected)} account(s)...")
    
    # Check max instances
    max_instances = config.get("max_instances", 3)
    if len(selected) > max_instances:
        print(f"\n⚠️  Max instances is {max_instances}, only launching first {max_instances}")
        selected = selected[:max_instances]
    
    # Launch each account
    for i, account in enumerate(selected, 1):
        print(f"\n[{i}/{len(selected)}] Launching {account.name}...")
        
        process = account_manager.launch_instance(
            account, 
            config.get("discord_path"),
            config.get("discord_executable"),
            config.get("debug_port_start", 9222) + (i * 10)
        )
        
        if process:
            print(f"  ✅ Launched (PID: {process.pid}, Port: {account.debug_port})")
        else:
            print(f"  ❌ Failed to launch")
        
        # Wait between launches
        if i < len(selected):
            delay = config.get("instance_delay", 5)
            print(f"  ⏱️  Waiting {delay} seconds...")
            time.sleep(delay)
    
    print(f"\n✅ Launched {len([a for a in selected if a.process])} instance(s)")
    
    # Ask if user wants to run quest helper
    run_now = input("\n🎮 Run quest helper on these instances? (y/N): ").strip().lower()
    if run_now == 'y':
        run_quest_helper_on_selected(selected, config)
    else:
        input("\nPress Enter to return to menu...")


def run_quest_helper_on_all(account_manager, config):
    """Run quest helper on all running instances"""
    clear_screen()
    print_banner()
    print("\n🎮 Running Quest Helper on all running instances...")
    
    running = [acc for acc in account_manager.accounts if acc.process and acc.process.poll() is None]
    
    if not running:
        print("\n❌ No running instances found!")
        input("Press Enter to continue...")
        return
    
    print(f"\n📊 Found {len(running)} running instance(s)")
    
    run_quest_helper_on_selected(running, config)


def run_quest_helper_on_selected(accounts, config):
    """Run quest helper on selected accounts"""
    
    for account in accounts:
        print(f"\n{'='*50}")
        print(f"🎮 Processing: {account.name}")
        print(f"{'='*50}")
        
        # Wait for Discord to fully load
        print(f"⏱️  Waiting {config.get('injection_delay', 15)} seconds for Discord to load...")
        time.sleep(config.get("injection_delay", 15))
        
        # Create injector for this account's port
        injector = DiscordInjector(debug_port=account.debug_port, config=config)
        
        try:
            # Connect to Discord
            print(f"🔌 Connecting to {account.name} on port {account.debug_port}...")
            if not injector.connect():
                print(f"❌ Failed to connect to {account.name}")
                continue
            
            # Load quest helper script
            script_path = Path(__file__).parent / "discord_quest_helper" / "quest_helper.js"
            if not script_path.exists():
                print(f"❌ Quest helper script not found!")
                continue
                
            with open(script_path, 'r', encoding='utf-8') as f:
                quest_script = f.read()
            
            # Inject script
            print(f"💉 Injecting quest helper...")
            if injector.inject_script(quest_script):
                print(f"✅ Injection successful for {account.name}!")
                account.quests_active = True
            else:
                print(f"❌ Injection failed for {account.name}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            injector.close()
    
    print(f"\n✅ Quest helper injected into {len(accounts)} instance(s)")
    print("📝 Check each Discord window for quest progress")
    input("\nPress Enter to continue...")


def launch_and_run_quests(account_manager, config):
    """Launch accounts and automatically run quest helper"""
    clear_screen()
    print_banner()
    print("\n🚀 Launch + Auto-Run Quests")
    
    enabled_accounts = [acc for acc in account_manager.accounts if acc.enabled]
    
    if not enabled_accounts:
        print("\n❌ No enabled accounts found!")
        input("Press Enter to continue...")
        return
    
    # Launch all enabled accounts
    max_instances = config.get("max_instances", 3)
    to_launch = enabled_accounts[:max_instances]
    
    print(f"\n📊 Launching {len(to_launch)} account(s)...")
    
    for i, account in enumerate(to_launch, 1):
        print(f"\n[{i}/{len(to_launch)}] {account.name}")
        
        # Launch
        process = account_manager.launch_instance(
            account, 
            config.get("discord_path"),
            config.get("discord_executable"),
            config.get("debug_port_start", 9222) + (i * 10)
        )
        
        if process:
            print(f"  ✅ Launched")
        else:
            print(f"  ❌ Launch failed")
            continue
        
        # Wait for Discord to load
        print(f"  ⏱️  Waiting {config.get('injection_delay', 15)} seconds...")
        time.sleep(config.get("injection_delay", 15))
        
        # Run quest helper
        print(f"  🎮 Running quest helper...")
        injector = DiscordInjector(debug_port=account.debug_port, config=config)
        
        try:
            if injector.connect():
                script_path = Path(__file__).parent / "discord_quest_helper" / "quest_helper.js"
                with open(script_path, 'r') as f:
                    quest_script = f.read()
                
                if injector.inject_script(quest_script):
                    print(f"  ✅ Quest helper injected")
                else:
                    print(f"  ❌ Injection failed")
            else:
                print(f"  ❌ Could not connect")
        except Exception as e:
            print(f"  ❌ Error: {e}")
        finally:
            injector.close()
        
        # Wait between accounts
        if i < len(to_launch):
            time.sleep(config.get("instance_delay", 5))
    
    print(f"\n✅ Done! Quest helpers running on {len(to_launch)} instance(s)")
    input("\nPress Enter to continue...")


def check_quest_status(account_manager, config):
    """Check quest status on running instances"""
    clear_screen()
    print_banner()
    print("\n📊 Quest Status Check")
    
    running = [acc for acc in account_manager.accounts if acc.process and acc.process.poll() is None]
    
    if not running:
        print("\n❌ No running instances found!")
        input("Press Enter to continue...")
        return
    
    print(f"\n📊 Checking quest status on {len(running)} instance(s)...")
    
    for account in running:
        print(f"\n{account.name}:")
        print(f"  PID: {account.process.pid}")
        print(f"  Port: {account.debug_port}")
        print(f"  Status: {'🟢 Quest helper active' if getattr(account, 'quests_active', False) else '🟡 No quest helper'}")
        
        # You could add more quest status checks here
    
    input("\nPress Enter to continue...")


def manage_accounts_menu(account_manager):
    """Account management menu"""
    while True:
        clear_screen()
        print_banner()
        print("\n👤 Account Management")
        
        print("\nCurrent accounts:")
        if not account_manager.accounts:
            print("  No accounts found")
        else:
            for i, account in enumerate(account_manager.accounts, 1):
                status = "✅" if account.enabled else "❌"
                quest_status = "🎮" if getattr(account, 'quests_active', False) else ""
                print(f"  {i}. {status} {account.name} {quest_status} - {account.notes}")
        
        print("\nOptions:")
        print("  1. Add new account")
        print("  2. Remove account")
        print("  3. Enable/disable account")
        print("  4. Edit account notes")
        print("  0. Back to main menu")
        
        choice = input("\n👉 Enter choice: ").strip()
        
        if choice == "1":
            add_account(account_manager)
        elif choice == "2":
            remove_account(account_manager)
        elif choice == "3":
            toggle_account(account_manager)
        elif choice == "4":
            edit_notes(account_manager)
        elif choice == "0":
            break
        else:
            input("\n❌ Invalid choice. Press Enter to continue...")


def add_account(account_manager):
    """Add a new account"""
    clear_screen()
    print_banner()
    print("\n➕ Add New Account")
    
    name = input("\nAccount name: ").strip()
    if not name:
        print("\n❌ Account name cannot be empty")
        input("Press Enter to continue...")
        return
    
    token = input("Discord token: ").strip()
    if not token:
        print("\n❌ Token cannot be empty")
        input("Press Enter to continue...")
        return
    
    notes = input("Notes (optional): ").strip()
    
    account_manager.add_account(name, token, True, notes)
    print(f"\n✅ Account '{name}' added successfully!")
    input("Press Enter to continue...")


def remove_account(account_manager):
    """Remove an account"""
    clear_screen()
    print_banner()
    
    if not account_manager.accounts:
        print("\n❌ No accounts to remove")
        input("Press Enter to continue...")
        return
    
    print("\n🗑️  Remove Account")
    print("\nSelect account to remove:")
    
    for i, account in enumerate(account_manager.accounts, 1):
        print(f"  {i}. {account.name}")
    
    try:
        choice = int(input("\n👉 Enter number: ").strip())
        if 1 <= choice <= len(account_manager.accounts):
            account = account_manager.accounts[choice - 1]
            confirm = input(f"Remove '{account.name}'? (y/N): ").strip().lower()
            if confirm == 'y':
                account_manager.remove_account(account.name)
                print(f"\n✅ Account removed")
            else:
                print("\n❌ Cancelled")
        else:
            print("\n❌ Invalid number")
    except:
        print("\n❌ Invalid input")
    
    input("Press Enter to continue...")


def toggle_account(account_manager):
    """Enable or disable an account"""
    clear_screen()
    print_banner()
    
    if not account_manager.accounts:
        print("\n❌ No accounts found")
        input("Press Enter to continue...")
        return
    
    print("\n🔀 Enable/Disable Account")
    print("\nSelect account:")
    
    for i, account in enumerate(account_manager.accounts, 1):
        status = "✅ Enabled" if account.enabled else "❌ Disabled"
        print(f"  {i}. {account.name} - {status}")
    
    try:
        choice = int(input("\n👉 Enter number: ").strip())
        if 1 <= choice <= len(account_manager.accounts):
            account = account_manager.accounts[choice - 1]
            account.enabled = not account.enabled
            account_manager.save_accounts()
            new_status = "enabled" if account.enabled else "disabled"
            print(f"\n✅ Account '{account.name}' {new_status}")
        else:
            print("\n❌ Invalid number")
    except:
        print("\n❌ Invalid input")
    
    input("Press Enter to continue...")


def edit_notes(account_manager):
    """Edit account notes"""
    clear_screen()
    print_banner()
    
    if not account_manager.accounts:
        print("\n❌ No accounts found")
        input("Press Enter to continue...")
        return
    
    print("\n📝 Edit Account Notes")
    print("\nSelect account:")
    
    for i, account in enumerate(account_manager.accounts, 1):
        print(f"  {i}. {account.name} - Current notes: {account.notes}")
    
    try:
        choice = int(input("\n👉 Enter number: ").strip())
        if 1 <= choice <= len(account_manager.accounts):
            account = account_manager.accounts[choice - 1]
            new_notes = input(f"New notes for '{account.name}': ").strip()
            account.notes = new_notes
            account_manager.save_accounts()
            print(f"\n✅ Notes updated")
        else:
            print("\n❌ Invalid number")
    except:
        print("\n❌ Invalid input")
    
    input("Press Enter to continue...")


def show_running_instances(account_manager):
    """Show currently running instances"""
    clear_screen()
    print_banner()
    print("\n📊 Running Instances:")
    
    running = [acc for acc in account_manager.accounts if acc.process and acc.process.poll() is None]
    
    if not running:
        print("\n  No instances currently running")
    else:
        for account in running:
            quest_status = "🎮 Quest Active" if getattr(account, 'quests_active', False) else "⏸️ No Quest"
            print(f"\n  {account.name}:")
            print(f"    PID: {account.process.pid}")
            print(f"    Port: {account.debug_port}")
            print(f"    Data Dir: {account.data_dir}")
            print(f"    Status: 🟢 Running | {quest_status}")
    
    input("\nPress Enter to continue...")


def settings_menu(config):
    """Settings menu"""
    while True:
        clear_screen()
        print_banner()
        print("\n⚙️  Settings")
        
        print(f"\nCurrent settings:")
        print(f"  1. Discord Path: {config.get('discord_path')}")
        print(f"  2. Discord Executable: {config.get('discord_executable')}")
        print(f"  3. Max Instances: {config.get('max_instances')}")
        print(f"  4. Instance Delay: {config.get('instance_delay')} seconds")
        print(f"  5. Debug Port Start: {config.get('debug_port_start')}")
        print(f"  6. Log Level: {config.get('log_level')}")
        print(f"  7. Injection Delay: {config.get('injection_delay')} seconds")
        print(f"  8. Auto-start Quests: {config.get('auto_start_quests')}")
        print(f"  0. Back to main menu")
        
        choice = input("\n👉 Enter setting to change: ").strip()
        
        if choice == "1":
            new_path = input("New Discord path: ").strip()
            if new_path:
                config['discord_path'] = new_path
        elif choice == "2":
            print("\nCommon options: Discord, Discord PTB, Discord Canary")
            new_exe = input("New executable name: ").strip()
            if new_exe:
                config['discord_executable'] = new_exe
        elif choice == "3":
            try:
                new_max = int(input("New max instances (1-10): ").strip())
                if 1 <= new_max <= 10:
                    config['max_instances'] = new_max
            except:
                print("❌ Invalid number")
        elif choice == "4":
            try:
                new_delay = int(input("New instance delay in seconds: ").strip())
                if new_delay >= 1:
                    config['instance_delay'] = new_delay
            except:
                print("❌ Invalid number")
        elif choice == "5":
            try:
                new_port = int(input("New starting debug port: ").strip())
                if 1024 <= new_port <= 65535:
                    config['debug_port_start'] = new_port
            except:
                print("❌ Invalid port number")
        elif choice == "6":
            print("\nOptions: INFO, DEBUG, WARNING, ERROR")
            new_level = input("New log level: ").strip().upper()
            if new_level in ['INFO', 'DEBUG', 'WARNING', 'ERROR']:
                config['log_level'] = new_level
        elif choice == "7":
            try:
                new_delay = int(input("New injection delay in seconds: ").strip())
                if new_delay >= 5:
                    config['injection_delay'] = new_delay
            except:
                print("❌ Invalid number")
        elif choice == "8":
            current = config.get('auto_start_quests', False)
            config['auto_start_quests'] = not current
            print(f"Auto-start quests set to: {config['auto_start_quests']}")
        elif choice == "0":
            # Save config
            config_path = Path(__file__).parent / "config.json"
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
            break
        
        # Save after each change
        config_path = Path(__file__).parent / "config.json"
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        
        input("\n✅ Setting updated. Press Enter to continue...")


def main():
    """Main entry point"""
    # Setup signal handling
    signal.signal(signal.SIGINT, signal_handler)
    
    # Load configuration
    config = load_config()
    logger = setup_logger(config.get("log_level", "INFO"))
    
    # Initialize account manager
    global account_manager
    account_manager = AccountManager("accounts.json")
    
    # Show main menu
    main_menu(account_manager, config)


if __name__ == "__main__":
    main()