"""Advanced options frame."""

import tkinter as tk
from tkinter import ttk

class AdvancedFrame(ttk.Frame):
    """Frame that holds advanced options: timing and concurrency."""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        # Timing template
        ttk.Label(self, text="Timing template:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.timing_var = tk.StringVar(value="normal")
        timing_combo = ttk.Combobox(self, textvariable=self.timing_var,
                                    values=["paranoid", "sneaky", "polite", "normal", "aggressive", "insane"],
                                    state="readonly")
        timing_combo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # Concurrency (threads)
        ttk.Label(self, text="Concurrency (max threads):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.concurrency_var = tk.IntVar(value=100)
        concurrency_spin = ttk.Spinbox(self, from_=1, to=500, textvariable=self.concurrency_var, width=8)
        concurrency_spin.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        self.columnconfigure(1, weight=1)

    def get_timing(self):
        """Return the selected timing delay in seconds."""
        mapping = {
            "paranoid": 5,
            "sneaky": 1,
            "polite": 0.5,
            "normal": 0.1,
            "aggressive": 0.02,
            "insane": 0
        }
        return mapping.get(self.timing_var.get(), 0.1)

    def get_concurrency(self):
        return self.concurrency_var.get()
