"""Tkinter UI for the Emboita Sync Agent — shows live sync progress/logs and
lets staff configure the cloud connection, API key, and ZK device list.
"""
import queue
import threading
import time
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

from agent import config as config_module
from agent import db
from agent.sync_engine import push_batch, sync_all

LOG_COLORS = {"info": "#94a3b8", "success": "#4ade80", "warn": "#fbbf24", "error": "#f87171"}


class SyncAgentApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Emboita Sync Agent")
        self.root.geometry("760x540")
        self.root.minsize(620, 420)

        self.config = config_module.load_config()
        self.log_queue = queue.Queue()
        self.sync_thread = None
        self.stop_event = threading.Event()

        self._build_ui()
        self._drain_log_queue()

        db.init_db()
        self._log_callback(datetime.now(), "info", "Emboita Sync Agent started.")
        if self.config.get("api_key") and self.config.get("devices"):
            self.start_loop()
        else:
            self._log_callback(datetime.now(), "warn", "Not configured yet — open Settings to add your API key and device(s).")

    # ---- UI construction ----
    def _build_ui(self):
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill="x")

        ttk.Label(top, text="Status:", font=("Segoe UI", 10, "bold")).pack(side="left")
        self.status_var = tk.StringVar(value="Idle")
        ttk.Label(top, textvariable=self.status_var, foreground="#334155").pack(side="left", padx=(4, 20))

        self.next_run_var = tk.StringVar(value="")
        ttk.Label(top, textvariable=self.next_run_var, foreground="#64748b").pack(side="left")

        btns = ttk.Frame(top)
        btns.pack(side="right")
        ttk.Button(btns, text="Sync Now", command=self.sync_now).pack(side="left", padx=4)
        ttk.Button(btns, text="Settings", command=self.open_settings).pack(side="left", padx=4)

        log_frame = ttk.Frame(self.root, padding=(10, 0, 10, 10))
        log_frame.pack(fill="both", expand=True)

        self.log_text = tk.Text(
            log_frame,
            wrap="word",
            state="disabled",
            bg="#0f172a",
            fg="#e2e8f0",
            insertbackground="#e2e8f0",
            font=("Consolas", 9),
            padx=8,
            pady=8,
        )
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for level, color in LOG_COLORS.items():
            self.log_text.tag_configure(level, foreground=color)

    def _append_log(self, when, level, message):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"[{when.strftime('%H:%M:%S')}] {message}\n", level)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _log_callback(self, when, level, message):
        self.log_queue.put((when, level, message))

    def _drain_log_queue(self):
        try:
            while True:
                when, level, message = self.log_queue.get_nowait()
                self._append_log(when, level, message)
        except queue.Empty:
            pass
        self.root.after(200, self._drain_log_queue)

    # ---- sync control ----
    def sync_now(self):
        threading.Thread(target=self._run_once, daemon=True).start()

    def _run_once(self):
        self.status_var.set("Syncing…")
        try:
            sync_all(self.config, log_callback=self._log_callback)
        finally:
            self.status_var.set("Idle")

    def start_loop(self):
        if self.sync_thread and self.sync_thread.is_alive():
            return
        self.stop_event.clear()
        self.sync_thread = threading.Thread(target=self._loop, daemon=True)
        self.sync_thread.start()

    def stop_loop(self):
        self.stop_event.set()

    def _loop(self):
        while not self.stop_event.is_set():
            self.status_var.set("Syncing…")
            try:
                sync_all(self.config, log_callback=self._log_callback)
            except Exception as exc:
                self._log_callback(datetime.now(), "error", f"Unexpected error: {exc}")
            self.status_var.set("Idle")

            interval = max(1, int(self.config.get("sync_interval_minutes", 5))) * 60
            for remaining in range(interval, 0, -1):
                if self.stop_event.is_set():
                    self.next_run_var.set("")
                    return
                mins, secs = divmod(remaining, 60)
                self.next_run_var.set(f"Next sync in {mins:02d}:{secs:02d}")
                time.sleep(1)
        self.next_run_var.set("")

    # ---- settings ----
    def open_settings(self):
        SettingsWindow(self.root, self.config, on_save=self._on_settings_saved)

    def _on_settings_saved(self, new_config):
        self.config = new_config
        config_module.save_config(new_config)
        self._log_callback(datetime.now(), "info", "Settings saved.")
        self.stop_loop()
        if self.config.get("api_key") and self.config.get("devices"):
            self.start_loop()


