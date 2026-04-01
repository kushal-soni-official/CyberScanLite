"""Main window for CyberScan Lite."""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from datetime import datetime
import os
import sys
import socket

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scanner.ping import ping_host
from scanner.tcp_scanner import TCPScanner
from scanner.service_detector import ServiceDetector
from scanner.os_fingerprinter import OSFingerprinter
from reporting.json_exporter import export_json
from reporting.html_exporter import export_html
from gui.widgets import ToolTip
from gui.advanced_frame import AdvancedFrame

import ttkbootstrap as tb
from ttkbootstrap.constants import *

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("CyberScan Lite")
        self.root.geometry("1000x700")

        # Style using ttkbootstrap
        self.style = tb.Style(theme="darkly")

        # Variables
        self.target_var = tk.StringVar()
        self.start_port_var = tk.IntVar(value=1)
        self.end_port_var = tk.IntVar(value=1024)
        self.advanced_visible = tk.BooleanVar(value=False)

        # Control
        self.stop_event = threading.Event()
        self.scan_thread = None
        self.start_time = None

        # Create the main frame
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=BOTH, expand=True)

        # Target entry
        target_frame = ttk.Frame(main_frame)
        target_frame.pack(fill=X, pady=5)
        ttk.Label(target_frame, text="Target:").pack(side=LEFT, padx=5)
        self.target_entry = ttk.Entry(target_frame, textvariable=self.target_var, width=30)
        self.target_entry.pack(side=LEFT, padx=5)
        ToolTip(self.target_entry, "Enter an IP address (e.g., 192.168.1.1) or domain name (e.g., google.com)")

        # Port range
        port_frame = ttk.Frame(main_frame)
        port_frame.pack(fill=X, pady=5)
        ttk.Label(port_frame, text="Port range:").pack(side=LEFT, padx=5)
        self.start_spin = ttk.Spinbox(port_frame, from_=1, to=65535, textvariable=self.start_port_var, width=6)
        self.start_spin.pack(side=LEFT, padx=2)
        ttk.Label(port_frame, text="-").pack(side=LEFT, padx=2)
        self.end_spin = ttk.Spinbox(port_frame, from_=1, to=65535, textvariable=self.end_port_var, width=6)
        self.end_spin.pack(side=LEFT, padx=2)
        ToolTip(self.start_spin, "Start port (1-65535)")
        ToolTip(self.end_spin, "End port (1-65535)")

        # Advanced toggle
        self.advanced_check = ttk.Checkbutton(main_frame, text="Show advanced options", variable=self.advanced_visible,
                                              command=self.toggle_advanced)
        self.advanced_check.pack(anchor=W, pady=5)

        # Advanced frame (initially hidden)
        self.advanced_frame = AdvancedFrame(main_frame)
        # We'll pack it later when toggled

        # Buttons frame
        self.btn_frame = ttk.Frame(main_frame)
        self.btn_frame.pack(fill=X, pady=10)

        self.scan_btn = ttk.Button(self.btn_frame, text="Start Scan", command=self.start_scan, bootstyle=SUCCESS)
        self.scan_btn.pack(side=LEFT, padx=5)

        self.stop_btn = ttk.Button(self.btn_frame, text="Stop", command=self.stop_scan, bootstyle=DANGER, state=DISABLED)
        self.stop_btn.pack(side=LEFT, padx=5)

        # Progress bar and timer
        self.progress = ttk.Progressbar(main_frame, orient=HORIZONTAL, length=400, mode='determinate')
        self.progress.pack(fill=X, pady=5)

        self.timer_label = ttk.Label(main_frame, text="Elapsed: 0s")
        self.timer_label.pack(anchor=W, pady=2)

        # Results treeview
        results_frame = ttk.LabelFrame(main_frame, text="Results", padding=5)
        results_frame.pack(fill=BOTH, expand=True, pady=10)

        # After creating the treeview, configure columns
        columns = ("port", "service", "version", "os")
        self.tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=15)

        # Configure each column
        self.tree.heading("port", text="Port", anchor='center')
        self.tree.heading("service", text="Service", anchor='center')
        self.tree.heading("version", text="Version", anchor='center')
        self.tree.heading("os", text="OS", anchor='center')

        self.tree.column("port", width=80, anchor='center')
        self.tree.column("service", width=150, anchor='center')
        self.tree.column("version", width=250, anchor='center')
        self.tree.column("os", width=200, anchor='center')

        scrollbar = ttk.Scrollbar(results_frame, orient=VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

        # Export buttons
        export_frame = ttk.Frame(main_frame)
        export_frame.pack(fill=X, pady=5)
        self.json_btn = ttk.Button(export_frame, text="Export as JSON", command=self.export_json, state=DISABLED)
        self.json_btn.pack(side=LEFT, padx=5)
        self.html_btn = ttk.Button(export_frame, text="Export as HTML", command=self.export_html, state=DISABLED)
        self.html_btn.pack(side=LEFT, padx=5)

        # Data storage
        self.results = []  # list of dicts: port, service, version, os

        # No timer update here; it starts when scan starts

    def toggle_advanced(self):
        if self.advanced_visible.get():
            self.advanced_frame.pack(fill=X, pady=5, before=self.btn_frame)
        else:
            self.advanced_frame.pack_forget()

    def start_scan(self):
        # Validate inputs
        target = self.target_var.get().strip()
        if not target:
            messagebox.showerror("Error", "Please enter a target.")
            return

        start = self.start_port_var.get()
        end = self.end_port_var.get()
        if start < 1 or end > 65535 or start > end:
            messagebox.showerror("Error", "Invalid port range.")
            return

        # Ping check
        reachable, ttl = ping_host(target)
        if not reachable:
            reply = messagebox.askyesno("Host unreachable",
                                        f"The host {target} did not respond to ping. Continue scanning anyway?")
            if not reply:
                return

        # Prepare UI
        self.scan_btn.config(state=DISABLED)
        self.stop_btn.config(state=NORMAL)
        self.json_btn.config(state=DISABLED)
        self.html_btn.config(state=DISABLED)
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.results.clear()
        self.progress['value'] = 0

        # Get advanced options
        concurrency = self.advanced_frame.get_concurrency() if self.advanced_visible.get() else 100
        timing = self.advanced_frame.get_timing() if self.advanced_visible.get() else 0.1

        # Reset stop event
        self.stop_event.clear()
        self.start_time = time.time()

        # Run scanner in thread
        self.scan_thread = threading.Thread(target=self.run_scan,
                                            args=(target, start, end, concurrency, timing),
                                            daemon=True)
        self.scan_thread.start()

        # Start updating timer
        self.update_progress()

    def run_scan(self, target, start_port, end_port, concurrency, timing):
        # Resolve hostname
        try:
            ip = socket.gethostbyname(target)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Resolution Error", f"Could not resolve {target}: {e}"))
            self.scan_done()
            return

        scanner = TCPScanner(ip, start_port, end_port, concurrency, timing, self.stop_event)
        scanner.run(progress_callback=self.on_progress, result_callback=self.on_result)
        self.scan_done()

    def on_progress(self, current, total):
        """Callback from scanner to update progress bar."""
        percent = (current / total) * 100 if total > 0 else 0
        self.root.after(0, lambda: self.progress.configure(value=percent))

    def on_result(self, port, service, version):
        """Callback from scanner when a port is found."""
        # Append to results
        self.results.append({
            "port": port,
            "service": service,
            "version": version,
            "os": ""  # OS guess will be added after scan
        })
        # Insert into treeview
        self.root.after(0, lambda: self.tree.insert("", "end", values=(port, service, version, "pending")))

    def scan_done(self):
        """Called when scan finishes or is stopped."""
        self.scan_btn.config(state=NORMAL)
        self.stop_btn.config(state=DISABLED)
        self.json_btn.config(state=NORMAL if self.results else DISABLED)
        self.html_btn.config(state=NORMAL if self.results else DISABLED)
        # Perform OS fingerprint on first open port
        if self.results:
            # Get IP from target (we stored it in run_scan, but we can re‑resolve)
            try:
                ip = socket.gethostbyname(self.target_var.get().strip())
            except:
                ip = None
            if ip:
                # Use the first open port
                open_port = self.results[0]["port"]
                fingerprinter = OSFingerprinter()
                os_guess = fingerprinter.guess_os(ip, open_port)
                # Update treeview with OS for all rows
                for item in self.tree.get_children():
                    self.tree.set(item, "os", os_guess)
                for r in self.results:
                    r["os"] = os_guess

    def stop_scan(self):
        self.stop_event.set()
        self.stop_btn.config(state=DISABLED)
        # The scan thread will exit soon; scan_done will be called when scanner.run() returns.

    def update_progress(self):
        """Update the elapsed time label."""
        if self.scan_thread and self.scan_thread.is_alive():
            elapsed = int(time.time() - self.start_time) if self.start_time else 0
            self.timer_label.config(text=f"Elapsed: {elapsed}s")
            self.root.after(1000, self.update_progress)
        else:
            # Scan done, final elapsed
            if self.start_time:
                elapsed = int(time.time() - self.start_time)
                self.timer_label.config(text=f"Elapsed: {elapsed}s")

    def export_json(self):
        if not self.results:
            return
        filename = f"cyberscan_{self.target_var.get().strip()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        from tkinter import filedialog
        file_path = filedialog.asksaveasfilename(defaultextension=".json", initialfile=filename,
                                                 filetypes=[("JSON files", "*.json")])
        if file_path:
            target = self.target_var.get().strip()
            start = self.start_port_var.get()
            end = self.end_port_var.get()
            os_guess = self.results[0]["os"] if self.results else "Unknown"
            export_json(self.results, target, start, end, os_guess, file_path)
            messagebox.showinfo("Export", f"JSON exported to {file_path}")

    def export_html(self):
        if not self.results:
            return
        filename = f"cyberscan_{self.target_var.get().strip()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        from tkinter import filedialog
        file_path = filedialog.asksaveasfilename(defaultextension=".html", initialfile=filename,
                                                 filetypes=[("HTML files", "*.html")])
        if file_path:
            target = self.target_var.get().strip()
            start = self.start_port_var.get()
            end = self.end_port_var.get()
            os_guess = self.results[0]["os"] if self.results else "Unknown"
            export_html(self.results, target, start, end, os_guess, file_path)
            messagebox.showinfo("Export", f"HTML report saved to {file_path}")
