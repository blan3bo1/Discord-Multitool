#!/usr/bin/env python3
"""
Discord Multi-Account Launcher - Dark Minimalist GUI
Inspired by https://blankboii.xyz
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import os
import sys
import json
import psutil
from pathlib import Path
from datetime import datetime
import pytz

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from discord_manager.account_manager import AccountManager
from discord_manager.logger import setup_logger
from launcher import load_config


class DiscordMultiGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Discord Multi‑Tool")
        self.root.geometry("1000x700")
        self.root.configure(bg='#000000')

        # Load config and accounts
        self.config = load_config()
        self.account_manager = AccountManager("accounts.json")
        self.logger = setup_logger(self.config.get("log_level", "INFO"))

        # Variables
        self.auto_refresh = tk.BooleanVar(value=True)
        self.selected_names = set()  # Store names of selected accounts

        # Configure dark theme
        self.setup_styles()

        # Build UI
        self.create_widgets()

        # Start background updater
        self.update_clock()
        self.update_status()

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_styles(self):
        self.root.option_add('*Background', '#000000')
        self.root.option_add('*Foreground', '#e0e0e0')
        self.root.option_add('*Font', 'Helvetica 10')

        style = ttk.Style()
        style.theme_use('clam')

        # Configure ttk styles for dark theme
        style.configure('TFrame', background='#000000')
        style.configure('TLabel', background='#000000', foreground='#e0e0e0')
        style.configure('TButton', background='#1a1a1a', foreground='#e0e0e0',
                        borderwidth=1, focusthickness=3, focuscolor='none')
        style.map('TButton',
                  background=[('active', '#333333'), ('pressed', '#444444')])
        style.configure('TNotebook', background='#000000', borderwidth=0)
        style.configure('TNotebook.Tab', background='#1a1a1a', foreground='#e0e0e0',
                        padding=[10, 2])
        style.map('TNotebook.Tab',
                  background=[('selected', '#000000'), ('active', '#333333')])
        style.configure('Treeview', background='#1a1a1a', foreground='#e0e0e0',
                        fieldbackground='#1a1a1a', borderwidth=0)
        style.map('Treeview', background=[('selected', '#333333')])
        style.configure('Treeview.Heading', background='#000000', foreground='#e0e0e0',
                        relief='flat')
        style.map('Treeview.Heading', background=[('active', '#1a1a1a')])
        style.configure('TSpinbox', background='#1a1a1a', foreground='#e0e0e0',
                        fieldbackground='#1a1a1a')
        style.configure('TEntry', background='#1a1a1a', foreground='#e0e0e0',
                        fieldbackground='#1a1a1a')
        style.configure('TCombobox', background='#1a1a1a', foreground='#e0e0e0',
                        fieldbackground='#1a1a1a')

    def create_widgets(self):
        # Header with snowflakes and time
        header = ttk.Frame(self.root)
        header.pack(fill=tk.X, padx=20, pady=(20,10))

        left = ttk.Frame(header)
        left.pack(side=tk.LEFT)
        ttk.Label(left, text="❄", font=('Helvetica', 24), foreground='#666666').pack(side=tk.LEFT)
        ttk.Label(left, text="❆", font=('Helvetica', 24), foreground='#888888').pack(side=tk.LEFT, padx=(0,10))

        self.time_label = ttk.Label(left, font=('Helvetica', 12), foreground='#aaaaaa')
        self.time_label.pack(side=tk.LEFT)

        right = ttk.Frame(header)
        right.pack(side=tk.RIGHT)
        ttk.Label(right, text="🎮", font=('Helvetica', 20)).pack(side=tk.RIGHT)

        # Main content
        main = ttk.Frame(self.root)
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Notebook (tabs)
        self.notebook = ttk.Notebook(main)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Accounts
        self.tab_accounts = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_accounts, text="📋 Accounts")
        self.build_accounts_tab()

        # Tab 2: Quest Helper
        self.tab_quest = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_quest, text="🎮 Quest Helper")
        self.build_quest_tab()

        # Tab 3: Settings
        self.tab_settings = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_settings, text="⚙️ Settings")
        self.build_settings_tab()

        # Footer
        footer = ttk.Frame(self.root)
        footer.pack(fill=tk.X, padx=20, pady=10)
        ttk.Label(footer, text="I'm Too Tired", foreground='#666666').pack(side=tk.LEFT)
        ttk.Label(footer, text="dnd", foreground='#ff5555').pack(side=tk.RIGHT, padx=5)
        ttk.Label(footer, text="Sleeping ngl is", foreground='#888888').pack(side=tk.RIGHT, padx=5)

    def build_accounts_tab(self):
        # Toolbar
        toolbar = ttk.Frame(self.tab_accounts)
        toolbar.pack(fill=tk.X, pady=(0,10))

        ttk.Button(toolbar, text="🚀 Launch Selected", command=self.launch_selected).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🔥 Launch All Enabled", command=self.launch_all_enabled).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="⏹️ Stop All", command=self.stop_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🔄 Refresh", command=lambda: self.refresh_account_list(keep_selection=False)).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="➕ Add", command=self.add_account_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="✏️ Edit", command=self.edit_selected_account).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🗑️ Delete", command=self.delete_selected_account).pack(side=tk.LEFT, padx=2)

        # Treeview with selection tracking
        tree_frame = ttk.Frame(self.tab_accounts)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        columns = ('enabled', 'name', 'status', 'pid', 'port', 'cpu', 'mem', 'notes')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15, selectmode='extended')
        self.tree.heading('enabled', text='✅')
        self.tree.heading('name', text='Name')
        self.tree.heading('status', text='Status')
        self.tree.heading('pid', text='PID')
        self.tree.heading('port', text='Port')
        self.tree.heading('cpu', text='CPU')
        self.tree.heading('mem', text='MEM')
        self.tree.heading('notes', text='Notes')

        self.tree.column('enabled', width=40, anchor='center')
        self.tree.column('name', width=150)
        self.tree.column('status', width=90)
        self.tree.column('pid', width=60)
        self.tree.column('port', width=60)
        self.tree.column('cpu', width=50)
        self.tree.column('mem', width=60)
        self.tree.column('notes', width=200)

        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # Bind selection events to track selected names
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        # Double-click to edit
        self.tree.bind('<Double-1>', lambda e: self.edit_selected_account())

        # Initial load
        self.refresh_account_list(keep_selection=False)

    def on_tree_select(self, event):
        """Store names of selected accounts."""
        self.selected_names.clear()
        for item in self.tree.selection():
            name = self.tree.item(item, 'tags')[0] if self.tree.item(item, 'tags') else None
            if name:
                self.selected_names.add(name)

    def refresh_account_list(self, keep_selection=True):
        """Update treeview, optionally preserving selection."""
        # Store current selection if requested
        if keep_selection:
            saved_selection = self.selected_names.copy()
        else:
            saved_selection = set()

        # Clear tree
        for row in self.tree.get_children():
            self.tree.delete(row)

        # Populate with fresh data
        for acc in self.account_manager.accounts:
            enabled = "✅" if acc.enabled else "❌"
            status = "Running" if (acc.process and acc.process.poll() is None) else "Stopped"
            pid = str(acc.process.pid) if acc.process and acc.process.poll() is None else ""
            port = str(acc.debug_port) if acc.debug_port else ""
            cpu = ""
            mem = ""
            if acc.process and acc.process.poll() is None:
                try:
                    proc = psutil.Process(acc.process.pid)
                    cpu = f"{proc.cpu_percent(interval=0.1):.0f}%"
                    mem = f"{proc.memory_info().rss / 1024 / 1024:.0f}"
                except:
                    pass

            tags = (acc.name,)
            item = self.tree.insert('', tk.END, values=(enabled, acc.name, status, pid, port, cpu, mem, acc.notes), tags=tags)

            # Apply row colour based on status
            if status == "Running":
                self.tree.tag_configure(acc.name, background='#1a3a1a')
            else:
                self.tree.tag_configure(acc.name, background='#1a1a1a')

            # Restore selection if this account was selected before
            if acc.name in saved_selection:
                self.tree.selection_add(item)

        # Update the stored selection to match what's actually selected (in case some were removed)
        self.selected_names = saved_selection.intersection({acc.name for acc in self.account_manager.accounts})

    def get_selected_accounts(self):
        """Return list of Account objects for selected tree rows."""
        return [next(acc for acc in self.account_manager.accounts if acc.name == name)
                for name in self.selected_names]

    def launch_selected(self):
        accounts = self.get_selected_accounts()
        if not accounts:
            messagebox.showinfo("No Selection", "Select at least one account.")
            return
        to_launch = [a for a in accounts if a.enabled]
        if not to_launch:
            messagebox.showinfo("No Enabled", "Selected accounts are disabled.")
            return
        threading.Thread(target=self._launch_thread, args=(to_launch,), daemon=True).start()

    def launch_all_enabled(self):
        enabled = [a for a in self.account_manager.accounts if a.enabled]
        if not enabled:
            messagebox.showinfo("No Enabled", "No enabled accounts.")
            return
        threading.Thread(target=self._launch_thread, args=(enabled,), daemon=True).start()

    def _launch_thread(self, accounts):
        for i, acc in enumerate(accounts, 1):
            print(f"[{i}/{len(accounts)}] Launching {acc.name}...")
            process = self.account_manager.launch_instance(
                acc,
                self.config.get("discord_path", "/Applications/Discord.app"),
                self.config.get("discord_executable", "Discord"),
                self.config.get("debug_port_start", 9222) + (i * 10),
                auto_login_enabled=self.config.get("auto_login", False)
            )
            if process:
                print(f"  ✅ Launched (PID: {process.pid})")
            else:
                print(f"  ❌ Failed")
            if i < len(accounts):
                time.sleep(self.config.get("instance_delay", 5))
        self.refresh_account_list(keep_selection=True)

    def stop_all(self):
        self.account_manager.stop_all()
        self.refresh_account_list(keep_selection=True)

    # --- Account editing dialogs (dark themed) ---
    def add_account_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Account")
        dialog.geometry("400x200")
        dialog.configure(bg='#000000')
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        name_entry = ttk.Entry(dialog, width=30)
        name_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(dialog, text="Token:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        token_entry = ttk.Entry(dialog, width=50, show="*")
        token_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(dialog, text="Notes:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        notes_entry = ttk.Entry(dialog, width=50)
        notes_entry.grid(row=2, column=1, padx=5, pady=5)

        def save():
            name = name_entry.get().strip()
            token = token_entry.get().strip()
            notes = notes_entry.get().strip()
            if not name or not token:
                messagebox.showerror("Error", "Name and token required.")
                return
            self.account_manager.add_account(name, token, True, notes)
            self.refresh_account_list(keep_selection=False)
            dialog.destroy()

        ttk.Button(dialog, text="Save", command=save).grid(row=3, column=0, pady=10)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).grid(row=3, column=1, pady=10)

    def edit_selected_account(self):
        selected = self.get_selected_accounts()
        if len(selected) != 1:
            messagebox.showinfo("Select One", "Select exactly one account.")
            return
        acc = selected[0]

        dialog = tk.Toplevel(self.root)
        dialog.title(f"Edit {acc.name}")
        dialog.geometry("400x220")
        dialog.configure(bg='#000000')
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        name_entry = ttk.Entry(dialog, width=30)
        name_entry.insert(0, acc.name)
        name_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(dialog, text="Token:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        token_entry = ttk.Entry(dialog, width=50, show="*")
        token_entry.insert(0, acc.token)
        token_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(dialog, text="Notes:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        notes_entry = ttk.Entry(dialog, width=50)
        notes_entry.insert(0, acc.notes)
        notes_entry.grid(row=2, column=1, padx=5, pady=5)

        enabled_var = tk.BooleanVar(value=acc.enabled)
        ttk.Checkbutton(dialog, text="Enabled", variable=enabled_var).grid(row=3, column=0, columnspan=2, pady=5)

        def save():
            acc.name = name_entry.get().strip()
            acc.token = token_entry.get().strip()
            acc.notes = notes_entry.get().strip()
            acc.enabled = enabled_var.get()
            self.account_manager.save_accounts()
            self.refresh_account_list(keep_selection=False)
            dialog.destroy()

        ttk.Button(dialog, text="Save", command=save).grid(row=4, column=0, pady=10)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).grid(row=4, column=1, pady=10)

    def delete_selected_account(self):
        selected = self.get_selected_accounts()
        if not selected:
            return
        names = ', '.join(a.name for a in selected)
        if messagebox.askyesno("Confirm Delete", f"Delete {names}?"):
            for acc in selected:
                self.account_manager.remove_account(acc.name)
            self.refresh_account_list(keep_selection=False)

    # --- Quest Tab ---
    def build_quest_tab(self):
        frame = ttk.Frame(self.tab_quest, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Quest Helper", font=('Helvetica', 14)).pack(anchor=tk.W)
        ttk.Label(frame, text="(Select accounts and run)", foreground='#888888').pack(anchor=tk.W, pady=(0,10))

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="Run on Selected", command=self.run_quest_selected).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Run on All Running", command=self.run_quest_all_running).pack(side=tk.LEFT, padx=2)

        self.quest_log = scrolledtext.ScrolledText(frame, height=15, bg='#1a1a1a', fg='#e0e0e0',
                                                   insertbackground='white', font=('Courier', 9))
        self.quest_log.pack(fill=tk.BOTH, expand=True, pady=10)
        self.quest_log.tag_config('info', foreground='#00ff00')
        self.quest_log.tag_config('error', foreground='#ff5555')

    def run_quest_selected(self):
        accounts = self.get_selected_accounts()
        if not accounts:
            messagebox.showinfo("No Selection", "Select accounts in the Accounts tab.")
            return
        threading.Thread(target=self._run_quest_thread, args=(accounts,), daemon=True).start()

    def run_quest_all_running(self):
        running = self.account_manager.get_running_instances()
        if not running:
            messagebox.showinfo("No Running", "No instances are running.")
            return
        threading.Thread(target=self._run_quest_thread, args=(running,), daemon=True).start()

    def _run_quest_thread(self, accounts):
        from discord_quest_helper import DiscordInjector
        for acc in accounts:
            self.quest_log_insert(f"🎮 Processing {acc.name}...\n", 'info')
            time.sleep(self.config.get("injection_delay", 15))
            injector = DiscordInjector(debug_port=acc.debug_port, config=self.config)
            try:
                if not injector.connect():
                    self.quest_log_insert(f"❌ Could not connect\n", 'error')
                    continue
                script_path = Path(__file__).parent / "discord_quest_helper" / "quest_helper.js"
                with open(script_path, 'r', encoding='utf-8') as f:
                    script = f.read()
                if injector.inject_script(script):
                    self.quest_log_insert(f"✅ Injected\n", 'info')
                else:
                    self.quest_log_insert(f"❌ Injection failed\n", 'error')
            except Exception as e:
                self.quest_log_insert(f"❌ Error: {e}\n", 'error')
            finally:
                injector.close()
        self.quest_log_insert("✅ Done.\n", 'info')

    def quest_log_insert(self, text, tag=None):
        self.quest_log.insert(tk.END, text, tag)
        self.quest_log.see(tk.END)
        self.quest_log.update_idletasks()

    # --- Settings Tab (fixed grid layout) ---
    def build_settings_tab(self):
        frame = ttk.Frame(self.tab_settings, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # Title – placed with grid (row 0)
        ttk.Label(frame, text="Settings", font=('Helvetica', 14)).grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=(0,10)
        )

        fields = [
            ("Discord Path", "discord_path", "/Applications/Discord.app"),
            ("Executable", "discord_executable", "Discord"),
            ("Max Instances", "max_instances", 3),
            ("Instance Delay (s)", "instance_delay", 5),
            ("Injection Delay (s)", "injection_delay", 15),
        ]

        self.entries = {}
        for i, (label, key, default) in enumerate(fields):
            # Row = i+1 (because row 0 is taken by the title)
            ttk.Label(frame, text=label).grid(
                row=i+1, column=0, sticky=tk.W, pady=2
            )
            var = tk.StringVar(value=str(self.config.get(key, default)))
            self.entries[key] = var
            ttk.Entry(frame, textvariable=var, width=30).grid(
                row=i+1, column=1, sticky=tk.W, pady=2
            )

        # Checkbox
        self.auto_login_var = tk.BooleanVar(value=self.config.get("auto_login", False))
        ttk.Checkbutton(
            frame, text="Auto‑login after launch", variable=self.auto_login_var
        ).grid(row=len(fields)+1, column=0, columnspan=2, sticky=tk.W, pady=5)

        # Save button
        ttk.Button(frame, text="Save", command=self.save_settings).grid(
            row=len(fields)+2, column=0, pady=10
        )

    def save_settings(self):
        for key, var in self.entries.items():
            val = var.get()
            if val.isdigit():
                self.config[key] = int(val)
            elif val.lower() in ('true', 'false'):
                self.config[key] = val.lower() == 'true'
            else:
                self.config[key] = val
        self.config['auto_login'] = self.auto_login_var.get()
        with open("config.json", 'w') as f:
            json.dump(self.config, f, indent=4)
        messagebox.showinfo("Saved", "Settings saved.")

    # --- Utility ---
    def update_clock(self):
        tz = pytz.timezone('America/Los_Angeles')
        now = datetime.now(tz)
        self.time_label.config(text=f"PDT: {now.strftime('%I:%M %p')}")
        self.root.after(1000, self.update_clock)

    def update_status(self):
        if self.auto_refresh.get():
            self.refresh_account_list(keep_selection=True)
        running = len(self.account_manager.get_running_instances())
        total = len(self.account_manager.accounts)
        self.root.title(f"Discord Multi‑Tool [{running}/{total}]")
        self.root.after(2000, self.update_status)

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Stop all instances?"):
            self.account_manager.stop_all()
            self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = DiscordMultiGUI(root)
    root.mainloop()