class SettingsWindow(tk.Toplevel):
    def __init__(self, parent, config, on_save):
        super().__init__(parent)
        self.title("Settings")
        self.geometry("540x520")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.devices = list(config.get("devices", []))
        self.on_save = on_save

        pad = {"padx": 12, "pady": 6}

        ttk.Label(self, text="Cloud URL").grid(row=0, column=0, sticky="w", **pad)
        self.cloud_url_var = tk.StringVar(value=config.get("cloud_url", ""))
        ttk.Entry(self, textvariable=self.cloud_url_var, width=42).grid(row=0, column=1, columnspan=2, **pad)

        ttk.Label(self, text="API Key").grid(row=1, column=0, sticky="w", **pad)
        self.api_key_var = tk.StringVar(value=config.get("api_key", ""))
        self.api_key_entry = ttk.Entry(self, textvariable=self.api_key_var, width=42, show="•")
        self.api_key_entry.grid(row=1, column=1, **pad)
        self.show_key = tk.BooleanVar(value=False)
        ttk.Checkbutton(self, text="Show", variable=self.show_key, command=self._toggle_key_visibility).grid(
            row=1, column=2, **pad
        )

        ttk.Label(self, text="Sync Interval (minutes)").grid(row=2, column=0, sticky="w", **pad)
        self.interval_var = tk.StringVar(value=str(config.get("sync_interval_minutes", 5)))
        ttk.Entry(self, textvariable=self.interval_var, width=10).grid(row=2, column=1, sticky="w", **pad)

        ttk.Button(self, text="Test Connection", command=self._test_connection).grid(row=3, column=1, sticky="w", **pad)
        self.test_result_var = tk.StringVar(value="")
        ttk.Label(self, textvariable=self.test_result_var, foreground="#334155", wraplength=460).grid(
            row=4, column=0, columnspan=3, sticky="w", **pad
        )

        ttk.Separator(self).grid(row=5, column=0, columnspan=3, sticky="ew", pady=8)
        ttk.Label(self, text="Devices", font=("Segoe UI", 9, "bold")).grid(row=6, column=0, sticky="w", **pad)

        self.device_list = tk.Listbox(self, height=7, width=58)
        self.device_list.grid(row=7, column=0, columnspan=3, padx=12)
        self._refresh_device_list()

        device_btns = ttk.Frame(self)
        device_btns.grid(row=8, column=0, columnspan=3, pady=6)
        ttk.Button(device_btns, text="Add Device", command=self._add_device).pack(side="left", padx=4)
        ttk.Button(device_btns, text="Remove Selected", command=self._remove_device).pack(side="left", padx=4)

        footer = ttk.Frame(self)
        footer.grid(row=9, column=0, columnspan=3, pady=16)
        ttk.Button(footer, text="Cancel", command=self.destroy).pack(side="left", padx=6)
        ttk.Button(footer, text="Save", command=self._save).pack(side="left", padx=6)

    def _toggle_key_visibility(self):
        self.api_key_entry.configure(show="" if self.show_key.get() else "•")

    def _refresh_device_list(self):
        self.device_list.delete(0, "end")
        for d in self.devices:
            type_label = "Hikvision" if d.get("type", "zkteco") == "hikvision" else "ZKTeco"
            default_port = 80 if type_label == "Hikvision" else 4370
            self.device_list.insert("end", f"{d['name']}  —  {type_label}  —  {d['ip']}:{d.get('port', default_port)}")

    def _add_device(self):
        DeviceDialog(self, on_add=self._on_device_added)

    def _on_device_added(self, device):
        self.devices.append(device)
        self._refresh_device_list()

    def _remove_device(self):
        selection = self.device_list.curselection()
        if not selection:
            return
        del self.devices[selection[0]]
        self._refresh_device_list()

    def _test_connection(self):
        self.test_result_var.set("Testing…")
        self.update_idletasks()
        ok, result = push_batch(self.cloud_url_var.get(), self.api_key_var.get(), "Settings Connection Test", None, [], [])
        self.test_result_var.set(
            f"✓ Connected successfully: {result.get('detail', 'OK')}" if ok else f"✗ Failed: {result}"
        )

    def _save(self):
        try:
            interval = max(1, int(self.interval_var.get()))
        except ValueError:
            messagebox.showerror("Invalid interval", "Sync interval must be a whole number of minutes.")
            return
        new_config = {
            "cloud_url": self.cloud_url_var.get().strip(),
            "api_key": self.api_key_var.get().strip(),
            "sync_interval_minutes": interval,
            "devices": self.devices,
        }
        self.on_save(new_config)
        self.destroy()


