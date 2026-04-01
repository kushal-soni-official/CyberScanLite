#!/usr/bin/env python3
"""Entry point for CyberScan Lite."""

import tkinter as tk
from gui.main_window import MainWindow

def main():
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()