class DeviceDialog(tk.Toplevel):
    def __init__(self, parent, on_add):
        super().__init__(parent)
        self.title("Add Device")
        self.geometry("320x340")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.on_add = on_add

        pad = {"padx": 12, "pady": 6}
        ttk.Label(self, text="Name").grid(row=0, column=0, sticky="w", **pad)
        self.name_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.name_var).grid(row=0, column=1, **pad)

        ttk.Label(self, text="Type").grid(row=1, column=0, sticky="w", **pad)
        self.type_var = tk.StringVar(value="ZKTeco")
        type_combo = ttk.Combobox(
            self, textvariable=self.type_var, values=["ZKTeco", "Hikvision"], state="readonly", width=17
        )
        type_combo.grid(row=1, column=1, **pad)
        type_combo.bind("<<ComboboxSelected>>", self._on_type_changed)

        ttk.Label(self, text="IP Address").grid(row=2, column=0, sticky="w", **pad)
        self.ip_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.ip_var).grid(row=2, column=1, **pad)

        ttk.Label(self, text="Port").grid(row=3, column=0, sticky="w", **pad)
        self.port_var = tk.StringVar(value="4370")
        ttk.Entry(self, textvariable=self.port_var).grid(row=3, column=1, **pad)

        self.username_label = ttk.Label(self, text="Username")
        self.username_var = tk.StringVar(value="admin")
        self.username_entry = ttk.Entry(self, textvariable=self.username_var)

        self.password_label = ttk.Label(self, text="Password")
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(self, textvariable=self.password_var, show="•")

        footer = ttk.Frame(self)
        footer.grid(row=6, column=0, columnspan=2, pady=16)
        ttk.Button(footer, text="Cancel", command=self.destroy).pack(side="left", padx=6)
        ttk.Button(footer, text="Add", command=self._add).pack(side="left", padx=6)

    def _on_type_changed(self, _event=None):
        pad = {"padx": 12, "pady": 6}
        if self.type_var.get() == "Hikvision":
            self.port_var.set("80")
            self.username_label.grid(row=4, column=0, sticky="w", **pad)
            self.username_entry.grid(row=4, column=1, **pad)
            self.password_label.grid(row=5, column=0, sticky="w", **pad)
            self.password_entry.grid(row=5, column=1, **pad)
        else:
            self.port_var.set("4370")
            self.username_label.grid_remove()
            self.username_entry.grid_remove()
            self.password_label.grid_remove()
            self.password_entry.grid_remove()

    def _add(self):
        name = self.name_var.get().strip()
        ip = self.ip_var.get().strip()
        if not name or not ip:
            messagebox.showerror("Missing fields", "Name and IP address are required.")
            return
        is_hikvision = self.type_var.get() == "Hikvision"
        try:
            port = int(self.port_var.get())
        except ValueError:
            port = 80 if is_hikvision else 4370
        device = {"name": name, "type": "hikvision" if is_hikvision else "zkteco", "ip": ip, "port": port}
        if is_hikvision:
            device["username"] = self.username_var.get().strip() or "admin"
            device["password"] = self.password_var.get()
        self.on_add(device)
        self.destroy()
